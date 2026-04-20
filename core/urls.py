"""
URLs for Core Analysis System - ExamAutoPro
Main motive: RESTful API and scoring configuration routing
"""

from django.urls import path
from . import api_views, views

app_name = 'core'

urlpatterns = [
    # Scoring Configuration Views
    path('scoring-dashboard/', views.scoring_dashboard, name='scoring_dashboard'),
    path('scoring-config/create/', views.ScoringConfigurationCreateView.as_view(), name='scoring_config_create'),
    path('scoring-config/<int:pk>/update/', views.ScoringConfigurationUpdateView.as_view(), name='scoring_config_update'),
    path('scoring-config/<int:config_id>/questions/', views.question_wise_scoring, name='question_wise_scoring'),
    path('scoring-config/<int:config_id>/similarity/', views.similarity_range_settings, name='similarity_range_settings'),
    path('scoring-config/<int:config_id>/preview/', views.scoring_preview, name='scoring_preview'),
    path('scoring-config/<int:config_id>/bulk-setup/', views.bulk_question_setup, name='bulk_question_setup'),
    path('scoring-config/<int:config_id>/delete-range/', views.delete_question_range, name='delete_question_range'),
    path('scoring-config/<int:config_id>/export/', views.export_scoring_config, name='export_scoring_config'),
    path('evaluation-templates/', views.evaluation_templates, name='evaluation_templates'),
    path('bulk-upload/', views.bulk_question_upload, name='bulk_question_upload'),
    path('import-config/', views.import_scoring_config, name='import_scoring_config'),
    
    # Document Analysis APIs
    path('api/documents/analyze/', api_views.DocumentAnalysisAPI.as_view(), name='api_document_analyze'),
    path('api/documents/status/', api_views.DocumentAnalysisAPI.as_view(), name='api_document_status'),
    
    # Health Check API
    path('api/health/', api_views.HealthCheckAPI.as_view(), name='api_health'),
    
    # Answer Sheet Evaluation APIs
    path('api/evaluate-answer-sheet/', api_views.EvaluateAnswerSheetAPI.as_view(), name='api_evaluate_answer_sheet'),
]
