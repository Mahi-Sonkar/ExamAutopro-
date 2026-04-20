"""
Batch Processor for API Operations
Handles batch processing of multiple documents
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import json
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone

from .analysis_engine import analysis_engine
from pdf_analysis.models import PDFDocument, PDFAnalysisResult, PDFProcessingLog

logger = logging.getLogger(__name__)

class BatchStatus(Enum):
    """Batch processing status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BatchTask:
    """Batch task data structure"""
    task_id: str
    document_ids: List[str]
    status: BatchStatus
    created_at: timezone.datetime
    started_at: Optional[timezone.datetime] = None
    completed_at: Optional[timezone.datetime] = None
    results: List[Dict] = None
    errors: List[str] = None
    progress: float = 0.0

class BatchProcessor:
    """Batch processor for handling multiple document processing"""
    
    def __init__(self):
        self.active_batches = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.max_concurrent_tasks = 4
    
    def process_batch(self, document_ids: List[str]) -> Dict:
        """Process a batch of documents"""
        try:
            # Generate batch ID
            batch_id = str(uuid.uuid4())
            
            # Create batch task
            batch_task = BatchTask(
                task_id=batch_id,
                document_ids=document_ids,
                status=BatchStatus.QUEUED,
                created_at=timezone.now()
            )
            
            # Store batch task
            self.active_batches[batch_id] = batch_task
            
            # Start batch processing in background
            self.executor.submit(self._process_batch_worker, batch_task)
            
            logger.info(f"Started batch processing for {len(document_ids)} documents")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'document_count': len(document_ids),
                'status': BatchStatus.QUEUED.value
            }
            
        except Exception as e:
            logger.error(f"Batch processing start failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'status': BatchStatus.FAILED.value
            }
    
    def _process_batch_worker(self, batch_task: BatchTask) -> None:
        """Worker function for batch processing"""
        try:
            # Update status to processing
            batch_task.status = BatchStatus.PROCESSING
            batch_task.started_at = timezone.now()
            batch_task.results = []
            batch_task.errors = []
            
            # Process each document
            total_docs = len(batch_task.document_ids)
            completed_docs = 0
            
            for i, doc_id in enumerate(batch_task.document_ids):
                try:
                    # Process single document
                    result = analysis_engine.analyze_document(doc_id, force_reanalyze=True)
                    
                    if result.get('success'):
                        batch_task.results.append({
                            'document_id': doc_id,
                            'status': 'completed',
                            'result': result
                        })
                    else:
                        batch_task.errors.append({
                            'document_id': doc_id,
                            'error': result.get('error', 'Unknown error')
                        })
                    
                    completed_docs += 1
                    batch_task.progress = (completed_docs / total_docs) * 100
                    
                    # Log progress
                    logger.info(f"Processed {completed_docs}/{total_docs} documents in batch {batch_task.task_id}")
                    
                except Exception as e:
                    batch_task.errors.append({
                        'document_id': doc_id,
                        'error': str(e)
                    })
                    logger.error(f"Document {doc_id} processing failed: {e}")
            
            # Update final status
            batch_task.status = BatchStatus.COMPLETED if not batch_task.errors else BatchStatus.FAILED
            batch_task.completed_at = timezone.now()
            
            logger.info(f"Batch {batch_task.task_id} completed with status: {batch_task.status.value}")
            
        except Exception as e:
            batch_task.status = BatchStatus.FAILED
            batch_task.completed_at = timezone.now()
            batch_task.errors = [{'error': str(e)}]
            logger.error(f"Batch processing worker failed: {e}")
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """Get status of a specific batch"""
        try:
            if batch_id not in self.active_batches:
                return {
                    'error': 'Batch not found',
                    'batch_id': batch_id
                }
            
            batch_task = self.active_batches[batch_id]
            
            return {
                'batch_id': batch_id,
                'status': batch_task.status.value,
                'progress': batch_task.progress,
                'created_at': batch_task.created_at.isoformat(),
                'started_at': batch_task.started_at.isoformat() if batch_task.started_at else None,
                'completed_at': batch_task.completed_at.isoformat() if batch_task.completed_at else None,
                'document_count': len(batch_task.document_ids),
                'completed_count': len(batch_task.results) if batch_task.results else 0,
                'error_count': len(batch_task.errors) if batch_task.errors else 0,
                'results': batch_task.results[:10] if batch_task.results else [],  # Return first 10 results
                'errors': batch_task.errors[:10] if batch_task.errors else []  # Return first 10 errors
            }
            
        except Exception as e:
            logger.error(f"Get batch status failed: {e}")
            return {
                'error': str(e),
                'batch_id': batch_id
            }
    
    def get_batch_status(self, task_ids: List[str]) -> Dict:
        """Get status for multiple tasks (for API compatibility)"""
        try:
            results = []
            
            for task_id in task_ids:
                status = self.get_batch_status(task_id)
                results.append(status)
            
            return {
                'success': True,
                'tasks': results,
                'total_tasks': len(results)
            }
            
        except Exception as e:
            logger.error(f"Get multiple batch status failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch processing task"""
        try:
            if batch_id not in self.active_batches:
                return False
            
            batch_task = self.active_batches[batch_id]
            
            if batch_task.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]:
                return False
            
            batch_task.status = BatchStatus.CANCELLED
            batch_task.completed_at = timezone.now()
            
            logger.info(f"Cancelled batch {batch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Cancel batch failed: {e}")
            return False
    
    def get_active_batches(self) -> List[Dict]:
        """Get list of all active batches"""
        try:
            active_batches = []
            
            for batch_id, batch_task in self.active_batches.items():
                if batch_task.status not in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]:
                    active_batches.append({
                        'batch_id': batch_id,
                        'status': batch_task.status.value,
                        'progress': batch_task.progress,
                        'document_count': len(batch_task.document_ids),
                        'created_at': batch_task.created_at.isoformat()
                    })
            
            return active_batches
            
        except Exception as e:
            logger.error(f"Get active batches failed: {e}")
            return []
    
    def cleanup_completed_batches(self, max_age_hours: int = 24) -> int:
        """Clean up completed batches older than specified hours"""
        try:
            cutoff_time = timezone.now() - timezone.timedelta(hours=max_age_hours)
            cleaned_count = 0
            
            batch_ids_to_remove = []
            
            for batch_id, batch_task in self.active_batches.items():
                if (batch_task.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED] and
                    batch_task.completed_at and batch_task.completed_at < cutoff_time):
                    batch_ids_to_remove.append(batch_id)
            
            for batch_id in batch_ids_to_remove:
                del self.active_batches[batch_id]
                cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} completed batches")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Cleanup completed batches failed: {e}")
            return 0


# Global batch processor instance
batch_processor = BatchProcessor()
