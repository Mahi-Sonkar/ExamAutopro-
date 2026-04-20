from django.urls import path
from . import views

urlpatterns = [
    # PDF document management
    path('', views.pdf_list_view, name='pdf_list'),
    path('upload/', views.pdf_upload_view, name='pdf_upload'),
    path('analysis/', views.pdf_analysis_view, name='pdf_analysis'),
    path('list/', views.pdf_list_view, name='pdf_list_view'),
    path('api/upload/', views.upload_pdf_api, name='upload_pdf_api'),
    path('api/evaluate/', views.evaluate_answer_sheet_api, name='evaluate_answer_sheet_api'),
    path('api/quick-evaluate/', views.quick_evaluate_api, name='quick_evaluate_api'),
    path('<uuid:pk>/', views.pdf_detail_view, name='pdf_detail'),
    path('<uuid:pk>/analysis/', views.pdf_analysis_detail_view, name='pdf_analysis'),
    path('<uuid:pk>/retry/', views.pdf_retry_view, name='pdf_retry'),
    path('<uuid:pk>/delete/', views.pdf_delete_view, name='pdf_delete'),
    path('<uuid:pk>/export/', views.pdf_export_view, name='pdf_export'),
]
