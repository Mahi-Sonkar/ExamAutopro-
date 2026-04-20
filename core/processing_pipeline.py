"""
Advanced PDF Processing Pipeline for ExamAutoPro
Main motive: Intelligent document processing and analysis
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import json
import hashlib

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone

from .analysis_engine import analysis_engine
from pdf_analysis.models import PDFDocument, PDFAnalysisResult, PDFProcessingLog

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    OCR_PROCESSING = "ocr_processing"
    NLP_PROCESSING = "nlp_processing"
    QUESTION_EXTRACTION = "question_extraction"
    CONTENT_ANALYSIS = "content_analysis"
    INSIGHTS_GENERATION = "insights_generation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProcessingTask:
    """Processing task data structure"""
    document_id: str
    task_id: str
    status: ProcessingStatus
    progress: float
    start_time: float
    current_step: str
    error_message: Optional[str] = None
    result: Optional[Dict] = None

class PDFProcessingPipeline:
    """
    Advanced PDF processing pipeline with multi-stage processing
    Main motive: Intelligent and efficient document analysis
    """
    
    def __init__(self):
        self.active_tasks = {}
        self.max_workers = getattr(settings, 'PDF_PROCESSING_WORKERS', 2)
        self.chunk_size = getattr(settings, 'PDF_PROCESSING_CHUNK_SIZE', 1024)
        self.timeout = getattr(settings, 'PDF_PROCESSING_TIMEOUT', 300)  # 5 minutes
        
    def process_document_async(self, document_id: str, priority: int = 0) -> str:
        """
        Start asynchronous document processing
        Returns task ID for tracking
        """
        task_id = self._generate_task_id(document_id)
        
        # Create processing task
        task = ProcessingTask(
            document_id=document_id,
            task_id=task_id,
            status=ProcessingStatus.QUEUED,
            progress=0.0,
            start_time=time.time(),
            current_step="queued"
        )
        
        self.active_tasks[task_id] = task
        
        # Log task creation
        self._log_processing_step(document_id, "info", f"Task {task_id} queued for processing")
        
        # Start processing in background
        self._start_background_processing(task, priority)
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of processing task"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.task_id,
            'document_id': task.document_id,
            'status': task.status.value,
            'progress': task.progress,
            'current_step': task.current_step,
            'start_time': task.start_time,
            'error_message': task.error_message,
            'is_complete': task.status == ProcessingStatus.COMPLETED,
            'is_failed': task.status == ProcessingStatus.FAILED
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel processing task"""
        task = self.active_tasks.get(task_id)
        if task and task.status in [ProcessingStatus.PENDING, ProcessingStatus.QUEUED]:
            task.status = ProcessingStatus.CANCELLED
            self._log_processing_step(task.document_id, "warning", f"Task {task_id} cancelled")
            return True
        return False
    
    def _start_background_processing(self, task: ProcessingTask, priority: int) -> None:
        """Start background processing using thread pool"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future = executor.submit(self._process_document_pipeline, task)
            
            # Add completion callback
            future.add_done_callback(lambda f: self._handle_task_completion(task, f))
    
    def _process_document_pipeline(self, task: ProcessingTask) -> Dict:
        """
        Main processing pipeline with multiple stages
        Main motive: Comprehensive and intelligent analysis
        """
        document_id = task.document_id
        
        try:
            # Get document
            document = PDFDocument.objects.get(id=document_id)
            
            # Update status to processing
            self._update_task_status(task, ProcessingStatus.PROCESSING, 0.0, "starting")
            
            # Stage 1: Document validation
            self._update_task_status(task, ProcessingStatus.PROCESSING, 5.0, "validating document")
            validation_result = self._validate_document(document)
            if not validation_result['valid']:
                raise Exception(validation_result['error'])
            
            # Stage 2: OCR Processing
            self._update_task_status(task, ProcessingStatus.OCR_PROCESSING, 10.0, "extracting text with OCR")
            ocr_result = self._process_ocr_stage(document)
            
            # Stage 3: NLP Analysis
            self._update_task_status(task, ProcessingStatus.NLP_PROCESSING, 40.0, "performing NLP analysis")
            nlp_result = self._process_nlp_stage(ocr_result['text'])
            
            # Stage 4: Question Extraction
            self._update_task_status(task, ProcessingStatus.QUESTION_EXTRACTION, 60.0, "extracting questions")
            questions_result = self._process_question_extraction_stage(ocr_result['text'])
            
            # Stage 5: Content Analysis
            self._update_task_status(task, ProcessingStatus.CONTENT_ANALYSIS, 80.0, "analyzing content quality")
            content_result = self._process_content_analysis_stage(ocr_result['text'])
            
            # Stage 6: Insights Generation
            self._update_task_status(task, ProcessingStatus.INSIGHTS_GENERATION, 90.0, "generating insights")
            insights_result = self._process_insights_generation_stage(nlp_result, questions_result, content_result)
            
            # Stage 7: Final Integration
            self._update_task_status(task, ProcessingStatus.PROCESSING, 95.0, "integrating results")
            final_result = self._integrate_results(document, ocr_result, nlp_result, questions_result, content_result, insights_result)
            
            # Stage 8: Save Results
            self._update_task_status(task, ProcessingStatus.PROCESSING, 98.0, "saving results")
            self._save_comprehensive_results(document, final_result)
            
            # Complete
            self._update_task_status(task, ProcessingStatus.COMPLETED, 100.0, "completed")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Processing pipeline failed for document {document_id}: {str(e)}")
            self._update_task_status(task, ProcessingStatus.FAILED, task.progress, str(e))
            self._log_processing_step(document_id, "error", f"Pipeline failed: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def _validate_document(self, document: PDFDocument) -> Dict:
        """Validate document before processing"""
        try:
            # Check file exists
            if not document.pdf_file or not default_storage.exists(document.pdf_file.name):
                return {'valid': False, 'error': 'PDF file not found'}
            
            # Check file size
            if document.file_size > 50 * 1024 * 1024:  # 50MB
                return {'valid': False, 'error': 'File too large (max 50MB)'}
            
            # Check file type
            if not document.pdf_file.name.lower().endswith('.pdf'):
                return {'valid': False, 'error': 'Invalid file type (must be PDF)'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _process_ocr_stage(self, document: PDFDocument) -> Dict:
        """Process OCR extraction stage"""
        try:
            self._log_processing_step(document.id, "info", "Starting OCR extraction")
            
            # Use analysis engine for OCR
            ocr_result = analysis_engine._extract_text_ocr(document)
            
            if not ocr_result['success']:
                raise Exception(f"OCR extraction failed: {ocr_result.get('error', 'Unknown error')}")
            
            # Update document metadata
            document.page_count = ocr_result.get('page_count')
            document.save()
            
            self._log_processing_step(document.id, "info", f"OCR extraction completed: {len(ocr_result['text'])} characters extracted")
            
            return ocr_result
            
        except Exception as e:
            self._log_processing_step(document.id, "error", f"OCR stage failed: {str(e)}")
            raise
    
    def _process_nlp_stage(self, text: str) -> Dict:
        """Process NLP analysis stage"""
        try:
            # Use analysis engine for NLP
            nlp_result = analysis_engine._analyze_text_nlp(text)
            
            if 'error' in nlp_result:
                raise Exception(f"NLP analysis failed: {nlp_result['error']}")
            
            return nlp_result
            
        except Exception as e:
            logger.error(f"NLP stage failed: {str(e)}")
            raise
    
    def _process_question_extraction_stage(self, text: str) -> Dict:
        """Process question extraction stage"""
        try:
            # Use analysis engine for question extraction
            questions_result = analysis_engine._extract_questions_advanced(text)
            
            if 'error' in questions_result:
                raise Exception(f"Question extraction failed: {questions_result['error']}")
            
            return questions_result
            
        except Exception as e:
            logger.error(f"Question extraction stage failed: {str(e)}")
            raise
    
    def _process_content_analysis_stage(self, text: str) -> Dict:
        """Process content analysis stage"""
        try:
            # Use analysis engine for content analysis
            content_result = analysis_engine._analyze_content_quality(text)
            
            if 'error' in content_result:
                raise Exception(f"Content analysis failed: {content_result['error']}")
            
            return content_result
            
        except Exception as e:
            logger.error(f"Content analysis stage failed: {str(e)}")
            raise
    
    def _process_insights_generation_stage(self, nlp_result: Dict, questions_result: Dict, content_result: Dict) -> Dict:
        """Process insights generation stage"""
        try:
            # Use analysis engine for insights
            insights_result = analysis_engine._generate_insights(nlp_result, questions_result, content_result)
            
            if 'error' in insights_result:
                raise Exception(f"Insights generation failed: {insights_result['error']}")
            
            return insights_result
            
        except Exception as e:
            logger.error(f"Insights generation stage failed: {str(e)}")
            raise
    
    def _integrate_results(self, document: PDFDocument, ocr_result: Dict, nlp_result: Dict, 
                         questions_result: Dict, content_result: Dict, insights_result: Dict) -> Dict:
        """Integrate all processing results"""
        try:
            integration_start = time.time()
            
            # Create comprehensive result
            integrated_result = {
                'document_info': {
                    'id': str(document.id),
                    'title': document.title,
                    'type': document.document_type,
                    'uploaded_at': document.uploaded_at.isoformat(),
                    'file_size': document.file_size,
                    'page_count': document.page_count
                },
                'processing_info': {
                    'pipeline_version': '2.0',
                    'processing_time': time.time() - integration_start,
                    'stages_completed': ['validation', 'ocr', 'nlp', 'questions', 'content', 'insights'],
                    'quality_metrics': self._calculate_processing_quality(ocr_result, nlp_result, questions_result, content_result)
                },
                'ocr_analysis': ocr_result,
                'nlp_analysis': nlp_result,
                'questions_analysis': questions_result,
                'content_analysis': content_result,
                'insights': insights_result,
                'integration_timestamp': timezone.now().isoformat()
            }
            
            return integrated_result
            
        except Exception as e:
            logger.error(f"Result integration failed: {str(e)}")
            raise
    
    def _save_comprehensive_results(self, document: PDFDocument, result: Dict) -> None:
        """Save comprehensive analysis results"""
        try:
            # Use analysis engine to save results
            analysis_engine._save_analysis_result(document, result)
            
            # Update document status
            document.analysis_status = 'completed'
            document.save()
            
            self._log_processing_step(document.id, "info", "Results saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")
            raise
    
    def _calculate_processing_quality(self, ocr_result: Dict, nlp_result: Dict, 
                                   questions_result: Dict, content_result: Dict) -> Dict:
        """Calculate overall processing quality metrics"""
        quality_scores = []
        
        # OCR quality
        if 'confidence' in ocr_result:
            quality_scores.append(ocr_result['confidence'])
        
        # NLP quality
        if 'overall_score' in nlp_result:
            quality_scores.append(nlp_result['overall_score'])
        
        # Questions quality
        if 'quality_assessment' in questions_result and 'quality_score' in questions_result['quality_assessment']:
            quality_scores.append(questions_result['quality_assessment']['quality_score'])
        
        # Content quality
        if 'overall_quality' in content_result and 'score' in content_result['overall_quality']:
            quality_scores.append(content_result['overall_quality']['score'])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            'overall_quality_score': avg_quality,
            'component_scores': {
                'ocr_quality': ocr_result.get('confidence', 0.0),
                'nlp_quality': nlp_result.get('overall_score', 0.0),
                'questions_quality': questions_result.get('quality_assessment', {}).get('quality_score', 0.0),
                'content_quality': content_result.get('overall_quality', {}).get('score', 0.0)
            },
            'quality_level': self._get_quality_level(avg_quality)
        }
    
    def _update_task_status(self, task: ProcessingTask, status: ProcessingStatus, 
                           progress: float, current_step: str, error_message: str = None) -> None:
        """Update task status and progress"""
        task.status = status
        task.progress = progress
        task.current_step = current_step
        if error_message:
            task.error_message = error_message
        
        # Log status update
        self._log_processing_step(task.document_id, "info", f"Status updated: {status.value} - {current_step}")
    
    def _handle_task_completion(self, task: ProcessingTask, future) -> None:
        """Handle task completion"""
        try:
            result = future.result()
            task.result = result
            
            if task.status == ProcessingStatus.COMPLETED:
                self._log_processing_step(task.document_id, "info", f"Task {task.task_id} completed successfully")
            elif task.status == ProcessingStatus.FAILED:
                self._log_processing_step(task.document_id, "error", f"Task {task.task_id} failed: {task.error_message}")
            
            # Clean up old tasks (keep last 100)
            if len(self.active_tasks) > 100:
                oldest_tasks = sorted(self.active_tasks.items(), key=lambda x: x[1].start_time)[:50]
                for task_id, _ in oldest_tasks:
                    del self.active_tasks[task_id]
            
        except Exception as e:
            logger.error(f"Task completion handler failed: {str(e)}")
            task.status = ProcessingStatus.FAILED
            task.error_message = str(e)
    
    def _generate_task_id(self, document_id: str) -> str:
        """Generate unique task ID"""
        timestamp = str(int(time.time()))
        unique_hash = hashlib.md5(f"{document_id}_{timestamp}".encode()).hexdigest()[:8]
        return f"task_{document_id}_{timestamp}_{unique_hash}"
    
    def _log_processing_step(self, document_id: str, level: str, message: str, details: Dict = None) -> None:
        """Log processing step"""
        try:
            PDFProcessingLog.objects.create(
                pdf_document_id=document_id,
                log_level=level,
                message=message,
                details=details or {}
            )
        except Exception as e:
            logger.error(f"Failed to log processing step: {str(e)}")
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level from score"""
        if score >= 0.9:
            return 'excellent'
        elif score >= 0.8:
            return 'very_good'
        elif score >= 0.7:
            return 'good'
        elif score >= 0.6:
            return 'fair'
        elif score >= 0.5:
            return 'poor'
        else:
            return 'very_poor'

class BatchProcessor:
    """Batch processing for multiple documents"""
    
    def __init__(self):
        self.pipeline = PDFProcessingPipeline()
        self.batch_size = getattr(settings, 'PDF_BATCH_SIZE', 10)
    
    def process_batch(self, document_ids: List[str]) -> Dict:
        """Process multiple documents in batch"""
        batch_id = self._generate_batch_id()
        task_ids = []
        
        try:
            # Queue all documents
            for doc_id in document_ids:
                task_id = self.pipeline.process_document_async(doc_id)
                task_ids.append(task_id)
            
            return {
                'batch_id': batch_id,
                'task_ids': task_ids,
                'total_documents': len(document_ids),
                'status': 'processing'
            }
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            return {'batch_id': batch_id, 'error': str(e), 'status': 'failed'}
    
    def get_batch_status(self, task_ids: List[str]) -> Dict:
        """Get status of batch processing"""
        statuses = []
        completed = 0
        failed = 0
        
        for task_id in task_ids:
            status = self.pipeline.get_task_status(task_id)
            if status:
                statuses.append(status)
                if status['is_complete']:
                    completed += 1
                elif status['is_failed']:
                    failed += 1
        
        return {
            'total_tasks': len(task_ids),
            'completed': completed,
            'failed': failed,
            'in_progress': len(task_ids) - completed - failed,
            'progress': (completed / len(task_ids)) * 100 if task_ids else 0,
            'status': 'completed' if completed == len(task_ids) else 'processing'
        }
    
    def _generate_batch_id(self) -> str:
        """Generate unique batch ID"""
        timestamp = str(int(time.time()))
        return f"batch_{timestamp}"

# Singleton instances
processing_pipeline = PDFProcessingPipeline()
batch_processor = BatchProcessor()
