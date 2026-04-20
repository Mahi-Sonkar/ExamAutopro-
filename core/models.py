"""
Scoring Configuration Models for ExamAutoPro
Main motive: Teacher scoring configuration and evaluation settings
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class ScoringConfiguration(models.Model):
    """Teacher scoring configuration for exams"""
    
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    
    class Meta:
        app_label = 'core'
        verbose_name = "Scoring Configuration"
        verbose_name_plural = "Scoring Configurations"
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, null=True, blank=True)
    
    # Similarity range settings
    full_marks_threshold = models.FloatField(
        default=0.8,
        help_text="Minimum similarity percentage for full marks (0.0-1.0)"
    )
    partial_marks_threshold = models.FloatField(
        default=0.6,
        help_text="Minimum similarity percentage for partial marks (0.0-1.0)"
    )
    minimum_marks_threshold = models.FloatField(
        default=0.4,
        help_text="Minimum similarity percentage for minimum marks (0.0-1.0)"
    )
    
    # Scoring percentages
    full_marks_percentage = models.FloatField(
        default=100.0,
        help_text="Percentage of marks to award for full similarity"
    )
    partial_marks_percentage = models.FloatField(
        default=50.0,
        help_text="Percentage of marks to award for partial similarity"
    )
    minimum_marks_percentage = models.FloatField(
        default=25.0,
        help_text="Percentage of marks to award for minimum similarity"
    )
    
    # Additional settings
    keyword_weight = models.FloatField(
        default=0.4,
        help_text="Weight for keyword matching (0.0-1.0)"
    )
    concept_weight = models.FloatField(
        default=0.3,
        help_text="Weight for concept understanding (0.0-1.0)"
    )
    structure_weight = models.FloatField(
        default=0.3,
        help_text="Weight for answer structure (0.0-1.0)"
    )
    
    # Grace marks settings
    enable_grace_marks = models.BooleanField(default=True)
    grace_marks_percentage = models.FloatField(
        default=10.0,
        help_text="Maximum grace marks percentage"
    )
    borderline_threshold = models.FloatField(
        default=55.0,
        help_text="Borderline score threshold for grace marks"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Scoring Configuration"
        verbose_name_plural = "Scoring Configurations"
        unique_together = ['teacher', 'exam']
    
    def __str__(self):
        return f"{self.teacher.username} - {self.exam.title if self.exam else 'Default'}"

class QuestionWiseScoring(models.Model):
    """Question-wise marks and scoring setup"""
    
    scoring_config = models.ForeignKey(ScoringConfiguration, on_delete=models.CASCADE)
    question_number = models.IntegerField()
    question_text = models.TextField(blank=True)
    max_marks = models.FloatField(default=1.0)
    
    # Question-specific settings
    question_type = models.CharField(
        max_length=20,
        choices=[
            ('mcq', 'Multiple Choice'),
            ('short_answer', 'Short Answer'),
            ('essay', 'Essay'),
            ('fill_blank', 'Fill in the Blank'),
            ('matching', 'Matching'),
            ('numerical', 'Numerical'),
        ],
        default='short_answer'
    )
    
    # Similarity thresholds for this specific question
    custom_full_threshold = models.FloatField(
        null=True, blank=True,
        help_text="Custom full marks threshold (overrides global)"
    )
    custom_partial_threshold = models.FloatField(
        null=True, blank=True,
        help_text="Custom partial marks threshold (overrides global)"
    )
    custom_minimum_threshold = models.FloatField(
        null=True, blank=True,
        help_text="Custom minimum marks threshold (overrides global)"
    )
    
    # Required keywords (for descriptive questions)
    required_keywords = models.TextField(
        blank=True,
        help_text="Comma-separated keywords required for full marks"
    )
    
    # Evaluation method
    evaluation_method = models.CharField(
        max_length=20,
        choices=[
            ('automatic', 'Automatic'),
            ('manual', 'Manual'),
            ('hybrid', 'Hybrid'),
        ],
        default='automatic'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Question Wise Scoring"
        verbose_name_plural = "Question Wise Scoring"
        unique_together = ['scoring_config', 'question_number']
        ordering = ['question_number']
    
    def __str__(self):
        return f"Q{self.question_number} - {self.max_marks} marks"
    
    def get_keywords_list(self):
        """Get keywords as list"""
        if self.required_keywords:
            return [kw.strip() for kw in self.required_keywords.split(',') if kw.strip()]
        return []
    
    def get_effective_thresholds(self):
        """Get effective thresholds (custom or global)"""
        config = self.scoring_config
        
        return {
            'full': self.custom_full_threshold or config.full_marks_threshold,
            'partial': self.custom_partial_threshold or config.partial_marks_threshold,
            'minimum': self.custom_minimum_threshold or config.minimum_marks_threshold,
        }

class EvaluationTemplate(models.Model):
    """Reusable evaluation templates"""
    
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Template configuration (JSON)
    configuration = models.JSONField(
        default=dict,
        help_text="Scoring configuration as JSON"
    )
    
    # Question template
    question_template = models.JSONField(
        default=dict,
        help_text="Question-wise scoring template"
    )
    
    is_public = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Evaluation Template"
        verbose_name_plural = "Evaluation Templates"
        unique_together = ['teacher', 'name']
    
    def __str__(self):
        return f"{self.teacher.username} - {self.name}"
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

class ScoringRule(models.Model):
    """Advanced scoring rules"""
    
    scoring_config = models.ForeignKey(ScoringConfiguration, on_delete=models.CASCADE)
    
    rule_name = models.CharField(max_length=100)
    rule_type = models.CharField(
        max_length=20,
        choices=[
            ('similarity', 'Similarity Based'),
            ('keyword', 'Keyword Based'),
            ('length', 'Length Based'),
            ('structure', 'Structure Based'),
            ('custom', 'Custom Rule'),
        ],
        default='similarity'
    )
    
    # Rule conditions (JSON)
    conditions = models.JSONField(
        default=dict,
        help_text="Rule conditions as JSON"
    )
    
    # Rule actions
    action_type = models.CharField(
        max_length=20,
        choices=[
            ('add_marks', 'Add Marks'),
            ('multiply', 'Multiply'),
            ('set_marks', 'Set Marks'),
            ('skip_question', 'Skip Question'),
        ],
        default='add_marks'
    )
    
    action_value = models.FloatField(default=0.0)
    
    # Rule priority and status
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Scoring Rule"
        verbose_name_plural = "Scoring Rules"
        ordering = ['-priority', 'created_at']
    
    def __str__(self):
        return f"{self.rule_name} - {self.scoring_config}"

class BulkQuestionUpload(models.Model):
    """Bulk question upload and scoring setup"""
    
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE)
    
    # Upload file
    upload_file = models.FileField(upload_to='bulk_uploads/')
    file_type = models.CharField(
        max_length=10,
        choices=[
            ('excel', 'Excel'),
            ('csv', 'CSV'),
            ('json', 'JSON'),
            ('pdf', 'PDF'),
        ],
        default='excel'
    )
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # Results
    total_questions = models.IntegerField(default=0)
    processed_questions = models.IntegerField(default=0)
    failed_questions = models.IntegerField(default=0)
    
    # Error log
    error_log = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Bulk Question Upload"
        verbose_name_plural = "Bulk Question Uploads"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.teacher.username} - {self.exam.title} - {self.status}"
    
    def mark_completed(self):
        """Mark upload as completed"""
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save()

class ScoringRange(models.Model):
    """
    Model to define scoring ranges for AI evaluation.
    Allows teachers to configure different scoring rules based on similarity thresholds.
    """
    
    name = models.CharField(max_length=100, help_text="Name of this scoring rule")
    description = models.TextField(blank=True, null=True, help_text="Description of when this rule applies")
    
    # Similarity range (0.0 to 1.0)
    min_score = models.FloatField(default=0.0, help_text="Minimum similarity score (0.0 to 1.0)")
    max_score = models.FloatField(default=1.0, help_text="Maximum similarity score (0.0 to 1.0)")
    
    # Marks allocation
    marks = models.IntegerField(help_text="Marks to award for this similarity range")
    
    # Additional fields for flexibility
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'}, related_name='core_scoring_ranges')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Scoring Range"
        verbose_name_plural = "Scoring Ranges"
        ordering = ['-min_score']

    def __str__(self):
        return f"{self.name} ({self.min_score:.2f}-{self.max_score:.2f} = {self.marks} marks)"

    def clean(self):
        if self.min_score > self.max_score:
            from django.core.exceptions import ValidationError
            raise ValidationError("Minimum score cannot be greater than maximum score.")
        
        if self.min_score < 0 or self.max_score > 1:
            from django.core.exceptions import ValidationError
            raise ValidationError("Similarity scores must be between 0.0 and 1.0.")
        
        if self.marks < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError("Marks cannot be negative.")
