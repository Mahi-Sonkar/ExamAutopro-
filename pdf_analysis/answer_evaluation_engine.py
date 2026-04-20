"""
Answer Evaluation Engine
Comprehensive OCR and NLP evaluation system for answer sheets
"""

import os
import time
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from django.conf import settings
from django.core.exceptions import ValidationError

# Setup logging
logger = logging.getLogger(__name__)

class AnswerEvaluationEngine:
    """
    Advanced OCR and NLP engine for evaluating answer sheets
    """
    
    def __init__(self, custom_scoring_rules=None):
        """
        Initialize evaluation engine with custom scoring rules
        """
        self.custom_scoring_rules = custom_scoring_rules or {}
        self.ocr_engine = None
        self.nlp_engine = None
        
        # Initialize OCR and NLP engines
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize OCR and NLP engines"""
        try:
            # Import enhanced OCR engine
            from .enhanced_ocr_engine import enhanced_ocr
            self.ocr_engine = enhanced_ocr
            logger.info("Enhanced OCR engine initialized")
        except ImportError as e:
            logger.warning(f"Enhanced OCR engine not available: {e}")
            # Fallback to basic OCR
            try:
                from examapp.ocr_engine import extract_text_from_pdf
                self.ocr_engine = extract_text_from_pdf
                logger.info("Basic OCR engine initialized as fallback")
            except ImportError:
                logger.error("No OCR engine available")
        
        try:
            # Import enhanced NLP engine
            from .enhanced_nlp_engine import EnhancedNLPEngine
            self.nlp_engine = EnhancedNLPEngine(custom_rules=self.custom_scoring_rules)
            logger.info("Enhanced NLP engine initialized")
        except ImportError as e:
            logger.warning(f"Enhanced NLP engine not available: {e}")
            # Fallback to basic NLP
            try:
                from examapp.nlp_engine import extract_questions, analyze_text
                self.nlp_engine = {
                    'extract_questions': extract_questions,
                    'analyze_text': analyze_text
                }
                logger.info("Basic NLP engine initialized as fallback")
            except ImportError:
                logger.error("No NLP engine available")
    
    def extract_text_from_answer_sheet(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from answer sheet using optimized OCR
        """
        try:
            logger.info(f"Extracting text from answer sheet: {file_path}")
            start_time = time.time()
            
            # Use enhanced OCR if available
            if hasattr(self.ocr_engine, 'extract_text_from_pdf'):
                result = self.ocr_engine.extract_text_from_pdf(file_path)
            else:
                # Fallback to basic OCR
                result = self.ocr_engine(file_path)
            
            processing_time = time.time() - start_time
            
            # Validate extraction result
            if not result.get('text') or len(result.get('text', '').strip()) < 10:
                raise Exception("Failed to extract meaningful text from answer sheet")
            
            logger.info(f"Text extraction successful: {len(result['text'])} characters in {processing_time:.2f}s")
            
            return {
                'text': result['text'],
                'confidence': result.get('confidence', 0.0),
                'method_used': result.get('method', 'Unknown'),
                'processing_time': processing_time,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'method_used': 'Failed',
                'processing_time': 0.0,
                'success': False,
                'error': str(e)
            }
    
    def detect_questions_from_paper(self, file_path: str) -> Dict[str, Any]:
        """
        Detect questions from question paper image/PDF
        """
        try:
            logger.info(f"Detecting questions from paper: {file_path}")
            start_time = time.time()
            
            # Extract text from question paper
            if hasattr(self.ocr_engine, 'extract_text_from_pdf'):
                result = self.ocr_engine.extract_text_from_pdf(file_path)
            else:
                result = self.ocr_engine(file_path)
            
            if not result.get('text') or len(result.get('text', '').strip()) < 10:
                raise Exception("Failed to extract meaningful text from question paper")
            
            # Use NLP to detect questions
            if hasattr(self.nlp_engine, 'analyze_text_comprehensive'):
                nlp_result = self.nlp_engine.analyze_text_comprehensive(result['text'])
                questions = nlp_result.get('question_analysis', [])
            elif isinstance(self.nlp_engine, dict) and 'extract_questions' in self.nlp_engine:
                questions = self.nlp_engine['extract_questions'](result['text'])
            else:
                # Basic question detection
                questions = self._basic_question_detection(result['text'])
            
            processing_time = time.time() - start_time
            
            logger.info(f"Question detection successful: {len(questions)} questions in {processing_time:.2f}s")
            
            return {
                'questions': questions,
                'raw_text': result['text'],
                'confidence': result.get('confidence', 0.0),
                'method_used': result.get('method', 'Unknown'),
                'processing_time': processing_time,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Question detection failed: {e}")
            return {
                'questions': [],
                'raw_text': '',
                'confidence': 0.0,
                'method_used': 'Failed',
                'processing_time': 0.0,
                'success': False,
                'error': str(e)
            }
    
    def _basic_question_detection(self, text: str) -> List[Dict[str, Any]]:
        """
        Basic question detection using regex patterns
        """
        import re
        
        questions = []
        
        # Common question patterns
        patterns = [
            r'(\d+)\.\s*(.+?)(?=\n\d+\.|\n\n|$)',  # Numbered questions
            r'([a-zA-Z])\)\s*(.+?)(?=\n[a-zA-Z]\)|\n\n|$)',  # Lettered questions
            r'Question\s*(\d+):\s*(.+?)(?=Question|\n\n|$)',  # "Question X:" format
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    question_text = match[-1].strip()
                    question_num = match[0] if match[0].isdigit() else len(questions) + 1
                else:
                    question_text = match.strip()
                    question_num = len(questions) + 1
                
                if len(question_text) > 10:  # Filter out very short matches
                    questions.append({
                        'question': question_text,
                        'question_number': int(question_num) if isinstance(question_num, str) and question_num.isdigit() else question_num,
                        'type': self._classify_question_type(question_text),
                        'weight': 1.0,
                        'score': 0.0
                    })
        
        return questions
    
    def _classify_question_type(self, question_text: str) -> str:
        """
        Classify question type based on text patterns
        """
        question_lower = question_text.lower()
        
        if any(word in question_lower for word in ['true', 'false', 'yes', 'no']):
            return 'true_false'
        elif any(word in question_lower for word in ['choose', 'select', 'option', 'a)', 'b)', 'c)', 'd)']):
            return 'multiple_choice'
        elif any(word in question_lower for word in ['explain', 'describe', 'discuss', 'elaborate']):
            return 'essay'
        else:
            return 'short_answer'
    
    def evaluate_answers_against_questions(self, 
                                    answer_text: str, 
                                    questions: List[Dict[str, Any]], 
                                    scoring_rules: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate answers against detected questions using scoring rules
        """
        try:
            logger.info(f"Evaluating {len(questions)} answers")
            start_time = time.time()
            
            scoring_rules = scoring_rules or self.custom_scoring_rules
            evaluation_results = []
            total_score = 0.0
            max_score = 0.0
            
            for i, question in enumerate(questions):
                # Extract relevant answer portion
                answer_portion = self._extract_answer_for_question(answer_text, i, question)
                
                # Evaluate using NLP engine
                if hasattr(self.nlp_engine, 'analyze_text_comprehensive'):
                    # Enhanced evaluation with custom rules
                    nlp_result = self.nlp_engine.analyze_text_comprehensive(answer_portion)
                    
                    # Calculate similarity with question
                    similarity_score = self._calculate_similarity(
                        question.get('question', ''), 
                        answer_portion
                    )
                    
                    # Apply scoring rules
                    marks = self._apply_scoring_rules(
                        similarity_score, 
                        scoring_rules,
                        question.get('weight', 1.0)
                    )
                    
                    evaluation_results.append({
                        'question_number': question.get('question_number', i + 1),
                        'question_text': question.get('question', ''),
                        'answer_text': answer_portion,
                        'similarity_score': similarity_score,
                        'raw_score': similarity_score * 100,
                        'marks_awarded': marks,
                        'max_marks': question.get('weight', 1.0) * 10,  # Assuming 10 marks per weight unit
                        'question_type': question.get('type', 'short_answer'),
                        'confidence': min(similarity_score, 1.0),
                        'feedback': self._generate_feedback(similarity_score, marks)
                    })
                    
                else:
                    # Basic evaluation
                    similarity_score = self._basic_similarity_check(
                        question.get('question', ''), 
                        answer_portion
                    )
                    
                    marks = self._apply_scoring_rules(
                        similarity_score, 
                        scoring_rules,
                        question.get('weight', 1.0)
                    )
                    
                    evaluation_results.append({
                        'question_number': question.get('question_number', i + 1),
                        'question_text': question.get('question', ''),
                        'answer_text': answer_portion,
                        'similarity_score': similarity_score,
                        'raw_score': similarity_score * 100,
                        'marks_awarded': marks,
                        'max_marks': question.get('weight', 1.0) * 10,
                        'question_type': question.get('type', 'short_answer'),
                        'confidence': min(similarity_score, 1.0),
                        'feedback': self._generate_feedback(similarity_score, marks)
                    })
                
                total_score += marks
                max_score += question.get('weight', 1.0) * 10
            
            processing_time = time.time() - start_time
            percentage = (total_score / max_score * 100) if max_score > 0 else 0.0
            
            logger.info(f"Evaluation completed: {total_score}/{max_score} ({percentage:.1f}%) in {processing_time:.2f}s")
            
            return {
                'evaluation_results': evaluation_results,
                'total_marks_obtained': total_score,
                'total_marks_possible': max_score,
                'percentage': percentage,
                'processing_time': processing_time,
                'scoring_rules_applied': scoring_rules,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Answer evaluation failed: {e}")
            return {
                'evaluation_results': [],
                'total_marks_obtained': 0.0,
                'total_marks_possible': 0.0,
                'percentage': 0.0,
                'processing_time': 0.0,
                'scoring_rules_applied': scoring_rules,
                'success': False,
                'error': str(e)
            }
    
    def _extract_answer_for_question(self, answer_text: str, question_index: int, question: Dict[str, Any]) -> str:
        """
        Extract the relevant answer portion for a specific question
        """
        # Simple approach: split by question numbers and get the relevant portion
        import re
        
        # Look for patterns like "1.", "2.", etc.
        answer_parts = re.split(r'\n\s*\d+\.\s*', answer_text)
        
        if question_index < len(answer_parts):
            return answer_parts[question_index].strip()
        else:
            # Fallback: return the whole text for the last question
            return answer_text.strip()
    
    def _calculate_similarity(self, question: str, answer: str) -> float:
        """
        Calculate similarity between question and answer using multiple methods
        """
        try:
            # Try to use enhanced NLP engine for similarity
            if hasattr(self.nlp_engine, 'analyze_text_comprehensive'):
                # Use semantic similarity from enhanced engine
                combined_text = f"{question} {answer}"
                result = self.nlp_engine.analyze_text_comprehensive(combined_text)
                
                # Extract similarity score from result (this would depend on the actual implementation)
                return result.get('overall_score', 0.0) / 100.0
            
            # Fallback to basic similarity
            return self._basic_similarity_check(question, answer)
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return self._basic_similarity_check(question, answer)
    
    def _basic_similarity_check(self, question: str, answer: str) -> float:
        """
        Basic similarity check using keyword matching
        """
        if not question or not answer:
            return 0.0
        
        # Extract keywords from question
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        
        # Calculate Jaccard similarity
        intersection = question_words.intersection(answer_words)
        union = question_words.union(answer_words)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _apply_scoring_rules(self, similarity_score: float, scoring_rules: Dict[str, Any], weight: float = 1.0) -> float:
        """
        Apply scoring rules based on similarity score
        """
        if not scoring_rules:
            # Default scoring: linear scaling
            return similarity_score * weight * 10  # Assuming 10 marks per weight unit
        
        # Find applicable scoring rule
        similarity_percentage = similarity_score * 100
        
        for rule_name, rule_config in scoring_rules.items():
            min_range, max_range = rule_config.get('range', (0, 100))
            marks_percentage = rule_config.get('marks_percentage', 100)
            
            if min_range <= similarity_percentage <= max_range:
                # Apply this rule
                return (similarity_percentage / 100.0) * weight * 10 * (marks_percentage / 100.0)
        
        # Default rule if no specific rule matches
        return similarity_score * weight * 10
    
    def _generate_feedback(self, similarity_score: float, marks: float) -> str:
        """
        Generate feedback based on similarity and marks
        """
        similarity_percentage = similarity_score * 100
        
        if similarity_percentage >= 80:
            return "Excellent answer! High similarity with expected content."
        elif similarity_percentage >= 60:
            return "Good answer with reasonable similarity."
        elif similarity_percentage >= 40:
            return "Acceptable answer but could be improved."
        elif similarity_percentage >= 20:
            return "Weak answer with low similarity."
        else:
            return "Poor answer with very low similarity."
    
    def evaluate_complete_paper(self, 
                           answer_sheet_path: str, 
                           question_paper_path: str = None,
                           scoring_rules: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Complete evaluation pipeline: extract answers, detect questions, evaluate
        """
        try:
            logger.info("Starting complete paper evaluation")
            start_time = time.time()
            
            # Step 1: Extract text from answer sheet
            answer_extraction = self.extract_text_from_answer_sheet(answer_sheet_path)
            if not answer_extraction['success']:
                raise Exception(f"Answer sheet extraction failed: {answer_extraction.get('error')}")
            
            # Step 2: Detect questions (if question paper provided)
            questions = []
            if question_paper_path and os.path.exists(question_paper_path):
                question_detection = self.detect_questions_from_paper(question_paper_path)
                if question_detection['success']:
                    questions = question_detection['questions']
                else:
                    logger.warning(f"Question detection failed: {question_detection.get('error')}")
            
            # If no questions detected, try to extract from answer text
            if not questions:
                questions = self._basic_question_detection(answer_extraction['text'])
            
            # Step 3: Evaluate answers against questions
            evaluation = self.evaluate_answers_against_questions(
                answer_extraction['text'],
                questions,
                scoring_rules
            )
            
            # Step 4: Compile final results
            total_processing_time = time.time() - start_time
            
            final_result = {
                'answer_extraction': answer_extraction,
                'question_detection': {
                    'questions': questions,
                    'success': True,
                    'method': 'auto_detection' if question_paper_path else 'from_answer_text'
                },
                'evaluation': evaluation,
                'final_results': {
                    'total_marks_obtained': evaluation['total_marks_obtained'],
                    'total_marks_possible': evaluation['total_marks_possible'],
                    'percentage': evaluation['percentage'],
                    'grade': self._calculate_grade(evaluation['percentage']),
                    'questions_evaluated': len(evaluation['evaluation_results']),
                    'processing_time': total_processing_time
                },
                'success': True
            }
            
            logger.info(f"Complete evaluation finished: {evaluation['percentage']:.1f}% in {total_processing_time:.2f}s")
            return final_result
            
        except Exception as e:
            logger.error(f"Complete paper evaluation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time if 'start_time' in locals() else 0.0
            }
    
    def _calculate_grade(self, percentage: float) -> str:
        """
        Calculate grade based on percentage
        """
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C+'
        elif percentage >= 40:
            return 'C'
        elif percentage >= 33:
            return 'D'
        else:
            return 'F'


# Singleton instance for easy import
answer_evaluation_engine = AnswerEvaluationEngine()
