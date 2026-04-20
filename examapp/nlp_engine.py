"""
NLP Engine - Tab 4 Implementation
Handles text analysis, question extraction, and answer evaluation
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
except ImportError:
    ANTHROPIC_AVAILABLE = False
    ANTHROPIC_API_KEY = None
    logger.warning("Anthropic library not available")

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("Scikit-learn not available")


class NLPEngine:
    """Main NLP Engine class for text analysis and evaluation"""
    
    def __init__(self):
        self.client = None
        if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
            try:
                self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
    
    def extract_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract questions from text using Claude API
        Returns: List of question dictionaries
        """
        if not self.client:
            return self._extract_questions_regex(text)
        
        try:
            prompt = f"""
            Extract all questions from the following text. For each question, identify:
            - Question text
            - Question type (multiple-choice, short-answer, essay, true-false)
            - Difficulty level (easy, medium, hard)
            - Topic/subject
            - Options (if multiple-choice)
            - Correct answer (if identifiable)
            
            Text to analyze:
            {text}
            
            Return as JSON array:
            [
                {{
                    "question": "question text",
                    "type": "question type",
                    "difficulty": "difficulty",
                    "topic": "subject/topic",
                    "options": ["option1", "option2", "option3", "option4"],
                    "correct_answer": "correct answer"
                }}
            ]
            """
            
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Parse JSON response
            try:
                questions = json.loads(response_text)
                return questions if isinstance(questions, list) else []
            except json.JSONDecodeError:
                return self._extract_questions_regex(text)
                
        except Exception as e:
            logger.error(f"Claude API question extraction failed: {e}")
            return self._extract_questions_regex(text)
    
    def _extract_questions_regex(self, text: str) -> List[Dict[str, Any]]:
        """Fallback question extraction using regex patterns"""
        questions = []
        
        # Common question patterns
        question_patterns = [
            r'(\d+\.\s*.*?\?)',  # Numbered questions
            r'(What|When|Where|Why|How|Who|Which).*?\?',  # Wh- questions
            r'(True|False)\s*.*?\?',  # True/False questions
            r'(A\)|B\)|C\)|D\))',  # Multiple choice
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                questions.append({
                    'question': match.strip(),
                    'type': 'unknown',
                    'difficulty': 'medium',
                    'topic': 'general',
                    'options': [],
                    'correct_answer': ''
                })
        
        return questions
    
    def evaluate_answer(self, question: str, correct_answer: str, student_answer: str) -> Dict[str, Any]:
        """
        Evaluate student answer against correct answer using multiple methods
        Returns: Dictionary with evaluation results
        """
        if not student_answer or not correct_answer:
            return {
                'score': 0,
                'similarity': 0,
                'feedback': 'No answer provided',
                'method': 'none'
            }
        
        # Method 1: Exact match
        exact_match = student_answer.strip().lower() == correct_answer.strip().lower()
        
        # Method 2: Semantic similarity (if available)
        semantic_score = 0
        if SKLEARN_AVAILABLE:
            semantic_score = self._calculate_semantic_similarity(correct_answer, student_answer)
        
        # Method 3: Claude API evaluation (if available)
        claude_score = 0
        if self.client:
            claude_score = self._evaluate_with_claude(question, correct_answer, student_answer)
        
        # Combine scores with weights
        final_score = 0
        method_used = 'none'
        
        if exact_match:
            final_score = 100
            method_used = 'exact_match'
        elif semantic_score > 0.7:
            final_score = semantic_score * 100
            method_used = 'semantic_similarity'
        elif claude_score > 0.7:
            final_score = claude_score * 100
            method_used = 'claude_evaluation'
        else:
            final_score = max(semantic_score * 100, claude_score * 100)
            method_used = 'combined'
        
        return {
            'score': min(final_score, 100),
            'similarity': max(semantic_score, claude_score),
            'exact_match': exact_match,
            'feedback': self._generate_feedback(final_score),
            'method': method_used
        }
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using TF-IDF and cosine similarity"""
        try:
            if not SKLEARN_AVAILABLE:
                return 0.0
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer().fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(vectorizer[0:1], vectorizer[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def _evaluate_with_claude(self, question: str, correct_answer: str, student_answer: str) -> float:
        """Evaluate answer using Claude API"""
        try:
            if not self.client:
                return 0.0
            
            prompt = f"""
            Evaluate the student's answer against the correct answer for the given question.
            Consider:
            - Content accuracy
            - Conceptual understanding
            - Completeness
            - Language quality
            
            Question: {question}
            Correct Answer: {correct_answer}
            Student Answer: {student_answer}
            
            Return a single number between 0.0 and 1.0 representing the score:
            """
            
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract score from response
            response_text = response.content[0].text
            score_match = re.search(r'0\.\d+|1\.0|0|1', response_text)
            
            if score_match:
                return float(score_match.group())
            else:
                return 0.5  # Default if no clear score found
                
        except Exception as e:
            logger.error(f"Claude evaluation failed: {e}")
            return 0.0
    
    def _generate_feedback(self, score: float) -> str:
        """Generate feedback based on score"""
        if score >= 90:
            return "Excellent answer! Full marks awarded."
        elif score >= 75:
            return "Good answer with minor improvements needed."
        elif score >= 60:
            return "Acceptable answer with some areas for improvement."
        elif score >= 40:
            return "Answer needs significant improvement."
        else:
            return "Answer is incorrect or incomplete."
    
    def analyze_text_complexity(self, text: str) -> Dict[str, Any]:
        """Analyze text complexity and readability"""
        try:
            if not NLTK_AVAILABLE:
                return {
                    'word_count': len(text.split()),
                    'sentence_count': text.count('.') + text.count('!') + text.count('?'),
                    'avg_words_per_sentence': 0,
                    'readability_score': 0
                }
            
            # Tokenize text
            words = word_tokenize(text.lower())
            sentences = sent_tokenize(text)
            
            # Remove stopwords
            stop_words = set(stopwords.words('english'))
            content_words = [word for word in words if word.isalpha() and word not in stop_words]
            
            # Calculate metrics
            word_count = len(words)
            sentence_count = len(sentences)
            avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
            
            # Simple readability score (based on average words per sentence)
            readability_score = max(0, 100 - (avg_words_per_sentence - 10) * 2)
            
            return {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'unique_words': len(set(words)),
                'content_words': len(content_words),
                'avg_words_per_sentence': avg_words_per_sentence,
                'readability_score': min(readability_score, 100),
                'complexity': 'high' if avg_words_per_sentence > 20 else 'medium' if avg_words_per_sentence > 15 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Text complexity analysis failed: {e}")
            return {'error': str(e)}
    
    def get_available_methods(self) -> Dict[str, bool]:
        """Get available NLP methods"""
        return {
            'claude_api': ANTHROPIC_AVAILABLE and bool(ANTHROPIC_API_KEY),
            'nltk': NLTK_AVAILABLE,
            'sklearn': SKLEARN_AVAILABLE
        }


# Singleton instance
nlp_engine = NLPEngine()


def extract_questions(text: str) -> List[Dict[str, Any]]:
    """Convenience function to extract questions from text"""
    return nlp_engine.extract_questions_from_text(text)


def evaluate_answer(question: str, correct_answer: str, student_answer: str) -> Dict[str, Any]:
    """Convenience function to evaluate answer"""
    return nlp_engine.evaluate_answer(question, correct_answer, student_answer)


def analyze_text(text: str) -> Dict[str, Any]:
    """Convenience function to analyze text"""
    return nlp_engine.analyze_text_complexity(text)


if __name__ == "__main__":
    # Test NLP engine
    print("Available NLP methods:", nlp_engine.get_available_methods())
    
    # Test question extraction
    sample_text = """
    1. What is the capital of France?
    2. Explain the process of photosynthesis.
    3. True or False: The Earth is flat.
    """
    
    questions = extract_questions(sample_text)
    print(f"Extracted questions: {questions}")
    
    # Test answer evaluation
    result = evaluate_answer(
        "What is the capital of France?",
        "Paris",
        "The capital of France is Paris."
    )
    print(f"Answer evaluation: {result}")
