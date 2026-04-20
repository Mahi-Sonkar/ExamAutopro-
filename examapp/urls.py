"""
Exam App URLs - Complete PDF Evaluation System
"""

from django.urls import path
from . import views

app_name = 'examapp'

urlpatterns = [
    # PDF Evaluation API
    path('api/evaluate-pdf/', views.EvaluatePDFView.as_view(), name='evaluate_pdf'),
]
