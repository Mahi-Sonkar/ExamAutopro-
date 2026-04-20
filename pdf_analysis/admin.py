from django.contrib import admin
from .models import PDFDocument, PDFAnalysisResult, PDFProcessingLog, PDFQuestion

@admin.register(PDFDocument)
class PDFDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'uploaded_by', 'analysis_status', 'uploaded_at', 'file_size']
    list_filter = ['document_type', 'analysis_status', 'uploaded_at']
    search_fields = ['title', 'description', 'uploaded_by__email']
    readonly_fields = ['id', 'file_size', 'page_count', 'uploaded_at']
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'document_type')
        }),
        ('File Information', {
            'fields': ('pdf_file', 'uploaded_by', 'analysis_status')
        }),
        ('Metadata', {
            'fields': ('id', 'file_size', 'page_count', 'uploaded_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(PDFAnalysisResult)
class PDFAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['pdf_document', 'word_count', 'question_count', 'language_detected', 'analyzed_at']
    list_filter = ['language_detected', 'analyzed_at']
    search_fields = ['pdf_document__title']
    readonly_fields = ['pdf_document', 'analyzed_at', 'analysis_version']
    
    fieldsets = (
        ('Document', {
            'fields': ('pdf_document', 'analyzed_at', 'analysis_version')
        }),
        ('OCR Results', {
            'fields': ('extracted_text', 'ocr_confidence', 'processing_time'),
            'classes': ('collapse',)
        }),
        ('Text Statistics', {
            'fields': ('word_count', 'sentence_count', 'paragraph_count', 'language_detected')
        }),
        ('Content Analysis', {
            'fields': ('readability_score', 'complexity_score', 'sentiment_score', 'sentiment_label')
        }),
        ('Topic Analysis', {
            'fields': ('main_topics', 'keywords', 'entities'),
            'classes': ('collapse',)
        }),
        ('Question Analysis', {
            'fields': ('detected_questions', 'question_count', 'question_types'),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('auto_summary', 'key_points'),
            'classes': ('collapse',)
        })
    )

@admin.register(PDFProcessingLog)
class PDFProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['pdf_document', 'log_level', 'message', 'timestamp']
    list_filter = ['log_level', 'timestamp']
    search_fields = ['pdf_document__title', 'message']
    readonly_fields = ['pdf_document', 'log_level', 'message', 'details', 'timestamp']
    date_hierarchy = 'timestamp'

@admin.register(PDFQuestion)
class PDFQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'question_type', 'pdf_document', 'page_number', 'marks', 'confidence_score']
    list_filter = ['question_type', 'pdf_document', 'page_number']
    search_fields = ['question_text', 'pdf_document__title']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Question Information', {
            'fields': ('question_text', 'question_type', 'options', 'correct_answer', 'marks')
        }),
        ('Location', {
            'fields': ('pdf_document', 'page_number', 'confidence_score')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
