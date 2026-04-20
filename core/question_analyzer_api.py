"""
Question Analyzer API Implementation
Implements missing analyze_question_batch method for API
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    NUMERICAL = "numerical"
    DIAGRAMMATIC = "diagrammatic"
    UNKNOWN = "unknown"

class CognitiveLevel(Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"

class DifficultyLevel(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class QuestionAnalysisResult:
    text: str
    question_type: QuestionType
    cognitive_level: CognitiveLevel
    difficulty_level: DifficultyLevel
    topic: str
    subject_area: str
    keywords: List[str]
    marks: int
    time_estimate: int
    confidence_score: float
    page_number: int
    options: List[str]
    correct_answer: str

class QuestionAnalyzerAPI:
    """Question analyzer for API operations"""
    
    def __init__(self):
        self.question_patterns = {
            'multiple_choice': [
                r'(?i)\b(?:which|what|who|when|where|why|how)\b.*\b(?:is|are|was|were)\b',
                r'(?i)\b(?:select|choose)\b.*\b(?:the|a)\s+.*',
                r'(?i)\b(?:which|what)\s+.*\b(?:of\s+the\s+following)\b'
            ],
            'true_false': [
                r'(?i)\b(?:true|false)\b',
                r'(?i)\b(?:correct|incorrect)\b',
                r'(?i)\b(?:right|wrong)\b'
            ],
            'short_answer': [
                r'(?i)\b(?:what|who|when|where|why|how)\b.*\?$',
                r'(?i)\b(?:define|describe|explain|state)\b.*\?$'
            ],
            'essay': [
                r'(?i)\b(?:discuss|analyze|evaluate|compare|contrast)\b.*\?$',
                r'(?i)\b(?:write|elaborate)\b.*\?$'
            ],
            'fill_blank': [
                r'(?i)\b.*___.*\b',
                r'(?i)\b.*\.\.\.\.*\b'
            ],
            'numerical': [
                r'(?i)\b(?:calculate|compute|find|determine)\b.*\?$',
                r'(?i)\b(?:solve)\b.*\?$'
            ]
        }
    
    def analyze_question_batch(self, questions: List[str], context: List[str] = None) -> List[QuestionAnalysisResult]:
        """Analyze a batch of questions"""
        results = []
        
        for i, question in enumerate(questions):
            try:
                # Analyze single question
                result = self._analyze_single_question(question, context[i] if context and i < len(context) else None)
                results.append(result)
            except Exception as e:
                logger.error(f"Question analysis failed: {e}")
                # Create default result
                results.append(self._create_default_result(question))
        
        return results
    
    def _analyze_single_question(self, question: str, context: str = None) -> QuestionAnalysisResult:
        """Analyze a single question"""
        # Determine question type
        question_type = self._determine_question_type(question)
        
        # Determine cognitive level
        cognitive_level = self._determine_cognitive_level(question)
        
        # Determine difficulty level
        difficulty_level = self._determine_difficulty_level(question)
        
        # Extract keywords
        keywords = self._extract_keywords(question)
        
        # Determine topic and subject area
        topic, subject_area = self._determine_topic_and_subject(question)
        
        # Estimate marks and time
        marks = self._estimate_marks(question, question_type)
        time_estimate = self._estimate_time(question, question_type)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(question, question_type)
        
        # Extract options and correct answer if multiple choice
        options, correct_answer = self._extract_options_and_answer(question)
        
        return QuestionAnalysisResult(
            text=question,
            question_type=question_type,
            cognitive_level=cognitive_level,
            difficulty_level=difficulty_level,
            topic=topic,
            subject_area=subject_area,
            keywords=keywords,
            marks=marks,
            time_estimate=time_estimate,
            confidence_score=confidence_score,
            page_number=0,  # Default, would be set by PDF processing
            options=options,
            correct_answer=correct_answer
        )
    
    def _determine_question_type(self, question: str) -> QuestionType:
        """Determine question type based on patterns"""
        question_lower = question.lower()
        
        # Check for multiple choice
        if any(re.search(pattern, question) for pattern in self.question_patterns['multiple_choice']):
            if '(' in question and ')' in question or 'a)' in question.lower():
                return QuestionType.MULTIPLE_CHOICE
        
        # Check for true/false
        if any(re.search(pattern, question) for pattern in self.question_patterns['true_false']):
            return QuestionType.TRUE_FALSE
        
        # Check for fill in the blanks
        if any(re.search(pattern, question) for pattern in self.question_patterns['fill_blank']):
            return QuestionType.FILL_BLANK
        
        # Check for numerical
        if any(re.search(pattern, question) for pattern in self.question_patterns['numerical']):
            return QuestionType.NUMERICAL
        
        # Check for essay
        if any(re.search(pattern, question) for pattern in self.question_patterns['essay']):
            return QuestionType.ESSAY
        
        # Check for short answer
        if any(re.search(pattern, question) for pattern in self.question_patterns['short_answer']):
            return QuestionType.SHORT_ANSWER
        
        return QuestionType.UNKNOWN
    
    def _determine_cognitive_level(self, question: str) -> CognitiveLevel:
        """Determine cognitive level based on keywords"""
        question_lower = question.lower()
        
        remember_keywords = ['define', 'list', 'name', 'identify', 'recall']
        understand_keywords = ['describe', 'explain', 'summarize', 'interpret']
        apply_keywords = ['apply', 'use', 'implement', 'demonstrate']
        analyze_keywords = ['analyze', 'compare', 'contrast', 'examine']
        evaluate_keywords = ['evaluate', 'judge', 'critique', 'assess']
        create_keywords = ['create', 'design', 'develop', 'construct']
        
        if any(keyword in question_lower for keyword in remember_keywords):
            return CognitiveLevel.REMEMBER
        elif any(keyword in question_lower for keyword in understand_keywords):
            return CognitiveLevel.UNDERSTAND
        elif any(keyword in question_lower for keyword in apply_keywords):
            return CognitiveLevel.APPLY
        elif any(keyword in question_lower for keyword in analyze_keywords):
            return CognitiveLevel.ANALYZE
        elif any(keyword in question_lower for keyword in evaluate_keywords):
            return CognitiveLevel.EVALUATE
        elif any(keyword in question_lower for keyword in create_keywords):
            return CognitiveLevel.CREATE
        else:
            return CognitiveLevel.UNDERSTAND  # Default
    
    def _determine_difficulty_level(self, question: str) -> DifficultyLevel:
        """Determine difficulty level"""
        question_lower = question.lower()
        
        # Simple indicators
        if any(word in question_lower for word in ['simple', 'basic', 'easy']):
            return DifficultyLevel.EASY
        elif any(word in question_lower for word in ['complex', 'difficult', 'hard', 'challenging']):
            return DifficultyLevel.HARD
        else:
            return DifficultyLevel.MEDIUM
    
    def _extract_keywords(self, question: str) -> List[str]:
        """Extract keywords from question"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', question.lower())
        
        # Remove common stop words
        stop_words = {'that', 'this', 'with', 'from', 'they', 'have', 'been', 'their', 'what', 'when', 'where', 'why', 'how', 'which', 'who', 'will', 'would', 'could', 'should'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        return keywords[:10]  # Return top 10 keywords
    
    def _determine_topic_and_subject(self, question: str) -> Tuple[str, str]:
        """Determine topic and subject area"""
        question_lower = question.lower()
        
        # Subject area mapping
        subject_keywords = {
            'mathematics': ['math', 'calculate', 'number', 'equation', 'formula', 'geometry', 'algebra'],
            'science': ['science', 'physics', 'chemistry', 'biology', 'experiment', 'hypothesis'],
            'computer': ['computer', 'programming', 'algorithm', 'software', 'hardware', 'code'],
            'english': ['english', 'grammar', 'literature', 'writing', 'reading'],
            'history': ['history', 'historical', 'ancient', 'modern', 'war', 'peace'],
            'geography': ['geography', 'map', 'country', 'city', 'climate', 'environment']
        }
        
        for subject, keywords in subject_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                return subject.capitalize(), subject.capitalize()
        
        return "General", "General"
    
    def _estimate_marks(self, question: str, question_type: QuestionType) -> int:
        """Estimate marks for question"""
        marks_mapping = {
            QuestionType.MULTIPLE_CHOICE: 1,
            QuestionType.TRUE_FALSE: 1,
            QuestionType.SHORT_ANSWER: 2,
            QuestionType.FILL_BLANK: 1,
            QuestionType.NUMERICAL: 3,
            QuestionType.ESSAY: 5,
            QuestionType.UNKNOWN: 2
        }
        
        return marks_mapping.get(question_type, 2)
    
    def _estimate_time(self, question: str, question_type: QuestionType) -> int:
        """Estimate time in minutes"""
        time_mapping = {
            QuestionType.MULTIPLE_CHOICE: 1,
            QuestionType.TRUE_FALSE: 1,
            QuestionType.SHORT_ANSWER: 3,
            QuestionType.FILL_BLANK: 2,
            QuestionType.NUMERICAL: 5,
            QuestionType.ESSAY: 10,
            QuestionType.UNKNOWN: 3
        }
        
        return time_mapping.get(question_type, 3)
    
    def _calculate_confidence(self, question: str, question_type: QuestionType) -> float:
        """Calculate confidence score"""
        # Base confidence based on question type
        type_confidence = {
            QuestionType.MULTIPLE_CHOICE: 0.9,
            QuestionType.TRUE_FALSE: 0.9,
            QuestionType.SHORT_ANSWER: 0.7,
            QuestionType.FILL_BLANK: 0.8,
            QuestionType.NUMERICAL: 0.6,
            QuestionType.ESSAY: 0.5,
            QuestionType.UNKNOWN: 0.3
        }
        
        base_confidence = type_confidence.get(question_type, 0.5)
        
        # Adjust based on question length
        length_factor = min(len(question) / 100, 1.0)
        
        return base_confidence * (0.5 + 0.5 * length_factor)
    
    def _extract_options_and_answer(self, question: str) -> Tuple[List[str], str]:
        """Extract options and correct answer for multiple choice questions"""
        options = []
        correct_answer = ""
        
        # Simple pattern matching for options
        option_patterns = [
            r'\(([a-d])\)\s*([^.!?]+)',  # (a) Option text
            r'([a-d])[\.\)]\s*([^.!?]+)',  # a. Option text
            r'([A-D])[\.\)]\s*([^.!?]+)'   # A. Option text
        ]
        
        for pattern in option_patterns:
            matches = re.findall(pattern, question)
            for match in matches:
                options.append(match[1].strip())
        
        # Try to identify correct answer (very basic)
        if 'correct' in question.lower():
            correct_match = re.search(r'correct.*?([a-d])', question.lower())
            if correct_match:
                correct_answer = correct_match.group(1).upper()
        
        return options, correct_answer
    
    def _create_default_result(self, question: str) -> QuestionAnalysisResult:
        """Create default result for failed analysis"""
        return QuestionAnalysisResult(
            text=question,
            question_type=QuestionType.UNKNOWN,
            cognitive_level=CognitiveLevel.UNDERSTAND,
            difficulty_level=DifficultyLevel.MEDIUM,
            topic="General",
            subject_area="General",
            keywords=[],
            marks=2,
            time_estimate=3,
            confidence_score=0.3,
            page_number=0,
            options=[],
            correct_answer=""
        )

# Global question analyzer instance
question_analyzer = QuestionAnalyzerAPI()
