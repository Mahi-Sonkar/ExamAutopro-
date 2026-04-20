"""
Intelligent Question Analysis System for ExamAutoPro
Main motive: Advanced question processing and intelligent classification
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from collections import Counter, defaultdict
import math

logger = logging.getLogger(__name__)

class QuestionType(Enum):
    """Question type enumeration"""
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
    """Bloom's taxonomy cognitive levels"""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"
    UNKNOWN = "unknown"

class DifficultyLevel(Enum):
    """Difficulty level enumeration"""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"
    UNKNOWN = "unknown"

@dataclass
class QuestionMetadata:
    """Question metadata structure"""
    text: str
    question_type: QuestionType
    cognitive_level: CognitiveLevel
    difficulty_level: DifficultyLevel
    topic: str
    subject_area: str
    keywords: List[str]
    marks: Optional[int]
    time_estimate: Optional[int]  # in minutes
    confidence_score: float
    page_number: Optional[int]
    options: Optional[List[str]]
    correct_answer: Optional[str]

class IntelligentQuestionAnalyzer:
    """
    Advanced question analysis system with intelligent classification
    Main motive: Comprehensive question understanding and processing
    """
    
    def __init__(self):
        self._initialize_patterns()
        self._initialize_knowledge_base()
        
    def _initialize_patterns(self) -> None:
        """Initialize question patterns and keywords"""
        
        # Question type patterns
        self.type_patterns = {
            QuestionType.MULTIPLE_CHOICE: [
                r'which\s+of\s+the\s+following',
                r'select\s+the\s+correct',
                r'choose\s+the\s+best',
                r'which\s+one\s+of\s+the',
                r'\([a-e]\)[\.\)]',
                r'^[A-E][\.\)]\s+',
                r'which\s+option',
                r'all\s+of\s+the\s+above',
                r'none\s+of\s+the\s+above'
            ],
            QuestionType.TRUE_FALSE: [
                r'true\s+or\s+false',
                r'\.?\s*(true|false)',
                r'(is|are)\s+(true|false)',
                r'state\s+whether\s+true\s+or\s+false',
                r'correct\s+or\s+incorrect'
            ],
            QuestionType.SHORT_ANSWER: [
                r'what\s+is',
                r'what\s+are',
                r'where\s+is',
                r'when\s+did',
                r'who\s+is',
                r'why\s+is',
                r'how\s+does',
                r'list\s+\d+',
                r'name\s+\d+',
                r'define\s+\w+',
                r'explain\s+briefly'
            ],
            QuestionType.ESSAY: [
                r'discuss\s+the',
                r'analyze\s+the',
                r'evaluate\s+the',
                r'compare\s+and\s+contrast',
                r'critically\s+analyze',
                r'explain\s+in\s+detail',
                r'describe\s+in\s+detail',
                r'write\s+an\s+essay',
                r'elaborate\s+on'
            ],
            QuestionType.FILL_BLANK: [
                r'fill\s+in\s+the\s+blank',
                r'complete\s+the\s+sentence',
                r'_____\s+is\s+',
                r'\[\s*\]\s+is\s+',
                r'___\s+represents'
            ],
            QuestionType.MATCHING: [
                r'match\s+the\s+following',
                r'column\s+[AB]\s+with\s+column\s+[AB]',
                r'pair\s+the\s+following',
                r'match\s+column\s+[AB]'
            ],
            QuestionType.NUMERICAL: [
                r'calculate\s+the',
                r'find\s+the\s+value',
                r'determine\s+the\s+number',
                r'how\s+many',
                r'what\s+is\s+the\s+value',
                r'solve\s+for\s+\w+',
                r'compute\s+the'
            ]
        }
        
        # Cognitive level indicators (Bloom's taxonomy)
        self.cognitive_indicators = {
            CognitiveLevel.REMEMBER: [
                'list', 'define', 'identify', 'name', 'recall', 'recognize', 
                'state', 'repeat', 'write', 'select', 'label', 'enumerate'
            ],
            CognitiveLevel.UNDERSTAND: [
                'explain', 'describe', 'summarize', 'interpret', 'classify', 
                'compare', 'contrast', 'paraphrase', 'discuss', 'predict'
            ],
            CognitiveLevel.APPLY: [
                'apply', 'use', 'implement', 'execute', 'demonstrate', 
                'solve', 'calculate', 'show', 'perform', 'practice'
            ],
            CognitiveLevel.ANALYZE: [
                'analyze', 'examine', 'break down', 'differentiate', 'distinguish', 
                'compare', 'contrast', 'investigate', 'categorize', 'attribute'
            ],
            CognitiveLevel.EVALUATE: [
                'evaluate', 'judge', 'critique', 'assess', 'justify', 'validate', 
                'defend', 'argue', 'rate', 'prioritize', 'determine'
            ],
            CognitiveLevel.CREATE: [
                'create', 'design', 'develop', 'construct', 'formulate', 
                'plan', 'produce', 'generate', 'invent', 'compose'
            ]
        }
        
        # Difficulty indicators
        self.difficulty_indicators = {
            DifficultyLevel.VERY_EASY: [
                'what is', 'name', 'list', 'simple', 'basic', 'easy'
            ],
            DifficultyLevel.EASY: [
                'describe', 'explain', 'define', 'identify', 'state'
            ],
            DifficultyLevel.MEDIUM: [
                'analyze', 'compare', 'discuss', 'explain why', 'how does'
            ],
            DifficultyLevel.HARD: [
                'evaluate', 'critique', 'analyze critically', 'synthesize'
            ],
            DifficultyLevel.VERY_HARD: [
                'create', 'design', 'develop', 'formulate', 'invent'
            ]
        }
        
        # Subject area keywords
        self.subject_keywords = {
            'mathematics': [
                'calculate', 'solve', 'equation', 'formula', 'number', 
                'algebra', 'geometry', 'statistics', 'probability', 'graph'
            ],
            'science': [
                'experiment', 'hypothesis', 'theory', 'observation', 'data',
                'biology', 'chemistry', 'physics', 'scientific', 'research'
            ],
            'history': [
                'historical', 'period', 'event', 'date', 'war', 'revolution',
                'ancient', 'modern', 'century', 'dynasty', 'empire'
            ],
            'literature': [
                'author', 'novel', 'poem', 'character', 'theme', 'literary',
                'genre', 'plot', 'setting', 'symbolism', 'metaphor'
            ],
            'geography': [
                'country', 'capital', 'continent', 'ocean', 'mountain',
                'river', 'climate', 'population', 'location', 'region'
            ],
            'computer_science': [
                'algorithm', 'programming', 'code', 'software', 'hardware',
                'database', 'network', 'security', 'system', 'interface'
            ],
            'business': [
                'management', 'marketing', 'finance', 'economics', 'strategy',
                'organization', 'market', 'customer', 'profit', 'investment'
            ]
        }
    
    def _initialize_knowledge_base(self) -> None:
        """Initialize knowledge base for analysis"""
        # Common question templates
        self.question_templates = {
            'definition': r'(what|who|which)\s+(is|are|was|were)\s+(\w+)',
            'explanation': r'why\s+(is|are|was|were)\s+(\w+)',
            'process': r'how\s+(does|do|did)\s+(\w+)',
            'comparison': r'compare\s+(\w+)\s+(and|with|to)\s+(\w+)',
            'evaluation': r'evaluate\s+the\s+(\w+)',
            'application': r'apply\s+(\w+)\s+to\s+(\w+)'
        }
        
        # Time estimation rules (in minutes)
        self.time_estimation_rules = {
            QuestionType.MULTIPLE_CHOICE: 1.5,
            QuestionType.TRUE_FALSE: 0.5,
            QuestionType.SHORT_ANSWER: 3.0,
            QuestionType.ESSAY: 15.0,
            QuestionType.FILL_BLANK: 1.0,
            QuestionType.MATCHING: 2.0,
            QuestionType.NUMERICAL: 5.0,
            QuestionType.DIAGRAMMATIC: 4.0
        }
        
        # Marks allocation rules
        self.marks_allocation = {
            QuestionType.MULTIPLE_CHOICE: 1,
            QuestionType.TRUE_FALSE: 1,
            QuestionType.SHORT_ANSWER: 3,
            QuestionType.ESSAY: 10,
            QuestionType.FILL_BLANK: 1,
            QuestionType.MATCHING: 2,
            QuestionType.NUMERICAL: 5,
            QuestionType.DIAGRAMMATIC: 4
        }
    
    def analyze_question(self, question_text: str, context: Dict = None) -> QuestionMetadata:
        """
        Comprehensive question analysis
        Main motive: Intelligent question understanding and classification
        """
        try:
            # Clean and preprocess question
            cleaned_text = self._preprocess_question(question_text)
            
            # Extract basic information
            question_type = self._classify_question_type(cleaned_text)
            cognitive_level = self._identify_cognitive_level(cleaned_text)
            difficulty_level = self._assess_difficulty(cleaned_text, cognitive_level)
            topic = self._identify_topic(cleaned_text)
            subject_area = self._identify_subject_area(cleaned_text)
            keywords = self._extract_keywords(cleaned_text)
            
            # Extract options and answers
            options, correct_answer = self._extract_options_and_answer(cleaned_text, question_type)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(cleaned_text, question_type, cognitive_level)
            
            # Estimate time and marks
            time_estimate = self._estimate_time(question_type, difficulty_level, cleaned_text)
            marks = self._estimate_marks(question_type, difficulty_level)
            
            # Create metadata
            metadata = QuestionMetadata(
                text=question_text,
                question_type=question_type,
                cognitive_level=cognitive_level,
                difficulty_level=difficulty_level,
                topic=topic,
                subject_area=subject_area,
                keywords=keywords,
                marks=marks,
                time_estimate=time_estimate,
                confidence_score=confidence_score,
                page_number=context.get('page_number') if context else None,
                options=options if options else None,
                correct_answer=correct_answer if correct_answer else None
            )
            
            return metadata
            
        except Exception as e:
            logger.error(f"Question analysis failed: {str(e)}")
            # Return basic metadata
            return QuestionMetadata(
                text=question_text,
                question_type=QuestionType.UNKNOWN,
                cognitive_level=CognitiveLevel.UNKNOWN,
                difficulty_level=DifficultyLevel.UNKNOWN,
                topic='unknown',
                subject_area='general',
                keywords=[],
                marks=None,
                time_estimate=None,
                confidence_score=0.0,
                page_number=None,
                options=None,
                correct_answer=None
            )
    
    def analyze_question_batch(self, questions: List[str], context: List[Dict] = None) -> List[QuestionMetadata]:
        """Analyze multiple questions in batch"""
        results = []
        
        for i, question in enumerate(questions):
            question_context = context[i] if context and i < len(context) else None
            metadata = self.analyze_question(question, question_context)
            results.append(metadata)
        
        return results
    
    def generate_question_insights(self, questions: List[QuestionMetadata]) -> Dict:
        """Generate insights from analyzed questions"""
        if not questions:
            return {'error': 'No questions provided'}
        
        # Type distribution
        type_counts = Counter(q.question_type for q in questions)
        
        # Cognitive level distribution
        cognitive_counts = Counter(q.cognitive_level for q in questions)
        
        # Difficulty distribution
        difficulty_counts = Counter(q.difficulty_level for q in questions)
        
        # Subject area distribution
        subject_counts = Counter(q.subject_area for q in questions)
        
        # Topic distribution
        topic_counts = Counter(q.topic for q in questions)
        
        # Average confidence
        avg_confidence = sum(q.confidence_score for q in questions) / len(questions)
        
        # Total estimated time
        total_time = sum(q.time_estimate for q in questions if q.time_estimate)
        
        # Total marks
        total_marks = sum(q.marks for q in questions if q.marks)
        
        # Quality assessment
        quality_score = self._assess_question_quality(questions)
        
        # Recommendations
        recommendations = self._generate_question_recommendations(questions)
        
        return {
            'total_questions': len(questions),
            'type_distribution': dict(type_counts),
            'cognitive_distribution': dict(cognitive_counts),
            'difficulty_distribution': dict(difficulty_counts),
            'subject_distribution': dict(subject_counts),
            'topic_distribution': dict(topic_counts),
            'average_confidence': avg_confidence,
            'total_estimated_time': total_time,
            'total_marks': total_marks,
            'quality_score': quality_score,
            'quality_level': self._get_quality_level(quality_score),
            'recommendations': recommendations,
            'insights': {
                'cognitive_balance': self._analyze_cognitive_balance(cognitive_counts),
                'difficulty_appropriateness': self._analyze_difficulty_appropriateness(difficulty_counts),
                'topic_coverage': self._analyze_topic_coverage(topic_counts),
                'type_variety': self._analyze_type_variety(type_counts)
            }
        }
    
    def _preprocess_question(self, question_text: str) -> str:
        """Preprocess question text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', question_text.strip())
        
        # Normalize case for pattern matching
        text_lower = text.lower()
        
        return text
    
    def _classify_question_type(self, question_text: str) -> QuestionType:
        """Classify question type using pattern matching"""
        text_lower = question_text.lower()
        
        # Check each question type
        for question_type, patterns in self.type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return question_type
        
        return QuestionType.UNKNOWN
    
    def _identify_cognitive_level(self, question_text: str) -> CognitiveLevel:
        """Identify cognitive level using Bloom's taxonomy"""
        text_lower = question_text.lower()
        
        # Check each cognitive level
        for cognitive_level, indicators in self.cognitive_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return cognitive_level
        
        return CognitiveLevel.UNKNOWN
    
    def _assess_difficulty(self, question_text: str, cognitive_level: CognitiveLevel) -> DifficultyLevel:
        """Assess question difficulty"""
        text_lower = question_text.lower()
        
        # Base difficulty from cognitive level
        cognitive_difficulty = {
            CognitiveLevel.REMEMBER: DifficultyLevel.EASY,
            CognitiveLevel.UNDERSTAND: DifficultyLevel.EASY,
            CognitiveLevel.APPLY: DifficultyLevel.MEDIUM,
            CognitiveLevel.ANALYZE: DifficultyLevel.HARD,
            CognitiveLevel.EVALUATE: DifficultyLevel.HARD,
            CognitiveLevel.CREATE: DifficultyLevel.VERY_HARD,
            CognitiveLevel.UNKNOWN: DifficultyLevel.MEDIUM
        }
        
        base_difficulty = cognitive_difficulty.get(cognitive_level, DifficultyLevel.MEDIUM)
        
        # Adjust based on difficulty indicators
        for difficulty_level, indicators in self.difficulty_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    # Override with specific difficulty indicators
                    return difficulty_level
        
        # Adjust based on question length and complexity
        word_count = len(question_text.split())
        if word_count > 20:
            # Longer questions tend to be more difficult
            difficulty_values = list(DifficultyLevel)
            current_index = difficulty_values.index(base_difficulty)
            if current_index < len(difficulty_values) - 1:
                return difficulty_values[current_index + 1]
        elif word_count < 5:
            # Very short questions tend to be easier
            difficulty_values = list(DifficultyLevel)
            current_index = difficulty_values.index(base_difficulty)
            if current_index > 0:
                return difficulty_values[current_index - 1]
        
        return base_difficulty
    
    def _identify_topic(self, question_text: str) -> str:
        """Identify the main topic of the question"""
        # Extract keywords and determine topic
        words = question_text.lower().split()
        
        # Simple topic identification based on common topics
        topic_keywords = {
            'mathematics': ['calculate', 'solve', 'equation', 'number', 'formula'],
            'science': ['experiment', 'theory', 'hypothesis', 'observation'],
            'history': ['historical', 'date', 'event', 'period'],
            'geography': ['country', 'capital', 'location', 'region'],
            'literature': ['author', 'novel', 'poem', 'character'],
            'technology': ['computer', 'software', 'internet', 'digital']
        }
        
        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in words)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        
        return 'general'
    
    def _identify_subject_area(self, question_text: str) -> str:
        """Identify subject area"""
        text_lower = question_text.lower()
        
        for subject, keywords in self.subject_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return subject
        
        return 'general'
    
    def _extract_keywords(self, question_text: str) -> List[str]:
        """Extract keywords from question"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'what', 'where', 'when', 'why', 'how', 'who', 'which'}
        
        words = question_text.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Return top 10 keywords
    
    def _extract_options_and_answer(self, question_text: str, question_type: QuestionType) -> Tuple[Optional[List[str]], Optional[str]]:
        """Extract options and correct answer if available"""
        if question_type == QuestionType.MULTIPLE_CHOICE:
            # Extract multiple choice options
            options = []
            
            # Pattern for lettered options
            lettered_pattern = r'([A-E])[\.\)]\s*([^.!?]+)'
            matches = re.findall(lettered_pattern, question_text)
            
            for letter, option in matches:
                options.append(f"{letter}) {option.strip()}")
            
            # Pattern for numbered options
            numbered_pattern = r'\d+[\.\)]\s*([^.!?]+)'
            numbered_matches = re.findall(numbered_pattern, question_text)
            
            for option in numbered_matches:
                options.append(option.strip())
            
            return options if options else None, None
        
        return None, None
    
    def _calculate_confidence_score(self, question_text: str, question_type: QuestionType, cognitive_level: CognitiveLevel) -> float:
        """Calculate confidence score for classification"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for clear question types
        if question_type != QuestionType.UNKNOWN:
            confidence += 0.2
        
        # Increase confidence for clear cognitive levels
        if cognitive_level != CognitiveLevel.UNKNOWN:
            confidence += 0.2
        
        # Increase confidence for well-formed questions
        if question_text.endswith('?'):
            confidence += 0.1
        
        # Check for clear structure
        if len(question_text.split()) >= 3:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _estimate_time(self, question_type: QuestionType, difficulty_level: DifficultyLevel, question_text: str) -> int:
        """Estimate time required to answer question"""
        base_time = self.time_estimation_rules.get(question_type, 5.0)
        
        # Adjust based on difficulty
        difficulty_multipliers = {
            DifficultyLevel.VERY_EASY: 0.5,
            DifficultyLevel.EASY: 0.75,
            DifficultyLevel.MEDIUM: 1.0,
            DifficultyLevel.HARD: 1.5,
            DifficultyLevel.VERY_HARD: 2.0,
            DifficultyLevel.UNKNOWN: 1.0
        }
        
        multiplier = difficulty_multipliers.get(difficulty_level, 1.0)
        
        # Adjust based on question length
        word_count = len(question_text.split())
        length_adjustment = 1.0 + (word_count - 10) * 0.05  # 5% adjustment per word over 10
        
        estimated_time = base_time * multiplier * length_adjustment
        
        return max(1, int(estimated_time))  # Minimum 1 minute
    
    def _estimate_marks(self, question_type: QuestionType, difficulty_level: DifficultyLevel) -> int:
        """Estimate marks for question"""
        base_marks = self.marks_allocation.get(question_type, 3)
        
        # Adjust based on difficulty
        difficulty_adjustments = {
            DifficultyLevel.VERY_EASY: 0.5,
            DifficultyLevel.EASY: 0.75,
            DifficultyLevel.MEDIUM: 1.0,
            DifficultyLevel.HARD: 1.5,
            DifficultyLevel.VERY_HARD: 2.0,
            DifficultyLevel.UNKNOWN: 1.0
        }
        
        adjustment = difficulty_adjustments.get(difficulty_level, 1.0)
        
        estimated_marks = base_marks * adjustment
        
        return max(1, int(estimated_marks))  # Minimum 1 mark
    
    def _assess_question_quality(self, questions: List[QuestionMetadata]) -> float:
        """Assess overall quality of questions"""
        if not questions:
            return 0.0
        
        quality_scores = []
        
        for question in questions:
            score = 0.0
            
            # Confidence score
            score += question.confidence_score * 0.3
            
            # Type clarity
            if question.question_type != QuestionType.UNKNOWN:
                score += 0.2
            
            # Cognitive level clarity
            if question.cognitive_level != CognitiveLevel.UNKNOWN:
                score += 0.2
            
            # Appropriate difficulty
            if question.difficulty_level != DifficultyLevel.UNKNOWN:
                score += 0.2
            
            # Has keywords
            if question.keywords:
                score += 0.1
            
            quality_scores.append(score)
        
        return sum(quality_scores) / len(quality_scores)
    
    def _generate_question_recommendations(self, questions: List[QuestionMetadata]) -> List[str]:
        """Generate recommendations for question improvement"""
        recommendations = []
        
        if not questions:
            return ['No questions to analyze']
        
        # Analyze type distribution
        type_counts = Counter(q.question_type for q in questions)
        total_questions = len(questions)
        
        # Type variety recommendations
        if type_counts.get(QuestionType.MULTIPLE_CHOICE, 0) > total_questions * 0.8:
            recommendations.append('Consider adding more diverse question types (short answer, essay, etc.)')
        
        # Cognitive balance recommendations
        cognitive_counts = Counter(q.cognitive_level for q in questions)
        if cognitive_counts.get(CognitiveLevel.REMEMBER, 0) > total_questions * 0.6:
            recommendations.append('Include more questions that require higher-order thinking (analysis, evaluation)')
        
        # Difficulty distribution recommendations
        difficulty_counts = Counter(q.difficulty_level for q in questions)
        if difficulty_counts.get(DifficultyLevel.EASY, 0) > total_questions * 0.7:
            recommendations.append('Add more challenging questions to test advanced understanding')
        
        # Subject area recommendations
        subject_counts = Counter(q.subject_area for q in questions)
        if len(subject_counts) == 1:
            recommendations.append('Consider including questions from multiple subject areas')
        
        return recommendations
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level from score"""
        if score >= 0.9:
            return 'excellent'
        elif score >= 0.8:
            return 'very_good'
        elif score >= 0.7:
            return 'good'
        elif score >= 0.6:
            return 'fair'
        elif score >= 0.5:
            return 'poor'
        else:
            return 'very_poor'
    
    def _analyze_cognitive_balance(self, cognitive_counts: Counter) -> Dict:
        """Analyze cognitive level balance"""
        total = sum(cognitive_counts.values())
        
        if total == 0:
            return {'balance_score': 0.0, 'recommendation': 'No cognitive levels identified'}
        
        # Ideal distribution (more higher-order thinking)
        ideal_distribution = {
            CognitiveLevel.REMEMBER: 0.15,
            CognitiveLevel.UNDERSTAND: 0.20,
            CognitiveLevel.APPLY: 0.25,
            CognitiveLevel.ANALYZE: 0.20,
            CognitiveLevel.EVALUATE: 0.15,
            CognitiveLevel.CREATE: 0.05
        }
        
        balance_score = 0.0
        for level, ideal_ratio in ideal_distribution.items():
            actual_ratio = cognitive_counts.get(level, 0) / total
            balance_score += 1.0 - abs(actual_ratio - ideal_ratio)
        
        balance_score /= len(ideal_distribution)
        
        return {
            'balance_score': balance_score,
            'distribution': {k.value: v/total for k, v in cognitive_counts.items()},
            'recommendation': 'Good cognitive balance' if balance_score > 0.7 else 'Improve cognitive level distribution'
        }
    
    def _analyze_difficulty_appropriateness(self, difficulty_counts: Counter) -> Dict:
        """Analyze difficulty distribution appropriateness"""
        total = sum(difficulty_counts.values())
        
        if total == 0:
            return {'appropriateness_score': 0.0, 'recommendation': 'No difficulty levels identified'}
        
        # Ideal difficulty distribution (bell curve)
        ideal_distribution = {
            DifficultyLevel.VERY_EASY: 0.10,
            DifficultyLevel.EASY: 0.25,
            DifficultyLevel.MEDIUM: 0.30,
            DifficultyLevel.HARD: 0.25,
            DifficultyLevel.VERY_HARD: 0.10
        }
        
        appropriateness_score = 0.0
        for level, ideal_ratio in ideal_distribution.items():
            actual_ratio = difficulty_counts.get(level, 0) / total
            appropriateness_score += 1.0 - abs(actual_ratio - ideal_ratio)
        
        appropriateness_score /= len(ideal_distribution)
        
        return {
            'appropriateness_score': appropriateness_score,
            'distribution': {k.value: v/total for k, v in difficulty_counts.items()},
            'recommendation': 'Appropriate difficulty distribution' if appropriateness_score > 0.7 else 'Adjust difficulty distribution'
        }
    
    def _analyze_topic_coverage(self, topic_counts: Counter) -> Dict:
        """Analyze topic coverage"""
        total = sum(topic_counts.values())
        
        if total == 0:
            return {'coverage_score': 0.0, 'recommendation': 'No topics identified'}
        
        # Good coverage means variety of topics
        coverage_score = min(len(topic_counts) / 5.0, 1.0)  # Normalize to 5 topics as ideal
        
        return {
            'coverage_score': coverage_score,
            'topic_count': len(topic_counts),
            'topics': dict(topic_counts.most_common(10)),
            'recommendation': 'Good topic coverage' if coverage_score > 0.6 else 'Increase topic variety'
        }
    
    def _analyze_type_variety(self, type_counts: Counter) -> Dict:
        """Analyze question type variety"""
        total = sum(type_counts.values())
        
        if total == 0:
            return {'variety_score': 0.0, 'recommendation': 'No question types identified'}
        
        # Good variety means multiple types
        variety_score = min(len(type_counts) / 4.0, 1.0)  # Normalize to 4 types as ideal
        
        return {
            'variety_score': variety_score,
            'type_count': len(type_counts),
            'types': {k.value: v for k, v in type_counts.items()},
            'recommendation': 'Good type variety' if variety_score > 0.5 else 'Increase question type variety'
        }

# Singleton instance
question_analyzer = IntelligentQuestionAnalyzer()
