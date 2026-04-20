"""
Advanced Proctoring Engine for ExamAutoPro
Main motive: Real-time activity monitoring and suspicious behavior detection
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque

try:
    from django.utils import timezone
    from django.db import models
    from django.core.cache import cache
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    timezone = None
    models = None
    cache = None

logger = logging.getLogger(__name__)

class ActivityType(Enum):
    """Activity type enumeration"""
    TAB_SWITCH = "tab_switch"
    WINDOW_BLUR = "window_blur"
    COPY_PASTE = "copy_paste"
    RIGHT_CLICK = "right_click"
    KEYBOARD_SHORTCUT = "keyboard_shortcut"
    FACE_DETECTION = "face_detection"
    MULTIPLE_FACES = "multiple_faces"
    NO_FACE = "no_face"
    SUSPICIOUS_MOVEMENT = "suspicious_movement"
    AUDIO_DETECTION = "audio_detection"
    SCREEN_CAPTURE = "screen_capture"
    DEVICE_DISCONNECT = "device_disconnect"

class SuspicionLevel(Enum):
    """Suspicion level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ActivityEvent:
    """Activity event structure"""
    timestamp: datetime
    activity_type: ActivityType
    user_id: str
    exam_id: str
    details: Dict[str, Any]
    suspicion_level: SuspicionLevel
    session_id: str

class ProctoringEngine:
    """
    Advanced proctoring engine with real-time monitoring
    Main motive: Comprehensive exam proctoring with intelligent detection
    """
    
    def __init__(self):
        self.activity_buffer = defaultdict(lambda: deque(maxlen=100))
        self.suspicion_thresholds = self._initialize_thresholds()
        self.monitoring_rules = self._initialize_rules()
        
    def _initialize_thresholds(self) -> Dict:
        """Initialize suspicion thresholds"""
        return {
            'tab_switch': {
                'low': 3,      # 3 tab switches
                'medium': 5,   # 5 tab switches
                'high': 10,     # 10 tab switches
                'time_window': 300  # 5 minutes
            },
            'window_blur': {
                'low': 2,
                'medium': 4,
                'high': 8,
                'time_window': 300
            },
            'copy_paste': {
                'low': 1,
                'medium': 3,
                'high': 5,
                'time_window': 600  # 10 minutes
            },
            'right_click': {
                'low': 5,
                'medium': 10,
                'high': 20,
                'time_window': 300
            },
            'face_detection': {
                'no_face_threshold': 30,  # 30 seconds
                'multiple_faces_threshold': 2,
                'movement_threshold': 0.3
            }
        }
    
    def _initialize_rules(self) -> Dict:
        """Initialize monitoring rules"""
        return {
            'enable_tab_detection': True,
            'enable_window_monitoring': True,
            'enable_copy_paste_detection': True,
            'enable_right_click_detection': True,
            'enable_face_detection': True,
            'enable_audio_monitoring': False,
            'enable_screen_recording': False,
            'log_all_activities': True,
            'auto_flag_suspicious': True,
            'notification_threshold': SuspicionLevel.HIGH
        }
    
    def log_activity(self, user_id: str, exam_id: str, activity_type: ActivityType, 
                   details: Dict[str, Any], session_id: str = None) -> Dict:
        """
        Log user activity and analyze for suspicious behavior
        Main motive: Real-time activity monitoring and analysis
        """
        try:
            timestamp = timezone.now() if DJANGO_AVAILABLE else datetime.now()
            
            # Create activity event
            event = ActivityEvent(
                timestamp=timestamp,
                activity_type=activity_type,
                user_id=user_id,
                exam_id=exam_id,
                details=details,
                suspicion_level=SuspicionLevel.LOW,
                session_id=session_id or f"{user_id}_{exam_id}"
            )
            
            # Calculate suspicion level
            suspicion_level = self._calculate_suspicion_level(event)
            event.suspicion_level = suspicion_level
            
            # Store in buffer
            self.activity_buffer[session_id or f"{user_id}_{exam_id}"].append(event)
            
            # Create log entry
            log_entry = self._create_log_entry(event)
            
            # Check if auto-flagging is needed
            should_flag = self._should_auto_flag(suspicion_level)
            
            # Generate alerts if needed
            alerts = []
            if should_flag:
                alerts = self._generate_alerts(event)
            
            # Store in cache for real-time monitoring (if available)
            if DJANGO_AVAILABLE and cache:
                cache_key = f"proctoring_{session_id or f'{user_id}_{exam_id}'}"
                cache.set(cache_key, {
                    'last_activity': timestamp.isoformat(),
                    'suspicion_level': suspicion_level.value,
                    'activity_count': len(self.activity_buffer[session_id or f"{user_id}_{exam_id}"]),
                    'alerts': alerts
                }, timeout=3600)  # 1 hour
            
            return {
                'success': True,
                'event_id': f"{timestamp.timestamp()}_{user_id}_{activity_type.value}",
                'suspicion_level': suspicion_level.value,
                'logged': True,
                'flagged': should_flag,
                'alerts': alerts,
                'log_entry': log_entry
            }
            
        except Exception as e:
            logger.error(f"Activity logging failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'logged': False
            }
    
    def detect_tab_switching(self, user_id: str, exam_id: str, from_tab: str, to_tab: str, 
                          session_id: str = None) -> Dict:
        """
        Detect tab switching activity
        Main motive: Monitor tab switching during exam
        """
        try:
            details = {
                'from_tab': from_tab,
                'to_tab': to_tab,
                'tab_count': self._count_open_tabs(user_id, exam_id),
                'switch_count': self._count_tab_switches(user_id, exam_id, session_id)
            }
            
            return self.log_activity(
                user_id=user_id,
                exam_id=exam_id,
                activity_type=ActivityType.TAB_SWITCH,
                details=details,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Tab switching detection failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def detect_window_blur(self, user_id: str, exam_id: str, duration: float = None, 
                         session_id: str = None) -> Dict:
        """
        Detect window blur/focus loss
        Main motive: Monitor window focus changes
        """
        try:
            details = {
                'blur_duration': duration,
                'window_title': self._get_active_window_title(),
                'blur_count': self._count_window_blurs(user_id, exam_id, session_id)
            }
            
            return self.log_activity(
                user_id=user_id,
                exam_id=exam_id,
                activity_type=ActivityType.WINDOW_BLUR,
                details=details,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Window blur detection failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def detect_copy_paste(self, user_id: str, exam_id: str, content: str = None, 
                       source: str = None, session_id: str = None) -> Dict:
        """
        Detect copy-paste activity
        Main motive: Monitor unauthorized content transfer
        """
        try:
            details = {
                'content_length': len(content) if content else 0,
                'source': source,
                'paste_count': self._count_copy_paste(user_id, exam_id, session_id),
                'suspicious_content': self._check_suspicious_content(content) if content else False
            }
            
            return self.log_activity(
                user_id=user_id,
                exam_id=exam_id,
                activity_type=ActivityType.COPY_PASTE,
                details=details,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Copy-paste detection failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def detect_right_click(self, user_id: str, exam_id: str, x: int = None, y: int = None,
                       target_element: str = None, session_id: str = None) -> Dict:
        """
        Detect right-click activity
        Main motive: Monitor potential cheating attempts
        """
        try:
            details = {
                'coordinates': {'x': x, 'y': y} if x and y else None,
                'target_element': target_element,
                'right_click_count': self._count_right_clicks(user_id, exam_id, session_id),
                'suspicious_element': self._is_suspicious_element(target_element)
            }
            
            return self.log_activity(
                user_id=user_id,
                exam_id=exam_id,
                activity_type=ActivityType.RIGHT_CLICK,
                details=details,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Right-click detection failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_face_detection(self, user_id: str, exam_id: str, face_count: int = 0,
                           face_coordinates: List[Dict] = None, confidence: float = None,
                           session_id: str = None) -> Dict:
        """
        Analyze face detection results
        Main motive: Monitor user presence and identity
        """
        try:
            details = {
                'face_count': face_count,
                'face_coordinates': face_coordinates,
                'detection_confidence': confidence,
                'no_face_duration': self._calculate_no_face_duration(user_id, exam_id, session_id),
                'multiple_faces_detected': face_count > 1,
                'face_movement': self._detect_face_movement(face_coordinates)
            }
            
            # Determine activity type based on face count
            if face_count == 0:
                activity_type = ActivityType.NO_FACE
            elif face_count > 1:
                activity_type = ActivityType.MULTIPLE_FACES
            else:
                activity_type = ActivityType.FACE_DETECTION
            
            return self.log_activity(
                user_id=user_id,
                exam_id=exam_id,
                activity_type=activity_type,
                details=details,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Face detection analysis failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_proctoring_summary(self, user_id: str, exam_id: str, session_id: str = None) -> Dict:
        """
        Get comprehensive proctoring summary
        Main motive: Complete analysis of user behavior during exam
        """
        try:
            session_key = session_id or f"{user_id}_{exam_id}"
            activities = list(self.activity_buffer[session_key])
            
            if not activities:
                return {
                    'user_id': user_id,
                    'exam_id': exam_id,
                    'total_activities': 0,
                    'suspicion_level': SuspicionLevel.LOW.value,
                    'activities_by_type': {},
                    'alerts': [],
                    'recommendations': []
                }
            
            # Analyze activities
            activity_counts = defaultdict(int)
            suspicion_scores = []
            alerts = []
            
            for activity in activities:
                activity_counts[activity.activity_type.value] += 1
                suspicion_scores.append(self._suspicion_level_to_score(activity.suspicion_level))
                
                # Collect high-suspicion activities
                if activity.suspicion_level in [SuspicionLevel.HIGH, SuspicionLevel.CRITICAL]:
                    alerts.append(self._create_alert_from_activity(activity))
            
            # Calculate overall suspicion level
            avg_suspicion = sum(suspicion_scores) / len(suspicion_scores) if suspicion_scores else 0
            overall_suspicion = self._score_to_suspicion_level(avg_suspicion)
            
            # Generate recommendations
            recommendations = self._generate_proctoring_recommendations(activities, overall_suspicion)
            
            return {
                'user_id': user_id,
                'exam_id': exam_id,
                'session_id': session_id,
                'total_activities': len(activities),
                'activities_by_type': dict(activity_counts),
                'overall_suspicion_level': overall_suspicion.value,
                'average_suspicion_score': avg_suspicion,
                'high_suspicion_activities': len([a for a in activities if a.suspicion_level in [SuspicionLevel.HIGH, SuspicionLevel.CRITICAL]]),
                'alerts': alerts,
                'recommendations': recommendations,
                'time_span': {
                    'start': activities[0].timestamp.isoformat() if activities else None,
                    'end': activities[-1].timestamp.isoformat() if activities else None,
                    'duration_minutes': self._calculate_duration(activities)
                }
            }
            
        except Exception as e:
            logger.error(f"Proctoring summary generation failed: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_suspicion_level(self, event: ActivityEvent) -> SuspicionLevel:
        """Calculate suspicion level for an activity"""
        activity_type = event.activity_type.value
        
        if activity_type not in self.suspicion_thresholds:
            return SuspicionLevel.LOW
        
        thresholds = self.suspicion_thresholds[activity_type]
        time_window = thresholds['time_window']
        
        # Count similar activities in time window
        recent_activities = [
            a for a in self.activity_buffer[event.session_id]
            if a.activity_type == event.activity_type and
            (event.timestamp - a.timestamp).total_seconds() <= time_window
        ]
        
        activity_count = len(recent_activities)
        
        # Determine suspicion level based on count
        if activity_count >= thresholds['high']:
            return SuspicionLevel.CRITICAL
        elif activity_count >= thresholds['medium']:
            return SuspicionLevel.HIGH
        elif activity_count >= thresholds['low']:
            return SuspicionLevel.MEDIUM
        else:
            return SuspicionLevel.LOW
    
    def _should_auto_flag(self, suspicion_level: SuspicionLevel) -> bool:
        """Determine if activity should be auto-flagged"""
        if not self.monitoring_rules['auto_flag_suspicious']:
            return False
        
        threshold = self.monitoring_rules['notification_threshold']
        
        # Convert enum to numeric for comparison
        level_values = {
            SuspicionLevel.LOW: 1,
            SuspicionLevel.MEDIUM: 2,
            SuspicionLevel.HIGH: 3,
            SuspicionLevel.CRITICAL: 4
        }
        
        return level_values[suspicion_level] >= level_values[threshold]
    
    def _generate_alerts(self, event: ActivityEvent) -> List[Dict]:
        """Generate alerts for suspicious activity"""
        alerts = []
        
        if event.suspicion_level in [SuspicionLevel.HIGH, SuspicionLevel.CRITICAL]:
            alert = {
                'alert_id': f"alert_{event.timestamp.timestamp()}_{event.user_id}",
                'timestamp': event.timestamp.isoformat(),
                'user_id': event.user_id,
                'exam_id': event.exam_id,
                'activity_type': event.activity_type.value,
                'suspicion_level': event.suspicion_level.value,
                'message': self._generate_alert_message(event),
                'requires_review': True,
                'auto_flagged': True
            }
            alerts.append(alert)
        
        return alerts
    
    def _generate_alert_message(self, event: ActivityEvent) -> str:
        """Generate alert message for activity"""
        messages = {
            ActivityType.TAB_SWITCH: f"Suspicious tab switching detected ({event.details.get('switch_count', 0)} switches)",
            ActivityType.WINDOW_BLUR: f"Window focus lost multiple times ({event.details.get('blur_count', 0)} times)",
            ActivityType.COPY_PASTE: f"Copy-paste activity detected ({event.details.get('paste_count', 0)} times)",
            ActivityType.RIGHT_CLICK: f"Right-click activity detected ({event.details.get('right_click_count', 0)} times)",
            ActivityType.NO_FACE: f"No face detected for {event.details.get('no_face_duration', 0)} seconds",
            ActivityType.MULTIPLE_FACES: f"Multiple faces detected ({event.details.get('face_count', 0)} faces)"
        }
        
        return messages.get(event.activity_type, f"Suspicious activity detected: {event.activity_type.value}")
    
    def _create_log_entry(self, event: ActivityEvent) -> Dict:
        """Create structured log entry"""
        return {
            'timestamp': event.timestamp.isoformat(),
            'user_id': event.user_id,
            'exam_id': event.exam_id,
            'session_id': event.session_id,
            'activity_type': event.activity_type.value,
            'suspicion_level': event.suspicion_level.value,
            'details': event.details,
            'logged_at': timezone.now().isoformat()
        }
    
    def _create_alert_from_activity(self, event: ActivityEvent) -> Dict:
        """Create alert from activity event"""
        return {
            'alert_id': f"alert_{event.timestamp.timestamp()}_{event.user_id}",
            'timestamp': event.timestamp.isoformat(),
            'activity_type': event.activity_type.value,
            'suspicion_level': event.suspicion_level.value,
            'details': event.details,
            'message': self._generate_alert_message(event)
        }
    
    # Helper methods
    def _count_open_tabs(self, user_id: str, exam_id: str) -> int:
        """Count open tabs (mock implementation)"""
        return 1  # Mock implementation
    
    def _count_tab_switches(self, user_id: str, exam_id: str, session_id: str) -> int:
        """Count tab switches in session"""
        session_key = session_id or f"{user_id}_{exam_id}"
        return len([
            a for a in self.activity_buffer[session_key]
            if a.activity_type == ActivityType.TAB_SWITCH
        ])
    
    def _count_window_blurs(self, user_id: str, exam_id: str, session_id: str) -> int:
        """Count window blur events"""
        session_key = session_id or f"{user_id}_{exam_id}"
        return len([
            a for a in self.activity_buffer[session_key]
            if a.activity_type == ActivityType.WINDOW_BLUR
        ])
    
    def _count_copy_paste(self, user_id: str, exam_id: str, session_id: str) -> int:
        """Count copy-paste events"""
        session_key = session_id or f"{user_id}_{exam_id}"
        return len([
            a for a in self.activity_buffer[session_key]
            if a.activity_type == ActivityType.COPY_PASTE
        ])
    
    def _count_right_clicks(self, user_id: str, exam_id: str, session_id: str) -> int:
        """Count right-click events"""
        session_key = session_id or f"{user_id}_{exam_id}"
        return len([
            a for a in self.activity_buffer[session_key]
            if a.activity_type == ActivityType.RIGHT_CLICK
        ])
    
    def _get_active_window_title(self) -> str:
        """Get active window title (mock implementation)"""
        return "Exam Window"  # Mock implementation
    
    def _check_suspicious_content(self, content: str) -> bool:
        """Check if content is suspicious"""
        if not content:
            return False
        
        suspicious_keywords = ['answer', 'solution', 'cheat', 'hack', 'copy']
        content_lower = content.lower()
        
        return any(keyword in content_lower for keyword in suspicious_keywords)
    
    def _is_suspicious_element(self, element: str) -> bool:
        """Check if right-clicked element is suspicious"""
        if not element:
            return False
        
        suspicious_elements = ['input', 'textarea', 'select', 'exam', 'question']
        element_lower = element.lower()
        
        return any(sus_element in element_lower for sus_element in suspicious_elements)
    
    def _calculate_no_face_duration(self, user_id: str, exam_id: str, session_id: str) -> float:
        """Calculate duration of no face detection"""
        session_key = session_id or f"{user_id}_{exam_id}"
        no_face_events = [
            a for a in self.activity_buffer[session_key]
            if a.activity_type == ActivityType.NO_FACE
        ]
        
        if not no_face_events:
            return 0.0
        
        # Calculate total no-face duration
        total_duration = 0.0
        for event in no_face_events:
            total_duration += event.details.get('no_face_duration', 0)
        
        return total_duration
    
    def _detect_face_movement(self, face_coordinates: List[Dict]) -> bool:
        """Detect suspicious face movement"""
        if not face_coordinates or len(face_coordinates) < 2:
            return False
        
        # Simple movement detection (can be enhanced with actual computer vision)
        return True  # Mock implementation
    
    def _suspicion_level_to_score(self, level: SuspicionLevel) -> float:
        """Convert suspicion level to numeric score"""
        scores = {
            SuspicionLevel.LOW: 0.25,
            SuspicionLevel.MEDIUM: 0.5,
            SuspicionLevel.HIGH: 0.75,
            SuspicionLevel.CRITICAL: 1.0
        }
        return scores.get(level, 0.0)
    
    def _score_to_suspicion_level(self, score: float) -> SuspicionLevel:
        """Convert numeric score to suspicion level"""
        if score >= 0.8:
            return SuspicionLevel.CRITICAL
        elif score >= 0.6:
            return SuspicionLevel.HIGH
        elif score >= 0.4:
            return SuspicionLevel.MEDIUM
        else:
            return SuspicionLevel.LOW
    
    def _calculate_duration(self, activities: List[ActivityEvent]) -> float:
        """Calculate duration of activities"""
        if not activities or len(activities) < 2:
            return 0.0
        
        start_time = activities[0].timestamp
        end_time = activities[-1].timestamp
        
        return (end_time - start_time).total_seconds() / 60  # Convert to minutes
    
    def _generate_proctoring_recommendations(self, activities: List[ActivityEvent], 
                                         overall_suspicion: SuspicionLevel) -> List[str]:
        """Generate proctoring recommendations"""
        recommendations = []
        
        if overall_suspicion in [SuspicionLevel.HIGH, SuspicionLevel.CRITICAL]:
            recommendations.append("Manual review recommended due to high suspicious activity")
        
        # Activity-specific recommendations
        activity_types = [a.activity_type for a in activities]
        
        if ActivityType.TAB_SWITCH in activity_types:
            tab_switch_count = len([a for a in activities if a.activity_type == ActivityType.TAB_SWITCH])
            if tab_switch_count > 5:
                recommendations.append("Excessive tab switching detected - consider flagging for review")
        
        if ActivityType.COPY_PASTE in activity_types:
            recommendations.append("Copy-paste activity detected - verify answer authenticity")
        
        if ActivityType.MULTIPLE_FACES in activity_types:
            recommendations.append("Multiple faces detected - verify student identity")
        
        if ActivityType.NO_FACE in activity_types:
            recommendations.append("Face not detected during exam - verify student presence")
        
        return recommendations

# Singleton instance
proctoring_engine = ProctoringEngine()
