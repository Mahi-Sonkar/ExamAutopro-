"""
Advanced Question Extraction Module
Extracts only actual exam questions from text with high precision
"""

import re
import logging
from typing import List, Set
from collections import OrderedDict

logger = logging.getLogger(__name__)

class QuestionExtractor:
    """Extract only actual exam questions from given text"""
    
    def __init__(self):
        # Question start words (case-insensitive)
        self.question_starters = [
            'what', 'where', 'when', 'why', 'how', 'who', 'which', 'whose', 'whom',
            'explain', 'define', 'describe', 'discuss', 'compare', 'contrast', 
            'analyze', 'evaluate', 'calculate', 'state', 'show', 'prove', 'list',
            'differentiate', 'illustrate', 'summarize', 'outline', 'demonstrate'
        ]
        
        # Question patterns
        self.question_patterns = [
            # Direct questions ending with ?
            r'(?i)^(?:' + '|'.join(self.question_starters) + r')\b.*?\?$',
            
            # Questions with question marks anywhere
            r'(?i)\b(?:' + '|'.join(self.question_starters) + r')\b[^.!?]*\?$',
            
            # Numbered questions
            r'(?i)^\d+[\.\)]\s*(?:' + '|'.join(self.question_starters) + r')\b.*?\?$',
            
            # Lettered questions  
            r'(?i)^[A-E][\.\)]\s*(?:' + '|'.join(self.question_starters) + r')\b.*?\?$',
            
            # Questions starting with Q/Question
            r'(?i)^(?:Q|Question)\s*\d*[\.\)]\s*(?:' + '|'.join(self.question_starters) + r')\b.*?\?$',
            
            # True/False questions
            r'(?i)^(?:true|false)\s*:?\s*.*?\?$',
            
            # Fill in the blanks (with ?)
            r'(?i)fill\s+in\s+the\s+blanks?.*?\?$',
            
            # Multiple choice questions
            r'(?i)choose\s+the\s+correct\s+option.*?\?$',
            
            # Any sentence ending with ?
            r'.*?\?$',
        ]
        
        # Noise patterns to exclude
        self.noise_patterns = [
            r'^\s*\d+\.\s*$',  # Just numbers
            r'^\s*[A-E]\)\s*$',  # Just letters
            r'^\s*$',  # Empty lines
            r'^\s*[\d\s\.\-\)]+$',  # Just numbering
            r'^\s*[a-zA-Z\s\.\-\)]+$',  # Just letters
            r'^\s*\d+\s*marks?\s*$',  # Marks indication
            r'^\s*\d+\s*points?\s*$',  # Points indication
        ]
        
        # OCR noise patterns
        self.ocr_noise = [
            r'[^\w\s\?\.\,\!\:\;\-\(\)\/]',  # Special characters
            r'\s+',  # Multiple spaces
            r'^\s*\d+\s*$',  # Isolated numbers
            r'^\s*[A-Za-z]\s*$',  # Isolated letters
        ]
    
    def extract_questions(self, text: str) -> str:
        """
        Extract only actual exam questions from the given text
        
        Args:
            text: Input text containing questions and other content
            
        Returns:
            String containing only valid questions, one per line
            or 'No questions detected' if no questions found
        """
        if not text or not text.strip():
            return 'No questions detected'
        
        # Clean the text
        cleaned_text = self._clean_text(text)
        
        # Split into sentences for better extraction
        sentences = self._split_into_sentences(cleaned_text)
        
        # Extract questions using patterns
        questions = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if sentence matches question patterns
            if self._is_question(sentence):
                questions.append(sentence)
        
        # Remove duplicates while preserving order
        unique_questions = list(OrderedDict.fromkeys(questions))
        
        # Return result
        if unique_questions:
            return '\n'.join(unique_questions)
        else:
            return 'No questions detected'
    
    def _split_into_sentences(self, text: str) -> list:
        """Split text into sentences for better question extraction"""
        # Split on . and ! but preserve ? for questions
        # First split on . and !
        parts = re.split(r'[.!]+\s*', text)
        sentences = []
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Check if part contains questions
            if '?' in part:
                # Split on ? but keep the ?
                question_parts = re.split(r'\?', part)
                for i, q_part in enumerate(question_parts):
                    q_part = q_part.strip()
                    if q_part:
                        if i < len(question_parts) - 1:  # Not the last part
                            sentences.append(q_part + '?')
                        else:
                            sentences.append(q_part)
            else:
                sentences.append(part)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing OCR noise and formatting issues"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove OCR noise
        for pattern in self.ocr_noise:
            text = re.sub(pattern, ' ', text)
        
        # Fix common OCR errors
        text = text.replace('rn', 'm')  # Common OCR error
        text = text.replace('cl', 'd')  # Common OCR error
        text = text.replace('vv', 'w')  # Common OCR error
        
        return text.strip()
    
    def _is_question(self, line: str) -> bool:
        """Check if a line is a valid question"""
        line = line.strip()
        
        # Skip if too short or too long
        if len(line) < 5 or len(line) > 500:
            return False
        
        # Skip noise patterns
        for pattern in self.noise_patterns:
            if re.match(pattern, line):
                return False
        
        # Check if it matches question patterns
        for pattern in self.question_patterns:
            if re.match(pattern, line):
                return True
        
        # Additional checks
        return self._additional_checks(line)
    
    def _additional_checks(self, line: str) -> bool:
        """Additional validation checks for questions"""
        # Must end with question mark
        if not line.endswith('?'):
            return False
        
        # Must start with question word or have question structure
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
        if any(marker in line.lower() for marker in ['?', 'what', 'why', 'how', 'when', 'where', 'who']):
            return True
        
        return False
    
    def get_question_count(self, text: str) -> int:
        """Get count of extracted questions"""
        questions = self.extract_questions(text)
        if questions == 'No questions detected':
            return 0
        return len(questions.split('\n'))
    
    def get_question_types(self, text: str) -> dict:
        """Get types of questions found"""
        questions = self.extract_questions(text)
        if questions == 'No questions detected':
            return {}
        
        question_types = {
            'what': 0, 'why': 0, 'how': 0, 'when': 0, 'where': 0, 'who': 0,
            'explain': 0, 'define': 0, 'describe': 0, 'discuss': 0,
            'compare': 0, 'analyze': 0, 'evaluate': 0, 'other': 0
        }
        
        for question in questions.split('\n'):
            words = question.lower().split()
            categorized = False
            
            for word in words:
                if word in question_types:
                    question_types[word] += 1
                    categorized = True
                    break
            
            if not categorized:
                question_types['other'] += 1
        
        return {k: v for k, v in question_types.items() if v > 0}

# Global instance
question_extractor = QuestionExtractor()

def extract_questions_from_text(text: str) -> str:
    """
    Convenience function to extract questions from text
    
    Args:
        text: Input text
        
    Returns:
        Extracted questions or 'No questions detected'
    """
    return question_extractor.extract_questions(text)
