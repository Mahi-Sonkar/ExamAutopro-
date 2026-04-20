from django.urls import path
from . import views

urlpatterns = [
    path('', views.ExamListView.as_view(), name='exam_list'),
    path('create/', views.ExamCreateView.as_view(), name='exam_create'),
    path('<int:pk>/', views.ExamDetailView.as_view(), name='exam_detail'),
    path('<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_update'),
    path('<int:exam_id>/add-question/', views.create_question, name='create_question'),
    path('<int:exam_id>/take/', views.take_exam, name='take_exam'),
    path('<int:exam_id>/submit/', views.submit_exam, name='submit_exam'),
    path('<int:exam_id>/results/', views.exam_results, name='exam_results'),
    path('<int:pk>/publish/', views.publish_exam, name='publish_exam'),
    path('search/', views.search_exams, name='search_exams'),
]
