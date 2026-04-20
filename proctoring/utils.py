import cv2
import numpy as np
import face_recognition
import logging
from django.conf import settings
from .models import ProctoringSession, ProctoringEvent

logger = logging.getLogger(__name__)

class ProctoringUtils:
    """Utility class for proctoring functionality"""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.known_face_encodings = []
        self.known_face_names = []
    
    def detect_faces(self, image_path):
        """Detect faces in an image"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {'faces_detected': 0, 'error': 'Could not read image'}
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            face_count = len(faces)
            face_locations = []
            
            for (x, y, w, h) in faces:
                face_locations.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h)
                })
            
            return {
                'faces_detected': face_count,
                'face_locations': face_locations,
                'image_shape': image.shape
            }
            
        except Exception as e:
            logger.error(f"Face detection failed: {str(e)}")
            return {'faces_detected': 0, 'error': str(e)}
    
    def verify_face_match(self, current_image, reference_image):
        """Verify if the face in current image matches reference image"""
        try:
            # Load images
            current_img = face_recognition.load_image_file(current_image)
            reference_img = face_recognition.load_image_file(reference_image)
            
            # Find face locations
            current_face_locations = face_recognition.face_locations(current_img)
            reference_face_locations = face_recognition.face_locations(reference_img)
            
            if not current_face_locations or not reference_face_locations:
                return {'match': False, 'confidence': 0.0, 'error': 'No faces found'}
            
            # Get face encodings
            current_face_encoding = face_recognition.face_encodings(current_img, current_face_locations)[0]
            reference_face_encoding = face_recognition.face_encodings(reference_img, reference_face_locations)[0]
            
            # Compare faces
            face_distance = face_recognition.face_distance([reference_face_encoding], current_face_encoding)[0]
            confidence = 1 - face_distance
            
            # Consider match if confidence > 0.6
            is_match = confidence > 0.6
            
            return {
                'match': is_match,
                'confidence': float(confidence),
                'face_distance': float(face_distance)
            }
            
        except Exception as e:
            logger.error(f"Face verification failed: {str(e)}")
            return {'match': False, 'confidence': 0.0, 'error': str(e)}
    
    def detect_eye_movement(self, image_path):
        """Detect eye movement and direction"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {'error': 'Could not read image'}
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            eye_detection_results = []
            
            for (x, y, w, h) in faces:
                # Extract face ROI
                face_roi = gray[y:y+h, x:x+w]
                
                # Detect eyes within face ROI
                eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
                eyes = eye_cascade.detectMultiScale(face_roi)
                
                if len(eyes) >= 2:
                    # Calculate eye center
                    eye_centers = []
                    for (ex, ey, ew, eh) in eyes[:2]:
                        eye_center_x = ex + ew // 2
                        eye_center_y = ey + eh // 2
                        eye_centers.append((eye_center_x, eye_center_y))
                    
                    # Determine gaze direction
                    if len(eye_centers) == 2:
                        avg_eye_x = sum(center[0] for center in eye_centers) / 2
                        face_center_x = w // 2
                        
                        if avg_eye_x < face_center_x - 20:
                            direction = 'left'
                        elif avg_eye_x > face_center_x + 20:
                            direction = 'right'
                        else:
                            direction = 'center'
                        
                        eye_detection_results.append({
                            'face_position': (x, y, w, h),
                            'eyes_detected': len(eyes),
                            'gaze_direction': direction,
                            'eye_centers': eye_centers
                        })
            
            return {
                'faces_processed': len(faces),
                'eye_detection_results': eye_detection_results
            }
            
        except Exception as e:
            logger.error(f"Eye movement detection failed: {str(e)}")
            return {'error': str(e)}
    
    def analyze_screen_content(self, image_path):
        """Analyze screen content for suspicious activity"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {'error': 'Could not read image'}
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect edges to identify potential window boundaries
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours that might represent windows or tabs
            window_like_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 10000:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Check if contour has window-like aspect ratio
                    if 0.5 < aspect_ratio < 3.0:
                        window_like_contours.append({
                            'x': int(x),
                            'y': int(y),
                            'width': int(w),
                            'height': int(h),
                            'area': int(area),
                            'aspect_ratio': float(aspect_ratio)
                        })
            
            # Detect potential browser tabs or multiple windows
            suspicious_indicators = []
            if len(window_like_contours) > 1:
                suspicious_indicators.append('multiple_windows_detected')
            
            # Check for common browser UI elements
            # This is a simplified version - in production, use more sophisticated detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detect blue colors (common in browser interfaces)
            lower_blue = np.array([100, 50, 50])
            upper_blue = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            blue_pixels = cv2.countNonZero(blue_mask)
            
            if blue_pixels > 5000:
                suspicious_indicators.append('browser_ui_detected')
            
            return {
                'window_like_contours': window_like_contours,
                'suspicious_indicators': suspicious_indicators,
                'blue_pixel_count': int(blue_pixels),
                'total_contours': len(contours)
            }
            
        except Exception as e:
            logger.error(f"Screen content analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def detect_audio_anomalies(self, audio_data):
        """Detect anomalies in audio data"""
        try:
            import librosa
            import numpy as np
            
            # Load audio data
            y, sr = librosa.load(audio_data)
            
            # Extract features
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
            
            # Detect anomalies
            anomalies = []
            
            # Check for unusual silence periods
            silence_threshold = 0.01
            silence_frames = np.sum(np.abs(y) < silence_threshold)
            silence_percentage = (silence_frames / len(y)) * 100
            
            if silence_percentage > 80:
                anomalies.append('excessive_silence')
            elif silence_percentage < 10:
                anomalies.append('no_silence_detected')
            
            # Check for unusual audio levels
            rms = librosa.feature.rms(y=y)
            avg_rms = np.mean(rms)
            
            if avg_rms > 0.1:
                anomalies.append('high_audio_level')
            elif avg_rms < 0.001:
                anomalies.append('very_low_audio_level')
            
            # Check for multiple speakers (simplified)
            spectral_centroid_mean = np.mean(spectral_centroids)
            if spectral_centroid_mean > 3000:
                anomalies.append('high_frequency_content')
            
            return {
                'anomalies': anomalies,
                'silence_percentage': float(silence_percentage),
                'avg_rms': float(avg_rms),
                'spectral_centroid_mean': float(spectral_centroid_mean),
                'audio_duration': float(len(y) / sr)
            }
            
        except Exception as e:
            logger.error(f"Audio anomaly detection failed: {str(e)}")
            return {'error': str(e)}
    
    def generate_session_report(self, session_id):
        """Generate comprehensive proctoring session report"""
        try:
            session = ProctoringSession.objects.get(session_id=session_id)
            
            # Get all events for the session
            events = session.events.all()
            alerts = session.alerts.all()
            
            # Analyze events
            event_summary = {}
            for event in events:
                event_type = event.event_type
                if event_type not in event_summary:
                    event_summary[event_type] = {
                        'count': 0,
                        'severity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
                    }
                
                event_summary[event_type]['count'] += 1
                event_summary[event_type]['severity_distribution'][event.severity] += 1
            
            # Calculate risk score
            risk_score = self.calculate_risk_score(events, alerts)
            
            # Generate recommendations
            recommendations = self.generate_recommendations(events, alerts, risk_score)
            
            report = {
                'session_info': {
                    'session_id': session.session_id,
                    'student_email': session.student.email,
                    'exam_title': session.exam.title,
                    'start_time': session.start_time,
                    'end_time': session.end_time,
                    'duration': str(session.duration),
                    'total_events': session.total_events,
                    'suspicious_activities': session.suspicious_activities
                },
                'event_summary': event_summary,
                'alerts': [
                    {
                        'alert_type': alert.alert_type,
                        'severity': alert.severity,
                        'message': alert.message,
                        'created_at': alert.created_at,
                        'acknowledged': alert.acknowledged
                    }
                    for alert in alerts
                ],
                'risk_assessment': {
                    'risk_score': risk_score,
                    'risk_level': self.get_risk_level(risk_score),
                    'confidence': self.calculate_confidence_score(events)
                },
                'recommendations': recommendations
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Session report generation failed: {str(e)}")
            return {'error': str(e)}
    
    def calculate_risk_score(self, events, alerts):
        """Calculate overall risk score for a session"""
        risk_score = 0
        
        # Weight different event types
        event_weights = {
            'tab_switch': 2,
            'face_not_detected': 3,
            'multiple_faces': 5,
            'copy_paste': 4,
            'right_click': 1,
            'fullscreen_exit': 3,
            'mobile_device': 4,
            'vpn_detected': 5
        }
        
        for event in events:
            weight = event_weights.get(event.event_type, 1)
            severity_multiplier = {'low': 1, 'medium': 2, 'high': 3, 'critical': 5}.get(event.severity, 1)
            risk_score += weight * severity_multiplier
        
        # Add alert contributions
        for alert in alerts:
            if alert.severity == 'critical':
                risk_score += 10
            elif alert.severity == 'error':
                risk_score += 7
            elif alert.severity == 'warning':
                risk_score += 3
        
        return min(risk_score, 100)  # Cap at 100
    
    def get_risk_level(self, risk_score):
        """Get risk level based on score"""
        if risk_score >= 80:
            return 'very_high'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        elif risk_score >= 20:
            return 'low'
        else:
            return 'very_low'
    
    def calculate_confidence_score(self, events):
        """Calculate confidence in the proctoring results"""
        if not events:
            return 0.0
        
        # More events = higher confidence (up to a point)
        event_count = len(events)
        confidence = min(event_count / 10, 1.0)  # Cap at 1.0
        
        # Reduce confidence if too many low-severity events (might be noise)
        low_severity_count = sum(1 for e in events if e.severity == 'low')
        if low_severity_count > event_count * 0.8:
            confidence *= 0.7
        
        return round(confidence, 2)
    
    def generate_recommendations(self, events, alerts, risk_score):
        """Generate recommendations based on proctoring data"""
        recommendations = []
        
        # Analyze event patterns
        tab_switches = [e for e in events if e.event_type == 'tab_switch']
        face_issues = [e for e in events if e.event_type == 'face_not_detected']
        
        if len(tab_switches) > 5:
            recommendations.append("High number of tab switches detected. Consider manual review.")
        
        if len(face_issues) > 10:
            recommendations.append("Frequent face detection failures. Verify student identity.")
        
        if risk_score >= 80:
            recommendations.append("Very high risk score detected. Immediate manual review recommended.")
        elif risk_score >= 60:
            recommendations.append("High risk score. Consider additional verification.")
        
        # Check for specific patterns
        critical_alerts = [a for a in alerts if a.severity == 'critical']
        if critical_alerts:
            recommendations.append("Critical alerts detected. Requires immediate attention.")
        
        if not recommendations:
            recommendations.append("No major concerns detected. Session appears normal.")
        
        return recommendations
