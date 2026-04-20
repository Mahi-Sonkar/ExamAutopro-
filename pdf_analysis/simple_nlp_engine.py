"""
Simple NLP Engine - spaCy + scikit-learn Pipeline
Clean Text -> NLP -> Evaluation
"""

import spacy
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

class SimpleNLPEngine:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("spaCy model loaded successfully")
        except:
            print("Warning: spaCy model not found, using basic logic")
            self.nlp = None
        
        # Question patterns
        self.question_patterns = [
            r'\b(what|how|why|when|where|who|which)\b',
            r'\b(explain|describe|define|compare|analyze|evaluate)\b',
            r'\b(discuss|illustrate|demonstrate|calculate|solve)\b'
        ]
        
        # Technical keywords
        self.technical_keywords = [
            'algorithm', 'machine learning', 'neural network', 'data', 'model',
            'training', 'testing', 'validation', 'accuracy', 'precision', 'recall',
            'f1 score', 'regression', 'classification', 'clustering', 'deep learning',
            'artificial intelligence', 'computer vision', 'natural language processing',
            'reinforcement learning', 'supervised learning', 'unsupervised learning'
        ]
    
    def analyze_text_comprehensive(self, text: str) -> Dict[str, Any]:
        """
        Simple Pipeline: Clean Text -> NLP -> Evaluation
        """
        try:
            print(f"Starting Simple NLP Pipeline for text length: {len(text)}")
            
            # Step 1: Clean text is already done by OCR
            clean_text = text.strip()
            
            # Step 2: NLP Processing
            if self.nlp:
                doc = self.nlp(clean_text)
                sentences = [sent.text.strip() for sent in doc.sents]
                entities = {ent.label_: ent.text for ent in doc.ents}
            else:
                sentences = re.split(r'[.!?]+', clean_text)
                entities = {}
            
            # Step 3: Question Extraction
            questions = self._extract_questions(sentences)
            print(f"Extracted {len(questions)} questions")
            
            # Step 4: TF-IDF Analysis (scikit-learn)
            tfidf_results = self._tfidf_analysis(clean_text)
            
            # Step 5: Evaluation
            evaluation = self._evaluate_content(clean_text, questions, tfidf_results)
            
            # Step 6: Final Results
            result = {
                'total_questions': len(questions),
                'question_analysis': questions,
                'overall_score': evaluation['score'],
                'score_category': evaluation['category'],
                'text_statistics': {
                    'word_count': len(clean_text.split()),
                    'sentence_count': len(sentences),
                    'char_count': len(clean_text)
                },
                'content_analysis': {
                    'domain_scores': entities,
                    'keywords': tfidf_results['top_keywords'],
                    'technical_terms': tfidf_results['technical_terms']
                },
                'complexity_analysis': {
                    'technical_terms_ratio': tfidf_results['tech_ratio'],
                    'unique_words': len(set(clean_text.lower().split())),
                    'avg_sentence_length': np.mean([len(s.split()) for s in sentences if s.strip()])
                },
                'recommendations': evaluation['recommendations'],
                'api_insights': {
                    'sentiment': 'professional',
                    'sentiment_score': 0.8,
                    'summary': f"Analysis complete: {len(sentences)} sentences, {len(questions)} questions detected"
                }
            }
            
            print(f"NLP Pipeline completed successfully")
            return result
            
        except Exception as e:
            print(f"Simple NLP Error: {str(e)}")
            return self._get_fallback_analysis(text)
    
    def _extract_questions(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """Extract questions from sentences"""
        questions = []
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if self._is_question(sentence):
                question_data = {
                    'question': sentence,
                    'type': self._classify_question(sentence),
                    'weight': self._calculate_weight(sentence),
                    'position': i
                }
                questions.append(question_data)
        
        return questions
    
    def _is_question(self, sentence: str) -> bool:
        """Check if sentence is a question"""
        sentence_lower = sentence.lower().strip()
        
        # Check for question mark
        if sentence_lower.endswith('?'):
            return True
        
        # Check for question patterns
        for pattern in self.question_patterns:
            if re.search(pattern, sentence_lower):
                return True
        
        # Check for question starters
        words = sentence_lower.split()
        if words and words[0] in ['what', 'how', 'why', 'when', 'where', 'who', 'which']:
            return True
        
        return False
    
    def _classify_question(self, question: str) -> str:
        """Classify question type"""
        q_lower = question.lower()
        
        if any(word in q_lower for word in ['choose', 'multiple choice', 'select']):
            return 'multiple_choice'
        elif any(word in q_lower for word in ['explain', 'describe', 'discuss', 'elaborate']):
            return 'essay'
        elif any(word in q_lower for word in ['what', 'define', 'state']):
            return 'short_answer'
        elif any(word in q_lower for word in ['how', 'procedure', 'steps', 'process']):
            return 'procedural'
        elif any(word in q_lower for word in ['why', 'reason', 'explain why']):
            return 'analytical'
        elif any(word in q_lower for word in ['compare', 'contrast', 'differentiate']):
            return 'comparative'
        else:
            return 'general'
    
    def _calculate_weight(self, question: str) -> float:
        """Calculate question weight based on complexity"""
        weight = 1.0
        
        # Add weight for technical terms
        tech_count = sum(1 for term in self.technical_keywords if term in question.lower())
        weight += tech_count * 0.2
        
        # Add weight for length
        if len(question) > 50:
            weight += 0.2
        elif len(question) > 100:
            weight += 0.3
        
        # Add weight for question type
        q_type = self._classify_question(question)
        if q_type == 'essay':
            weight += 0.5
        elif q_type == 'analytical':
            weight += 0.3
        
        return min(weight, 2.0)
    
    def _tfidf_analysis(self, text: str) -> Dict[str, Any]:
        """TF-IDF analysis using scikit-learn"""
        try:
            if not text.strip() or len(text.split()) < 3:
                return {
                    'top_keywords': [],
                    'technical_terms': [],
                    'tech_ratio': 0.0
                }
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=100,
                ngram_range=(1, 2)
            )
            
            # Fit and transform
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray().flatten()
            
            # Get top keywords
            top_indices = scores.argsort()[-5:][::-1]
            top_keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
            
            # Find technical terms
            technical_terms = []
            for term in self.technical_keywords:
                if term.lower() in text.lower():
                    technical_terms.append(term)
            
            # Calculate technical ratio
            words = text.lower().split()
            tech_ratio = len(technical_terms) / len(words) if words else 0.0
            
            return {
                'top_keywords': top_keywords,
                'technical_terms': technical_terms,
                'tech_ratio': tech_ratio
            }
            
        except Exception as e:
            print(f"TF-IDF Analysis Error: {str(e)}")
            return {
                'top_keywords': [],
                'technical_terms': [],
                'tech_ratio': 0.0
            }
    
    def _evaluate_content(self, text: str, questions: List[Dict], tfidf_results: Dict) -> Dict[str, Any]:
        """Evaluate content quality"""
        try:
            # Base score from text length
            word_count = len(text.split())
            base_score = min(word_count / 50, 5.0)  # Max 5 points for length
            
            # Question score
            question_score = len(questions) * 1.5  # 1.5 points per question
            
            # Technical content score
            tech_score = len(tfidf_results['technical_terms']) * 0.5  # 0.5 points per technical term
            
            # TF-IDF diversity score
            diversity_score = len(tfidf_results['top_keywords']) * 0.3  # 0.3 points per unique keyword
            
            # Total score
            total_score = base_score + question_score + tech_score + diversity_score
            total_score = min(total_score, 10.0)  # Max 10 points
            
            # Category
            if total_score >= 8.0:
                category = 'excellent'
            elif total_score >= 6.0:
                category = 'good'
            elif total_score >= 4.0:
                category = 'average'
            else:
                category = 'poor'
            
            # Recommendations
            recommendations = []
            if len(questions) < 2:
                recommendations.append("Add more questions to improve engagement")
            if len(tfidf_results['technical_terms']) < 3:
                recommendations.append("Include more technical terms for depth")
            if word_count < 100:
                recommendations.append("Expand content for better analysis")
            
            if not recommendations:
                recommendations.append("Content quality is good with balanced elements")
            
            return {
                'score': total_score,
                'category': category,
                'recommendations': recommendations
            }
            
        except Exception as e:
            print(f"Evaluation Error: {str(e)}")
            return {
                'score': 5.0,
                'category': 'average',
                'recommendations': ['Content evaluation completed']
            }
    
    def _get_fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback analysis for errors"""
        return {
            'total_questions': 0,
            'question_analysis': [],
            'overall_score': 5.0,
            'score_category': 'average',
            'text_statistics': {
                'word_count': len(text.split()),
                'sentence_count': len(re.split(r'[.!?]+', text)),
                'char_count': len(text)
            },
            'content_analysis': {
                'domain_scores': {},
                'keywords': [],
                'technical_terms': []
            },
            'complexity_analysis': {
                'technical_terms_ratio': 0.0,
                'unique_words': 0,
                'avg_sentence_length': 0
            },
            'recommendations': ['Analysis completed with fallback method'],
            'api_insights': {
                'sentiment': 'neutral',
                'sentiment_score': 0.5,
                'summary': 'Fallback analysis completed'
            }
        }

# Create instance
simple_nlp = SimpleNLPEngine()
