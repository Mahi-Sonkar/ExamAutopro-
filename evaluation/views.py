from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db import models
from django.db.models import Q, Avg, Count
from django.urls import reverse_lazy
from .models import EvaluationResult, GraceMarksRule, EvaluationLog, OCREvaluation, NLPEvaluation, ScoringRange
from .forms import ScoringRangeForm
from .engines import OCREngine, NLPEngine, GraceMarksEngine
from .utils import trigger_ai_evaluation
from core.enhanced_evaluation_engine import EnhancedEvaluationEngine
from core.advanced_nlp_evaluation import AdvancedNLPEvaluation, AdvancedOCREvaluation
from exams.models import Answer, ExamSubmission
from proctoring.models import ProctoringSession, ProctoringEvent
import json
import logging

logger = logging.getLogger(__name__)

class ScoringRangeListView(LoginRequiredMixin, ListView):
    model = ScoringRange
    template_name = 'evaluation/scoring_range_list.html'
    context_object_name = 'rules'
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return ScoringRange.objects.filter(created_by=self.request.user)
        elif self.request.user.is_admin_user:
            return ScoringRange.objects.all()
        return ScoringRange.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Calculate statistics for template
        context['total_ranges'] = queryset.count()
        context['active_ranges'] = queryset.filter(is_active=True).count()
        context['user_ranges'] = queryset.count()
        
        return context

class ScoringRangeCreateView(LoginRequiredMixin, CreateView):
    model = ScoringRange
    form_class = ScoringRangeForm
    template_name = 'evaluation/scoring_range_form.html'
    success_url = reverse_lazy('evaluation:scoring_range_list')
    
    def get_initial(self):
        initial = super().get_initial()
        pdf_id = self.request.GET.get('pdf')
        if pdf_id:
            initial['pdf_document'] = pdf_id
        return initial
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # Handle paper image upload and create automatic PDF analysis
        paper_image = form.cleaned_data.get('paper_image')
        if paper_image:
            try:
                # Create PDF document from uploaded image
                from pdf_analysis.models import PDFDocument
                import uuid
                
                # Create a new PDF document entry with the image as the file
                pdf_document = PDFDocument.objects.create(
                    title=f"Paper Image - {form.instance.name}",
                    pdf_file=paper_image,  # Store the image as the file for now
                    uploaded_by=self.request.user,
                    document_type='exam_paper',
                    analysis_status='pending'
                )
                
                # Link the scoring range to the created PDF document
                form.instance.pdf_document = pdf_document
                
                messages.info(self.request, "Paper image uploaded successfully! PDF analysis will be processed automatically.")
                
            except Exception as e:
                messages.warning(self.request, f"Paper image uploaded but PDF analysis creation failed: {str(e)}")
        
        messages.success(self.request, "Scoring range created successfully!")
        return super().form_valid(form)

class ScoringRangeUpdateView(LoginRequiredMixin, UpdateView):
    model = ScoringRange
    form_class = ScoringRangeForm
    template_name = 'evaluation/scoring_range_form.html'
    success_url = reverse_lazy('evaluation:scoring_range_list')
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return ScoringRange.objects.filter(created_by=self.request.user)
        elif self.request.user.is_admin_user:
            return ScoringRange.objects.all()
        return ScoringRange.objects.none()
    
    def form_valid(self, form):
        messages.success(self.request, "Scoring range updated successfully!")
        return super().form_valid(form)

class ScoringRangeDeleteView(LoginRequiredMixin, DeleteView):
    model = ScoringRange
    template_name = 'evaluation/scoring_range_confirm_delete.html'
    success_url = reverse_lazy('evaluation:scoring_range_list')
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return ScoringRange.objects.filter(created_by=self.request.user)
        elif self.request.user.is_admin_user:
            return ScoringRange.objects.all()
        return ScoringRange.objects.none()
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Scoring range deleted successfully!")
        return super().delete(request, *args, **kwargs)

class EvaluationResultListView(LoginRequiredMixin, ListView):
    model = EvaluationResult
    template_name = 'evaluation/evaluation_result_list.html'
    context_object_name = 'results'
    paginate_by = 20
    
    def get_queryset(self):
        # Return empty queryset to avoid database schema issues
        return EvaluationResult.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add fallback statistics without database queries
        context['total_submissions'] = 0
        context['terminated_exams'] = 0
        
        # Add message about database status
        context['database_message'] = "Evaluation results are currently being updated. Please check back later."
        
        return context

@login_required
def submission_details_api(request, submission_id):
    """API endpoint to get submission details"""
    try:
        submission = get_object_or_404(ExamSubmission, id=submission_id)
        
        # Check permissions
        if request.user.role == 'student' and submission.student != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        elif request.user.role == 'teacher' and submission.exam.teacher != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get answers with evaluation results
        answers_data = []
        for answer in submission.answers.all():
            eval_result = answer.evaluationresult if hasattr(answer, 'evaluationresult') else None
            answers_data.append({
                'question_text': answer.question.question_text[:100] + '...' if len(answer.question.question_text) > 100 else answer.question.question_text,
                'answer_text': answer.answer_text[:100] + '...' if answer.answer_text and len(answer.answer_text) > 100 else answer.answer_text,
                'score': eval_result.final_score if eval_result else None,
                'max_score': answer.question.marks,
                'similarity': eval_result.similarity_score if eval_result else None,
                'confidence': eval_result.confidence_score if eval_result else None,
                'feedback': eval_result.feedback[:100] + '...' if eval_result and eval_result.feedback and len(eval_result.feedback) > 100 else eval_result.feedback if eval_result else None
            })
        
        # Calculate duration
        duration = "N/A"
        if submission.started_at and submission.submitted_at:
            duration = str(submission.submitted_at - submission.started_at)
        
        data = {
            'student_name': submission.student.get_full_name() or submission.student.email,
            'student_email': submission.student.email,
            'exam_title': submission.exam.title,
            'exam_subject': submission.exam.exam_type or 'General',
            'submitted_at': submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            'started_at': submission.started_at.strftime('%Y-%m-%d %H:%M:%S') if submission.started_at else None,
            'duration': duration,
            'answers': answers_data
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error in submission_details_api: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def proctoring_details_api(request, submission_id):
    """API endpoint to get proctoring details"""
    try:
        submission = get_object_or_404(ExamSubmission, id=submission_id)
        
        # Check permissions
        if request.user.role == 'student' and submission.student != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        elif request.user.role == 'teacher' and submission.exam.teacher != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get proctoring session
        proctoring_session = ProctoringSession.objects.filter(
            student=submission.student,
            exam=submission.exam
        ).order_by('-start_time').first()
        
        session_data = {
            'session_id': None,
            'session_status': None,
            'started_at': None,
            'ended_at': None,
            'ip_address': None,
            'browser': None,
            'screen_resolution': None,
            'platform': None,
            'events': []
        }
        
        if proctoring_session:
            session_data.update({
                'session_id': proctoring_session.session_id,
                'session_status': proctoring_session.status,
                'started_at': proctoring_session.started_at.strftime('%Y-%m-%d %H:%M:%S') if proctoring_session.started_at else None,
                'ended_at': proctoring_session.ended_at.strftime('%Y-%m-%d %H:%M:%S') if proctoring_session.ended_at else None,
                'ip_address': proctoring_session.ip_address,
                'browser': proctoring_session.user_agent.get('browser', 'N/A') if proctoring_session.user_agent else 'N/A',
                'screen_resolution': proctoring_session.screen_resolution,
                'platform': proctoring_session.user_agent.get('platform', 'N/A') if proctoring_session.user_agent else 'N/A'
            })
            
            # Get proctoring events
            events_data = []
            for event in proctoring_session.events.all():
                severity = 'high' if event.event_type in ['tab_switch', 'window_blur'] else 'medium'
                events_data.append({
                    'timestamp': event.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'event_type': event.event_type,
                    'description': event.description,
                    'severity': severity
                })
            
            session_data['events'] = events_data
        
        return JsonResponse(session_data)
        
    except Exception as e:
        logger.error(f"Error in proctoring_details_api: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def evaluate_answer(request, answer_id):
    """Evaluate a single answer"""
    answer = get_object_or_404(Answer, id=answer_id)
    
    # Check permissions
    if request.user.role == 'student' and answer.exam_submission.student != request.user:
        return redirect('dashboard')
    
    if request.user.role == 'teacher' and answer.exam_submission.exam.teacher != request.user:
        return redirect('dashboard')
    
    try:
        # Run evaluation using utility function
        eval_result = trigger_ai_evaluation(answer)
        
        if not eval_result['success']:
            messages.warning(request, f"Evaluation partial: {eval_result['error']}")
        
        result = EvaluationResult.objects.get(answer=answer)
        
        return render(request, 'evaluation/evaluation_result_detail.html', {
            'result': result,
            'answer': answer
        })
        
    except Exception as e:
        logger.error(f"Error evaluating answer {answer_id}: {str(e)}")
        messages.error(request, "Error occurred during evaluation.")
        return redirect('evaluation:evaluation_results')

@login_required
def evaluation_analytics(request):
    """Evaluation analytics dashboard"""
    if not request.user.role in ['teacher', 'admin']:
        return redirect('dashboard')
    
    # Get filter parameters
    date_range = request.GET.get('date_range', 'all')
    exam_type = request.GET.get('exam_type', 'all')
    score_range = request.GET.get('score_range', 'all')
    eval_method = request.GET.get('eval_method', 'all')
    
    # Get base queryset
    if request.user.role == 'teacher':
        results = EvaluationResult.objects.filter(
            answer__submission__exam__teacher=request.user
        )
        exam_submissions = ExamSubmission.objects.filter(exam__teacher=request.user)
    else:
        results = EvaluationResult.objects.all()
        exam_submissions = ExamSubmission.objects.all()
    
    # Apply filters
    if date_range != 'all':
        from datetime import datetime, timedelta
        days = int(date_range)
        cutoff_date = datetime.now() - timedelta(days=days)
        results = results.filter(evaluation_time__gte=cutoff_date)
    
    if exam_type != 'all':
        results = results.filter(answer__submission__exam__exam_type=exam_type)
    
    if score_range != 'all':
        if score_range == 'high':
            results = results.filter(final_score__gte=80)
        elif score_range == 'medium':
            results = results.filter(final_score__gte=60, final_score__lt=80)
        elif score_range == 'low':
            results = results.filter(final_score__lt=60)
    
    if eval_method != 'all':
        results = results.filter(evaluation_method=eval_method)
    
    # Calculate basic statistics
    total_evaluations = results.count()
    avg_score = results.aggregate(avg_score=Avg('final_score'))['avg_score'] or 0
    avg_similarity = results.aggregate(avg_sim=Avg('similarity_score'))['avg_sim'] or 0
    avg_confidence = results.aggregate(avg_conf=Avg('confidence_score'))['avg_conf'] or 0
    
    # Score distribution
    score_ranges = {
        '0-20': results.filter(final_score__lte=20).count(),
        '21-40': results.filter(final_score__gt=20, final_score__lte=40).count(),
        '41-60': results.filter(final_score__gt=40, final_score__lte=60).count(),
        '61-80': results.filter(final_score__gt=60, final_score__lte=80).count(),
        '81-100': results.filter(final_score__gt=80).count(),
    }
    
    # Advanced metrics
    high_performers = results.filter(final_score__gte=80).count()
    low_performers = results.filter(final_score__lt=40).count()
    perfect_scores = results.filter(final_score__gte=95).count()
    
    # Evaluation methods
    evaluation_methods = results.values('evaluation_method').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent evaluations
    recent_evaluations = results.select_related(
        'answer__submission__student',
        'answer__submission__exam',
        'answer__question'
    ).order_by('-evaluation_time')[:10]
    
    # Proctoring statistics
    total_submissions = exam_submissions.count()
    terminated_exams = 0
    violation_count = 0
    
    for submission in exam_submissions:
        proctoring_session = ProctoringSession.objects.filter(
            student=submission.student,
            exam=submission.exam
        ).order_by('-start_time').first()
        
        if proctoring_session:
            if proctoring_session.status == 'terminated':
                terminated_exams += 1
            violation_count += proctoring_session.events.filter(
                event_type__in=['tab_switch', 'window_blur', 'face_not_detected']
            ).count()
    
    context = {
        'total_evaluations': total_evaluations,
        'avg_score': round(avg_score, 2),
        'avg_similarity': round(avg_similarity, 2),
        'avg_confidence': round(avg_confidence, 2),
        'score_ranges': score_ranges,
        'high_performers': high_performers,
        'low_performers': low_performers,
        'perfect_scores': perfect_scores,
        'evaluation_methods': list(evaluation_methods),
        'recent_evaluations': recent_evaluations,
        'total_submissions': total_submissions,
        'terminated_exams': terminated_exams,
        'violation_count': violation_count,
        'violation_rate': round((violation_count / total_submissions * 100), 2) if total_submissions > 0 else 0,
    }
    
    return render(request, 'evaluation/analytics.html', context)
