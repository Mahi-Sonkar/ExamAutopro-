"""
Enhanced Evaluation Engine for ExamAutoPro
Advanced NLP-based evaluation with TF-IDF and Cosine Similarity
Main motive: Intelligent answer evaluation with multiple techniques
"""

import re
import math
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter, defaultdict

# Import advanced NLP evaluation
from .advanced_nlp_evaluation import AdvancedNLPEvaluation, AdvancedOCREvaluation

# Try to import sklearn, fallback to basic implementation if not available
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import normalize
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    np = None
    TfidfVectorizer = None
    cosine_similarity = None
    normalize = None

logger = logging.getLogger(__name__)

class EnhancedEvaluationEngine:
    """
    Advanced evaluation engine with NLP techniques
    Main motive: Comprehensive answer evaluation using advanced NLP
    """
    
    def __init__(self):
        # Initialize advanced NLP evaluators
        self.advanced_nlp = AdvancedNLPEvaluation()
        self.advanced_ocr = AdvancedOCREvaluation()
        
        # Fallback TF-IDF for backward compatibility
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3),
            lowercase=True,
            strip_accents='ascii'
        ) if SKLEARN_AVAILABLE else None
        
        self._initialize_evaluation_rules()
        
    def _initialize_evaluation_rules(self) -> None:
        """Initialize evaluation rules and thresholds"""
        
        # MCQ Evaluation Rules
        self.mcq_rules = {
            'exact_match_weight': 1.0,
            'partial_match_weight': 0.5,
            'case_insensitive': True,
            'whitespace_flexible': True,
            'min_similarity_threshold': 0.8
        }
        
        # Descriptive Answer Evaluation Rules
        self.descriptive_rules = {
            'tfidf_weight': 0.6,
            'semantic_weight': 0.3,
            'length_weight': 0.1,
            'keyword_weight': 0.4,
            'concept_weight': 0.3,
            'structure_weight': 0.3,
            'min_words_threshold': 10,
            'max_words_penalty': 0.1,
            'cosine_similarity_threshold': 0.3
        }
        
        # OCR Handwritten Answer Rules
        self.ocr_rules = {
            'confidence_threshold': 0.7,
            'text_extraction_weight': 0.8,
            'manual_review_weight': 0.2,
            'handwriting_penalty': 0.1,
            'image_quality_weight': 0.2
        }
        
        # Grace Marks Rules
        self.grace_marks_rules = {
            'borderline_threshold': 0.55,  # 55-60% range
            'max_grace_percentage': 0.1,  # Maximum 10% grace marks
            'difficulty_based_grace': True,
            'subject_based_grace': True,
            'attempt_based_grace': True
        }
    
    def evaluate_mcq_answer(self, student_answer: str, correct_answer: str, options: List[str] = None) -> Dict:
        """
        Evaluate MCQ answer using direct matching
        Main motive: Accurate MCQ evaluation with partial matching
        """
        try:
            if not student_answer or not correct_answer:
                return {'score': 0.0, 'confidence': 0.0, 'method': 'mcq_exact_match'}
            
            # Normalize answers
            student_normalized = self._normalize_text(student_answer)
            correct_normalized = self._normalize_text(correct_answer)
            
            # Exact match check
            if student_normalized == correct_normalized:
                return {
                    'score': 1.0,
                    'confidence': 1.0,
                    'method': 'mcq_exact_match',
                    'details': {'match_type': 'exact', 'student_answer': student_answer, 'correct_answer': correct_answer}
                }
            
            # Partial match check
            partial_score = self._calculate_partial_match(student_normalized, correct_normalized)
            
            if partial_score >= self.mcq_rules['min_similarity_threshold']:
                return {
                    'score': partial_score * self.mcq_rules['partial_match_weight'],
                    'confidence': partial_score,
                    'method': 'mcq_partial_match',
                    'details': {
                        'match_type': 'partial',
                        'similarity_score': partial_score,
                        'student_answer': student_answer,
                        'correct_answer': correct_answer
                    }
                }
            
            # Option matching (if options provided)
            if options:
                option_score = self._match_with_options(student_normalized, options, correct_normalized)
                if option_score > 0:
                    return {
                        'score': option_score,
                        'confidence': 0.7,
                        'method': 'mcq_option_match',
                        'details': {
                            'match_type': 'option',
                            'matched_option': option_score,
                            'student_answer': student_answer,
                            'correct_answer': correct_answer
                        }
                    }
            
            return {
                'score': 0.0,
                'confidence': 0.0,
                'method': 'mcq_no_match',
                'details': {'match_type': 'none', 'student_answer': student_answer, 'correct_answer': correct_answer}
            }
            
        except Exception as e:
            logger.error(f"MCQ evaluation failed: {str(e)}")
            return {'score': 0.0, 'confidence': 0.0, 'method': 'mcq_error', 'error': str(e)}
    
    def evaluate_descriptive_answer(self, student_answer: str, model_answer: str, keywords: List[str] = None) -> Dict:
        """
        Evaluate descriptive answer using advanced NLP techniques
        Main motive: Most accurate descriptive answer evaluation
        """
        try:
            if not student_answer or not model_answer:
                return {'score': 0.0, 'confidence': 0.0, 'method': 'descriptive_no_answer'}
            
            # Use advanced NLP evaluation for maximum accuracy
            try:
                advanced_result = self.advanced_nlp.evaluate_answer_comprehensive(
                    student_answer, model_answer, keywords, 'descriptive'
                )
                
                # Add method identifier
                advanced_result['method'] = 'descriptive_advanced_nlp'
                
                logger.info(f"Advanced NLP evaluation completed with score: {advanced_result['score']:.3f}")
                return advanced_result
                
            except Exception as e:
                logger.warning(f"Advanced NLP evaluation failed: {str(e)}, falling back to basic method")
                return self._fallback_descriptive_evaluation(student_answer, model_answer, keywords)
            
        except Exception as e:
            logger.error(f"Descriptive evaluation failed: {str(e)}")
            return {'score': 0.0, 'confidence': 0.0, 'method': 'descriptive_error', 'error': str(e)}
    
    def evaluate_handwritten_answer(self, image_path: str, model_answer: str, ocr_confidence: float = None) -> Dict:
        """
        Evaluate handwritten answer using advanced OCR + NLP
        Main motive: Most accurate handwritten answer evaluation
        """
        try:
            # Extract text from image using OCR
            extracted_text, extraction_confidence = self._extract_text_from_image(image_path)
            
            if not extracted_text:
                return {
                    'score': 0.0,
                    'confidence': 0.0,
                    'method': 'handwritten_no_text',
                    'details': {'error': 'No text extracted from image'}
                }
            
            # Use advanced OCR evaluation for maximum accuracy
            try:
                advanced_result = self.advanced_ocr.evaluate_handwritten_answer(
                    extracted_text, model_answer, ocr_confidence or extraction_confidence
                )
                
                # Add additional metadata
                advanced_result['method'] = 'handwritten_advanced_ocr'
                advanced_result['details']['image_path'] = image_path
                
                logger.info(f"Advanced OCR evaluation completed with score: {advanced_result['score']:.3f}")
                return advanced_result
                
            except Exception as e:
                logger.warning(f"Advanced OCR evaluation failed: {str(e)}, falling back to basic method")
                return self._fallback_handwritten_evaluation(extracted_text, model_answer, ocr_confidence or extraction_confidence)
            
        except Exception as e:
            logger.error(f"Handwritten evaluation failed: {str(e)}")
            return {'score': 0.0, 'confidence': 0.0, 'method': 'handwritten_error', 'error': str(e)}
    
    def calculate_grace_marks(self, original_score: float, max_marks: float, difficulty: str = 'medium', 
                           subject: str = 'general', attempt_count: int = 0) -> Dict:
        """
        Calculate grace marks based on predefined rules
        Main motive: Intelligent grace marks allocation
        """
        try:
            grace_marks = 0.0
            reasons = []
            
            # Check if student is in borderline range
            percentage_score = (original_score / max_marks) * 100
            
            if self.grace_marks_rules['borderline_threshold'] * 100 <= percentage_score < 60:
                # Student is in borderline range (55-60%)
                base_grace = max_marks * self.grace_marks_rules['max_grace_percentage']
                
                # Difficulty-based grace
                if self.grace_marks_rules['difficulty_based_grace']:
                    difficulty_multiplier = self._get_difficulty_multiplier(difficulty)
                    base_grace *= difficulty_multiplier
                    reasons.append(f"Difficulty-based grace (x{difficulty_multiplier})")
                
                # Subject-based grace
                if self.grace_marks_rules['subject_based_grace']:
                    subject_multiplier = self._get_subject_multiplier(subject)
                    base_grace *= subject_multiplier
                    reasons.append(f"Subject-based grace (x{subject_multiplier})")
                
                # Attempt-based grace
                if self.grace_marks_rules['attempt_based_grace'] and attempt_count > 0:
                    attempt_bonus = min(base_grace * 0.2, max_marks * 0.02)  # Max 2% extra
                    base_grace += attempt_bonus
                    reasons.append(f"Attempt bonus (+{attempt_bonus:.2f})")
                
                grace_marks = min(base_grace, max_marks * self.grace_marks_rules['max_grace_percentage'])
            
            final_score = min(original_score + grace_marks, max_marks)
            
            return {
                'original_score': original_score,
                'grace_marks': grace_marks,
                'final_score': final_score,
                'percentage_before_grace': percentage_score,
                'percentage_after_grace': (final_score / max_marks) * 100,
                'reasons': reasons,
                'method': 'grace_marks_calculation'
            }
            
        except Exception as e:
            logger.error(f"Grace marks calculation failed: {str(e)}")
            return {
                'original_score': original_score,
                'grace_marks': 0.0,
                'final_score': original_score,
                'error': str(e)
            }
    
    def generate_comprehensive_result(self, evaluations: List[Dict], max_marks: float) -> Dict:
        """
        Generate comprehensive evaluation result
        Main motive: Complete result generation with all components
        """
        try:
            total_score = sum(eval_result['score'] for eval_result in evaluations)
            total_confidence = sum(eval_result['confidence'] for eval_result in evaluations) / len(evaluations) if evaluations else 0
            
            # Calculate grace marks
            grace_result = self.calculate_grace_marks(total_score, max_marks)
            
            # Generate grade
            grade = self._calculate_grade(grace_result['final_score'], max_marks)
            
            # Analyze performance
            performance_analysis = self._analyze_performance(evaluations)
            
            return {
                'total_score': grace_result['final_score'],
                'original_score': grace_result['original_score'],
                'grace_marks': grace_result['grace_marks'],
                'max_marks': max_marks,
                'percentage': grace_result['percentage_after_grace'],
                'grade': grade,
                'confidence': total_confidence,
                'evaluations': evaluations,
                'performance_analysis': performance_analysis,
                'grace_details': grace_result,
                'recommendations': self._generate_recommendations(evaluations, grace_result['final_score'], max_marks)
            }
            
        except Exception as e:
            logger.error(f"Result generation failed: {str(e)}")
            return {'error': str(e)}
    
    def _fallback_descriptive_evaluation(self, student_answer: str, model_answer: str, keywords: List[str] = None) -> Dict:
        """
        Fallback descriptive evaluation using basic techniques
        Main motive: Robust evaluation when advanced NLP fails
        """
        try:
            # Basic preprocessing
            student_clean = self._preprocess_text(student_answer)
            model_clean = self._preprocess_text(model_answer)
            
            # Basic word overlap similarity
            student_words = set(student_clean.split())
            model_words = set(model_clean.split())
            
            if not model_words:
                return {'score': 0.0, 'confidence': 0.0, 'method': 'descriptive_fallback_no_words'}
            
            # Calculate basic similarity
            common_words = student_words.intersection(model_words)
            similarity = len(common_words) / len(model_words)
            
            # Basic keyword matching
            keyword_score = 0.0
            if keywords:
                matched_keywords = 0
                for keyword in keywords:
                    keyword_clean = self._preprocess_text(keyword)
                    if keyword_clean in student_clean:
                        matched_keywords += 1
                keyword_score = matched_keywords / len(keywords)
            
            # Combine scores
            final_score = similarity * 0.7 + keyword_score * 0.3
            
            return {
                'score': min(1.0, max(0.0, final_score)),
                'confidence': 0.6,  # Lower confidence for fallback
                'method': 'descriptive_fallback',
                'details': {
                    'similarity': similarity,
                    'keyword_score': keyword_score,
                    'final_score': final_score
                }
            }
            
        except Exception as e:
            logger.error(f"Fallback descriptive evaluation failed: {str(e)}")
            return {'score': 0.0, 'confidence': 0.0, 'method': 'descriptive_fallback_error', 'error': str(e)}
    
    def _fallback_handwritten_evaluation(self, extracted_text: str, model_answer: str, ocr_confidence: float) -> Dict:
        """
        Fallback handwritten evaluation using basic techniques
        Main motive: Robust OCR evaluation when advanced methods fail
        """
        try:
            # Use fallback descriptive evaluation
            descriptive_result = self._fallback_descriptive_evaluation(extracted_text, model_answer)
            
            # Apply OCR confidence adjustment
            if ocr_confidence:
                adjusted_score = descriptive_result['score'] * ocr_confidence
                adjusted_confidence = (descriptive_result['confidence'] + ocr_confidence) / 2
            else:
                adjusted_score = descriptive_result['score'] * 0.7  # Default penalty
                adjusted_confidence = descriptive_result['confidence'] * 0.7
            
            return {
                'score': adjusted_score,
                'confidence': adjusted_confidence,
                'method': 'handwritten_fallback',
                'details': {
                    'extracted_text': extracted_text,
                    'ocr_confidence': ocr_confidence,
                    'base_score': descriptive_result['score'],
                    'adjusted_score': adjusted_score,
                    'requires_manual_review': ocr_confidence and ocr_confidence < 0.7
                }
            }
            
        except Exception as e:
            logger.error(f"Fallback handwritten evaluation failed: {str(e)}")
            return {'score': 0.0, 'confidence': 0.0, 'method': 'handwritten_fallback_error', 'error': str(e)}
    
    # Helper methods
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        normalized = text.strip()
        
        if self.mcq_rules['case_insensitive']:
            normalized = normalized.lower()
        
        if self.mcq_rules['whitespace_flexible']:
            normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _calculate_partial_match(self, student: str, correct: str) -> float:
        """Calculate partial match score"""
        if not student or not correct:
            return 0.0
        
        # Simple character-based similarity
        student_chars = set(student.lower())
        correct_chars = set(correct.lower())
        
        intersection = student_chars & correct_chars
        union = student_chars | correct_chars
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _match_with_options(self, student: str, options: List[str], correct: str) -> float:
        """Match student answer with options"""
        if not options:
            return 0.0
        
        # Find correct option
        correct_option = None
        for i, option in enumerate(options):
            if self._normalize_text(option) == correct:
                correct_option = i
                break
        
        if correct_option is None:
            return 0.0
        
        # Check if student answer matches correct option
        student_normalized = self._normalize_text(student)
        
        # Direct match
        if student_normalized == str(correct_option) or student_normalized == str(correct_option + 1):
            return 1.0
        
        # Option text match
        if correct_option < len(options):
            option_text = self._normalize_text(options[correct_option])
            if student_normalized == option_text:
                return 1.0
        
        return 0.0
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for NLP analysis"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _fallback_similarity(self, text1: str, text2: str) -> float:
        """Fallback similarity calculation when TF-IDF fails"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _calculate_keyword_score(self, student_text: str, keywords: List[str]) -> float:
        """Calculate keyword matching score"""
        if not keywords:
            return 0.0
        
        student_words = set(student_text.lower().split())
        keyword_words = set(kw.lower() for kw in keywords)
        
        matched_keywords = student_words & keyword_words
        
        return len(matched_keywords) / len(keywords)
    
    def _get_matched_keywords(self, student_text: str, keywords: List[str]) -> List[str]:
        """Get list of matched keywords"""
        if not keywords:
            return []
        
        student_words = set(student_text.lower().split())
        matched = [kw for kw in keywords if kw.lower() in student_words]
        
        return matched
    
    def _calculate_concept_score(self, student_text: str, model_text: str) -> float:
        """Calculate concept matching score"""
        # Extract key concepts (simplified)
        student_concepts = self._extract_concepts(student_text)
        model_concepts = self._extract_concepts(model_text)
        
        if not model_concepts:
            return 0.0
        
        matched_concepts = student_concepts & model_concepts
        
        return len(matched_concepts) / len(model_concepts)
    
    def _extract_concepts(self, text: str) -> set:
        """Extract key concepts from text"""
        # Simple concept extraction (can be enhanced with NLP libraries)
        words = text.split()
        
        # Filter out common words and keep meaningful words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        concepts = set(word for word in words if len(word) > 3 and word not in stop_words)
        
        return concepts
    
    def _calculate_structure_score(self, text: str) -> float:
        """Calculate text structure score"""
        if not text:
            return 0.0
        
        sentences = text.split('.')
        words = text.split()
        
        # Basic structure indicators
        has_multiple_sentences = len(sentences) > 1
        has_reasonable_length = len(words) >= self.descriptive_rules['min_words_threshold']
        
        score = 0.0
        if has_multiple_sentences:
            score += 0.5
        if has_reasonable_length:
            score += 0.5
        
        return score
    
    def _calculate_length_score(self, student_text: str, model_text: str) -> float:
        """Calculate length-based score"""
        student_words = len(student_text.split())
        model_words = len(model_text.split())
        
        if model_words == 0:
            return 0.0
        
        # Calculate length ratio
        length_ratio = student_words / model_words
        
        # Ideal ratio is around 0.8-1.2
        if 0.8 <= length_ratio <= 1.2:
            return 1.0
        elif length_ratio < 0.8:
            return length_ratio  # Too short
        else:
            # Too long - apply penalty
            penalty = self.descriptive_rules['max_words_penalty']
            return max(0.0, 1.0 - (length_ratio - 1.2) * penalty)
    
    def _calculate_evaluation_confidence(self, cosine_score: float, keyword_score: float, 
                                   concept_score: float, structure_score: float) -> float:
        """Calculate overall evaluation confidence"""
        # Weighted confidence based on component scores
        confidence_weights = {
            'cosine': 0.4,
            'keyword': 0.3,
            'concept': 0.2,
            'structure': 0.1
        }
        
        confidence = (
            cosine_score * confidence_weights['cosine'] +
            keyword_score * confidence_weights['keyword'] +
            concept_score * confidence_weights['concept'] +
            structure_score * confidence_weights['structure']
        )
        
        return min(confidence, 1.0)
    
    def _extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """Extract text from image using OCR"""
        # This would integrate with actual OCR service
        # For now, return mock data
        try:
            # Mock OCR extraction
            mock_text = "This is a sample extracted text from handwritten answer."
            mock_confidence = 0.85
            
            return mock_text, mock_confidence
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return "", 0.0
    
    def _get_difficulty_multiplier(self, difficulty: str) -> float:
        """Get difficulty-based grace multiplier"""
        multipliers = {
            'easy': 0.5,
            'medium': 1.0,
            'hard': 1.5,
            'very_hard': 2.0
        }
        return multipliers.get(difficulty, 1.0)
    
    def _get_subject_multiplier(self, subject: str) -> float:
        """Get subject-based grace multiplier"""
        multipliers = {
            'mathematics': 1.2,
            'science': 1.1,
            'history': 0.8,
            'literature': 0.7,
            'general': 1.0
        }
        return multipliers.get(subject, 1.0)
    
    def _calculate_grade(self, score: float, max_marks: float) -> str:
        """Calculate grade from score"""
        percentage = (score / max_marks) * 100
        
        if percentage >= 90:
            return 'A+'
        elif percentage >= 85:
            return 'A'
        elif percentage >= 80:
            return 'B+'
        elif percentage >= 75:
            return 'B'
        elif percentage >= 70:
            return 'C+'
        elif percentage >= 65:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'
    
    def _analyze_performance(self, evaluations: List[Dict]) -> Dict:
        """Analyze performance across all evaluations"""
        if not evaluations:
            return {}
        
        methods = [eval_result['method'] for eval_result in evaluations]
        scores = [eval_result['score'] for eval_result in evaluations]
        confidences = [eval_result['confidence'] for eval_result in evaluations]
        
        return {
            'evaluation_methods_used': list(set(methods)),
            'average_score': sum(scores) / len(scores),
            'average_confidence': sum(confidences) / len(confidences),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'score_distribution': self._calculate_score_distribution(scores),
            'method_distribution': Counter(methods)
        }
    
    def _calculate_score_distribution(self, scores: List[float]) -> Dict:
        """Calculate score distribution"""
        if not scores:
            return {}
        
        distribution = {
            'excellent': sum(1 for score in scores if score >= 0.8),
            'good': sum(1 for score in scores if 0.6 <= score < 0.8),
            'average': sum(1 for score in scores if 0.4 <= score < 0.6),
            'poor': sum(1 for score in scores if score < 0.4)
        }
        
        return distribution
    
    def _generate_recommendations(self, evaluations: List[Dict], final_score: float, max_marks: float) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        percentage = (final_score / max_marks) * 100
        
        if percentage < 40:
            recommendations.append("Significant improvement needed in all areas")
        elif percentage < 60:
            recommendations.append("Focus on understanding key concepts and improving answer structure")
        elif percentage < 75:
            recommendations.append("Good effort, but work on providing more detailed answers")
        
        # Method-specific recommendations
        methods = [eval_result['method'] for eval_result in evaluations]
        if 'mcq_no_match' in methods:
            recommendations.append("Review MCQ answering strategies and read questions carefully")
        
        if 'descriptive_tfidf_cosine' in methods:
            descriptive_scores = [eval_result['score'] for eval_result in evaluations if eval_result['method'] == 'descriptive_tfidf_cosine']
            if descriptive_scores and sum(descriptive_scores) / len(descriptive_scores) < 0.6:
                recommendations.append("Improve descriptive answers by including more keywords and concepts")
        
        return recommendations

# Singleton instance
enhanced_evaluation_engine = EnhancedEvaluationEngine()
