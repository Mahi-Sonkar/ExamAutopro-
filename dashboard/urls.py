from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('analytics/', views.ExamAnalyticsView.as_view(), name='analytics'),
]
