"""
Advanced OCR Processor with Question Extraction
STEP 8: Questions Extract Karo
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class AdvancedOCRProcessor:
    """Advanced OCR processor with intelligent question extraction"""
    
    def __init__(self):
        # Question starters for detection
        self.question_starters = [
            'what', 'where', 'when', 'why', 'how', 'who', 'which', 'whose', 'whom',
            'explain', 'define', 'describe', 'discuss', 'compare', 'contrast',
            'analyze', 'evaluate', 'calculate', 'state', 'show', 'prove', 'list',
            'differentiate', 'illustrate', 'summarize', 'outline', 'demonstrate'
        ]
    
    def extract_questions_from_text(self, text: str) -> List[str]:
        """
        STEP 8: Questions extract karo
        Extract only actual questions from OCR text
        """
        if not text or not text.strip():
            return []
        
        questions = []
        
        # Split text into lines
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a question
            if self._is_question(line):
                questions.append(line)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_questions = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                unique_questions.append(q)
        
        return unique_questions
    
    def _is_question(self, line: str) -> bool:
        """Check if a line is a valid question"""
        # Must end with question mark
        if not line.endswith('?'):
            return False
        
        # Must start with question word or contain question indicators
        words = line.lower().split()
        if not words:
            return False
        
        # Check first word
        first_word = words[0].strip('.,!?()[]{}')
        if first_word in self.question_starters:
            return True
        
        # Check if contains question words
        for word in words:
            if word in self.question_starters:
                return True
        
        # Check for question structure
        if any(marker in line.lower() for marker in ['what', 'why', 'how', 'when', 'where', 'who']):
            return True
        
        return False
    
    def get_question_statistics(self, questions: List[str]) -> Dict:
        """Get statistics about extracted questions"""
        if not questions:
            return {
                'total_questions': 0,
                'question_types': {},
                'average_length': 0,
                'complexity_score': 0
            }
        
        # Analyze question types
        question_types = {
            'what': 0, 'why': 0, 'how': 0, 'when': 0, 'where': 0, 'who': 0,
            'explain': 0, 'define': 0, 'describe': 0, 'discuss': 0,
            'compare': 0, 'analyze': 0, 'evaluate': 0, 'other': 0
        }
        
        total_length = 0
        complexity_score = 0
        
        for question in questions:
            # Length analysis
            total_length += len(question)
            
            # Complexity based on words
            words = question.lower().split()
            if len(words) > 10:
                complexity_score += 3
            elif len(words) > 6:
                complexity_score += 2
            else:
                complexity_score += 1
            
            # Type classification
            categorized = False
            for word in words:
                if word in question_types:
                    question_types[word] += 1
                    categorized = True
                    break
            
            if not categorized:
                question_types['other'] += 1
        
        # Remove empty types
        question_types = {k: v for k, v in question_types.items() if v > 0}
        
        return {
            'total_questions': len(questions),
            'question_types': question_types,
            'average_length': total_length / len(questions),
            'complexity_score': complexity_score / len(questions)
        }

# Global instance
advanced_ocr_processor = AdvancedOCRProcessor()
