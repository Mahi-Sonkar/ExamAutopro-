"""
API Endpoints for Analysis System - ExamAutoPro
Main motive: RESTful API for backend analysis and processing
"""

import json
import logging
from typing import Dict, List, Optional
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
import os
import tempfile

try:
    from .analysis_engine import analysis_engine
except Exception as e:
    analysis_engine = None
    logger = logging.getLogger(__name__)
    logger.warning("analysis_engine unavailable at import time: %s", e)

try:
    from .processing_pipeline import processing_pipeline
except Exception as e:
    processing_pipeline = None
    logger = logging.getLogger(__name__)
    logger.warning("processing_pipeline unavailable at import time: %s", e)

try:
    from .batch_processor import batch_processor
except Exception as e:
    batch_processor = None
    logger = logging.getLogger(__name__)
    logger.warning("batch_processor unavailable at import time: %s", e)

try:
    from .question_analyzer_api import question_analyzer
except Exception as e:
    question_analyzer = None
    logger = logging.getLogger(__name__)
    logger.warning("question_analyzer unavailable at import time: %s", e)

try:
    from .ai_evaluator import ai_evaluator
except Exception as e:
    ai_evaluator = None
    logger = logging.getLogger(__name__)
    logger.warning("ai_evaluator unavailable at import time: %s", e)
from pdf_analysis.models import PDFDocument, PDFAnalysisResult

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class DocumentAnalysisAPI(View):
    """API for document analysis operations"""
    
    def post(self, request):
        """Start document analysis"""
        try:
            if analysis_engine is None:
                return JsonResponse({'error': 'Document analysis engine unavailable'}, status=503)
            data = json.loads(request.body)
            document_id = data.get('document_id')
            force_reanalyze = data.get('force_reanalyze', False)
            
            if not document_id:
                return JsonResponse({'error': 'document_id is required'}, status=400)
            
            # Start analysis
            result = analysis_engine.analyze_document(document_id, force_reanalyze)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Document analysis API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def get(self, request):
        """Get analysis status"""
        try:
            document_id = request.GET.get('document_id')
            
            if not document_id:
                return JsonResponse({'error': 'document_id is required'}, status=400)
            
            # Get document
            try:
                document = PDFDocument.objects.get(id=document_id)
            except PDFDocument.DoesNotExist:
                return JsonResponse({'error': 'Document not found'}, status=404)
            
            # Get analysis result if available
            try:
                analysis_result = document.analysis_result
                result = {
                    'document_id': document_id,
                    'status': document.analysis_status,
                    'analysis_result': {
                        'word_count': analysis_result.word_count,
                        'question_count': analysis_result.question_count,
                        'language_detected': analysis_result.language_detected,
                        'readability_score': analysis_result.readability_score,
                        'main_topics': analysis_result.main_topics,
                        'keywords': analysis_result.keywords,
                        'sentiment_score': analysis_result.sentiment_score,
                        'auto_summary': analysis_result.auto_summary,
                        'analyzed_at': analysis_result.analyzed_at.isoformat()
                    }
                }
            except PDFAnalysisResult.DoesNotExist:
                result = {
                    'document_id': document_id,
                    'status': document.analysis_status,
                    'analysis_result': None
                }
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Analysis status API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ProcessingPipelineAPI(View):
    """API for processing pipeline operations"""
    
    def post(self, request):
        """Start document processing"""
        try:
            if processing_pipeline is None:
                return JsonResponse({'error': 'Processing pipeline unavailable'}, status=503)
            data = json.loads(request.body)
            document_id = data.get('document_id')
            priority = data.get('priority', 0)
            
            if not document_id:
                return JsonResponse({'error': 'document_id is required'}, status=400)
            
            # Start processing
            task_id = processing_pipeline.process_document_async(document_id, priority)
            
            return JsonResponse({
                'success': True,
                'task_id': task_id,
                'document_id': document_id
            })
            
        except Exception as e:
            logger.error(f"Processing pipeline API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def get(self, request):
        """Get processing status"""
        try:
            if processing_pipeline is None:
                return JsonResponse({'error': 'Processing pipeline unavailable'}, status=503)
            task_id = request.GET.get('task_id')
            
            if not task_id:
                return JsonResponse({'error': 'task_id is required'}, status=400)
            
            # Get task status
            status = processing_pipeline.get_task_status(task_id)
            
            if not status:
                return JsonResponse({'error': 'Task not found'}, status=404)
            
            return JsonResponse(status)
            
        except Exception as e:
            logger.error(f"Processing status API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def delete(self, request):
        """Cancel processing task"""
        try:
            if processing_pipeline is None:
                return JsonResponse({'error': 'Processing pipeline unavailable'}, status=503)
            task_id = request.GET.get('task_id')
            
            if not task_id:
                return JsonResponse({'error': 'task_id is required'}, status=400)
            
            # Cancel task
            success = processing_pipeline.cancel_task(task_id)
            
            return JsonResponse({
                'success': success,
                'task_id': task_id
            })
            
        except Exception as e:
            logger.error(f"Task cancellation API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class BatchProcessingAPI(View):
    """API for batch processing operations"""
    
    def post(self, request):
        """Start batch processing"""
        try:
            if batch_processor is None:
                return JsonResponse({'error': 'Batch processor unavailable'}, status=503)
            data = json.loads(request.body)
            document_ids = data.get('document_ids', [])
            
            if not document_ids:
                return JsonResponse({'error': 'document_ids is required'}, status=400)
            
            # Start batch processing
            result = batch_processor.process_batch(document_ids)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Batch processing API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def get(self, request):
        """Get batch processing status"""
        try:
            if batch_processor is None:
                return JsonResponse({'error': 'Batch processor unavailable'}, status=503)
            batch_id = request.GET.get('batch_id')
            task_ids = request.GET.getlist('task_ids')
            
            if not batch_id and not task_ids:
                return JsonResponse({'error': 'batch_id or task_ids is required'}, status=400)
            
            if task_ids:
                # Get status for specific tasks
                result = batch_processor.get_batch_status(task_ids)
            else:
                # This would require storing batch information
                result = {'error': 'Batch status tracking not implemented yet'}
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Batch status API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class QuestionAnalysisAPI(View):
    """API for question analysis operations"""
    
    def post(self, request):
        """Analyze questions"""
        try:
            if question_analyzer is None:
                return JsonResponse({'error': 'Question analyzer unavailable'}, status=503)
            data = json.loads(request.body)
            questions = data.get('questions', [])
            context_list = data.get('context', [])
            
            if not questions:
                return JsonResponse({'error': 'questions is required'}, status=400)
            
            # Analyze questions
            if context_list and len(context_list) == len(questions):
                results = question_analyzer.analyze_question_batch(questions, context_list)
            else:
                results = question_analyzer.analyze_question_batch(questions)
            
            # Convert to serializable format
            serialized_results = []
            for result in results:
                serialized_results.append({
                    'text': result.text,
                    'question_type': result.question_type.value,
                    'cognitive_level': result.cognitive_level.value,
                    'difficulty_level': result.difficulty_level.value,
                    'topic': result.topic,
                    'subject_area': result.subject_area,
                    'keywords': result.keywords,
                    'marks': result.marks,
                    'time_estimate': result.time_estimate,
                    'confidence_score': result.confidence_score,
                    'page_number': result.page_number,
                    'options': result.options,
                    'correct_answer': result.correct_answer
                })
            
            return JsonResponse({
                'success': True,
                'results': serialized_results,
                'total_questions': len(results)
            })
            
        except Exception as e:
            logger.error(f"Question analysis API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def get(self, request):
        """Get question insights"""
        try:
            # This would analyze questions from a document or exam
            document_id = request.GET.get('document_id')
            exam_id = request.GET.get('exam_id')
            
            if not document_id and not exam_id:
                return JsonResponse({'error': 'document_id or exam_id is required'}, status=400)
            
            # For now, return a placeholder
            return JsonResponse({
                'message': 'Question insights API not fully implemented yet',
                'document_id': document_id,
                'exam_id': exam_id
            })
            
        except Exception as e:
            logger.error(f"Question insights API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class PDFEvaluationAPI(View):
    """API for PDF evaluation with Google Vision OCR"""
    
    def post(self, request):
        """Evaluate PDF file with Google Vision OCR"""
        temp_file_path = None
        try:
            # Handle file upload
            if 'file' not in request.FILES:
                return JsonResponse({'error': 'No file uploaded'}, status=400)
            
            file = request.FILES['file']
            
            # Validate file type
            if not file.name.lower().endswith('.pdf'):
                return JsonResponse({'error': 'Only PDF files are supported'}, status=400)
            
            # Create dedicated temp directory if it doesn't exist
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            temp_dir = os.path.join(media_root, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save file temporarily with a unique name
            _, ext = os.path.splitext(file.name)
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext or '.pdf', dir=temp_dir) as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
                temp_file_path = destination.name
            
            # Import OCR utility
            from pdf_analysis.utils_ocr import extract_text_from_pdf
            
            # Extract text using Google Vision API
            extracted_text = extract_text_from_pdf(temp_file_path)
            
            if not extracted_text:
                return JsonResponse({
                    'success': False,
                    'error': 'OCR failed - no text extracted',
                    'file_name': file.name
                }, status=500)
            
            # Basic analysis of extracted text
            word_count = len(extracted_text.split())
            char_count = len(extracted_text)
            line_count = extracted_text.count('\n') + 1
            
            # Format response
            return JsonResponse({
                'success': True,
                'file_name': file.name,
                'extracted_text': extracted_text,
                'analysis': {
                    'word_count': word_count,
                    'character_count': char_count,
                    'line_count': line_count,
                    'processing_method': 'Google Vision OCR',
                    'engine_status': 'working'
                },
                'message': 'PDF processed successfully with Google Vision OCR'
            })
            
        except Exception as e:
            logger.error(f"PDF evaluation API error: {str(e)}")
            return JsonResponse({'error': f'API Error: {str(e)}'}, status=500)
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    logger.warning("Failed to clean up temp file: %s", temp_file_path)
    
    def get(self, request):
        """Get evaluation status or sample format"""
        try:
            return JsonResponse({
                'message': 'PDF Evaluation API',
                'usage': 'POST /api/evaluate-pdf/',
                'parameters': {
                    'file': 'PDF file to evaluate',
                    'answer_key': 'JSON string with correct answers (optional)'
                },
                'example_answer_key': {
                    "Q1": "Correct answer for question 1",
                    "Q2": "Correct answer for question 2"
                }
            })
            
        except Exception as e:
            logger.error(f"PDF evaluation GET error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ExamEvaluationAPI(View):
    """API for exam evaluation operations"""
    
    def post(self, request):
        """Evaluate exam submission"""
        try:
            data = json.loads(request.body)
            submission_id = data.get('submission_id')
            evaluation_type = data.get('evaluation_type', 'automatic')
            
            if not submission_id:
                return JsonResponse({'error': 'submission_id is required'}, status=400)
            
            # Convert evaluation type
            from .exam_evaluator import EvaluationType
            eval_type_map = {
                'automatic': EvaluationType.AUTOMATIC,
                'manual': EvaluationType.MANUAL,
                'hybrid': EvaluationType.HYBRID,
                'peer': EvaluationType.PEER,
                'self': EvaluationType.SELF
            }
            
            eval_type = eval_type_map.get(evaluation_type, EvaluationType.AUTOMATIC)
            
            # Evaluate submission
            result = exam_evaluator.evaluate_submission(submission_id, eval_type)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Exam evaluation API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def get(self, request):
        """Get evaluation results"""
        try:
            submission_id = request.GET.get('submission_id')
            exam_id = request.GET.get('exam_id')
            
            if submission_id:
                # Get specific submission evaluation
                # This would be implemented based on stored results
                return JsonResponse({
                    'message': 'Individual evaluation results not fully implemented yet',
                    'submission_id': submission_id
                })
            elif exam_id:
                # Get exam evaluation summary
                result = exam_evaluator.evaluate_exam_batch(exam_id)
                return JsonResponse(result)
            else:
                return JsonResponse({'error': 'submission_id or exam_id is required'}, status=400)
            
        except Exception as e:
            logger.error(f"Evaluation results API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class AnalyticsAPI(View):
    """API for analytics and insights"""
    
    def get(self, request):
        """Get analytics data"""
        try:
            analytics_type = request.GET.get('type', 'overview')
            
            if analytics_type == 'overview':
                result = self._get_overview_analytics()
            elif analytics_type == 'documents':
                result = self._get_document_analytics()
            elif analytics_type == 'questions':
                result = self._get_question_analytics()
            elif analytics_type == 'exams':
                result = self._get_exam_analytics()
            else:
                return JsonResponse({'error': 'Invalid analytics type'}, status=400)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Analytics API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def _get_overview_analytics(self) -> Dict:
        """Get overview analytics"""
        try:
            # Document statistics
            total_documents = PDFDocument.objects.count()
            completed_analyses = PDFDocument.objects.filter(analysis_status='completed').count()
            processing_documents = PDFDocument.objects.filter(analysis_status='processing').count()
            
            # Question statistics (placeholder)
            total_questions = 0
            avg_confidence = 0.0
            
            # Exam statistics (placeholder)
            total_exams = 0
            total_evaluations = 0
            
            return {
                'documents': {
                    'total': total_documents,
                    'completed': completed_analyses,
                    'processing': processing_documents,
                    'completion_rate': (completed_analyses / total_documents * 100) if total_documents > 0 else 0
                },
                'questions': {
                    'total': total_questions,
                    'avg_confidence': avg_confidence
                },
                'exams': {
                    'total': total_exams,
                    'evaluations': total_evaluations
                },
                'system': {
                    'status': 'healthy',
                    'last_updated': timezone.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Overview analytics error: {str(e)}")
            return {'error': str(e)}
    
    def _get_document_analytics(self) -> Dict:
        """Get document analytics"""
        try:
            # Document type distribution
            type_distribution = PDFDocument.objects.values('document_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Analysis status distribution
            status_distribution = PDFDocument.objects.values('analysis_status').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Recent uploads
            recent_documents = PDFDocument.objects.order_by('-uploaded_at')[:10]
            
            return {
                'type_distribution': list(type_distribution),
                'status_distribution': list(status_distribution),
                'recent_uploads': [
                    {
                        'id': str(doc.id),
                        'title': doc.title,
                        'type': doc.document_type,
                        'status': doc.analysis_status,
                        'uploaded_at': doc.uploaded_at.isoformat()
                    }
                    for doc in recent_documents
                ]
            }
            
        except Exception as e:
            logger.error(f"Document analytics error: {str(e)}")
            return {'error': str(e)}
    
    def _get_question_analytics(self) -> Dict:
        """Get question analytics"""
        # Placeholder implementation
        return {
            'message': 'Question analytics not fully implemented yet',
            'total_questions': 0,
            'type_distribution': {},
            'difficulty_distribution': {}
        }
    
    def _get_exam_analytics(self) -> Dict:
        """Get exam analytics"""
        # Placeholder implementation
        return {
            'message': 'Exam analytics not fully implemented yet',
            'total_exams': 0,
            'average_scores': {},
            'completion_rates': {}
        }

@method_decorator(csrf_exempt, name='dispatch')
class SearchAPI(View):
    """API for search operations"""
    
    def get(self, request):
        """Search documents, questions, etc."""
        try:
            query = request.GET.get('q', '')
            search_type = request.GET.get('type', 'documents')
            page = int(request.GET.get('page', 1))
            per_page = int(request.GET.get('per_page', 10))
            
            if not query:
                return JsonResponse({'error': 'Search query is required'}, status=400)
            
            if search_type == 'documents':
                results = self._search_documents(query, page, per_page)
            elif search_type == 'questions':
                results = self._search_questions(query, page, per_page)
            elif search_type == 'all':
                results = self._search_all(query, page, per_page)
            else:
                return JsonResponse({'error': 'Invalid search type'}, status=400)
            
            return JsonResponse(results)
            
        except Exception as e:
            logger.error(f"Search API error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def _search_documents(self, query: str, page: int, per_page: int) -> Dict:
        """Search documents"""
        try:
            documents = PDFDocument.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            ).order_by('-uploaded_at')
            
            # Paginate
            paginator = Paginator(documents, per_page)
            page_obj = paginator.get_page(page)
            
            results = []
            for doc in page_obj:
                results.append({
                    'id': str(doc.id),
                    'title': doc.title,
                    'description': doc.description,
                    'type': doc.document_type,
                    'status': doc.analysis_status,
                    'uploaded_at': doc.uploaded_at.isoformat()
                })
            
            return {
                'results': results,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': paginator.count,
                    'total_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
            
        except Exception as e:
            logger.error(f"Document search error: {str(e)}")
            return {'error': str(e)}
    
    def _search_questions(self, query: str, page: int, per_page: int) -> Dict:
        """Search questions"""
        # Placeholder implementation
        return {
            'results': [],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': 0,
                'total_pages': 0,
                'has_next': False,
                'has_previous': False
            }
        }
    
    def _search_all(self, query: str, page: int, per_page: int) -> Dict:
        """Search all content"""
        # Combine results from different search types
        documents = self._search_documents(query, page, per_page)
        questions = self._search_questions(query, page, per_page)
        
        return {
            'documents': documents,
            'questions': questions,
            'total_results': len(documents.get('results', [])) + len(questions.get('results', []))
        }

# API endpoint mappings
api_endpoints = {
    'document-analysis': DocumentAnalysisAPI.as_view(),
    'processing-pipeline': ProcessingPipelineAPI.as_view(),
    'batch-processing': BatchProcessingAPI.as_view(),
    'question-analysis': QuestionAnalysisAPI.as_view(),
    'exam-evaluation': ExamEvaluationAPI.as_view(),
    'analytics': AnalyticsAPI.as_view(),
    'search': SearchAPI.as_view(),
}

# Decorators for API endpoints
def api_login_required(view_func):
    """Custom login required decorator for API"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper

@method_decorator(csrf_exempt, name='dispatch')
class EvaluateAnswerSheetAPI(View):
    """
    API for complete answer sheet evaluation
    PDF upload -> OCR -> Question detection -> NLP comparison -> Scoring rules -> Final result
    """
    
    def post(self, request):
        try:
            # Get uploaded files
            answer_pdf = request.FILES.get('answer_pdf')
            question_paper = request.FILES.get('question_paper')

            if not answer_pdf or not question_paper:
                return Response({
                    "success": False,
                    "error": "Both answer_pdf and question_paper are required"
                })

            # File validation - accept PDF and image formats
            allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg']
            
            # Validate answer sheet
            if not any(answer_pdf.name.lower().endswith(ext) for ext in allowed_extensions):
                return Response({
                    "success": False,
                    "error": "Answer sheet must be PDF or image file (PDF, PNG, JPG, JPEG)"
                })
            
            # Validate question paper
            if not any(question_paper.name.lower().endswith(ext) for ext in allowed_extensions):
                return Response({
                    "success": False,
                    "error": "Question paper must be PDF or image file (PDF, PNG, JPG, JPEG)"
                })

            # Check file sizes (max 10MB each)
            max_size = 10 * 1024 * 1024  # 10MB
            if answer_pdf.size > max_size:
                return Response({
                    "success": False,
                    "error": "Answer sheet file too large (max 10MB)"
                })
            
            if question_paper.size > max_size:
                return Response({
                    "success": False,
                    "error": "Question paper file too large (max 10MB)"
                })

            # STEP 1: OCR - Extract text from both files
            from pdf_analysis.utils_ocr import extract_text_from_uploaded_file
            
            answer_text = extract_text_from_uploaded_file(answer_pdf)
            question_text = extract_text_from_uploaded_file(question_paper)

            if not answer_text.strip():
                return Response({
                    "success": False, 
                    "error": "OCR failed on answer sheet - no text extracted"
                })

            if not question_text.strip():
                return Response({
                    "success": False,
                    "error": "OCR failed on question paper - no text extracted"
                })

            # STEP 2: NLP Evaluation - Compare answers with questions
            from pdf_analysis.utils_nlp import evaluate_answers
            
            results = evaluate_answers(answer_text, question_text)

            if not results:
                return Response({
                    "success": False,
                    "error": "NLP evaluation failed - no results generated"
                })

            # STEP 3: Apply Scoring Rules
            from core.models import ScoringRange
            
            scoring_rules = ScoringRange.objects.filter(is_active=True).order_by('-min_score')
            
            total_marks = 0
            evaluated_answers = []

            for result in results:
                similarity = result['similarity']
                question_text = result['question']
                answer_text = result['answer']

                # Find applicable scoring rule
                marks = 0
                applied_rule = None
                
                for rule in scoring_rules:
                    if rule.min_score <= similarity <= rule.max_score:
                        marks = rule.marks
                        applied_rule = rule.name
                        break

                total_marks += marks

                evaluated_answers.append({
                    "question": question_text,
                    "answer": answer_text,
                    "similarity": round(similarity, 3),
                    "marks": marks,
                    "applied_rule": applied_rule or "default"
                })

            # STEP 4: Generate Final Result
            return Response({
                "success": True,
                "total_marks": total_marks,
                "total_questions": len(evaluated_answers),
                "average_similarity": round(sum(r['similarity'] for r in evaluated_answers) / len(evaluated_answers), 3),
                "answers": evaluated_answers,
                "processing_info": {
                    "ocr_method": "enhanced",
                    "nlp_model": "sentence-transformers",
                    "scoring_rules_applied": len(scoring_rules)
                }
            })

        except Exception as e:
            logger.error(f"EvaluateAnswerSheetAPI error: {str(e)}")
            return Response({
                "success": False,
                "error": str(e)
            })
    
    def get(self, request):
        """Get API information and usage"""
        try:
            from core.models import ScoringRange
            
            scoring_rules = ScoringRange.objects.filter(is_active=True)
            rules_info = []
            
            for rule in scoring_rules:
                rules_info.append({
                    "name": rule.name,
                    "min_score": rule.min_score,
                    "max_score": rule.max_score,
                    "marks": rule.marks
                })
            
            return Response({
                "api_name": "EvaluateAnswerSheetAPI",
                "description": "Complete answer sheet evaluation with OCR, NLP, and scoring",
                "usage": {
                    "method": "POST",
                    "endpoint": "/core/api/evaluate-answer-sheet/",
                    "files": {
                        "answer_pdf": "PDF file containing student answers (required)",
                        "question_paper": "PDF/image file containing questions (required)"
                    },
                    "response": {
                        "success": "boolean",
                        "total_marks": "integer",
                        "answers": "array of evaluated answers with similarity and marks"
                    }
                },
                "scoring_rules": rules_info,
                "status": "active"
            })
            
        except Exception as e:
            logger.error(f"EvaluateAnswerSheetAPI GET error: {str(e)}")
            return Response({
                "success": False,
                "error": str(e)
            })

# Apply authentication to sensitive endpoints
sensitive_endpoints = ['document-analysis', 'processing-pipeline', 'exam-evaluation']

for endpoint_name in sensitive_endpoints:
    if endpoint_name in api_endpoints:
        api_endpoints[endpoint_name] = api_login_required(api_endpoints[endpoint_name])
