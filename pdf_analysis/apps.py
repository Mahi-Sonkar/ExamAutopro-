from django.apps import AppConfig

class PdfAnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pdf_analysis'
    verbose_name = 'PDF Analysis'
    
    def ready(self):
        # Import signals when app is ready
        try:
            import pdf_analysis.signals
        except ImportError:
            pass
