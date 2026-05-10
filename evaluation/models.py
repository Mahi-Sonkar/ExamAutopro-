from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()

class QuestionPaper(models.Model):
    """Model for storing question papers with questions and marks"""
    
    id = models.UUIDField(primary_key=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

class Question(models.Model):
    """Model for storing individual questions with marks"""
    
    QUESTION_TYPES = [
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
    ]
    
    question_paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE, related_name='questions')
    question_number = models.PositiveIntegerField()
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='short_answer')
    marks = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    model_answer = models.TextField(blank=True)
    
    def __str__(self):
        return f"Q{self.question_number}: {self.question_text[:50]}..."
    
    class Meta:
        ordering = ['question_number']
        unique_together = ['question_paper', 'question_number']

class PDFEvaluationResult(models.Model):
    """Model for storing evaluation results for uploaded PDF answer sheets"""
    
    answer_sheet = models.ForeignKey('pdf_analysis.PDFDocument', on_delete=models.CASCADE)
    question_paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE)
    
    total_marks = models.FloatField(default=0.0)
    obtained_marks = models.FloatField(default=0.0)
    percentage = models.FloatField(default=0.0)
    
    evaluation_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"PDF Evaluation: {self.obtained_marks}/{self.total_marks} ({self.percentage:.1f}%)"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "PDF Evaluation Result"
        verbose_name_plural = "PDF Evaluation Results"

class ScoringRange(models.Model):
    """
    Model to define scoring ranges for AI evaluation.
    Allows teachers to configure different scoring rules based on similarity thresholds.
    """
    
    name = models.CharField(max_length=100, help_text="Name of this scoring rule")
    description = models.TextField(blank=True, null=True, help_text="Description of when this rule applies")
    
    # Similarity range
    min_similarity = models.FloatField(default=0.0, help_text="Minimum similarity score (0.0 to 1.0)")
    max_similarity = models.FloatField(default=1.0, help_text="Maximum similarity score (0.0 to 1.0)")
    
    # Original fields - keeping only working fields
    marks_percentage = models.FloatField(help_text="Percentage of total marks to award for this range (0 to 100)")
    
    # Question and marks information
    total_questions = models.IntegerField(default=0, help_text="Total number of questions in this evaluation")
    total_marks = models.FloatField(default=0.0, help_text="Total marks for all questions")
    marks_per_question = models.FloatField(default=0.0, help_text="Marks allocated per question")
    
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, null=True, blank=True, related_name='scoring_ranges', help_text="If null, rule applies globally")
    pdf_document = models.ForeignKey('pdf_analysis.PDFDocument', on_delete=models.CASCADE, null=True, blank=True, related_name='scoring_ranges', help_text="If set, rule applies specifically to this PDF")
    
    # Image upload for automatic PDF analysis creation
    paper_image = models.ImageField(upload_to='scoring_ranges/papers/', null=True, blank=True, help_text="Upload an image of the paper to automatically create a PDF analysis")
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Scoring Range"
        verbose_name_plural = "Scoring Ranges"

    def __str__(self):
        return f"{self.name} ({self.min_similarity:.2f}-{self.max_similarity:.2f})"

    def clean(self):
        if self.min_similarity > self.max_similarity:
            from django.core.exceptions import ValidationError
            raise ValidationError("Minimum similarity cannot be greater than maximum similarity.")
        
        if self.marks_percentage < 0 or self.marks_percentage > 100:
            from django.core.exceptions import ValidationError
            raise ValidationError("Marks percentage must be between 0 and 100.")
        
        if self.total_questions < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError("Total questions cannot be negative.")
        
        if self.total_marks < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError("Total marks cannot be negative.")
        
        if self.marks_per_question < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError("Marks per question cannot be negative.")

class EvaluationResult(models.Model):
    """
    Stores the results of AI evaluation for each answer.
    """
    answer = models.OneToOneField('exams.Answer', on_delete=models.CASCADE)
    similarity_score = models.FloatField(default=0.0, help_text="Similarity score from NLP analysis")
    keyword_match_score = models.FloatField(default=0.0, help_text="Score based on keyword matching")
    confidence_score = models.FloatField(default=0.0, help_text="Confidence score of AI evaluation")
    initial_score = models.FloatField(default=0.0, help_text="Initial score from AI evaluation")
    grace_marks_applied = models.FloatField(default=0.0, help_text="Grace marks applied")
    final_score = models.FloatField(default=0.0, help_text="Final score after grace marks")
    feedback = models.TextField(default='', help_text="AI-generated feedback")
    evaluation_time = models.DateTimeField(auto_now_add=True)
    evaluation_method = models.CharField(max_length=50, default='nlp', help_text="Method used for evaluation")

    class Meta:
        ordering = ['-evaluation_time']

    def __str__(self):
        return f"Evaluation for {self.answer} - Score: {self.final_score}"

class GraceMarksRule(models.Model):
    """
    Rules for applying grace marks based on various conditions.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    condition_type = models.CharField(max_length=50, choices=[
        ('similarity_threshold', 'Similarity Threshold'),
        ('keyword_count', 'Keyword Count'),
        ('manual', 'Manual Override'),
    ])
    condition_value = models.FloatField(help_text="Value for the condition")
    grace_marks = models.FloatField(help_text="Grace marks to apply")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.grace_marks} marks"

class EvaluationLog(models.Model):
    """
    Logs all evaluation activities for audit purposes.
    """
    answer = models.ForeignKey('exams.Answer', on_delete=models.CASCADE)
    action = models.CharField(max_length=100, default='evaluated')
    details = models.TextField(default='')
    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.answer} at {self.timestamp}"

class OCREvaluation(models.Model):
    """
    Stores OCR evaluation results for handwritten answers.
    """
    answer = models.OneToOneField('exams.Answer', on_delete=models.CASCADE)
    extracted_text = models.TextField(default='', help_text="Text extracted from handwritten answer")
    confidence_score = models.FloatField(default=0.0, help_text="Confidence score of OCR extraction")
    processing_time = models.FloatField(default=0.0, help_text="Time taken for OCR processing")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OCR for {self.answer} - Confidence: {self.confidence_score}"

class NLPEvaluation(models.Model):
    """
    Stores NLP evaluation results.
    """
    answer = models.OneToOneField('exams.Answer', on_delete=models.CASCADE)
    text_similarity = models.FloatField(default=0.0, help_text="Text similarity score")
    semantic_similarity = models.FloatField(default=0.0, help_text="Semantic similarity score")
    keyword_matches = models.JSONField(default=dict, help_text="Keyword matching results")
    processing_time = models.FloatField(default=0.0, help_text="Time taken for NLP processing")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"NLP for {self.answer} - Similarity: {self.text_similarity}"
