"""
Core App Configuration for ExamAutoPro
Main motive: Backend analysis and intelligent processing
"""

from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Analysis Engine'
    
    def ready(self):
        # Import signals when app is ready
        try:
            import core.signals
        except ImportError:
            pass
        
        # Temporarily comment out core component imports to fix server startup
# from .enhanced_evaluation_engine import EnhancedEvaluationEngine
# from .proctoring_engine import ProctoringEngine
# from .analysis_engine import AnalysisEngine
# from .processing_pipeline import ProcessingPipeline
# from .question_analyzer import QuestionAnalyzer
# from .exam_evaluator import ExamEvaluator

        # Log initialization
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Core app initialized successfully")
