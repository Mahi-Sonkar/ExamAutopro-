from django.contrib import admin
from .models import Exam, Question, Answer, ExamSubmission, QuestionOption

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'exam_type', 'duration', 'total_marks', 'created_at']
    list_filter = ['exam_type', 'created_at', 'teacher']
    search_fields = ['title', 'description', 'teacher__email']
    readonly_fields = ['created_at', 'updated_at']

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'exam', 'question_type', 'marks', 'created_at']
    list_filter = ['question_type', 'exam', 'created_at']
    search_fields = ['question_text', 'exam__title']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [QuestionOptionInline]

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'submission', 'is_correct', 'marks_obtained', 'submitted_at']
    list_filter = ['is_correct', 'submitted_at', 'question__exam']
    search_fields = ['submission__student__email', 'question__question_text']
    readonly_fields = ['submitted_at']

@admin.register(ExamSubmission)
class ExamSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'status', 'total_marks_obtained', 'submitted_at']
    list_filter = ['status', 'submitted_at', 'exam']
    search_fields = ['student__email', 'exam__title']
    readonly_fields = ['submitted_at', 'started_at']
