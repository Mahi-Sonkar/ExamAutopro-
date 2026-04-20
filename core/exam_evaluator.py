"""
Advanced Exam Evaluation Backend for ExamAutoPro
Main motive: Intelligent exam assessment and automated evaluation
"""

import json
import logging
import time
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter
from datetime import datetime, timedelta

from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from django.core.cache import cache

from exams.models import Exam, Question, Answer, ExamSubmission
from .question_analyzer import question_analyzer

logger = logging.getLogger(__name__)

class EvaluationType(Enum):
    """Evaluation type enumeration"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    HYBRID = "hybrid"
    PEER = "peer"
    SELF = "self"

class EvaluationMethod(Enum):
    """Evaluation method enumeration"""
    EXACT_MATCH = "exact_match"
    KEYWORD_MATCH = "keyword_match"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    PATTERN_MATCHING = "pattern_matching"
    RUBRIC_BASED = "rubric_based"
    AI_POWERED = "ai_powered"

@dataclass
class EvaluationResult:
    """Evaluation result structure"""
    submission_id: str
    question_id: str
    score: float
    max_score: float
    confidence: float
    evaluation_method: EvaluationMethod
    feedback: str
    evaluation_time: float
    evaluator_notes: Dict[str, Any]

@dataclass
class ExamEvaluationSummary:
    """Exam evaluation summary structure"""
    exam_id: str
    total_submissions: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    evaluation_method: EvaluationMethod
    evaluation_time: float
    quality_metrics: Dict[str, float]
    recommendations: List[str]

class AdvancedExamEvaluator:
    """
    Advanced exam evaluation system with intelligent assessment
    Main motive: Comprehensive and accurate exam evaluation
    """
    
    def __init__(self):
        self._initialize_evaluation_rules()
        self._initialize_rubrics()
        
    def _initialize_evaluation_rules(self) -> None:
        """Initialize evaluation rules and criteria"""
        
        # Question type evaluation methods
        self.question_evaluation_methods = {
            'multiple_choice': EvaluationMethod.EXACT_MATCH,
            'true_false': EvaluationMethod.EXACT_MATCH,
            'short_answer': EvaluationMethod.KEYWORD_MATCH,
            'essay': EvaluationMethod.SEMANTIC_SIMILARITY,
            'fill_blank': EvaluationMethod.KEYWORD_MATCH,
            'matching': EvaluationMethod.EXACT_MATCH,
            'numerical': EvaluationMethod.PATTERN_MATCHING
        }
        
        # Scoring weights
        self.scoring_weights = {
            'correctness': 0.6,      # Correctness of answer
            'completeness': 0.2,    # Completeness of answer
            'clarity': 0.1,         # Clarity and organization
            'relevance': 0.1        # Relevance to question
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            EvaluationMethod.EXACT_MATCH: 0.95,
            EvaluationMethod.KEYWORD_MATCH: 0.7,
            EvaluationMethod.SEMANTIC_SIMILARITY: 0.6,
            EvaluationMethod.PATTERN_MATCHING: 0.8,
            EvaluationMethod.RUBRIC_BASED: 0.75,
            EvaluationMethod.AI_POWERED: 0.8
        }
        
        # Grade boundaries
        self.grade_boundaries = {
            'A': (90, 100),
            'B': (80, 89),
            'C': (70, 79),
            'D': (60, 69),
            'F': (0, 59)
        }
    
    def _initialize_rubrics(self) -> None:
        """Initialize evaluation rubrics"""
        
        # Essay evaluation rubric
        self.essay_rubric = {
            'content_understanding': {
                'excellent': (90, 100),
                'good': (80, 89),
                'satisfactory': (70, 79),
                'needs_improvement': (60, 69),
                'poor': (0, 59)
            },
            'organization': {
                'excellent': (90, 100),
                'good': (80, 89),
                'satisfactory': (70, 79),
                'needs_improvement': (60, 69),
                'poor': (0, 59)
            },
            'analysis': {
                'excellent': (90, 100),
                'good': (80, 89),
                'satisfactory': (70, 79),
                'needs_improvement': (60, 69),
                'poor': (0, 59)
            },
            'writing_quality': {
                'excellent': (90, 100),
                'good': (80, 89),
                'satisfactory': (70, 79),
                'needs_improvement': (60, 69),
                'poor': (0, 59)
            }
        }
        
        # Short answer evaluation criteria
        self.short_answer_criteria = {
            'key_concepts': 0.4,
            'accuracy': 0.3,
            'completeness': 0.2,
            'clarity': 0.1
        }
    
    def evaluate_submission(self, submission_id: str, evaluation_type: EvaluationType = EvaluationType.AUTOMATIC) -> Dict:
        """
        Evaluate a complete exam submission
        Main motive: Comprehensive and intelligent assessment
        """
        try:
            start_time = time.time()
            
            # Get submission
            submission = ExamSubmission.objects.get(id=submission_id)
            
            # Update status
            submission.status = 'evaluating'
            submission.save()
            
            # Get all answers for this submission
            answers = Answer.objects.filter(submission=submission)
            
            evaluation_results = []
            total_score = 0.0
            total_max_score = 0.0
            
            # Evaluate each answer
            for answer in answers:
                result = self._evaluate_answer(answer, evaluation_type)
                evaluation_results.append(result)
                total_score += result.score
                total_max_score += result.max_score
            
            # Calculate overall metrics
            percentage_score = (total_score / total_max_score * 100) if total_max_score > 0 else 0
            grade = self._calculate_grade(percentage_score)
            
            # Generate feedback
            feedback = self._generate_submission_feedback(evaluation_results, percentage_score)
            
            # Create evaluation summary
            summary = ExamEvaluationSummary(
                exam_id=str(submission.exam.id),
                total_submissions=1,
                average_score=percentage_score,
                highest_score=percentage_score,
                lowest_score=percentage_score,
                pass_rate=1.0 if percentage_score >= 60 else 0.0,
                evaluation_method=self._determine_primary_method(evaluation_results),
                evaluation_time=time.time() - start_time,
                quality_metrics=self._calculate_quality_metrics(evaluation_results),
                recommendations=self._generate_recommendations(evaluation_results)
            )
            
            # Update submission
            submission.total_score = total_score
            submission.percentage_score = percentage_score
            submission.grade = grade
            submission.status = 'evaluated'
            submission.evaluated_at = timezone.now()
            submission.save()
            
            return {
                'success': True,
                'submission_id': submission_id,
                'evaluation_results': evaluation_results,
                'summary': {
                    'total_score': total_score,
                    'total_max_score': total_max_score,
                    'percentage_score': percentage_score,
                    'grade': grade,
                    'evaluation_time': time.time() - start_time
                },
                'feedback': feedback,
                'detailed_summary': summary
            }
            
        except Exception as e:
            logger.error(f"Submission evaluation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def evaluate_exam_batch(self, exam_id: str, evaluation_type: EvaluationType = EvaluationType.AUTOMATIC) -> Dict:
        """Evaluate all submissions for an exam"""
        try:
            start_time = time.time()
            
            # Get exam
            exam = Exam.objects.get(id=exam_id)
            
            # Get all submissions
            submissions = ExamSubmission.objects.filter(exam=exam, status='submitted')
            
            if not submissions:
                return {'success': False, 'error': 'No submissions found for evaluation'}
            
            evaluation_results = []
            total_scores = []
            
            # Evaluate each submission
            for submission in submissions:
                result = self.evaluate_submission(str(submission.id), evaluation_type)
                if result['success']:
                    evaluation_results.append(result)
                    total_scores.append(result['summary']['percentage_score'])
            
            # Calculate exam statistics
            if total_scores:
                average_score = sum(total_scores) / len(total_scores)
                highest_score = max(total_scores)
                lowest_score = min(total_scores)
                pass_count = sum(1 for score in total_scores if score >= 60)
                pass_rate = pass_count / len(total_scores)
            else:
                average_score = highest_score = lowest_score = pass_rate = 0.0
            
            # Generate exam-level insights
            insights = self._generate_exam_insights(evaluation_results, exam)
            
            return {
                'success': True,
                'exam_id': exam_id,
                'total_submissions': len(submissions),
                'evaluated_submissions': len(evaluation_results),
                'statistics': {
                    'average_score': average_score,
                    'highest_score': highest_score,
                    'lowest_score': lowest_score,
                    'pass_rate': pass_rate,
                    'grade_distribution': self._calculate_grade_distribution(total_scores)
                },
                'evaluation_time': time.time() - start_time,
                'insights': insights,
                'recommendations': self._generate_exam_recommendations(insights)
            }
            
        except Exception as e:
            logger.error(f"Batch evaluation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _evaluate_answer(self, answer: Answer, evaluation_type: EvaluationType) -> EvaluationResult:
        """Evaluate a single answer"""
        try:
            start_time = time.time()
            
            # Get question
            question = answer.question
            
            # Determine evaluation method
            method = self._determine_evaluation_method(question, evaluation_type)
            
            # Evaluate based on method
            if method == EvaluationMethod.EXACT_MATCH:
                score, confidence = self._evaluate_exact_match(answer, question)
            elif method == EvaluationMethod.KEYWORD_MATCH:
                score, confidence = self._evaluate_keyword_match(answer, question)
            elif method == EvaluationMethod.SEMANTIC_SIMILARITY:
                score, confidence = self._evaluate_semantic_similarity(answer, question)
            elif method == EvaluationMethod.PATTERN_MATCHING:
                score, confidence = self._evaluate_pattern_matching(answer, question)
            elif method == EvaluationMethod.RUBRIC_BASED:
                score, confidence = self._evaluate_rubric_based(answer, question)
            else:
                score, confidence = self._evaluate_ai_powered(answer, question)
            
            # Generate feedback
            feedback = self._generate_answer_feedback(answer, question, score, method)
            
            # Create result
            result = EvaluationResult(
                submission_id=str(answer.submission.id),
                question_id=str(question.id),
                score=score,
                max_score=question.marks,
                confidence=confidence,
                evaluation_method=method,
                feedback=feedback,
                evaluation_time=time.time() - start_time,
                evaluator_notes={
                    'question_type': question.question_type,
                    'answer_text': answer.answer_text,
                    'correct_answer': question.correct_answer,
                    'evaluation_type': evaluation_type.value
                }
            )
            
            # Update answer
            answer.marks_obtained = score
            answer.is_correct = score >= question.marks * 0.6  # 60% threshold
            answer.save()
            
            return result
            
        except Exception as e:
            logger.error(f"Answer evaluation failed: {str(e)}")
            # Return default result
            return EvaluationResult(
                submission_id=str(answer.submission.id),
                question_id=str(answer.id),
                score=0.0,
                max_score=answer.question.marks,
                confidence=0.0,
                evaluation_method=EvaluationMethod.EXACT_MATCH,
                feedback="Evaluation failed",
                evaluation_time=0.0,
                evaluator_notes={'error': str(e)}
            )
    
    def _determine_evaluation_method(self, question: Question, evaluation_type: EvaluationType) -> EvaluationMethod:
        """Determine the best evaluation method for a question"""
        if evaluation_type == EvaluationType.MANUAL:
            return EvaluationMethod.RUBRIC_BASED
        
        # Use question type to determine method
        return self.question_evaluation_methods.get(question.question_type, EvaluationMethod.KEYWORD_MATCH)
    
    def _evaluate_exact_match(self, answer: Answer, question: Question) -> Tuple[float, float]:
        """Evaluate using exact matching"""
        if not answer.answer_text or not question.correct_answer:
            return 0.0, 0.0
        
        # Normalize both answers
        student_answer = answer.answer_text.strip().lower()
        correct_answer = question.correct_answer.strip().lower()
        
        # Exact match
        if student_answer == correct_answer:
            return float(question.marks), 1.0
        
        # Partial match (for multiple choice)
        if question.question_type == 'multiple_choice':
            # Check if the option is correct
            options = question.options.all()
            for option in options:
                if option.text.strip().lower() == student_answer and option.is_correct:
                    return float(question.marks), 1.0
        
        return 0.0, 0.0
    
    def _evaluate_keyword_match(self, answer: Answer, question: Question) -> Tuple[float, float]:
        """Evaluate using keyword matching"""
        if not answer.answer_text:
            return 0.0, 0.0
        
        # Extract keywords from correct answer
        if not question.correct_answer:
            return 0.0, 0.0
        
        correct_keywords = self._extract_keywords(question.correct_answer)
        student_keywords = self._extract_keywords(answer.answer_text)
        
        # Calculate keyword overlap
        if not correct_keywords:
            return 0.0, 0.0
        
        matching_keywords = set(correct_keywords) & set(student_keywords)
        keyword_ratio = len(matching_keywords) / len(correct_keywords)
        
        # Calculate score based on keyword ratio
        score = float(question.marks) * keyword_ratio
        confidence = min(keyword_ratio * 1.2, 1.0)  # Boost confidence slightly
        
        return score, confidence
    
    def _evaluate_semantic_similarity(self, answer: Answer, question: Question) -> Tuple[float, float]:
        """Evaluate using semantic similarity"""
        if not answer.answer_text or not question.correct_answer:
            return 0.0, 0.0
        
        # Simple semantic similarity based on word overlap
        student_words = set(answer.answer_text.lower().split())
        correct_words = set(question.correct_answer.lower().split())
        
        if not correct_words:
            return 0.0, 0.0
        
        # Jaccard similarity
        intersection = student_words & correct_words
        union = student_words | correct_words
        similarity = len(intersection) / len(union) if union else 0.0
        
        # Calculate score
        score = float(question.marks) * similarity
        confidence = similarity
        
        return score, confidence
    
    def _evaluate_pattern_matching(self, answer: Answer, question: Question) -> Tuple[float, float]:
        """Evaluate using pattern matching"""
        if not answer.answer_text:
            return 0.0, 0.0
        
        # For numerical questions
        if question.question_type == 'numerical':
            return self._evaluate_numerical_answer(answer, question)
        
        # For other pattern-based questions
        return self._evaluate_general_pattern(answer, question)
    
    def _evaluate_numerical_answer(self, answer: Answer, question: Question) -> Tuple[float, float]:
        """Evaluate numerical answer"""
        try:
            # Extract numbers from answers
            import re
            student_numbers = re.findall(r'[-+]?\d*\.?\d+', answer.answer_text)
            correct_numbers = re.findall(r'[-+]?\d*\.?\d+', question.correct_answer)
            
            if not student_numbers or not correct_numbers:
                return 0.0, 0.0
            
            # Compare first numbers (simplified)
            student_val = float(student_numbers[0])
            correct_val = float(correct_numbers[0])
            
            # Allow small tolerance
            tolerance = correct_val * 0.05  # 5% tolerance
            if abs(student_val - correct_val) <= tolerance:
                return float(question.marks), 1.0
            else:
                # Partial credit based on closeness
                difference = abs(student_val - correct_val)
                max_difference = correct_val * 0.5  # 50% difference threshold
                if difference <= max_difference:
                    partial_score = 1.0 - (difference / max_difference)
                    return float(question.marks) * partial_score, 0.5
                else:
                    return 0.0, 0.0
                    
        except (ValueError, IndexError):
            return 0.0, 0.0
    
    def _evaluate_general_pattern(self, answer: Answer, question: Question) -> Tuple[float, float]:
        """Evaluate general pattern-based answer"""
        # Simple pattern matching
        student_answer = answer.answer_text.strip().lower()
        correct_answer = question.correct_answer.strip().lower()
        
        # Check if student answer contains key parts of correct answer
        correct_parts = correct_answer.split()
        matching_parts = sum(1 for part in correct_parts if part in student_answer)
        
        if not correct_parts:
            return 0.0, 0.0
        
        match_ratio = matching_parts / len(correct_parts)
        score = float(question.marks) * match_ratio
        confidence = match_ratio
        
        return score, confidence
    
    def _evaluate_rubric_based(self, answer: Answer, question: Question) -> Tuple[float, float]:
        """Evaluate using rubric-based assessment"""
        if question.question_type == 'essay':
            return self._evaluate_essay_rubric(answer, question)
        else:
            return self._evaluate_general_rubric(answer, question)
    
    def _evaluate_essay_rubric(self, answer: Answer, question: Question) -> Tuple[float, float]:
        """Evaluate essay using rubric"""
        if not answer.answer_text:
            return 0.0, 0.0
        
        # Simple rubric evaluation based on length and content
        essay_text = answer.answer_text
        
        # Length assessment
        word_count = len(essay_text.split())
        length_score = min(word_count / 100, 1.0)  # Assume 100 words is ideal
        
        # Content assessment (simplified)
        content_score = self._assess_essay_content(essay_text, question.correct_answer)
        
        # Organization assessment (simplified)
        organization_score = self._assess_essay_organization(essay_text)
        
        # Calculate overall score
        overall_score = (length_score * 0.2 + content_score * 0.5 + organization_score * 0.3)
        final_score = float(question.marks) * overall_score
        confidence = 0.7  # Medium confidence for rubric evaluation
        
        return final_score, confidence
    
    def _assess_essay_content(self, essay_text: str, expected_content: str) -> float:
        """Assess essay content quality"""
        if not expected_content:
            return 0.5  # Default score
        
        # Keyword matching with expected content
        expected_keywords = self._extract_keywords(expected_content)
        essay_keywords = self._extract_keywords(essay_text)
        
        if not expected_keywords:
            return 0.5
        
        matching_keywords = set(expected_keywords) & set(essay_keywords)
        content_score = len(matching_keywords) / len(expected_keywords)
        
        return min(content_score * 1.2, 1.0)  # Boost slightly
    
    def _assess_essay_organization(self, essay_text: str) -> float:
        """Assess essay organization"""
        # Simple organization assessment based on structure
        sentences = essay_text.split('.')
        
        # Check for basic structure indicators
        has_intro = any(word in sentences[0].lower() for word in ['introduction', 'first', 'beginning']) if sentences else False
        has_conclusion = any(word in sentences[-1].lower() for word in ['conclusion', 'finally', 'in conclusion']) if sentences else False
        
        # Length-based organization
        organization_score = 0.5  # Base score
        if len(sentences) >= 3:  # Has intro, body, conclusion
            organization_score += 0.3
        if has_intro:
            organization_score += 0.1
        if has_conclusion:
            organization_score += 0.1
        
        return min(organization_score, 1.0)
    
    def _evaluate_general_rubric(self, answer: Answer, question: Question) -> Tuple[float, float]:
        """Evaluate using general rubric"""
        # Use keyword matching as fallback
        return self._evaluate_keyword_match(answer, question)
    
    def _evaluate_ai_powered(self, answer: Answer, question: Question) -> Tuple[float, float]:
        """Evaluate using AI-powered methods"""
        # For now, fall back to semantic similarity
        # In a real implementation, this would use advanced AI models
        return self._evaluate_semantic_similarity(answer, question)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        
        words = text.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _generate_answer_feedback(self, answer: Answer, question: Question, score: float, method: EvaluationMethod) -> str:
        """Generate feedback for an answer"""
        max_score = question.marks
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        feedback_parts = []
        
        # Performance feedback
        if percentage >= 90:
            feedback_parts.append("Excellent answer!")
        elif percentage >= 80:
            feedback_parts.append("Good answer.")
        elif percentage >= 70:
            feedback_parts.append("Satisfactory answer.")
        elif percentage >= 60:
            feedback_parts.append("Answer needs improvement.")
        else:
            feedback_parts.append("Incorrect answer.")
        
        # Method-specific feedback
        if method == EvaluationMethod.EXACT_MATCH:
            if percentage < 100:
                feedback_parts.append("The correct answer was: " + str(question.correct_answer))
        elif method == EvaluationMethod.KEYWORD_MATCH:
            if percentage < 80:
                feedback_parts.append("Consider including more key concepts from the question.")
        elif method == EvaluationMethod.SEMANTIC_SIMILARITY:
            if percentage < 70:
                feedback_parts.append("Try to focus more closely on the main topic.")
        
        # Question-specific feedback
        if question.question_type == 'essay':
            if percentage < 70:
                feedback_parts.append("Consider developing your ideas more fully and providing better structure.")
        elif question.question_type == 'short_answer':
            if percentage < 80:
                feedback_parts.append("Be more concise and focus on the key points.")
        
        return " ".join(feedback_parts)
    
    def _generate_submission_feedback(self, evaluation_results: List[EvaluationResult], percentage_score: float) -> str:
        """Generate feedback for the entire submission"""
        feedback_parts = []
        
        # Overall performance
        if percentage_score >= 90:
            feedback_parts.append("Outstanding performance! You've demonstrated excellent understanding of the material.")
        elif percentage_score >= 80:
            feedback_parts.append("Very good performance! You have a strong grasp of the subject matter.")
        elif percentage_score >= 70:
            feedback_parts.append("Good performance! You understand most of the key concepts.")
        elif percentage_score >= 60:
            feedback_parts.append("Satisfactory performance. Review the areas where you lost marks.")
        else:
            feedback_parts.append("You need to study the material more thoroughly. Consider reviewing all topics.")
        
        # Question-specific insights
        question_types = Counter(result.evaluator_notes.get('question_type', 'unknown') for result in evaluation_results)
        
        if 'essay' in question_types:
            essay_results = [r for r in evaluation_results if r.evaluator_notes.get('question_type') == 'essay']
            avg_essay_score = sum(r.score / r.max_score for r in essay_results) / len(essay_results) if essay_results else 0
            if avg_essay_score < 0.7:
                feedback_parts.append("Focus on improving your essay writing skills with better structure and content development.")
        
        if 'short_answer' in question_types:
            short_results = [r for r in evaluation_results if r.evaluator_notes.get('question_type') == 'short_answer']
            avg_short_score = sum(r.score / r.max_score for r in short_results) / len(short_results) if short_results else 0
            if avg_short_score < 0.8:
                feedback_parts.append("Work on being more precise in your short answers.")
        
        return " ".join(feedback_parts)
    
    def _calculate_grade(self, percentage_score: float) -> str:
        """Calculate grade from percentage score"""
        for grade, (min_score, max_score) in self.grade_boundaries.items():
            if min_score <= percentage_score <= max_score:
                return grade
        return 'F'
    
    def _determine_primary_method(self, evaluation_results: List[EvaluationResult]) -> EvaluationMethod:
        """Determine the primary evaluation method used"""
        if not evaluation_results:
            return EvaluationMethod.EXACT_MATCH
        
        method_counts = Counter(result.evaluation_method for result in evaluation_results)
        return method_counts.most_common(1)[0][0]
    
    def _calculate_quality_metrics(self, evaluation_results: List[EvaluationResult]) -> Dict[str, float]:
        """Calculate quality metrics for evaluation"""
        if not evaluation_results:
            return {}
        
        avg_confidence = sum(r.confidence for r in evaluation_results) / len(evaluation_results)
        avg_score_ratio = sum(r.score / r.max_score for r in evaluation_results) / len(evaluation_results)
        
        return {
            'average_confidence': avg_confidence,
            'average_score_ratio': avg_score_ratio,
            'evaluation_consistency': self._calculate_evaluation_consistency(evaluation_results),
            'method_diversity': len(set(r.evaluation_method for r in evaluation_results)) / len(EvaluationMethod)
        }
    
    def _calculate_evaluation_consistency(self, evaluation_results: List[EvaluationResult]) -> float:
        """Calculate evaluation consistency"""
        if len(evaluation_results) < 2:
            return 1.0
        
        scores = [r.score / r.max_score for r in evaluation_results]
        mean_score = sum(scores) / len(scores)
        
        # Calculate variance
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        # Consistency is inverse of variance (normalized)
        consistency = 1.0 - min(variance, 1.0)
        return consistency
    
    def _generate_recommendations(self, evaluation_results: List[EvaluationResult]) -> List[str]:
        """Generate recommendations based on evaluation results"""
        recommendations = []
        
        if not evaluation_results:
            return recommendations
        
        # Analyze question types
        question_types = Counter(r.evaluator_notes.get('question_type', 'unknown') for r in evaluation_results)
        
        # Check for weak areas
        type_scores = defaultdict(list)
        for result in evaluation_results:
            q_type = result.evaluator_notes.get('question_type', 'unknown')
            score_ratio = result.score / result.max_score if result.max_score > 0 else 0
            type_scores[q_type].append(score_ratio)
        
        for q_type, scores in type_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 0.6:
                if q_type == 'essay':
                    recommendations.append("Focus on improving essay writing skills")
                elif q_type == 'short_answer':
                    recommendations.append("Practice writing more concise short answers")
                elif q_type == 'multiple_choice':
                    recommendations.append("Review multiple choice question strategies")
        
        # General recommendations
        avg_confidence = sum(r.confidence for r in evaluation_results) / len(evaluation_results)
        if avg_confidence < 0.7:
            recommendations.append("Some answers were difficult to evaluate automatically - consider writing more clearly")
        
        return recommendations
    
    def _calculate_grade_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate grade distribution"""
        distribution = {grade: 0 for grade in self.grade_boundaries.keys()}
        
        for score in scores:
            grade = self._calculate_grade(score)
            distribution[grade] += 1
        
        return distribution
    
    def _generate_exam_insights(self, evaluation_results: List[Dict], exam: Exam) -> Dict:
        """Generate insights for exam evaluation"""
        insights = {
            'question_difficulty': self._analyze_question_difficulty(evaluation_results),
            'student_performance': self._analyze_student_performance(evaluation_results),
            'exam_quality': self._analyze_exam_quality(evaluation_results),
            'time_analysis': self._analyze_completion_times(evaluation_results)
        }
        
        return insights
    
    def _analyze_question_difficulty(self, evaluation_results: List[Dict]) -> Dict:
        """Analyze question difficulty based on performance"""
        # This would analyze how students performed on each question
        return {'average_difficulty': 0.5, 'difficulty_distribution': {}}
    
    def _analyze_student_performance(self, evaluation_results: List[Dict]) -> Dict:
        """Analyze student performance patterns"""
        return {'performance_trends': {}, 'outlier_students': []}
    
    def _analyze_exam_quality(self, evaluation_results: List[Dict]) -> Dict:
        """Analyze exam quality metrics"""
        return {'quality_score': 0.8, 'improvement_suggestions': []}
    
    def _analyze_completion_times(self, evaluation_results: List[Dict]) -> Dict:
        """Analyze exam completion times"""
        return {'average_time': 45, 'time_distribution': {}}
    
    def _generate_exam_recommendations(self, insights: Dict) -> List[str]:
        """Generate recommendations for exam improvement"""
        recommendations = []
        
        # Based on insights
        if insights.get('question_difficulty', {}).get('average_difficulty', 0.5) > 0.8:
            recommendations.append("Consider making some questions easier")
        elif insights.get('question_difficulty', {}).get('average_difficulty', 0.5) < 0.3:
            recommendations.append("Consider adding more challenging questions")
        
        return recommendations

# Singleton instance
exam_evaluator = AdvancedExamEvaluator()
