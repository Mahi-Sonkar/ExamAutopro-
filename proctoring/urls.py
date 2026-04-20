from django.urls import path
from . import views

urlpatterns = [
    path('start/<int:exam_id>/', views.start_proctoring_session, name='start_proctoring'),
    path('event/<str:session_id>/', views.log_proctoring_event, name='log_event'),
    path('end/<str:session_id>/', views.end_proctoring_session, name='end_proctoring'),
    path('dashboard/<int:exam_id>/', views.get_proctoring_dashboard, name='proctoring_dashboard'),
    path('acknowledge/<int:alert_id>/', views.acknowledge_alert, name='acknowledge_alert'),
    path('terminate/<str:session_id>/', views.terminate_session, name='terminate_session'),
    path('decline/<str:session_id>/', views.decline_exam_on_violation, name='decline_exam'),
]
