"""
Enhanced NLP Engine for Score Range Based Evaluation
Perfect NLP Analysis with Accurate Scoring Rules
"""

import re
import logging
from typing import Dict, List, Tuple
from collections import Counter
import math

logger = logging.getLogger(__name__)

class EnhancedNLPEngine:
    """Enhanced NLP Engine with score range based evaluation"""
    
    def __init__(self, custom_rules: Dict = None):
        # Default score range rules if none provided
        self.score_rules = custom_rules or {
            'excellent': {'range': (80, 100), 'criteria': ['comprehensive', 'detailed', 'accurate']},
            'good': {'range': (60, 79), 'criteria': ['adequate', 'relevant', 'mostly_correct']},
            'average': {'range': (40, 59), 'criteria': ['basic', 'partial', 'some_correct']},
            'poor': {'range': (0, 39), 'criteria': ['incomplete', 'incorrect', 'minimal']}
        }
        
        # Question type weights
        self.question_weights = {
            'what': 0.2,
            'how': 0.25,
            'why': 0.25,
            'explain': 0.3,
            'describe': 0.2,
            'define': 0.15,
            'compare': 0.3,
            'analyze': 0.35,
            'evaluate': 0.35
        }
        
        # Technical keywords for different domains
        self.technical_keywords = {
            'machine_learning': ['algorithm', 'model', 'training', 'prediction', 'classification', 'regression', 'neural', 'network'],
            'data_science': ['data', 'analysis', 'statistics', 'visualization', 'preprocessing', 'feature'],
            'artificial_intelligence': ['intelligence', 'reasoning', 'learning', 'perception', 'problem_solving'],
            'computer_science': ['programming', 'algorithm', 'data_structure', 'complexity', 'optimization']
        }
    
    def analyze_text_comprehensive(self, text: str) -> Dict:
        """Comprehensive text analysis with score range evaluation"""
        if not text or not text.strip():
            return self._get_empty_analysis()
        
        # Extract questions
        questions = self._extract_questions(text)
        
        # Analyze each question
        question_analysis = []
        total_score = 0
        total_weight = 0
        
        for question in questions:
            analysis = self._analyze_single_question(question)
            question_analysis.append(analysis)
            total_score += analysis['score'] * analysis['weight']
            total_weight += analysis['weight']
        
        # Calculate overall score
        overall_score = total_score / total_weight if total_weight > 0 else 0
        
        # Determine score category and adjusted score based on rules
        score_category, final_adjusted_score = self._get_score_category(overall_score)
        
        # Content analysis
        content_analysis = self._analyze_content(text)
        
        # Complexity analysis
        complexity_analysis = self._analyze_complexity(text)
        
        return {
            'overall_score': final_adjusted_score,
            'original_score': overall_score,
            'score_category': score_category,
            'total_questions': len(questions),
            'question_analysis': question_analysis,
            'content_analysis': content_analysis,
            'complexity_analysis': complexity_analysis,
            'text_statistics': self._get_text_statistics(text),
            'recommendations': self._generate_recommendations(overall_score, questions)
        }
    
    def _extract_questions(self, text: str) -> List[str]:
        """Extract questions with high accuracy using multiple strategies"""
        if not text:
            return []
            
        questions = []
        
        # 1. Split by question marks and process each segment
        # This handles multiple sentences before a question mark
        segments = text.split('?')
        for i, segment in enumerate(segments):
            if i == len(segments) - 1 and not segment.strip():
                continue # Last segment empty
            
            # For each segment, we might have multiple sentences/lines
            # The last part of the segment *is* the question that ends with ?
            if i < len(segments) - 1:
                # Add back the ?
                current_question_text = segment + '?'
                
                # If segment has multiple lines, the question is likely the last line
                lines = current_question_text.strip().split('\n')
                potential_q = lines[-1].strip()
                if self._is_question(potential_q):
                    questions.append(potential_q)
                    # Process preceding lines as potential non-? questions
                    for line in lines[:-1]:
                        if self._is_question(line.strip()):
                            questions.append(line.strip())
                else:
                    # Fallback to checking the whole segment
                    if self._is_question(current_question_text.strip()):
                        questions.append(current_question_text.strip())
            else:
                # Last segment (doesn't end with ?)
                lines = segment.strip().split('\n')
                for line in lines:
                    if self._is_question(line.strip()):
                        questions.append(line.strip())

        # 2. Also split by common numbering patterns (1., 2., a), b), etc.)
        # and check each part
        pattern = r'(?:\n|^)(?:\d+[\.\)]|[a-z][\.\)])\s+'
        numbered_parts = re.split(pattern, text)
        for part in numbered_parts:
            part = part.strip()
            if part and self._is_question(part) and part not in questions:
                questions.append(part)
        
        # 3. Final cleanup and duplicate removal
        seen = set()
        unique_questions = []
        for q in questions:
            # Clean numbering
            clean_q = re.sub(r'^\d+[\.\)]\s*', '', q).strip()
            if clean_q and clean_q.lower() not in seen:
                seen.add(clean_q.lower())
                unique_questions.append(q)
        
        return unique_questions
    
    def _is_question(self, text: str) -> bool:
        """Check if text is a valid question with high accuracy for exam papers"""
        text_lower = text.lower().strip()
        
        # 1. Ends with a question mark
        if text_lower.endswith('?'):
            return True
            
        # 2. Exam specific patterns (Q1, Question 1, etc.)
        exam_patterns = [
            r'^q\d+[:.]',
            r'^question\s+\d+[:.]',
            r'^part\s+[a-z][:.]',
            r'^\(\w\)\s+',
            r'^\d+[\.\)]\s+'
        ]
        for pattern in exam_patterns:
            if re.match(pattern, text_lower):
                # If it's just numbering, check if the rest of the text is a question
                cleaned = re.sub(pattern, '', text_lower).strip()
                if self._is_question(cleaned):
                    return True
        
        # 3. Question starters (common in exam papers)
        question_starters = [
            'what', 'where', 'when', 'why', 'how', 'who', 'which', 'whose', 'whom',
            'explain', 'define', 'describe', 'discuss', 'compare', 'contrast',
            'analyze', 'evaluate', 'calculate', 'state', 'show', 'prove', 'list',
            'give', 'mention', 'write', 'draw', 'identify', 'suggest', 'enumerate',
            'elaborate', 'justify', 'outline', 'sketch', 'determine', 'solve',
            'derive', 'verify', 'illustrate', 'summarize'
        ]
        
        # Clean numbering from the start of the text for checking
        clean_text = re.sub(r'^\d+[\.\)]\s*', '', text_lower).strip()
        words = clean_text.split()
        if not words:
            return False
            
        # 4. Starts with a question starter and is reasonably long
        first_word = words[0]
        if first_word in question_starters and len(words) >= 2:
            return True
            
        # 5. Modal verbs (Is, Can, Do, etc.)
        modal_starters = ['is', 'are', 'can', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'must', 'may']
        if len(words) >= 2:
            if words[0] in modal_starters:
                return True
        
        return False
    
    def _analyze_single_question(self, question: str) -> Dict:
        """Analyze a single question"""
        # Determine question type
        q_type = self._get_question_type(question)
        
        # Calculate weight
        weight = self.question_weights.get(q_type, 0.2)
        
        # Calculate quality score based on multiple factors
        quality_score = self._calculate_question_quality(question)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(question)
        
        # Calculate technical relevance
        tech_score = self._calculate_technical_relevance(question)
        
        # Final score (weighted average with improved calculation)
        final_score = (quality_score * 0.5 + complexity_score * 0.25 + tech_score * 0.25)
        # Ensure minimum score for valid questions
        if final_score < 30:
            final_score = 30 + (final_score * 0.7)  # Boost low scores
        
        return {
            'question': question,
            'type': q_type,
            'weight': weight,
            'quality_score': quality_score,
            'complexity_score': complexity_score,
            'technical_score': tech_score,
            'score': final_score,
            'word_count': len(question.split()),
            'char_count': len(question)
        }
    
    def _get_question_type(self, question: str) -> str:
        """Determine question type"""
        question_lower = question.lower()
        
        for q_type in self.question_weights.keys():
            if question_lower.startswith(q_type):
                return q_type
        
        return 'general'
    
    def _calculate_question_quality(self, question: str) -> float:
        """Calculate question quality score"""
        score = 0
        
        # Length appropriateness
        word_count = len(question.split())
        if 10 <= word_count <= 20:
            score += 30
        elif 6 <= word_count <= 25:
            score += 20
        else:
            score += 10
        
        # Structure quality
        if any(word in question.lower() for word in ['explain', 'describe', 'discuss']):
            score += 25
        elif any(word in question.lower() for word in ['what', 'how', 'why']):
            score += 20
        else:
            score += 15
        
        # Clarity (no ambiguous terms)
        ambiguous_terms = ['thing', 'stuff', 'something', 'anything']
        if not any(term in question.lower() for term in ambiguous_terms):
            score += 25
        else:
            score += 10
        
        # Specificity
        specific_indicators = ['specific', 'particular', 'exact', 'precise', 'detailed']
        if any(indicator in question.lower() for indicator in specific_indicators):
            score += 20
        else:
            score += 10
        
        return min(score, 100)
    
    def _calculate_complexity_score(self, question: str) -> float:
        """Calculate complexity score"""
        score = 0
        
        # Word complexity
        words = question.lower().split()
        complex_words = ['analysis', 'evaluation', 'implementation', 'optimization', 'architecture']
        complex_count = sum(1 for word in words if any(complex in word for complex in complex_words))
        score += min(complex_count * 15, 30)
        
        # Sentence structure
        if 'and' in question.lower() or 'or' in question.lower():
            score += 20  # Compound sentence
        else:
            score += 10  # Simple sentence
        
        # Technical terms
        tech_terms = sum(1 for domain, terms in self.technical_keywords.items() 
                       for term in terms if term in question.lower())
        score += min(tech_terms * 10, 30)
        
        # Question depth
        depth_indicators = ['why', 'how', 'explain', 'analyze', 'evaluate']
        if any(indicator in question.lower() for indicator in depth_indicators):
            score += 20
        else:
            score += 10
        
        return min(score, 100)
    
    def _calculate_technical_relevance(self, question: str) -> float:
        """Calculate technical relevance score"""
        score = 0
        question_lower = question.lower()
        
        # Check against all technical domains
        for domain, keywords in self.technical_keywords.items():
            domain_score = 0
            for keyword in keywords:
                if keyword in question_lower:
                    domain_score += 20
            score = max(score, domain_score)
        
        # General technical indicators
        tech_indicators = ['algorithm', 'data', 'system', 'process', 'method', 'technique']
        tech_count = sum(1 for indicator in tech_indicators if indicator in question_lower)
        score += min(tech_count * 10, 40)
        
        return min(score, 100)
    
    def _get_score_category(self, score: float) -> Tuple[str, float]:
        """Get score category and adjusted score based on score range rules"""
        for category, rules in self.score_rules.items():
            min_score, max_score = rules['range']
            if min_score <= score <= max_score:
                # If custom rules provide a marks_percentage, use it as the adjusted score
                adjusted_score = rules.get('marks_percentage', score)
                return category, adjusted_score
        return 'average', score  # Default to average instead of poor
    
    def _analyze_content(self, text: str) -> Dict:
        """Analyze content characteristics"""
        # Domain detection
        domain_scores = {}
        for domain, keywords in self.technical_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text.lower())
            domain_scores[domain] = score
        
        # Identify main domain
        main_domain = max(domain_scores.items(), key=lambda x: x[1])[0] if domain_scores else 'general'
        
        return {
            'main_domain': main_domain,
            'domain_scores': domain_scores,
            'technical_density': sum(domain_scores.values()) / len(text.split()) if text.split() else 0
        }
    
    def _analyze_complexity(self, text: str) -> Dict:
        """Analyze text complexity"""
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Vocabulary diversity
        unique_words = len(set(words))
        vocab_diversity = unique_words / len(words) if words else 0
        
        # Technical terms ratio
        tech_terms = set()
        for domain_keywords in self.technical_keywords.values():
            tech_terms.update(domain_keywords)
        
        tech_count = sum(1 for word in words if word.lower() in tech_terms)
        tech_ratio = tech_count / len(words) if words else 0
        
        return {
            'avg_sentence_length': avg_sentence_length,
            'vocab_diversity': vocab_diversity,
            'technical_terms_ratio': tech_ratio,
            'complexity_level': self._get_complexity_level(avg_sentence_length, vocab_diversity, tech_ratio)
        }
    
    def _get_complexity_level(self, avg_length: float, vocab_diversity: float, tech_ratio: float) -> str:
        """Determine complexity level"""
        complexity_score = (avg_length * 2 + vocab_diversity * 30 + tech_ratio * 50)
        
        if complexity_score >= 70:
            return 'high'
        elif complexity_score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def _get_text_statistics(self, text: str) -> Dict:
        """Get basic text statistics"""
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        
        return {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0
        }
    
    def _generate_recommendations(self, score: float, questions: List[str]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if score < 40:
            recommendations.append("Add more specific and detailed questions")
            recommendations.append("Include technical terms relevant to the subject")
        elif score < 60:
            recommendations.append("Improve question clarity and structure")
            recommendations.append("Add more analytical and evaluative questions")
        elif score < 80:
            recommendations.append("Include more complex problem-solving questions")
            recommendations.append("Add questions that require critical thinking")
        else:
            recommendations.append("Excellent question set! Maintain this quality")
            recommendations.append("Consider adding real-world application questions")
        
        return recommendations
    
    def _get_empty_analysis(self) -> Dict:
        """Get empty analysis result"""
        return {
            'overall_score': 0,
            'score_category': 'poor',
            'total_questions': 0,
            'question_analysis': [],
            'content_analysis': {'main_domain': 'general', 'domain_scores': {}, 'technical_density': 0},
            'complexity_analysis': {'avg_sentence_length': 0, 'vocab_diversity': 0, 'technical_terms_ratio': 0, 'complexity_level': 'low'},
            'text_statistics': {'char_count': 0, 'word_count': 0, 'sentence_count': 0, 'avg_word_length': 0},
            'recommendations': ['No content to analyze']
        }

# Global instance
enhanced_nlp = EnhancedNLPEngine()
