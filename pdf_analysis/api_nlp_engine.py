"""
Local NLP Engine using spaCy and scikit-learn
"""

import re
import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
from collections import Counter

class LocalNLPEngine:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            # Fallback if model not found
            self.nlp = None
            print("Warning: spaCy model 'en_core_web_sm' not found. Using basic logic.")
            
        # Question keywords
        self.question_keywords = [
            'what', 'how', 'why', 'when', 'where', 'who', 'which', 'explain',
            'describe', 'define', 'compare', 'contrast', 'analyze', 'evaluate',
            'discuss', 'illustrate', 'demonstrate', 'calculate', 'solve',
            'prove', 'derive', 'show'
        ]
        
        # Technical keywords for scoring
        self.technical_keywords = [
            'algorithm', 'machine learning', 'neural network', 'data', 'model',
            'training', 'testing', 'validation', 'accuracy', 'precision', 'recall',
            'f1 score', 'regression', 'classification', 'clustering', 'deep learning',
            'artificial intelligence', 'computer vision', 'natural language processing',
            'reinforcement learning', 'supervised learning', 'unsupervised learning'
        ]

    def analyze_text_comprehensive(self, text: str) -> Dict[str, Any]:
        """Comprehensive text analysis using spaCy and scikit-learn"""
        try:
            # 1. Use spaCy for sentence segmentation and NER if available
            if self.nlp:
                doc = self.nlp(text)
                sentences = [sent.text.strip() for sent in doc.sents]
                entities = {ent.label_: ent.text for ent in doc.ents}
            else:
                sentences = re.split(r'[.!?]+', text)
                entities = {}

            # 2. Extract questions
            questions = []
            for i, sent in enumerate(sentences):
                if self._is_question(sent):
                    questions.append({
                        'question': sent,
                        'type': self._classify_question(sent),
                        'weight': self._calculate_weight(sent),
                        'position': i
                    })

            # 3. Calculate scores using TF-IDF (scikit-learn)
            vectorizer = TfidfVectorizer(stop_words='english')
            if text.strip() and len(text.split()) > 2:
                tfidf_matrix = vectorizer.fit_transform([text])
                feature_names = vectorizer.get_feature_names_out()
                scores = tfidf_matrix.toarray().flatten()
                top_keywords = [feature_names[i] for i in scores.argsort()[-5:][::-1]]
            else:
                top_keywords = []

            # 4. Final Result
            result = {
                'total_questions': len(questions),
                'question_analysis': questions,
                'overall_score': self._calculate_overall_score(text, questions),
                'score_category': 'academic',
                'text_statistics': {
                    'word_count': len(text.split()),
                    'sentence_count': len(sentences),
                    'char_count': len(text)
                },
                'content_analysis': {
                    'domain_scores': entities,
                    'keywords': top_keywords
                },
                'complexity_analysis': {
                    'technical_terms_ratio': self._calculate_tech_ratio(text)
                },
                'recommendations': ["Focus on key concepts identified.", "Review detected questions."],
                'api_insights': {
                    'sentiment': 'professional',
                    'sentiment_score': 0.8,
                    'summary': f"Analysis of {len(sentences)} sentences with {len(questions)} questions detected."
                }
            }
            return result

        except Exception as e:
            print(f"Local NLP Error: {str(e)}")
            return self._get_fallback_analysis(text)

    def _is_question(self, text: str) -> bool:
        text_lower = text.lower().strip()
        if text_lower.endswith('?') or re.search(r'\?$', text_lower):
            return True
        
        words = text_lower.split()
        if not words: return False
        
        first_word = re.sub(r'^\d+[\.\)]', '', words[0]).strip()
        if first_word in self.question_keywords:
            return True
            
        modal_starters = ['is', 'are', 'can', 'do', 'does', 'did', 'will', 'would', 'could', 'should']
        if first_word in modal_starters and len(words) >= 3:
            return True
            
        return False

    def _classify_question(self, question: str) -> str:
        q_lower = question.lower()
        if any(w in q_lower for w in ['choose', 'multiple choice']): return 'multiple_choice'
        if any(w in q_lower for w in ['explain', 'describe', 'discuss']): return 'essay'
        if any(w in q_lower for w in ['what', 'define']): return 'short_answer'
        return 'unknown'

    def _calculate_weight(self, question: str) -> float:
        weight = 1.0
        tech_count = sum(1 for w in self.technical_keywords if w in question.lower())
        return min(weight + (tech_count * 0.2), 2.0)

    def _calculate_tech_ratio(self, text: str) -> float:
        words = text.lower().split()
        if not words: return 0.0
        tech_count = sum(1 for w in words if w in self.technical_keywords)
        return tech_count / len(words)

    def _calculate_overall_score(self, text: str, questions: list) -> float:
        base = min(len(text.split()) / 100, 5.0)
        q_bonus = len(questions) * 0.5
        return min(base + q_bonus, 10.0)

    def _get_fallback_analysis(self, text: str):
        return {
            'total_questions': 0,
            'question_analysis': [],
            'overall_score': 0.0,
            'api_insights': {'summary': 'Analysis failed, using fallback.'}
        }

# Create instance
api_nlp = LocalNLPEngine()
