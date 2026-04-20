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
    """Complete PDF Evaluation View - End-to-End Implementation"""
    
    def post(self, request):
        """
        Handle PDF evaluation with OCR and NLP
        Expected flow:
        1. Extract text using OCR (PyMuPDF → Vision → Tesseract)
        2. Extract questions using NLP (Claude API → Regex fallback)
        3. Evaluate answers if answer_key provided
        4. Return comprehensive analysis
        """
        temp_file_path = None
        try:
            # Step 1: Validate file upload
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
                            'suggestion': 'Try uploading a text-based PDF or ensure the PDF contains extractable text'
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
                            # For demo, we'll use the question text as student answer
                            # In real implementation, this would come from form submission
                            student_answer = question_text  # Placeholder
                            
                            evaluation = evaluate_answer(question_text, correct_answer, student_answer)
                            evaluation_results.append({
                                'question_number': i + 1,
                                'question': question_text,
                                'correct_answer': correct_answer,
                                'student_answer': student_answer,
                                'evaluation': evaluation
                            })
                    
                    answer_evaluation = {
                        'total_questions': len(questions),
                        'evaluated_answers': len(evaluation_results),
                        'results': evaluation_results,
                        'average_score': sum(r['evaluation']['score'] for r in evaluation_results) / len(evaluation_results) if evaluation_results else 0
                    }
                    
                except json.JSONDecodeError:
                    logger.warning("Invalid answer_key format")
                    answer_evaluation = {'error': 'Invalid answer_key format'}
            
            # Step 7: Return comprehensive response
            response_data = {
                'success': True,
                'file_name': file.name,
                'extraction': {
                    'text': extracted_text,
                    'method': ocr_result.get('method', 'unknown'),
                    'confidence': ocr_result.get('confidence', 0),
                    'pages': ocr_result.get('pages', 0)
                },
                'questions': {
                    'count': len(questions),
                    'extracted': questions
                },
                'analysis': text_analysis,
                'evaluation': answer_evaluation,
                'processing_steps': [
                    'file_validation',
                    'ocr_extraction',
                    'question_extraction',
                    'text_analysis',
                    'answer_evaluation' if answer_key else 'skipped'
                ]
            }
            
            logger.info(f"PDF evaluation completed: {len(extracted_text)} chars, {len(questions)} questions")
            
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"PDF evaluation error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Evaluation failed: {str(e)}',
                'step': 'general_error'
            }, status=500)
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"Cleaned up temporary file: {temp_file_path}")
                except OSError:
                    logger.warning(f"Failed to clean up temp file: {temp_file_path}")
    
    def get(self, request):
        """
        Get API information and available methods
        """
        try:
            from .ocr_engine import ocr_engine
            from .nlp_engine import nlp_engine
            
            return JsonResponse({
                'message': 'ExamAutoPro PDF Evaluation API',
                'version': '2.0',
                'endpoints': {
                    'post': '/api/evaluate-pdf/',
                    'method': 'POST',
                    'content_type': 'multipart/form-data'
                },
                'parameters': {
                    'file': 'PDF file to evaluate (required)',
                    'answer_key': 'JSON string with correct answers (optional)'
                },
                'available_methods': {
                    'ocr': ocr_engine.get_available_methods(),
                    'nlp': nlp_engine.get_available_methods()
                },
                'example_usage': {
                    'curl': 'curl -X POST http://127.0.0.1:8000/api/evaluate-pdf/ -F "file=@sample.pdf" -F "answer_key={\"Q1\":\"Paris\"}"',
                    'javascript': '''
                        async function evaluatePDF(file) {
                            const formData = new FormData();
                            formData.append("file", file);
                            formData.append("answer_key", JSON.stringify({"Q1": "Paris"}));
                            
                            const response = await fetch("/api/evaluate-pdf/", {
                                method: "POST",
                                body: formData
                            });
                            
                            const data = await response.json();
                            console.log(data);
                        }
                    '''
                }
            })
            
        except Exception as e:
            logger.error(f"API info error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


# Add method decorator import
from django.utils.decorators import method_decorator
from django.urls import path
from . import views

app_name = 'examapp'

urlpatterns = [
    # PDF Evaluation API
    path('api/evaluate-pdf/', views.EvaluatePDFView.as_view(), name='evaluate_pdf'),
]
