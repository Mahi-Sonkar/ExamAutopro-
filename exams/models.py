from django.db import models
from django.conf import settings
import re

class Exam(models.Model):
    EXAM_TYPES = [
        ('mcq', 'Multiple Choice Questions'),
        ('descriptive', 'Descriptive Questions'),
        ('mixed', 'Mixed Type'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, default='mixed')
    duration = models.IntegerField(help_text="Duration in minutes")
    total_marks = models.IntegerField(default=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    instructions = models.TextField(blank=True, null=True)
    allow_multiple_attempts = models.BooleanField(default=False)
    max_attempts = models.IntegerField(default=1)
    show_results_immediately = models.BooleanField(default=False)
    negative_marking = models.BooleanField(default=False)
    negative_marks_percentage = models.IntegerField(default=0, help_text="Percentage of marks to deduct for wrong answers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.teacher.email}"
    
    @property
    def status_color(self):
        colors = {
            'draft': 'secondary',
            'published': 'success',
            'ongoing': 'primary',
            'completed': 'info',
        }
        return colors.get(self.status, 'secondary')
    
    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.status == 'published'
    
    @property
    def total_questions(self):
        return self.questions.count()

class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice Question'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('long_answer', 'Long Answer'),
        ('essay', 'Essay'),
    ]
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    marks = models.IntegerField(default=1)
    required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    model_answer = models.TextField(blank=True, null=True, help_text="Model answer for descriptive questions")
    keywords = models.TextField(blank=True, null=True, help_text="Comma-separated keywords for evaluation")
    has_image = models.BooleanField(default=False)
    question_image = models.ImageField(upload_to='question_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.question.question_text[:30]} - {self.option_text[:30]}"

class ExamSubmission(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('evaluated', 'Evaluated'),
        ('cancelled', 'Cancelled'),
    ]
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    total_marks_obtained = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    attempt_number = models.IntegerField(default=1)
    time_taken = models.IntegerField(default=0, help_text="Time taken in seconds")
    
    class Meta:
        unique_together = ['student', 'exam', 'attempt_number']
    
    def __str__(self):
        return f"{self.student.email} - {self.exam.title} (Attempt {self.attempt_number})"
    
    @property
    def status_color(self):
        colors = {
            'in_progress': 'warning',
            'submitted': 'info',
            'evaluated': 'success',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')

class Answer(models.Model):
    submission = models.ForeignKey(ExamSubmission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    marks_obtained = models.IntegerField(default=0)
    feedback = models.TextField(blank=True, null=True)
    evaluated_by_ai = models.BooleanField(default=False)
    confidence_score = models.FloatField(default=0.0, help_text="AI confidence in evaluation")
    uploaded_file = models.FileField(upload_to='handwritten_answers/', blank=True, null=True, help_text="PDF or Image of the handwritten answer")
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['submission', 'question']
    
    def __str__(self):
        return f"Answer for {self.question.question_text[:30]} by {self.submission.student.email}"

    @property
    def correct_answer_text(self):
        correct_options = list(self.question.options.filter(is_correct=True))
        if correct_options:
            return ", ".join(option.option_text for option in correct_options)

        feedback = self.feedback or ""
        match = re.search(r"Correct answer:\s*(.+?)(?:\s*\||$)", feedback, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

        if self.is_correct and self.selected_option:
            return self.selected_option.option_text

        return ""
