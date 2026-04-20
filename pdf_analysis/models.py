from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import uuid
import os

User = get_user_model()

def pdf_upload_path(instance, filename):
    """Generate unique path for PDF uploads"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('pdfs', 'uploads', filename)

class PDFDocument(models.Model):
    """Model for storing uploaded PDF documents"""
    
    ANALYSIS_STATUS_CHOICES = [
        ('pending', 'Pending Analysis'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    DOCUMENT_TYPE_CHOICES = [
        ('exam_paper', 'Exam Paper'),
        ('question_bank', 'Question Bank'),
        ('study_material', 'Study Material'),
        ('answer_sheet', 'Answer Sheet'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    pdf_file = models.FileField(
        upload_to=pdf_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'gif'])]
    )
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPE_CHOICES, 
        default='other'
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    analysis_status = models.CharField(
        max_length=20, 
        choices=ANALYSIS_STATUS_CHOICES, 
        default='pending'
    )
    file_size = models.BigIntegerField(null=True, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'PDF Document'
        verbose_name_plural = 'PDF Documents'
    
    def __str__(self):
        return f"{self.title} - {self.uploaded_by.email}"
    
    def save(self, *args, **kwargs):
        if self.pdf_file and not self.file_size:
            self.file_size = self.pdf_file.size
        super().save(*args, **kwargs)

class PDFAnalysisResult(models.Model):
    """Model for storing PDF analysis results"""
    
    pdf_document = models.OneToOneField(
        PDFDocument, 
        on_delete=models.CASCADE, 
        related_name='analysis_result'
    )
    
    # OCR Results
    extracted_text = models.TextField(blank=True)
    ocr_confidence = models.FloatField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    
    # NLP Analysis Results
    word_count = models.IntegerField(null=True, blank=True)
    sentence_count = models.IntegerField(null=True, blank=True)
    paragraph_count = models.IntegerField(null=True, blank=True)
    
    # Content Analysis
    language_detected = models.CharField(max_length=10, blank=True)
    readability_score = models.FloatField(null=True, blank=True)
    complexity_score = models.FloatField(null=True, blank=True)
    
    # Topic Analysis
    main_topics = models.JSONField(default=list, blank=True)
    keywords = models.JSONField(default=list, blank=True)
    entities = models.JSONField(default=dict, blank=True)
    
    # Question Detection (for exam papers)
    detected_questions = models.JSONField(default=list, blank=True)
    question_count = models.IntegerField(null=True, blank=True)
    question_types = models.JSONField(default=dict, blank=True)
    
    # Enhanced Analysis Fields
    overall_score = models.FloatField(null=True, blank=True)
    score_category = models.CharField(max_length=20, blank=True)
    summary = models.TextField(blank=True)
    content_analysis = models.JSONField(default=dict, blank=True)
    complexity_analysis = models.JSONField(default=dict, blank=True)
    question_analysis = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    
    # Sentiment Analysis
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_label = models.CharField(max_length=20, blank=True)
    
    # Summary
    auto_summary = models.TextField(blank=True)
    key_points = models.JSONField(default=list, blank=True)
    
    # Metadata
    analyzed_at = models.DateTimeField(auto_now_add=True)
    analysis_version = models.CharField(max_length=10, default='1.0')
    
    class Meta:
        verbose_name = 'PDF Analysis Result'
        verbose_name_plural = 'PDF Analysis Results'
    
    def __str__(self):
        return f"Analysis of {self.pdf_document.title}"

class PDFProcessingLog(models.Model):
    """Model for tracking PDF processing logs"""
    
    LOG_LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]
    
    pdf_document = models.ForeignKey(
        PDFDocument, 
        on_delete=models.CASCADE, 
        related_name='processing_logs'
    )
    log_level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Processing Log'
        verbose_name_plural = 'Processing Logs'
    
    def __str__(self):
        return f"{self.pdf_document.title} - {self.log_level.upper()}"

class PDFQuestion(models.Model):
    """Model for storing questions extracted from PDF"""
    
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
        ('fill_blank', 'Fill in the Blank'),
        ('matching', 'Matching'),
        ('unknown', 'Unknown'),
    ]
    
    pdf_document = models.ForeignKey(
        PDFDocument, 
        on_delete=models.CASCADE, 
        related_name='extracted_questions'
    )
    
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20, 
        choices=QUESTION_TYPE_CHOICES, 
        default='unknown'
    )
    options = models.JSONField(default=list, blank=True)  # For MCQ
    correct_answer = models.TextField(blank=True)
    marks = models.IntegerField(null=True, blank=True)
    page_number = models.IntegerField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['page_number', 'created_at']
        verbose_name = 'Extracted Question'
        verbose_name_plural = 'Extracted Questions'
    
    def __str__(self):
        return f"Question from {self.pdf_document.title} (Page {self.page_number})"
