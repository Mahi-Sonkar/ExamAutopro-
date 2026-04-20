"""
Exam App Views - Tab 2 Implementation
Complete end-to-end PDF evaluation with OCR and NLP
"""

import os
import json
import tempfile
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils.decorators import method_decorator

# Import our custom engines
from .ocr_engine import extract_text_from_pdf, extract_text_from_pdf_bytes
from .nlp_engine import extract_questions, evaluate_answer, analyze_text

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class EvaluatePDFView(View):
    """Complete end-to-end PDF evaluation API"""
    
    def post(self, request):
        """Handle PDF upload and evaluation"""
        try:
            # Step 1: Validate request
            logger.info("Starting PDF evaluation process")
            
            if 'file' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'No file uploaded',
                    'step': 'file_validation'
                }, status=400)
            
            file = request.FILES['file']
            answer_key = request.POST.get('answer_key', '')
            
            # Validate file type
            if not file.name.lower().endswith('.pdf'):
                return JsonResponse({
                    'success': False,
                    'error': 'Only PDF files are supported',
                    'step': 'file_validation'
                }, status=400)
            
            # Step 2: Save file temporarily
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            temp_dir = os.path.join(media_root, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            _, ext = os.path.splitext(file.name)
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext or '.pdf', dir=temp_dir) as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
                temp_file_path = destination.name
            
            # Step 3: Validate file and extract text using OCR
            logger.info(f"Starting OCR extraction for {file.name}")
            
            # Validate file content before processing
            try:
                # Check if file is actually a PDF
                file_header = open(temp_file_path, 'rb').read(4)
                if not file_header.startswith(b'%PDF'):
                    logger.warning(f"File {file.name} is not a valid PDF")
                    # Try to read as text file
                    try:
                        with open(temp_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text_content = f.read()
                            if text_content.strip():
                                extracted_text = text_content
                                ocr_method = 'Direct Text Read'
                                logger.info(f"Extracted {len(extracted_text)} characters via direct read")
                            else:
                                return JsonResponse({
                                    'success': False,
                                    'error': 'File appears to be empty',
                                    'step': 'file_validation',
                                    'file_type': 'text'
                                }, status=400)
                    except Exception as e:
                        logger.error(f"Direct text read failed: {e}")
                        return JsonResponse({
                            'success': False,
                            'error': f'Failed to read text file: {str(e)}',
                            'step': 'text_extraction',
                            'file_type': 'text'
                        }, status=500)
                else:
                    # Valid PDF - use OCR
                    ocr_result = extract_text_from_pdf(temp_file_path)
                    
                    if not ocr_result.get('text') or len(ocr_result.get('text', '').strip()) == 0:
                        logger.warning(f"OCR extraction failed for {file.name}")
                        return JsonResponse({
                            'success': False,
                            'error': 'OCR failed - no text extracted from PDF',
                            'step': 'ocr_extraction',
                            'ocr_method': ocr_result.get('method', 'unknown'),
                            'ocr_error': ocr_result.get('error', 'Unknown error'),
                            'suggestion': 'Try uploading a text-based PDF or ensure that PDF contains extractable text'
                        }, status=500)
                    
                    extracted_text = ocr_result['text']
                    ocr_method = ocr_result.get('method', 'Unknown')
                    logger.info(f"OCR successful: {ocr_method} - {len(extracted_text)} characters")
                    
            except Exception as e:
                logger.error(f"File validation failed: {e}")
                return JsonResponse({
                    'success': False,
                    'error': f'File validation error: {str(e)}',
                    'step': 'file_validation',
                    'error_details': str(e)
                }, status=500)
            
            # Step 4: Extract questions using NLP
            logger.info("Starting question extraction")
            questions = extract_questions(extracted_text)
            logger.info(f"Extracted {len(questions)} questions")
            
            # Step 5: Analyze text complexity
            text_analysis = analyze_text(extracted_text)
            
            # Step 6: Evaluate answers if answer_key provided
            answer_evaluation = None
            if answer_key and questions:
                try:
                    answer_key_data = json.loads(answer_key)
                    logger.info("Starting answer evaluation")
                    
                    evaluation_results = []
                    for i, question in enumerate(questions):
                        question_text = question.get('question', '')
                        
                        # Find corresponding answer in answer_key
                        correct_answer = None
                        if isinstance(answer_key_data, dict):
                            correct_answer = answer_key_data.get(f'Q{i+1}') or answer_key_data.get(str(i+1))
                        elif isinstance(answer_key_data, list):
                            correct_answer = answer_key_data[i] if i < len(answer_key_data) else None
                        
                        if correct_answer:
                            student_answer = question.get('answer', '')
                            evaluation = evaluate_answer(student_answer, correct_answer, question_text)
                            evaluation_results.append({
                                'question_number': i + 1,
                                'question': question_text,
                                'student_answer': student_answer,
                                'correct_answer': correct_answer,
                                'evaluation': evaluation
                            })
                    
                    answer_evaluation = {
                        'total_questions': len(questions),
                        'evaluated_answers': len(evaluation_results),
                        'results': evaluation_results,
                        'summary': self._generate_evaluation_summary(evaluation_results)
                    }
                    
                except json.JSONDecodeError:
                    logger.warning("Invalid answer_key JSON format")
                    answer_evaluation = {'error': 'Invalid answer_key format'}
                except Exception as e:
                    logger.error(f"Answer evaluation failed: {e}")
                    answer_evaluation = {'error': str(e)}
            
            # Step 7: Build comprehensive response
            response_data = {
                'success': True,
                'file_name': file.name,
                'file_size': file.size,
                'extraction': {
                    'text': extracted_text,
                    'method': ocr_method,
                    'confidence': ocr_result.get('confidence', 0.0) if 'ocr_result' in locals() else 1.0,
                    'pages': ocr_result.get('pages', 1) if 'ocr_result' in locals() else 1
                },
                'questions': {
                    'count': len(questions),
                    'list': questions
                },
                'analysis': {
                    'word_count': len(extracted_text.split()),
                    'character_count': len(extracted_text),
                    'sentence_count': extracted_text.count('.') + extracted_text.count('!') + extracted_text.count('?'),
                    'complexity': text_analysis
                },
                'answer_evaluation': answer_evaluation,
                'processing_steps': [
                    'File upload and validation',
                    'Text extraction via ' + ocr_method,
                    'Question extraction using NLP',
                    'Text complexity analysis',
                    'Answer evaluation (if answer key provided)'
                ],
                'timestamp': str(timezone.now())
            }
            
            logger.info(f"Successfully processed {file.name}")
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"PDF evaluation failed: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Evaluation failed: {str(e)}',
                'step': 'general_error'
            }, status=500)
    
    def get(self, request):
        """Handle API info requests"""
        try:
            return JsonResponse({
                'success': True,
                'message': 'PDF Evaluation API - End-to-End Implementation',
                'version': '2.0',
                'features': {
                    'ocr_methods': ['PyMuPDF', 'Google Vision', 'Tesseract'],
                    'nlp_methods': ['Claude API', 'NLTK', 'Scikit-learn'],
                    'supported_formats': ['PDF'],
                    'max_file_size': '50MB',
                    'response_format': 'JSON'
                },
                'endpoints': {
                    'evaluate_pdf': '/core/api/evaluate-pdf/',
                    'upload': 'POST',
                    'info': 'GET'
                }
            })
            
        except Exception as e:
            logger.error(f"API info error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def _generate_evaluation_summary(self, evaluation_results):
        """Generate summary of evaluation results"""
        if not evaluation_results:
            return {'total': 0, 'correct': 0, 'accuracy': 0.0}
        
        total = len(evaluation_results)
        correct = sum(1 for result in evaluation_results if result['evaluation'].get('is_correct', False))
        accuracy = (correct / total) * 100 if total > 0 else 0.0
        
        return {
            'total': total,
            'correct': correct,
            'incorrect': total - correct,
            'accuracy': round(accuracy, 2)
        }


# Add method decorator import
from django.utils.decorators import method_decorator
from django.urls import path
from . import views

app_name = 'examapp'

urlpatterns = [
    # PDF Evaluation API
    path('api/evaluate-pdf/', views.EvaluatePDFView.as_view(), name='evaluate_pdf'),
]
