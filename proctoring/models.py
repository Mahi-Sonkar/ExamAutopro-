from django.db import models
from django.conf import settings
from django.utils import timezone

class ProctoringSession(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
        ('suspended', 'Suspended'),
    ]
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    screen_resolution = models.CharField(max_length=20, blank=True, null=True)
    browser_info = models.JSONField(default=dict, blank=True, null=True)
    suspicious_activities = models.IntegerField(default=0)
    total_events = models.IntegerField(default=0)
    session_data = models.JSONField(default=dict, blank=True, null=True)
    
    def __str__(self):
        return f"Proctoring Session: {self.student.email} - {self.exam.title}"
    
    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return timezone.now() - self.start_time
    
    @property
    def is_active(self):
        return self.status == 'active'

class ProctoringEvent(models.Model):
    EVENT_TYPES = [
        ('tab_switch', 'Tab Switch'),
        ('window_focus_lost', 'Window Focus Lost'),
        ('face_not_detected', 'Face Not Detected'),
        ('multiple_faces', 'Multiple Faces Detected'),
        ('suspicious_movement', 'Suspicious Movement'),
        ('copy_paste', 'Copy/Paste Detected'),
        ('right_click', 'Right Click Attempt'),
        ('keyboard_shortcut', 'Keyboard Shortcut'),
        ('fullscreen_exit', 'Fullscreen Exit'),
        ('mobile_device', 'Mobile Device Detected'),
        ('vpn_detected', 'VPN Detected'),
        ('unusual_activity', 'Unusual Activity'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    session = models.ForeignKey(ProctoringSession, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='low')
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    screenshot = models.ImageField(upload_to='proctoring_screenshots/', blank=True, null=True)
    camera_snapshot = models.ImageField(upload_to='proctoring_camera/', blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    
    @property
    def severity_color(self):
        colors = {
            'info': 'info',
            'warning': 'warning',
            'error': 'danger',
            'critical': 'dark',
        }
        return colors.get(self.severity, 'secondary')

    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.event_type} - {self.session.student.email} at {self.timestamp}"

class ProctoringAlert(models.Model):
    ALERT_TYPES = [
        ('warning', 'Warning'),
        ('suspicious', 'Suspicious Activity'),
        ('cheating_detected', 'Cheating Detected'),
        ('technical_issue', 'Technical Issue'),
        ('session_terminated', 'Session Terminated'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    session = models.ForeignKey(ProctoringSession, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='warning')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        limit_choices_to={'role': 'teacher'}
    )
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    auto_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, null=True)
    
    @property
    def severity_color(self):
        colors = {
            'info': 'info',
            'warning': 'warning',
            'error': 'danger',
            'critical': 'dark',
        }
        return colors.get(self.severity, 'secondary')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_type} - {self.session.student.email}"

class ProctoringSettings(models.Model):
    exam = models.OneToOneField('exams.Exam', on_delete=models.CASCADE)
    enable_webcam = models.BooleanField(default=True)
    enable_screen_recording = models.BooleanField(default=False)
    enable_tab_detection = models.BooleanField(default=True)
    enable_face_detection = models.BooleanField(default=True)
    enable_audio_monitoring = models.BooleanField(default=False)
    max_tab_switches = models.IntegerField(default=3)
    max_face_detection_failures = models.IntegerField(default=5)
    session_timeout_minutes = models.IntegerField(default=30)
    auto_terminate_on_violation = models.BooleanField(default=False)
    violation_threshold = models.IntegerField(default=10)
    notify_teacher_on_violation = models.BooleanField(default=True)
    allow_teacher_intervention = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Proctoring Settings for {self.exam.title}"

class ProctoringLog(models.Model):
    session = models.ForeignKey(ProctoringSession, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=50)
    message = models.TextField()
    level = models.CharField(max_length=20, default='INFO')
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.log_type} - {self.session.student.email} at {self.timestamp}"
