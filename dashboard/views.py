from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count, Avg, Sum
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta
import json

from accounts.models import User
from exams.models import Exam, Question, Answer, ExamSubmission
from evaluation.models import EvaluationResult, GraceMarksRule, ScoringRange
from proctoring.models import ProctoringSession, ProctoringEvent
from core.models import ScoringConfiguration

def dashboard_view(request):
    """Main dashboard view - redirects based on user role"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.role == 'admin':
        return admin_dashboard(request)
    elif request.user.role == 'teacher':
        return teacher_dashboard(request)
    elif request.user.role == 'student':
        return student_dashboard(request)
    else:
        return redirect('login')

def admin_dashboard(request):
    """Admin dashboard with system-wide statistics"""
    try:
        # System statistics
        total_users = User.objects.count()
        total_teachers = User.objects.filter(role='teacher').count()
        total_students = User.objects.filter(role='student').count()
        total_exams = Exam.objects.count()
        published_exams = Exam.objects.filter(status='published').count()
        total_submissions = ExamSubmission.objects.count()
        
        # Recent activity
        recent_exams = Exam.objects.order_by('-created_at')[:5]
        recent_users = User.objects.order_by('-date_joined')[:5]
        
        context = {
            'user_type': 'admin',
            'stats': {
                'total_users': total_users,
                'total_teachers': total_teachers,
                'total_students': total_students,
                'total_exams': total_exams,
                'published_exams': published_exams,
                'total_submissions': total_submissions,
            },
            'recent_exams': recent_exams,
            'recent_users': recent_users,
        }
        
        return render(request, 'dashboard/admin_dashboard.html', context)
    except Exception as e:
        # Fallback context if there's an error
        context = {
            'user_type': 'admin',
            'stats': {
                'total_users': 0,
                'total_teachers': 0,
                'total_students': 0,
                'total_exams': 0,
                'published_exams': 0,
                'total_submissions': 0,
            },
            'recent_exams': [],
            'recent_users': [],
        }
        return render(request, 'dashboard/admin_dashboard.html', context)

def teacher_dashboard(request):
    """Teacher dashboard with exam and evaluation statistics"""
    try:
        # Basic statistics
        total_exams = Exam.objects.filter(teacher=request.user).count()
        published_exams = Exam.objects.filter(teacher=request.user, status='published').count()
        
        # Submission statistics
        total_submissions = Answer.objects.filter(question__exam__teacher=request.user).count()
        
        # Evaluation statistics
        pending_evaluations = Answer.objects.filter(
            question__exam__teacher=request.user,
            evaluationresult__isnull=True
        ).count()
        
        # Average scores
        avg_score = EvaluationResult.objects.filter(
            answer__question__exam__teacher=request.user
        ).aggregate(avg_score=Avg('final_score'))['avg_score'] or 0
        
        # Recent exams
        recent_exams = Exam.objects.filter(teacher=request.user).order_by('-created_at')[:5]
        
        # Recent alerts (placeholder)
        recent_alerts = []
        
        # Active proctoring sessions
        active_proctoring_sessions = ProctoringSession.objects.filter(
            exam__teacher=request.user,
            status='active'
        ).count()
        
        # Scoring ranges count with error handling
        try:
            scoring_ranges_count = ScoringRange.objects.filter(created_by=request.user).count()
        except:
            scoring_ranges_count = 0
        
        context = {
            'user_type': 'teacher',
            'stats': {
                'total_exams': total_exams,
                'published_exams': published_exams,
                'total_submissions': total_submissions,
                'pending_evaluations': pending_evaluations,
                'avg_score': round(avg_score, 2),
                'scoring_ranges_count': scoring_ranges_count,
                'active_proctoring_sessions': active_proctoring_sessions,
            },
            'recent_exams': recent_exams,
            'recent_alerts': recent_alerts,
        }
        
        return render(request, 'dashboard/teacher_dashboard.html', context)
    except Exception as e:
        # Fallback context if there's an error
        context = {
            'user_type': 'teacher',
            'stats': {
                'total_exams': 0,
                'published_exams': 0,
                'total_submissions': 0,
                'pending_evaluations': 0,
                'avg_score': 0,
                'scoring_ranges_count': 0,
                'active_proctoring_sessions': 0,
            },
            'recent_exams': [],
            'recent_alerts': [],
        }
        return render(request, 'dashboard/teacher_dashboard.html', context)

def student_dashboard(request):
    """Student dashboard with exam and submission statistics"""
    try:
        # Basic statistics
        total_exams_available = Exam.objects.filter(status='published').count()
        exams_taken = ExamSubmission.objects.filter(student=request.user).count()
        
        # Recent submissions
        recent_submissions = ExamSubmission.objects.filter(
            student=request.user
        ).order_by('-submitted_at')[:5]
        
        # Average scores
        avg_score = EvaluationResult.objects.filter(
            answer__submission__student=request.user
        ).aggregate(avg_score=Avg('final_score'))['avg_score'] or 0
        
        # Pending exams (published and not taken)
        now = timezone.now()
        pending_exams_query = Exam.objects.filter(
            status='published'
        ).exclude(
            id__in=ExamSubmission.objects.filter(student=request.user).values('exam')
        )
        
        # Available now (start_time <= now <= end_time)
        available_exams = pending_exams_query.filter(
            start_time__lte=now,
            end_time__gte=now
        ).order_by('-start_time')[:5]
        
        # Upcoming (start_time > now)
        upcoming_exams = pending_exams_query.filter(
            start_time__gt=now
        ).order_by('start_time')[:5]
        
        # Recent results (evaluated submissions)
        recent_results = ExamSubmission.objects.filter(
            student=request.user,
            status='evaluated'
        ).order_by('-submitted_at')[:5]
        
        context = {
            'user_type': 'student',
            'stats': {
                'total_exams_available': total_exams_available,
                'exams_taken': exams_taken,
                'avg_score': round(avg_score, 2),
                'pending_exams': pending_exams_query.count(),
            },
            'recent_submissions': recent_submissions,
            'recent_results': recent_results,
            'available_exams': available_exams,
            'upcoming_exams': upcoming_exams,
        }
        
        return render(request, 'dashboard/student_dashboard.html', context)
    except Exception as e:
        # Fallback context if there's an error
        context = {
            'user_type': 'student',
            'stats': {
                'total_exams_available': 0,
                'exams_taken': 0,
                'avg_score': 0,
                'pending_exams': 0,
            },
            'recent_submissions': [],
        }
        return render(request, 'dashboard/student_dashboard.html', context)

@login_required
def dashboard_api(request):
    """Dashboard API endpoint for AJAX requests"""
    try:
        if request.user.role == 'teacher':
            # Teacher data
            data = {
                'exam_stats': {
                    'total': Exam.objects.filter(teacher=request.user).count(),
                    'published': Exam.objects.filter(teacher=request.user, status='published').count(),
                },
                'submission_stats': {
                    'total': Answer.objects.filter(question__exam__teacher=request.user).count(),
                    'pending': Answer.objects.filter(
                        question__exam__teacher=request.user,
                        evaluationresult__isnull=True
                    ).count(),
                }
            }
        elif request.user.role == 'student':
            # Student data
            data = {
                'exam_stats': {
                    'available': Exam.objects.filter(status='published').count(),
                    'taken': ExamSubmission.objects.filter(student=request.user).count(),
                }
            }
        else:
            data = {}
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class ExamAnalyticsView(LoginRequiredMixin, ListView):
    """Analytics view for exam performance"""
    model = Exam
    template_name = 'dashboard/exam_analytics.html'
    context_object_name = 'exams'
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return Exam.objects.filter(teacher=self.request.user)
        elif self.request.user.is_admin_user:
            return Exam.objects.all()
        return Exam.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Calculate analytics
            queryset = self.get_queryset()
            
            # Basic stats
            context['total_exams'] = queryset.count()
            context['published_exams'] = queryset.filter(status='published').count()
            
            # Average scores
            avg_scores = []
            for exam in queryset:
                avg_score = EvaluationResult.objects.filter(
                    answer__question__exam=exam
                ).aggregate(avg_score=Avg('final_score'))['avg_score']
                avg_scores.append(avg_score or 0)
            
            context['average_score'] = sum(avg_scores) / len(avg_scores) if avg_scores else 0
            
        except Exception as e:
            # Fallback values
            context['total_exams'] = 0
            context['published_exams'] = 0
            context['average_score'] = 0
        
        return context
