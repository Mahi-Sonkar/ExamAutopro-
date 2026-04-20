from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
import json
import uuid
from .models import ProctoringSession, ProctoringEvent, ProctoringAlert, ProctoringSettings, ProctoringLog
from .utils import ProctoringUtils
from exams.models import Exam, ExamSubmission

@login_required
def start_proctoring_session(request, exam_id):
    """Start a proctoring session for an exam"""
    if not request.user.is_student:
        return JsonResponse({'error': 'Only students can start proctoring sessions'}, status=403)
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    if not exam.is_active:
        return JsonResponse({'error': 'Exam is not currently active'}, status=400)
    
    # Check if session already exists
    existing_session = ProctoringSession.objects.filter(
        student=request.user,
        exam=exam,
        status='active'
    ).first()
    
    if existing_session:
        return JsonResponse({
            'session_id': existing_session.session_id,
            'message': 'Session already active'
        })
    
    # Create new proctoring session
    session_id = str(uuid.uuid4())
    session = ProctoringSession.objects.create(
        student=request.user,
        exam=exam,
        session_id=session_id,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        screen_resolution=request.POST.get('screen_resolution', ''),
        browser_info={
            'browser': request.POST.get('browser', ''),
            'version': request.POST.get('browser_version', ''),
            'platform': request.POST.get('platform', ''),
        }
    )
    
    # Log session start
    ProctoringLog.objects.create(
        session=session,
        log_type='session_start',
        message=f'Proctoring session started for {request.user.email}',
        level='INFO'
    )
    
    return JsonResponse({
        'session_id': session_id,
        'settings': get_proctoring_settings(exam)
    })

@csrf_exempt
@require_http_methods(["POST"])
def log_proctoring_event(request, session_id):
    """Log proctoring events from the client"""
    try:
        session = get_object_or_404(ProctoringSession, session_id=session_id)
        
        if session.status != 'active':
            return JsonResponse({'error': 'Session is not active'}, status=400)
        
        data = json.loads(request.body)
        event_type = data.get('event_type')
        severity = data.get('severity', 'low')
        description = data.get('description', '')
        metadata = data.get('metadata', {})
        
        # Create proctoring event
        event = ProctoringEvent.objects.create(
            session=session,
            event_type=event_type,
            severity=severity,
            description=description,
            metadata=metadata
        )
        
        # Update session counters
        session.total_events += 1
        if severity in ['high', 'critical']:
            session.suspicious_activities += 1
        session.save()
        
        # Check if alert should be created
        if should_create_alert(event_type, severity, session):
            create_alert_for_event(event, session)
        
        # Log the event
        ProctoringLog.objects.create(
            session=session,
            log_type='event',
            message=f'Event logged: {event_type} - {description}',
            level='INFO' if severity == 'low' else 'WARNING'
        )
        
        return JsonResponse({'success': True, 'event_id': event.id})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def end_proctoring_session(request, session_id):
    """End a proctoring session"""
    try:
        session = get_object_or_404(ProctoringSession, session_id=session_id)
        
        if request.user != session.student and not request.user.is_teacher:
            return HttpResponseForbidden("Permission denied")
        
        session.status = 'completed'
        session.end_time = timezone.now()
        session.save()
        
        # Log session end
        ProctoringLog.objects.create(
            session=session,
            log_type='session_end',
            message=f'Proctoring session ended for {session.student.email}',
            level='INFO'
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_proctoring_dashboard(request, exam_id):
    """Get proctoring dashboard for teachers"""
    if not request.user.is_teacher:
        return HttpResponseForbidden("Only teachers can access proctoring dashboard")
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.user != exam.teacher:
        return HttpResponseForbidden("Only exam creator can access proctoring dashboard")
    
    # Get active sessions
    active_sessions = ProctoringSession.objects.filter(
        exam=exam,
        status='active'
    ).select_related('student')
    
    # Get recent alerts
    recent_alerts = ProctoringAlert.objects.filter(
        session__exam=exam,
        acknowledged=False
    ).select_related('session', 'session__student').order_by('-created_at')[:20]
    
    # Get statistics
    total_students = ExamSubmission.objects.filter(exam=exam).count()
    active_sessions_count = active_sessions.count()
    suspicious_activities = ProctoringEvent.objects.filter(
        session__exam=exam,
        severity__in=['high', 'critical']
    ).count()
    
    context = {
        'exam': exam,
        'active_sessions': active_sessions,
        'recent_alerts': recent_alerts,
        'statistics': {
            'total_students': total_students,
            'active_sessions': active_sessions_count,
            'suspicious_activities': suspicious_activities,
        }
    }
    
    return render(request, 'proctoring/dashboard.html', context)

@login_required
def acknowledge_alert(request, alert_id):
    """Acknowledge a proctoring alert"""
    if not request.user.is_teacher:
        return HttpResponseForbidden("Only teachers can acknowledge alerts")
    
    try:
        alert = get_object_or_404(ProctoringAlert, id=alert_id)
        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def terminate_session(request, session_id):
    """Terminate a proctoring session (teacher action)"""
    if not request.user.is_teacher:
        return HttpResponseForbidden("Only teachers can terminate sessions")
    
    try:
        session = get_object_or_404(ProctoringSession, session_id=session_id)
        session.status = 'terminated'
        session.end_time = timezone.now()
        session.save()
        
        # Create alert for termination
        ProctoringAlert.objects.create(
            session=session,
            alert_type='session_terminated',
            severity='critical',
            message=f'Session terminated by teacher: {request.user.email}'
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_proctoring_settings(exam):
    """Get proctoring settings for an exam"""
    settings, created = ProctoringSettings.objects.get_or_create(
        exam=exam,
        defaults={
            'enable_webcam': True,
            'enable_tab_detection': True,
            'enable_face_detection': True,
            'max_tab_switches': 3,
            'max_face_detection_failures': 5,
        }
    )
    
    return {
        'enable_webcam': settings.enable_webcam,
        'enable_screen_recording': settings.enable_screen_recording,
        'enable_tab_detection': settings.enable_tab_detection,
        'enable_face_detection': settings.enable_face_detection,
        'enable_audio_monitoring': settings.enable_audio_monitoring,
        'max_tab_switches': settings.max_tab_switches,
        'max_face_detection_failures': settings.max_face_detection_failures,
        'session_timeout_minutes': settings.session_timeout_minutes,
        'auto_terminate_on_violation': settings.auto_terminate_on_violation,
        'violation_threshold': settings.violation_threshold,
    }

def should_create_alert(event_type, severity, session):
    """Determine if an alert should be created for an event"""
    # Create alerts for high severity events
    if severity in ['high', 'critical']:
        return True
    
    # Create alerts for repeated tab switches
    if event_type == 'tab_switch':
        tab_switch_count = ProctoringEvent.objects.filter(
            session=session,
            event_type='tab_switch'
        ).count()
        return tab_switch_count >= 3
    
    # Create alerts for repeated face detection failures
    if event_type == 'face_not_detected':
        face_failure_count = ProctoringEvent.objects.filter(
            session=session,
            event_type='face_not_detected'
        ).count()
        return face_failure_count >= 5
    
    return False

@csrf_exempt
@require_http_methods(["POST"])
def decline_exam_on_violation(request, session_id):
    """Decline (cancel) the exam submission immediately due to a proctoring violation like tab switching"""
    try:
        session = get_object_or_404(ProctoringSession, session_id=session_id)
        
        # Already terminated or completed?
        if session.status != 'active':
            return JsonResponse({'success': True, 'message': 'Session already inactive'})
            
        data = json.loads(request.body)
        violation_type = data.get('violation_type', 'tab_switch')
        
        # 1. Update proctoring session status
        session.status = 'terminated'
        session.end_time = timezone.now()
        session.suspicious_activities += 1
        session.save()
        
        # 2. Update the associated exam submission to 'cancelled'
        submission = ExamSubmission.objects.filter(
            student=session.student,
            exam=session.exam,
            status='in_progress'
        ).first()
        
        if submission:
            submission.status = 'cancelled'
            submission.submitted_at = timezone.now()
            submission.save()
            
            # Log the cancellation
            ProctoringLog.objects.create(
                session=session,
                log_type='violation_cancellation',
                message=f'Exam submission CANCELLED for {session.student.email} due to {violation_type}',
                level='CRITICAL'
            )
            
            # Create a critical alert for the teacher
            ProctoringAlert.objects.create(
                session=session,
                alert_type='cheating_detected',
                severity='critical',
                message=f'Exam auto-cancelled for {session.student.email} due to critical violation: {violation_type}'
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Exam declined due to proctoring violation',
                'redirect_url': f'/exams/{session.exam.id}/results/'
            })
        
        return JsonResponse({'error': 'Active submission not found'}, status=404)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def create_alert_for_event(event, session):
    """Create an alert for a proctoring event"""
    alert_type = 'suspicious'
    message = f'Suspicious activity detected: {event.event_type}'
    
    if event.severity == 'critical':
        alert_type = 'cheating_detected'
        message = f'Critical violation detected: {event.event_type}'
    
    ProctoringAlert.objects.create(
        session=session,
        alert_type=alert_type,
        severity=event.severity,
        message=message
    )
