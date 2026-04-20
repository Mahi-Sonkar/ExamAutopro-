from django.contrib import admin
from .models import EvaluationResult, GraceMarksRule, EvaluationLog, ScoringRange

@admin.register(ScoringRange)
class ScoringRangeAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_similarity', 'max_similarity', 'marks_percentage', 'exam', 'is_active']
    list_filter = ['is_active', 'exam']
    search_fields = ['name', 'description']

@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ['answer', 'final_score', 'grace_marks_applied', 'confidence_score', 'evaluation_time']
    list_filter = ['grace_marks_applied']
    search_fields = ['answer__question__question_text', 'answer__submission__student__email']
    readonly_fields = ['evaluation_time']

@admin.register(GraceMarksRule)
class GraceMarksRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'condition_type', 'condition_value', 'grace_marks', 'is_active']
    list_filter = ['condition_type', 'is_active']
    search_fields = ['name', 'description']

@admin.register(EvaluationLog)
class EvaluationLogAdmin(admin.ModelAdmin):
    list_display = ['answer', 'action', 'timestamp', 'user']
    list_filter = ['timestamp']
    search_fields = ['answer__question__question_text', 'details']
    readonly_fields = ['timestamp']
