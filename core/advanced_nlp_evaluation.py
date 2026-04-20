"""
Advanced NLP and OCR Evaluation Engine for ExamAutoPro
Main motive: Highly accurate text evaluation with multiple NLP techniques
"""

import re
import math
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter, defaultdict
import json

# Try to import advanced NLP libraries
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import normalize
    from sklearn.metrics import jaccard_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    np = None
    TfidfVectorizer = None
    cosine_similarity = None
    normalize = None
    jaccard_score = None

# Try to import NLTK for advanced processing
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.metrics import edit_distance
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    nltk = None
    word_tokenize = None
    sent_tokenize = None
    stopwords = None
    WordNetLemmatizer = None
    edit_distance = None

logger = logging.getLogger(__name__)

class AdvancedNLPEvaluation:
    """
    Advanced NLP evaluation with multiple techniques for maximum accuracy
    Main motive: Highly intelligent answer evaluation
    """
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer() if NLTK_AVAILABLE else None
        self.stop_words = set(stopwords.words('english')) if NLTK_AVAILABLE else set()
        
        # Advanced TF-IDF configuration
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=2000,
            stop_words='english',
            ngram_range=(1, 3),
            lowercase=True,
            strip_accents='ascii',
            sublinear_tf=True,
            min_df=1,
            max_df=0.9,
            analyzer='word'
        ) if SKLEARN_AVAILABLE else None
        
        # Initialize evaluation weights
        self.weights = {
            'semantic_similarity': 0.35,
            'keyword_matching': 0.25,
            'concept_coverage': 0.20,
            'structure_analysis': 0.10,
            'length_appropriateness': 0.05,
            'context_relevance': 0.05
        }
        
    def preprocess_text_advanced(self, text: str) -> str:
        """
        Advanced text preprocessing for better NLP accuracy
        Main motive: Clean and normalize text for optimal processing
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\']', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Advanced tokenization and lemmatization
        if NLTK_AVAILABLE and self.lemmatizer:
            try:
                tokens = word_tokenize(text)
                # Remove stop words and lemmatize
                tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                         if token not in self.stop_words and len(token) > 1]
                text = ' '.join(tokens)
            except Exception as e:
                logger.warning(f"NLTK preprocessing failed: {str(e)}")
        
        return text
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity using multiple techniques
        Main motive: Most accurate text similarity calculation
        """
        try:
            # Preprocess texts
            text1_clean = self.preprocess_text_advanced(text1)
            text2_clean = self.preprocess_text_advanced(text2)
            
            if not text1_clean or not text2_clean:
                return 0.0
            
            similarity_scores = []
            
            # 1. TF-IDF Cosine Similarity (if available)
            if SKLEARN_AVAILABLE and self.tfidf_vectorizer:
                try:
                    documents = [text1_clean, text2_clean]
                    tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
                    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                    similarity_scores.append(cosine_sim)
                except Exception as e:
                    logger.warning(f"TF-IDF similarity failed: {str(e)}")
            
            # 2. Jaccard Similarity
            try:
                words1 = set(text1_clean.split())
                words2 = set(text2_clean.split())
                jaccard_sim = len(words1.intersection(words2)) / len(words1.union(words2)) if words1.union(words2) else 0
                similarity_scores.append(jaccard_sim)
            except Exception as e:
                logger.warning(f"Jaccard similarity failed: {str(e)}")
            
            # 3. Word Overlap with Weighting
            try:
                words1 = text1_clean.split()
                words2 = text2_clean.split()
                
                # Calculate weighted word overlap
                word_freq1 = Counter(words1)
                word_freq2 = Counter(words2)
                
                common_words = set(word_freq1.keys()) & set(word_freq2.keys())
                if common_words:
                    weighted_overlap = sum(min(word_freq1[w], word_freq2[w]) for w in common_words)
                    total_words = sum(word_freq1.values()) + sum(word_freq2.values())
                    overlap_sim = (2 * weighted_overlap) / total_words if total_words > 0 else 0
                    similarity_scores.append(overlap_sim)
            except Exception as e:
                logger.warning(f"Word overlap similarity failed: {str(e)}")
            
            # 4. Edit Distance Similarity (for shorter texts)
            if len(text1_clean) < 200 and len(text2_clean) < 200:
                try:
                    if NLTK_AVAILABLE and edit_distance:
                        max_len = max(len(text1_clean), len(text2_clean))
                        if max_len > 0:
                            edit_dist = edit_distance(text1_clean, text2_clean)
                            edit_sim = 1 - (edit_dist / max_len)
                            similarity_scores.append(max(0, edit_sim))
                except Exception as e:
                    logger.warning(f"Edit distance similarity failed: {str(e)}")
            
            # Return weighted average of all similarity scores
            if similarity_scores:
                return sum(similarity_scores) / len(similarity_scores)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {str(e)}")
            return 0.0
    
    def calculate_keyword_matching_score(self, student_text: str, keywords: List[str]) -> float:
        """
        Advanced keyword matching with partial matching and context
        Main motive: Intelligent keyword detection beyond exact matching
        """
        if not keywords or not student_text:
            return 0.0
        
        try:
            student_clean = self.preprocess_text_advanced(student_text)
            student_words = student_clean.split()
            
            keyword_scores = []
            
            for keyword in keywords:
                keyword_clean = self.preprocess_text_advanced(keyword)
                keyword_words = keyword_clean.split()
                
                # Exact phrase matching
                if keyword_clean in student_clean:
                    keyword_scores.append(1.0)
                    continue
                
                # Partial word matching
                matched_words = 0
                for kw_word in keyword_words:
                    if kw_word in student_words:
                        matched_words += 1
                
                if matched_words > 0:
                    # Score based on proportion of keyword words matched
                    partial_score = matched_words / len(keyword_words)
                    keyword_scores.append(partial_score)
                else:
                    # Check for similar words using edit distance
                    for kw_word in keyword_words:
                        best_match = 0
                        for student_word in student_words:
                            if NLTK_AVAILABLE and edit_distance:
                                max_len = max(len(kw_word), len(student_word))
                                if max_len > 0:
                                    edit_dist = edit_distance(kw_word, student_word)
                                    similarity = 1 - (edit_dist / max_len)
                                    if similarity > 0.7:  # 70% similarity threshold
                                        best_match = max(best_match, similarity)
                        keyword_scores.append(best_match * 0.5)  # Weight partial matches lower
            
            # Calculate final keyword score
            if keyword_scores:
                return sum(keyword_scores) / len(keywords)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Keyword matching failed: {str(e)}")
            return 0.0
    
    def calculate_concept_coverage(self, student_text: str, model_text: str) -> float:
        """
        Calculate how well student covers concepts from model answer
        Main motive: Concept-level understanding evaluation
        """
        try:
            student_clean = self.preprocess_text_advanced(student_text)
            model_clean = self.preprocess_text_advanced(model_text)
            
            if not student_clean or not model_clean:
                return 0.0
            
            # Extract key concepts (important words and phrases)
            student_words = set(student_clean.split())
            model_words = set(model_clean.split())
            
            # Calculate concept coverage
            covered_concepts = student_words.intersection(model_words)
            total_concepts = model_words
            
            if total_concepts:
                coverage = len(covered_concepts) / len(total_concepts)
                
                # Bonus for covering rare/important concepts
                word_freq = Counter(model_clean.split())
                rare_words = {word for word, freq in word_freq.items() if freq == 1}
                rare_coverage = len(covered_concepts.intersection(rare_words)) / len(rare_words) if rare_words else 0
                
                # Combine coverage with rare concept bonus
                final_score = coverage * 0.8 + rare_coverage * 0.2
                return min(1.0, final_score)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Concept coverage calculation failed: {str(e)}")
            return 0.0
    
    def calculate_structure_analysis(self, text: str) -> float:
        """
        Analyze text structure for coherence and organization
        Main motive: Evaluate answer structure and coherence
        """
        try:
            if not text:
                return 0.0
            
            structure_score = 0.0
            max_score = 0.0
            
            # 1. Sentence structure analysis
            sentences = text.split('.')
            if len(sentences) > 1:
                avg_sentence_length = sum(len(s.strip().split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
                # Good sentence length is between 10-25 words
                if 10 <= avg_sentence_length <= 25:
                    structure_score += 0.3
                max_score += 0.3
            
            # 2. Paragraph structure
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if len(paragraphs) > 1:
                structure_score += 0.2
            max_score += 0.2
            
            # 3. Use of transition words
            transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'consequently', 'thus', 'hence']
            transition_count = sum(1 for word in transition_words if word in text.lower())
            if transition_count > 0:
                structure_score += min(0.2, transition_count * 0.05)
            max_score += 0.2
            
            # 4. Punctuation and grammar
            punctuation_score = 0.3
            if any(punct in text for punct in [',', ';', ':']):
                punctuation_score += 0.1
            if text.count('.') > 1:
                punctuation_score += 0.1
            if text[0].isupper() if text else False:
                punctuation_score += 0.1
            
            structure_score += punctuation_score
            max_score += 0.3
            
            return structure_score / max_score if max_score > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Structure analysis failed: {str(e)}")
            return 0.0
    
    def calculate_length_appropriateness(self, student_text: str, model_text: str) -> float:
        """
        Evaluate if answer length is appropriate
        Main motive: Check if answer length is reasonable
        """
        try:
            if not student_text or not model_text:
                return 0.0
            
            student_len = len(student_text.split())
            model_len = len(model_text.split())
            
            # Calculate length ratio
            if model_len > 0:
                length_ratio = student_len / model_len
                
                # Ideal ratio is between 0.5 and 2.0
                if 0.5 <= length_ratio <= 2.0:
                    return 1.0
                elif 0.3 <= length_ratio < 0.5:
                    return 0.7
                elif 2.0 < length_ratio <= 3.0:
                    return 0.8
                else:
                    return 0.5
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Length appropriateness calculation failed: {str(e)}")
            return 0.0
    
    def evaluate_answer_comprehensive(self, student_answer: str, model_answer: str, 
                                     keywords: List[str] = None, question_type: str = 'descriptive') -> Dict:
        """
        Comprehensive answer evaluation using all NLP techniques
        Main motive: Most accurate answer evaluation possible
        """
        try:
            if not student_answer or not model_answer:
                return {
                    'score': 0.0,
                    'confidence': 0.0,
                    'method': 'no_answer',
                    'details': {'error': 'No answer provided'}
                }
            
            # Calculate all evaluation components
            semantic_score = self.calculate_semantic_similarity(student_answer, model_answer)
            keyword_score = self.calculate_keyword_matching_score(student_answer, keywords or [])
            concept_score = self.calculate_concept_coverage(student_answer, model_answer)
            structure_score = self.calculate_structure_analysis(student_answer)
            length_score = self.calculate_length_appropriateness(student_answer, model_answer)
            
            # Calculate context relevance (bonus for relevant content)
            context_score = min(1.0, (semantic_score + concept_score) / 2 * 1.1)
            
            # Combine scores using weighted average
            final_score = (
                semantic_score * self.weights['semantic_similarity'] +
                keyword_score * self.weights['keyword_matching'] +
                concept_score * self.weights['concept_coverage'] +
                structure_score * self.weights['structure_analysis'] +
                length_score * self.weights['length_appropriateness'] +
                context_score * self.weights['context_relevance']
            )
            
            # Calculate confidence based on consistency of scores
            scores = [semantic_score, keyword_score, concept_score, structure_score, length_score]
            confidence = 1.0 - (max(scores) - min(scores))  # Higher confidence for consistent scores
            
            # Determine evaluation method used
            method = 'advanced_nlp_comprehensive'
            if SKLEARN_AVAILABLE:
                method += '_sklearn'
            if NLTK_AVAILABLE:
                method += '_nltk'
            
            return {
                'score': min(1.0, max(0.0, final_score)),
                'confidence': min(1.0, max(0.0, confidence)),
                'method': method,
                'details': {
                    'semantic_similarity': semantic_score,
                    'keyword_matching': keyword_score,
                    'concept_coverage': concept_score,
                    'structure_analysis': structure_score,
                    'length_appropriateness': length_score,
                    'context_relevance': context_score,
                    'weights_used': self.weights,
                    'preprocessing_successful': True
                }
            }
            
        except Exception as e:
            logger.error(f"Comprehensive evaluation failed: {str(e)}")
            return {
                'score': 0.0,
                'confidence': 0.0,
                'method': 'evaluation_error',
                'details': {'error': str(e)}
            }

class AdvancedOCREvaluation:
    """
    Advanced OCR evaluation with confidence scoring and error correction
    Main motive: Highly accurate handwritten answer evaluation
    """
    
    def __init__(self):
        self.confidence_thresholds = {
            'high': 0.85,
            'medium': 0.70,
            'low': 0.50
        }
        
        self.ocr_weights = {
            'text_confidence': 0.4,
            'content_similarity': 0.4,
            'handwriting_quality': 0.2
        }
    
    def preprocess_ocr_text(self, ocr_text: str) -> str:
        """
        Advanced OCR text preprocessing for error correction
        Main motive: Clean OCR output for better evaluation
        """
        if not ocr_text:
            return ""
        
        # Common OCR corrections
        corrections = {
            'rn': 'm',
            'cl': 'd',
            'vv': 'w',
            'l1': 'll',
            '0o': 'o',
            '1i': 'i',
            '5s': 's'
        }
        
        text = ocr_text.lower().strip()
        
        # Apply common corrections
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def evaluate_handwritten_answer(self, ocr_text: str, model_answer: str, 
                                  ocr_confidence: float = None) -> Dict:
        """
        Advanced handwritten answer evaluation
        Main motive: Accurate evaluation with OCR confidence consideration
        """
        try:
            if not ocr_text or not model_answer:
                return {
                    'score': 0.0,
                    'confidence': 0.0,
                    'method': 'handwritten_no_text',
                    'details': {'error': 'No text available'}
                }
            
            # Preprocess OCR text
            cleaned_text = self.preprocess_ocr_text(ocr_text)
            
            # Use advanced NLP evaluation
            nlp_evaluator = AdvancedNLPEvaluation()
            nlp_result = nlp_evaluator.evaluate_answer_comprehensive(
                cleaned_text, model_answer, question_type='handwritten'
            )
            
            # Adjust score based on OCR confidence
            if ocr_confidence is not None:
                # Apply OCR confidence weighting
                adjusted_score = nlp_result['score'] * ocr_confidence
                
                # Additional penalty for very low confidence
                if ocr_confidence < self.confidence_thresholds['low']:
                    adjusted_score *= 0.5
                
                # Combine confidence scores
                combined_confidence = (nlp_result['confidence'] + ocr_confidence) / 2
                
                return {
                    'score': adjusted_score,
                    'confidence': combined_confidence,
                    'method': 'advanced_ocr_evaluation',
                    'details': {
                        'original_ocr_text': ocr_text,
                        'cleaned_text': cleaned_text,
                        'ocr_confidence': ocr_confidence,
                        'nlp_score': nlp_result['score'],
                        'nlp_confidence': nlp_result['confidence'],
                        'confidence_level': self._get_confidence_level(ocr_confidence),
                        'requires_manual_review': ocr_confidence < self.confidence_thresholds['medium']
                    }
                }
            else:
                return nlp_result
            
        except Exception as e:
            logger.error(f"Advanced OCR evaluation failed: {str(e)}")
            return {
                'score': 0.0,
                'confidence': 0.0,
                'method': 'ocr_evaluation_error',
                'details': {'error': str(e)}
            }
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level description"""
        if confidence >= self.confidence_thresholds['high']:
            return 'high'
        elif confidence >= self.confidence_thresholds['medium']:
            return 'medium'
        elif confidence >= self.confidence_thresholds['low']:
            return 'low'
        else:
            return 'very_low'
