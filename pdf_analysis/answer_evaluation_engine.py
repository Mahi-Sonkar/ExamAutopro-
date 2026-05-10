"""
Answer Evaluation Engine
Comprehensive OCR and NLP evaluation system for answer sheets
"""

import os
import time
import json
import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from django.conf import settings
from django.core.exceptions import ValidationError

# Setup logging
logger = logging.getLogger(__name__)

DEFAULT_SCORING_RULES = {
    'excellent': {
        'range': (90, 100),
        'marks_percentage': 100,
        'criteria': ['90-100% similarity: full marks'],
    },
    'good': {
        'range': (70, 89.99),
        'marks_percentage': 80,
        'criteria': ['70-89% similarity: 80% marks'],
    },
    'partial': {
        'range': (50, 69.99),
        'marks_percentage': 50,
        'criteria': ['50-69% similarity: 50% marks'],
    },
    'low': {
        'range': (0, 49.99),
        'marks_percentage': 0,
        'criteria': ['Below 50% similarity: zero marks by default'],
    },
}

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
        self.ai_evaluator = None

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

        try:
            from evaluation.ai_clients import FreeAIEvaluator
            self.ai_evaluator = FreeAIEvaluator()
            if self.ai_evaluator.available:
                logger.info("External AI evaluator initialized")
        except Exception as e:
            logger.warning(f"External AI evaluator not available: {e}")

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
                'method_used': result.get('method_used') or result.get('method', 'Unknown'),
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
            questions = self._basic_question_detection(result['text'])
            if not questions:
                if hasattr(self.nlp_engine, 'analyze_text_comprehensive'):
                    nlp_result = self.nlp_engine.analyze_text_comprehensive(result['text'])
                    questions = nlp_result.get('question_analysis', [])
                elif isinstance(self.nlp_engine, dict) and 'extract_questions' in self.nlp_engine:
                    questions = self.nlp_engine['extract_questions'](result['text'])

            processing_time = time.time() - start_time

            logger.info(f"Question detection successful: {len(questions)} questions in {processing_time:.2f}s")

            return {
                'questions': questions,
                'raw_text': result['text'],
                'confidence': result.get('confidence', 0.0),
                'method_used': result.get('method_used') or result.get('method', 'Unknown'),
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
        questions = []

        # Handles: Q1. ..., Question 2: ..., 3) ..., 4 - ...
        pattern = re.compile(
            r'(?is)(?:^|\n)\s*(?:q(?:uestion)?\s*)?(\d{1,3})\s*[\.\):\-]\s*'
            r'(.+?)(?=\n\s*(?:q(?:uestion)?\s*)?\d{1,3}\s*[\.\):\-]|\Z)'
        )
        matches = pattern.findall(text or "")

        if not matches:
            # Last resort: use question-like lines, preserving order.
            for index, line in enumerate((text or "").splitlines(), start=1):
                line = line.strip()
                if len(line) > 10 and (
                    line.endswith("?")
                    or re.match(r'(?i)^(explain|define|describe|discuss|state|write|list|compare|calculate)\b', line)
                ):
                    matches.append((str(index), line))

        seen = set()
        for question_num, question_text in matches:
            question_text = re.sub(r'\s+', ' ', question_text).strip()
            key = question_text.lower()
            if len(question_text) <= 6 or key in seen:
                continue
            seen.add(key)

            marks = self._extract_marks(question_text)
            questions.append({
                'question': question_text,
                'question_number': int(question_num),
                'type': self._classify_question_type(question_text),
                'weight': max(marks / 10.0, 0.1),
                'marks': marks,
                'score': 0.0
            })

        return questions

    def _parse_marking_scheme(self, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Parse teacher-provided marks/model answers from plain text.

        Supported examples:
        Q1 [5 marks]: model answer...
        2. (10) expected answer...
        Question 3 - 4 marks: keywords: foo, bar
        """
        if not text or not text.strip():
            return {}

        scheme = {}
        pattern = re.compile(
            r'(?is)(?:^|\n)\s*(?:q(?:uestion)?\s*)?(\d+)\s*'
            r'(?:[\[\(]\s*(\d+(?:\.\d+)?)\s*(?:marks?|m)?\s*[\]\)])?\s*'
            r'[\.\):\-]?\s*(.*?)(?=\n\s*(?:q(?:uestion)?\s*)?\d+\s*'
            r'(?:[\[\(]\s*\d+(?:\.\d+)?\s*(?:marks?|m)?\s*[\]\)])?\s*[\.\):\-]?|\Z)'
        )
        matches = pattern.findall(text)
        if not matches:
            matches = [(str(index + 1), '', part.strip()) for index, part in enumerate(re.split(r'\n\s*\n+', text)) if part.strip()]

        for number, inline_marks, body in matches:
            body = body.strip()
            marks = float(inline_marks) if inline_marks else self._extract_marks(body)
            cleaned = re.sub(r'(?i)\b(?:marks?|m)\s*[:=]?\s*\d+(?:\.\d+)?', '', body)
            cleaned = re.sub(r'[\[\(]\s*\d+(?:\.\d+)?\s*(?:marks?|m)?\s*[\]\)]', '', cleaned).strip()
            keywords_match = re.search(r'(?is)\bkeywords?\s*[:\-]\s*(.+)$', body)
            scheme[str(number)] = {
                'question_number': int(number),
                'marks': marks,
                'model_answer': cleaned,
                'keywords': keywords_match.group(1).strip() if keywords_match else '',
            }
        return scheme

    def _merge_question_specs(
        self,
        questions: List[Dict[str, Any]],
        marking_scheme_text: str = "",
        total_marks: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Combine question-paper questions with teacher marks/model-answer input."""
        marking_scheme = self._parse_marking_scheme(marking_scheme_text)
        merged = []

        source_questions = questions or list(marking_scheme.values())
        for index, question in enumerate(source_questions):
            q_number = str(question.get('question_number') or index + 1)
            scheme_item = marking_scheme.get(q_number, {})
            max_marks = (
                scheme_item.get('marks')
                or question.get('marks')
                or (question.get('weight', 1.0) * 10)
                or 10.0
            )
            merged.append({
                **question,
                'question_number': int(q_number) if str(q_number).isdigit() else index + 1,
                'question': question.get('question') or scheme_item.get('question', '') or f'Question {index + 1}',
                'type': question.get('type') or self._classify_question_type(question.get('question', '')),
                'marks': float(max_marks),
                'weight': float(max_marks) / 10.0,
                'model_answer': scheme_item.get('model_answer') or question.get('model_answer', ''),
                'keywords': scheme_item.get('keywords') or question.get('keywords', ''),
            })

        if total_marks and merged:
            current_total = sum(float(item.get('marks') or 0) for item in merged)
            if current_total > 0 and abs(current_total - float(total_marks)) > 0.01:
                scale = float(total_marks) / current_total
                for item in merged:
                    item['marks'] = round(float(item.get('marks') or 0) * scale, 2)
                    item['weight'] = item['marks'] / 10.0

        return merged

    def _extract_marks(self, text: str) -> float:
        """Extract marks from common question paper formats like [5 marks] or (10)."""
        import re
        patterns = [
            r'\[\s*(\d+(?:\.\d+)?)\s*(?:marks?|m)?\s*\]',
            r'\(\s*(\d+(?:\.\d+)?)\s*(?:marks?|m)\s*\)',
            r'(\d+(?:\.\d+)?)\s*(?:marks?|m)\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 10.0

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

            scoring_rules = scoring_rules or self.custom_scoring_rules or DEFAULT_SCORING_RULES
            evaluation_results = []
            total_score = 0.0
            max_score = 0.0

            for i, question in enumerate(questions):
                # Extract relevant answer portion
                answer_portion = self._extract_answer_for_question(answer_text, i, question, len(questions))
                reference_text = (
                    question.get('model_answer')
                    or question.get('correct_answer')
                    or question.get('expected_answer')
                    or ''
                )
                max_marks = float(question.get('marks') or question.get('weight', 1.0) * 10)
                keywords = question.get('keywords', '')

                ai_result = None
                if self.ai_evaluator and self.ai_evaluator.available and reference_text:
                    ai_result = self.ai_evaluator.evaluate(
                        student_answer=answer_portion,
                        model_answer=reference_text,
                        question_text=question.get('question', ''),
                        max_marks=max_marks,
                        keywords=keywords,
                        question_type=question.get('type', 'short_answer'),
                    )

                if ai_result:
                    similarity_score = float(ai_result.get('similarity', 0.0))
                    marks = self._apply_scoring_rules(
                        similarity_score,
                        scoring_rules,
                        max_marks
                    )
                    feedback = self._format_ai_feedback(ai_result)
                    provider = ai_result.get('provider', 'external_ai_api')
                    confidence = float(ai_result.get('confidence', similarity_score))
                else:
                    similarity_score = self._basic_similarity_check(
                        reference_text or question.get('question', ''),
                        answer_portion
                    )
                    marks = self._apply_scoring_rules(
                        similarity_score,
                        scoring_rules,
                        max_marks
                    )
                    feedback = self._generate_feedback(similarity_score, marks)
                    provider = 'local_similarity'
                    confidence = similarity_score

                evaluation_results.append({
                    'question_number': question.get('question_number', i + 1),
                    'question_text': question.get('question', ''),
                    'model_answer': reference_text,
                    'answer_text': answer_portion,
                    'similarity_score': similarity_score,
                    'raw_score': similarity_score * 100,
                    'marks_awarded': max(0.0, min(marks, max_marks)),
                    'max_marks': max_marks,
                    'question_type': question.get('type', 'short_answer'),
                    'confidence': max(0.0, min(confidence, 1.0)),
                    'feedback': feedback,
                    'evaluation_method': provider,
                })

                total_score += max(0.0, min(marks, max_marks))
                max_score += max_marks

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

    def _extract_answer_for_question(self, answer_text: str, question_index: int, question: Dict[str, Any], total_questions: int = 1) -> str:
        """
        Extract the relevant answer portion for a specific question
        """
        import re

        question_number = question.get('question_number', question_index + 1)
        pattern = re.compile(
            rf'(?is)(?:^|\n)\s*(?:q(?:uestion)?\s*)?{question_number}\s*[\.\):\-]\s*(.*?)(?=\n\s*(?:q(?:uestion)?\s*)?\d+\s*[\.\):\-]|\Z)'
        )
        match = pattern.search(answer_text)
        if match:
            return match.group(1).strip()

        parts = [
            part.strip()
            for part in re.split(r'(?m)^\s*(?:q(?:uestion)?\s*)?\d+\s*[\.\):\-]\s*', answer_text)
            if part.strip()
        ]
        if question_index < len(parts):
            return parts[question_index]

        return answer_text.strip() if total_questions == 1 else ''

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

    def _apply_scoring_rules(self, similarity_score: float, scoring_rules: Dict[str, Any], max_marks: float = 10.0) -> float:
        """
        Apply scoring rules based on similarity score
        """
        if not scoring_rules:
            scoring_rules = DEFAULT_SCORING_RULES

        # Find applicable scoring rule
        similarity_percentage = similarity_score * 100

        for rule_name, rule_config in scoring_rules.items():
            min_range, max_range = rule_config.get('range', (0, 100))
            marks_percentage = rule_config.get('marks_percentage', 100)

            if min_range <= similarity_percentage <= max_range:
                return max_marks * (marks_percentage / 100.0)

        # Default rule if no specific rule matches
        return similarity_score * max_marks

    def _format_ai_feedback(self, ai_result: Dict[str, Any]) -> str:
        parts = []
        for key in ['feedback', 'score_reason']:
            value = ai_result.get(key)
            if value:
                parts.append(str(value).strip())

        for label, key in [('Correct', 'correct_points'), ('Missing', 'missing_points'), ('Incorrect', 'incorrect_points')]:
            values = ai_result.get(key) or []
            if values:
                parts.append(f"{label}: " + "; ".join(str(value).strip() for value in values if str(value).strip()))

        return " | ".join(parts) or "Evaluated with external AI API."

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
                           scoring_rules: Dict[str, Any] = None,
                           marking_scheme_text: str = "",
                           total_marks: Optional[float] = None) -> Dict[str, Any]:
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
            question_detection = {
                'questions': [],
                'raw_text': '',
                'confidence': 0.0,
                'method_used': 'not_provided',
                'success': False,
            }
            if question_paper_path and os.path.exists(question_paper_path):
                question_detection = self.detect_questions_from_paper(question_paper_path)
                if question_detection['success']:
                    questions = question_detection['questions']
                else:
                    logger.warning(f"Question detection failed: {question_detection.get('error')}")

            # If no questions detected, try to extract from answer text
            if not questions:
                questions = self._basic_question_detection(answer_extraction['text'])

            questions = self._merge_question_specs(
                questions,
                marking_scheme_text=marking_scheme_text,
                total_marks=total_marks,
            )

            if not questions:
                raise Exception("No questions or marking scheme could be detected. Upload a question paper or paste a marking scheme.")

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
                    'raw_text': question_detection.get('raw_text', ''),
                    'confidence': question_detection.get('confidence', 0.0),
                    'method_used': question_detection.get('method_used', 'not_provided'),
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
