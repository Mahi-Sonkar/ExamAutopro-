from django.contrib import admin
from .models import ProctoringSession, ProctoringEvent, ProctoringAlert

@admin.register(ProctoringSession)
class ProctoringSessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'start_time', 'end_time', 'status', 'suspicious_activities']
    list_filter = ['status', 'start_time', 'exam']
    search_fields = ['student__email', 'exam__title']
    readonly_fields = ['start_time', 'end_time']

@admin.register(ProctoringEvent)
class ProctoringEventAdmin(admin.ModelAdmin):
    list_display = ['session', 'event_type', 'timestamp', 'severity']
    list_filter = ['event_type', 'severity', 'timestamp']
    search_fields = ['session__student__email', 'description']
    readonly_fields = ['timestamp']

@admin.register(ProctoringAlert)
class ProctoringAlertAdmin(admin.ModelAdmin):
    list_display = ['session', 'alert_type', 'severity', 'created_at', 'acknowledged']
    list_filter = ['alert_type', 'severity', 'acknowledged', 'created_at']
    search_fields = ['session__student__email', 'message']
    readonly_fields = ['created_at']
