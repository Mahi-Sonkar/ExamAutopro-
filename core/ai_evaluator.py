"""
AI Evaluator - Complete Backend Solution
PDF Upload → OCR → NLP → Marks → Result
"""

import os
import re
import logging
from typing import Dict, List, Tuple

# Import required libraries
try:
    import pytesseract
    from pdf2image import convert_from_path
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install: pip install pytesseract pdf2image sentence-transformers scikit-learn numpy")
    # Fallback to basic implementation
    pytesseract = None
    convert_from_path = None
    SentenceTransformer = None
    cosine_similarity = None
    np = None

logger = logging.getLogger(__name__)

class AIEvaluator:
    """Complete AI Evaluator for PDF Analysis"""
    
    def __init__(self):
        """Initialize AI models and settings"""
        self.model = None
        self.setup_tesseract()
        self.setup_nlp_model()
    
    def setup_tesseract(self):
        """Setup Tesseract OCR path"""
        if pytesseract:
            # Common Tesseract paths
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                "/usr/bin/tesseract",  # Linux
                "/usr/local/bin/tesseract"  # macOS
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    logger.info(f"Tesseract path set to: {path}")
                    break
            else:
                logger.warning("Tesseract not found in common paths")
    
    def setup_nlp_model(self):
        """Setup NLP model for semantic similarity"""
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("NLP model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load NLP model: {e}")
                self.model = None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR"""
        try:
            if not convert_from_path:
                return "OCR not available - please install pdf2image"
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=200, fmt='jpeg')
            
            full_text = ""
            for i, img in enumerate(images):
                try:
                    if pytesseract:
                        text = pytesseract.image_to_string(img, config='--oem 3 --psm 6')
                        full_text += f"Page {i+1}:\n{text}\n\n"
                    else:
                        full_text += f"Page {i+1}: OCR not available\n\n"
                except Exception as e:
                    logger.error(f"OCR failed for page {i+1}: {e}")
                    full_text += f"Page {i+1}: OCR Error\n\n"
            
            return self.preprocess_ocr_text(full_text)
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return f"Error extracting PDF: {str(e)}"
    
    def preprocess_ocr_text(self, text: str) -> str:
        """Preprocess OCR text to fix common errors"""
        if not text:
            return ""
        
        # Remove OCR artifacts
        text = re.sub(r'[^\w\s\.\?\!\,\;\:\-\n]', ' ', text)
        
        # Fix common OCR errors
        ocr_corrections = {
            'rn': 'm', 'cl': 'd', 'vv': 'w', '|': 'l',
            '0': 'o', '1': 'l', '5': 's', '8': 'B', '9': 'g'
        }
        
        for wrong, correct in ocr_corrections.items():
            text = text.replace(wrong, correct)
        
        # Normalize question numbering
        text = re.sub(r'Q\s*([0-9]+)\s*[\.\:\-]', r'Q\1. ', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def segment_answers(self, text: str) -> Dict[str, str]:
        """Segment answers by question numbers"""
        answers = {}
        
        # Multiple patterns for answer segmentation
        patterns = [
            r'Q\s*([0-9]+)\s*[\.\:\-]\s*(.*?)(?=Q\s*[0-9]+[\.\:\-]|$)',
            r'([0-9]+)\s*[\.\:\-]\s*(.*?)(?=[0-9]+[\.\:\-]|$)',
            r'Question\s*([0-9]+)\s*[\.\:\-]\s*(.*?)(?=Question\s*[0-9]+[\.\:\-]|$)',
            r'Ans\s*([0-9]+)\s*[\.\:\-]\s*(.*?)(?=Ans\s*[0-9]+[\.\:\-]|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        q_num = int(match[0])
                        answer = match[1].strip()
                    else:
                        q_num = int(re.findall(r'[0-9]+', match)[0])
                        answer = re.sub(r'[0-9]+[\.\:\-]\s*', '', match).strip()
                    
                    if len(answer) > 10:  # Filter out very short answers
                        answers[f"Q{q_num}"] = answer
                
                if answers:
                    break
        
        # Fallback: split by paragraphs if no pattern matches
        if not answers:
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 20]
            for i, para in enumerate(paragraphs[:5]):  # Limit to first 5 paragraphs
                answers[f"Q{i+1}"] = para
        
        return answers
    
    def calculate_similarity(self, student_answer: str, model_answer: str) -> float:
        """Calculate semantic similarity between answers"""
        if not self.model or not cosine_similarity:
            # Fallback to simple text similarity
            return self.simple_text_similarity(student_answer, model_answer)
        
        try:
            # Encode both answers
            student_embedding = self.model.encode([student_answer])
            model_embedding = self.model.encode([model_answer])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(student_embedding, model_embedding)[0][0]
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return self.simple_text_similarity(student_answer, model_answer)
    
    def simple_text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity as fallback"""
        if not text1 or not text2:
            return 0.0
        
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def evaluate_answers(self, student_text: str, answer_key: Dict[str, str]) -> Dict:
        """Evaluate student answers against answer key"""
        # Segment student answers
        student_answers = self.segment_answers(student_text)
        
        results = {}
        total_marks = 0
        max_marks = 0
        
        for q_key, model_answer in answer_key.items():
            student_answer = student_answers.get(q_key, "")
            
            # Calculate similarity
            similarity = self.calculate_similarity(student_answer, model_answer)
            
            # Calculate marks (out of 10)
            marks = round(similarity * 10, 2)
            
            results[q_key] = {
                "student_answer": student_answer[:200] + "..." if len(student_answer) > 200 else student_answer,
                "model_answer": model_answer,
                "similarity": round(similarity, 3),
                "marks": marks,
                "max_marks": 10
            }
            
            total_marks += marks
            max_marks += 10
        
        return {
            "results": results,
            "total_marks": total_marks,
            "max_marks": max_marks,
            "percentage": round((total_marks / max_marks) * 100, 1) if max_marks > 0 else 0,
            "answers_found": len(student_answers),
            "total_questions": len(answer_key)
        }

# Global instance for easy use
ai_evaluator = AIEvaluator()

# Convenience functions
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF"""
    return ai_evaluator.extract_text_from_pdf(pdf_path)

def evaluate_answers(student_text: str, answer_key: Dict[str, str]) -> Dict:
    """Evaluate answers"""
    return ai_evaluator.evaluate_answers(student_text, answer_key)

def calculate_similarity(answer1: str, answer2: str) -> float:
    """Calculate similarity between two answers"""
    return ai_evaluator.calculate_similarity(answer1, answer2)
