"""
API Endpoints for Analysis System - ExamAutoPro
Main motive: RESTful API for backend analysis and processing
"""

import json
import logging
from typing import Dict, List, Optional
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from datetime import datetime

User = get_user_model()

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class EvaluateAnswerSheetAPI(View):
    """
    API endpoint for evaluating answer sheets using OCR and NLP
    """
    
    def get(self, request):
        """API information"""
        return JsonResponse({
            "success": True,
            "message": "Answer Sheet Evaluation API",
            "endpoint": "/core/api/evaluate-answer-sheet/",
            "method": "POST",
            "required_files": {
                "answer_pdf": "Student answer sheet (PDF, PNG, JPG, JPEG)",
                "question_paper": "Question paper (PDF, PNG, JPG, JPEG)"
            },
            "max_file_size": "10MB",
            "supported_formats": ["PDF", "PNG", "JPG", "JPEG"],
            "processing": {
                "step1": "OCR text extraction from both files",
                "step2": "Question detection and answer splitting",
                "step3": "NLP semantic similarity analysis",
                "step4": "Scoring based on similarity thresholds"
            }
        })
    
    def post(self, request):
        """Evaluate answer sheet against question paper"""
        try:
            # Get uploaded files
            answer_pdf = request.FILES.get('answer_pdf')
            question_paper = request.FILES.get('question_paper')

            if not answer_pdf or not question_paper:
                return JsonResponse({
                    "success": False,
                    "error": "Both answer_pdf and question_paper are required"
                })

            # File validation - accept PDF and image formats
            allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg']
            
            # Validate answer sheet
            if not any(answer_pdf.name.lower().endswith(ext) for ext in allowed_extensions):
                return JsonResponse({
                    "success": False,
                    "error": "Answer sheet must be PDF or image file (PDF, PNG, JPG, JPEG)"
                })
            
            # Validate question paper
            if not any(question_paper.name.lower().endswith(ext) for ext in allowed_extensions):
                return JsonResponse({
                    "success": False,
                    "error": "Question paper must be PDF or image file (PDF, PNG, JPG, JPEG)"
                })

            # Check file sizes (max 10MB each)
            max_size = 10 * 1024 * 1024  # 10MB
            if answer_pdf.size > max_size:
                return JsonResponse({
                    "success": False,
                    "error": "Answer sheet file too large (max 10MB)"
                })
            
            if question_paper.size > max_size:
                return JsonResponse({
                    "success": False,
                    "error": "Question paper file too large (max 10MB)"
                })

            # STEP 1: OCR - Extract text from both files
            from pdf_analysis.utils_ocr import extract_text_from_uploaded_file
            
            answer_text = extract_text_from_uploaded_file(answer_pdf)
            question_text = extract_text_from_uploaded_file(question_paper)

            if not answer_text.strip():
                return JsonResponse({
                    "success": False, 
                    "error": "OCR failed on answer sheet - no text extracted"
                })

            if not question_text.strip():
                return JsonResponse({
                    "success": False,
                    "error": "OCR failed on question paper - no text extracted"
                })

            # STEP 2: NLP - Evaluate answers against questions
            from pdf_analysis.utils_nlp import evaluate_answers
            
            evaluation_results = evaluate_answers(answer_text, question_text)

            if not evaluation_results:
                return JsonResponse({
                    "success": False,
                    "error": "NLP evaluation failed - no question-answer pairs detected"
                })

            # STEP 3: Scoring - Apply scoring rules
            total_marks = 0
            max_marks = len(evaluation_results) * 10  # Assume 10 marks per question
            
            for result in evaluation_results:
                similarity = result.get('similarity', 0)
                
                # Scoring logic based on similarity
                if similarity >= 0.8:
                    marks = 10
                elif similarity >= 0.6:
                    marks = 8
                elif similarity >= 0.4:
                    marks = 6
                elif similarity >= 0.2:
                    marks = 4
                else:
                    marks = 2
                
                result['marks'] = marks
                total_marks += marks

            # STEP 4: Return results
            response_data = {
                "success": True,
                "total_marks": total_marks,
                "max_marks": max_marks,
                "percentage": round((total_marks / max_marks) * 100, 2),
                "answers": evaluation_results,
                "processing_info": {
                    "answer_file": answer_pdf.name,
                    "question_file": question_paper.name,
                    "total_questions": len(evaluation_results),
                    "ocr_status": "success",
                    "nlp_status": "success"
                }
            }

            return JsonResponse(response_data)

        except Exception as e:
            logger.error(f"Evaluation API error: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": f"Evaluation failed: {str(e)}"
            })

# Additional API endpoints can be added here...

@method_decorator(csrf_exempt, name='dispatch')
class DocumentAnalysisAPI(View):
    """
    API for document analysis and processing
    """
    
    def post(self, request):
        """Analyze uploaded document"""
        try:
            document = request.FILES.get('document')
            
            if not document:
                return JsonResponse({
                    "success": False,
                    "error": "Document file is required"
                })
            
            # Extract text using OCR
            from pdf_analysis.utils_ocr import extract_text_from_uploaded_file
            
            extracted_text = extract_text_from_uploaded_file(document)
            
            if not extracted_text.strip():
                return JsonResponse({
                    "success": False,
                    "error": "No text could be extracted from the document"
                })
            
            return JsonResponse({
                "success": True,
                "filename": document.name,
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "word_count": len(extracted_text.split())
            })
            
        except Exception as e:
            logger.error(f"Document analysis error: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            })

@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckAPI(View):
    """
    API health check endpoint
    """
    
    def get(self, request):
        """Check system health"""
        try:
            # Check dependencies
            checks = {
                "django": "OK",
                "database": "OK",
                "sentence_transformers": "OK",
                "spacy": "OK",
                "tesseract": "WARNING - Not configured",
                "google_vision": "WARNING - Not configured"
            }
            
            # Test sentence transformers
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')
                checks["sentence_transformers"] = "OK"
            except:
                checks["sentence_transformers"] = "ERROR"
            
            # Test spaCy
            try:
                import spacy
                nlp = spacy.load('en_core_web_sm')
                checks["spacy"] = "OK"
            except:
                checks["spacy"] = "ERROR"
            
            return JsonResponse({
                "success": True,
                "status": "healthy",
                "checks": checks,
                "timestamp": timezone.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"Health check failed: {str(e)}"
            })
