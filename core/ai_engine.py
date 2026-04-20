"""
FIXED AI ENGINE - Robust Backend Logic
PDF → Text Extraction → Smart Splitting → NLP → Accurate Marks
"""

import os
import re
import logging
import sys
from typing import Dict, List, Optional, Tuple

# Ensure global site-packages is available in this portable Python setup.
base_lib_site_packages = os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages')
if os.path.isdir(base_lib_site_packages) and base_lib_site_packages not in sys.path:
    sys.path.append(base_lib_site_packages)

# Import with per-library fallback (one failure should not disable all)
try:
    import pytesseract
except Exception as e:
    print(f"Import error (pytesseract): {e}")
    pytesseract = None

try:
    from pdf2image import convert_from_path
except Exception as e:
    print(f"Import error (pdf2image): {e}")
    convert_from_path = None

try:
    from PyPDF2 import PdfReader
except Exception as e:
    print(f"Import error (PyPDF2): {e}")
    PdfReader = None

try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    print(f"Import error (sentence_transformers): {e}")
    SentenceTransformer = None

try:
    from sklearn.metrics.pairwise import cosine_similarity
except Exception as e:
    print(f"Import error (sklearn cosine_similarity): {e}")
    cosine_similarity = None

try:
    import numpy as np
except Exception as e:
    print(f"Import error (numpy): {e}")
    np = None

try:
    from google.cloud import vision
except Exception as e:
    print(f"Import error (google vision): {e}")
    vision = None

logger = logging.getLogger(__name__)

class FixedAIEngine:
    """Fixed AI Engine with Robust Logic"""
    
    def __init__(self):
        self.model = None
        self.vision_client = None
        self.setup_complete = False
        self.initialize_components()
    
    def initialize_components(self):
        """Initialize all components with error handling"""
        try:
            # Initialize NLP model
            if SentenceTransformer:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("NLP model loaded successfully")

            # Initialize Google Vision client when credentials are available
            if vision and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                try:
                    self.vision_client = vision.ImageAnnotatorClient()
                    logger.info("Google Vision client initialized")
                except Exception as vision_err:
                    logger.warning("Google Vision client init failed: %s", vision_err)
            
            # Setup Tesseract path
            if pytesseract:
                tesseract_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
                ]
                for path in tesseract_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"Tesseract path: {path}")
                        break
            
            self.setup_complete = True
            logger.info("AI Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"AI Engine initialization failed: {e}")
            self.setup_complete = False

    def extract_text_google_vision(self, pdf_path: str) -> str:
        """
        Handwriting-friendly OCR via Google Vision DOCUMENT_TEXT_DETECTION.
        Requires GOOGLE_APPLICATION_CREDENTIALS and google-cloud-vision package.
        """
        if not self.vision_client or not convert_from_path:
            return ""

        text = ""
        try:
            images = convert_from_path(pdf_path, dpi=300, fmt='jpeg')
            for i, img in enumerate(images):
                try:
                    import io
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG')
                    image_bytes = buffer.getvalue()
                    image = vision.Image(content=image_bytes)
                    response = self.vision_client.document_text_detection(image=image)
                    if response.error and response.error.message:
                        logger.warning("Google Vision OCR error page %s: %s", i + 1, response.error.message)
                        continue
                    page_text = (response.full_text_annotation.text or "").strip()
                    if page_text:
                        text += f"Page {i+1}:\n{page_text}\n\n"
                except Exception as page_err:
                    logger.warning("Google Vision OCR failed page %s: %s", i + 1, page_err)
                    continue
        except Exception as e:
            logger.warning("Google Vision OCR failed: %s", e)
            return ""

        return text.strip()
    
    def extract_text_robust(self, pdf_path: str) -> str:
        """
        ✅ FIXED TEXT EXTRACTION
        Multiple methods with intelligent fallback
        """
        text = ""
        
        # Method 1: Direct PyPDF2 extraction (most reliable)
        try:
            if PdfReader:
                reader = PdfReader(pdf_path)
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) > 10:
                        text += f"Page {i+1}:\n{page_text}\n\n"
                
                if len(text.strip()) > 100:
                    logger.info(f"Direct extraction successful: {len(text)} chars")
                    return text.strip()
        except Exception as e:
            logger.error(f"Direct extraction failed: {e}")

        # Method 2: Google Vision OCR (best for handwriting)
        try:
            vision_text = self.extract_text_google_vision(pdf_path)
            if len(vision_text) > 60:
                logger.info("Google Vision extraction successful: %s chars", len(vision_text))
                return vision_text
        except Exception as e:
            logger.error(f"Google Vision extraction failed: {e}")

        # Method 3: Tesseract OCR with better error handling
        try:
            if convert_from_path and pytesseract:
                logger.info("Switching to OCR extraction...")
                images = convert_from_path(pdf_path, dpi=200, fmt='jpeg')
                
                for i, img in enumerate(images):
                    try:
                        # Better OCR configuration
                        ocr_text = pytesseract.image_to_string(
                            img, 
                            config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:?!- '
                        )
                        if ocr_text and len(ocr_text.strip()) > 10:
                            text += f"Page {i+1}:\n{ocr_text}\n\n"
                    except Exception as e:
                        logger.error(f"OCR failed page {i+1}: {e}")
                        continue
                
                if len(text.strip()) > 100:
                    logger.info(f"OCR extraction successful: {len(text)} chars")
                    return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")

        # Method 4: Last resort - return what we have
        logger.warning("Using minimal text extraction")
        return text.strip() if text.strip() else "No text extracted"
    
    def clean_text_advanced(self, text: str) -> str:
        """
        ✅ FIXED TEXT CLEANING
        Better preprocessing for similarity
        """
        if not text:
            return ""
        
        # Remove OCR artifacts
        text = re.sub(r'[^\w\s\.\?\!\,\;\:\-\(\)\[\]\"\'\/]', ' ', text)
        
        # Fix common OCR errors
        ocr_fixes = {
            'rn': 'm', 'cl': 'd', 'vv': 'w', '|': 'l',
            '0': 'o', '1': 'l', '5': 's', '8': 'B', '9': 'g',
            'll': 'h', 'ii': 'n', 'uu': 'w'
        }
        
        for wrong, right in ocr_fixes.items():
            text = text.replace(wrong, right)
        
        # Normalize spacing and case
        text = re.sub(r'\s+', ' ', text)
        text = text.lower().strip()
        
        return text
    
    def split_answers_intelligent(self, text: str) -> List[str]:
        """
        ✅ FIXED ANSWER SPLITTING
        Multiple patterns with better matching
        """
        answers = []
        
        # Pattern 1: Standard question format (Q1, Q2, etc.)
        pattern1 = r'Q\s*(\d+)\s*[\.\:\-]\s*([^\n]*?)(?=Q\s*\d+[\.\:\-]|$)'
        matches = re.findall(pattern1, text, re.IGNORECASE | re.DOTALL)
        if matches:
            answers = [match[1].strip() for match in matches if len(match[1].strip()) > 15]
        
        # Pattern 2: Question word format
        if not answers:
            pattern2 = r'Question\s*(\d+)\s*[\.\:\-]\s*([^\n]*?)(?=Question\s*\d+[\.\:\-]|$)'
            matches = re.findall(pattern2, text, re.IGNORECASE | re.DOTALL)
            if matches:
                answers = [match[1].strip() for match in matches if len(match[1].strip()) > 15]
        
        # Pattern 3: Simple numbered format
        if not answers:
            pattern3 = r'^\s*(\d+)\s*[\.\:\-]\s*([^\n]*?)(?=^\s*\d+[\.\:\-]|$)'
            matches = re.findall(pattern3, text, re.MULTILINE | re.DOTALL)
            if matches:
                answers = [match[1].strip() for match in matches if len(match[1].strip()) > 15]
        
        # Pattern 4: Paragraph-based (last resort)
        if not answers:
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 30]
            answers = paragraphs[:6]  # Limit to first 6 paragraphs
        
        return answers

    def extract_answers_with_labels(self, text: str) -> List[Dict]:
        """
        Extract answer blocks with question labels from OCR text.
        Supports Q1/Ans: style and question-number style.
        """
        blocks: List[Dict] = []
        if not text:
            return blocks

        patterns = [
            r'(?:Q(?:uestion)?\s*(\d+)\s*[:\.\-]?\s*)(.*?)(?=(?:Q(?:uestion)?\s*\d+\s*[:\.\-]?)|$)',
            r'(?:(\d+)\s*[:\.\-]\s*)(.*?)(?=(?:\n\s*\d+\s*[:\.\-])|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            if matches:
                for q_no, answer in matches:
                    normalized = answer.strip()
                    if len(normalized) < 8:
                        continue
                    blocks.append({
                        "question": f"Q{q_no}",
                        "answer": normalized
                    })
                if blocks:
                    return blocks

        fallback_answers = self.split_answers_intelligent(text)
        for idx, answer in enumerate(fallback_answers, start=1):
            blocks.append({
                "question": f"Q{idx}",
                "answer": answer
            })
        return blocks
    
    def calculate_similarity_advanced(self, text1: str, text2: str) -> float:
        """
        ✅ FIXED SIMILARITY CALCULATION
        Multiple methods with fallback
        """
        if not text1 or not text2:
            return 0.0
        
        # Clean both texts
        text1_clean = self.clean_text_advanced(text1)
        text2_clean = self.clean_text_advanced(text2)
        
        # Method 1: Semantic similarity (best)
        if self.model and cosine_similarity:
            try:
                emb1 = self.model.encode([text1_clean])
                emb2 = self.model.encode([text2_clean])
                similarity = cosine_similarity(emb1, emb2)[0][0]
                return float(similarity)
            except Exception as e:
                logger.error(f"Semantic similarity failed: {e}")
        
        # Method 2: Jaccard similarity (good fallback)
        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def allocate_marks(self, similarity: float, max_marks: float = 10.0) -> float:
        """
        Rule-based marks allocation:
        >= 0.80 full, 0.50-0.79 partial proportional, else low partial.
        """
        if similarity >= 0.80:
            return round(max_marks, 2)
        if similarity >= 0.50:
            scaled = 0.5 + ((similarity - 0.5) / 0.3) * 0.5
            return round(max_marks * scaled, 2)
        return round(max_marks * max(similarity, 0.0) * 0.5, 2)
    
    def evaluate_comprehensive(self, pdf_path: str, answer_key: Optional[List[str]] = None) -> Dict:
        """
        ✅ FIXED COMPREHENSIVE EVALUATION
        Robust evaluation with error handling
        """
        try:
            # Step 1: Extract text
            extracted_text = self.extract_text_robust(pdf_path)
            
            if not extracted_text or len(extracted_text.strip()) < 20:
                return {
                    "success": False,
                    "error": "Insufficient text extracted from PDF",
                    "extracted_text": extracted_text
                }
            
            # Step 2: Segment student answers from extracted text
            extracted_answers = self.extract_answers_with_labels(extracted_text)
            student_answers = [item["answer"] for item in extracted_answers]

            # If no answer key provided, return extraction-only response (no fake scoring)
            if not answer_key:
                return {
                    "success": True,
                    "extracted_text": extracted_text,
                    "results": [
                        {
                            "question": item["question"],
                            "student_answer": item["answer"],
                            "correct_answer": None,
                            "similarity": None,
                            "marks": None,
                            "max_marks": 10,
                            "grade": None,
                            "has_answer": len(item["answer"].strip()) > 0
                        }
                        for item in extracted_answers
                    ],
                    "total_marks": 0,
                    "max_marks": 0,
                    "percentage": 0,
                    "answers_found": len(student_answers),
                    "total_questions": len(extracted_answers),
                    "processing_method": "ocr_nlp_extraction",
                    "engine_status": "working_no_answer_key"
                }

            # Step 3: Evaluate each answer
            results = []
            total_marks = 0
            max_marks = len(answer_key) * 10
            
            for i, correct_answer in enumerate(answer_key):
                student_answer = student_answers[i] if i < len(student_answers) else ""
                
                # Calculate similarity and marks
                similarity = self.calculate_similarity_advanced(student_answer, correct_answer)
                marks = self.allocate_marks(similarity, 10)
                total_marks += marks
                
                # Determine grade
                grade = self.get_grade(similarity)
                
                results.append({
                    "question": f"Q{i+1}",
                    "student_answer": student_answer[:150] + "..." if len(student_answer) > 150 else student_answer,
                    "correct_answer": correct_answer,
                    "similarity": round(similarity, 3),
                    "marks": marks,
                    "max_marks": 10,
                    "grade": grade,
                    "has_answer": len(student_answer.strip()) > 0
                })
            
            return {
                "success": True,
                "extracted_text": extracted_text,
                "results": results,
                "total_marks": total_marks,
                "max_marks": max_marks,
                "percentage": round((total_marks / max_marks) * 100, 1) if max_marks > 0 else 0,
                "answers_found": len([a for a in student_answers if len(a.strip()) > 0]),
                "total_questions": len(answer_key),
                "processing_method": "ocr_nlp_similarity",
                "engine_status": "fixed_and_working"
            }
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {
                "success": False,
                "error": f"Evaluation error: {str(e)}",
                "extracted_text": "Error during processing"
            }
    
    def get_grade(self, similarity: float) -> str:
        """Get grade based on similarity score"""
        if similarity >= 0.9:
            return "Excellent"
        elif similarity >= 0.7:
            return "Good"
        elif similarity >= 0.5:
            return "Average"
        else:
            return "Poor"

# Convenience functions (create new instance each call)
def extract_text_robust(pdf_path: str) -> str:
    engine = FixedAIEngine()
    return engine.extract_text_robust(pdf_path)

def split_answers_intelligent(text: str) -> List[str]:
    engine = FixedAIEngine()
    return engine.split_answers_intelligent(text)

def calculate_similarity_advanced(text1: str, text2: str) -> float:
    engine = FixedAIEngine()
    return engine.calculate_similarity_advanced(text1, text2)

def evaluate_comprehensive(pdf_path: str, answer_key: Optional[List[str]] = None) -> Dict:
    engine = FixedAIEngine()
    return engine.evaluate_comprehensive(pdf_path, answer_key)
