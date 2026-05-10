"""
Enhanced OCR Engine for Accurate Text Extraction
Perfect OCR + NLP Integration for Score Range Based Evaluation
"""

import os
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import logging
from .google_vision_engine import google_vision

logger = logging.getLogger(__name__)

class EnhancedOCREngine:
    """Enhanced OCR Engine with perfect text extraction"""
    
    def __init__(self):
        # Set Tesseract path
        tesseract_paths = [
            os.environ.get('TESSERACT_CMD', ''),
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tesseract-OCR\tesseract.exe"
        ]
        
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"Tesseract found at: {path}")
                break
    
    def extract_text_from_pdf(self, pdf_path: str) -> dict:
        """Extract text with perfect accuracy"""
        try:
            # Step 1: Try Google Vision (Best for Handwriting)
            if google_vision.is_active():
                logger.info("Using Google Vision OCR for handwritten text recognition")
                vision_result = google_vision.extract_text_from_pdf(pdf_path)
                
                # Check if we got any meaningful text
                if vision_result.get('success') and vision_result.get('text') and len(vision_result['text'].strip()) > 10:
                    logger.info("Google Vision OCR successful")
                    return {
                        'text': self._enhance_text(vision_result['text']),
                        'confidence': vision_result.get('confidence', 95.0),
                        'page_count': vision_result.get('page_count', 1),
                        'method_used': vision_result.get('method', 'vision_ocr')
                    }
                else:
                    logger.warning("Google Vision returned empty or insufficient text. Falling back to Tesseract.")
            else:
                logger.info("Google Vision is not active. Using Tesseract for OCR.")

            # Step 2: Fallback to Tesseract (Good for printed text)
            file_ext = os.path.splitext(pdf_path)[1].lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']:
                images = [Image.open(pdf_path).convert('RGB')]
            else:
                # Convert PDF to high-quality images
                images = convert_from_path(pdf_path, dpi=300, fmt='jpeg')
            
            all_text = []
            total_confidence = 0
            
            for i, image in enumerate(images):
                # Enhanced preprocessing
                processed_image = self._preprocess_image(image)
                
                # Multiple OCR attempts with different configurations
                text_results = []
                
                # Configuration 1: Standard text
                config1 = '--psm 6 --oem 3'
                text1 = pytesseract.image_to_string(processed_image, config=config1)
                text_results.append(text1)
                
                # Configuration 2: Single column
                config2 = '--psm 4 --oem 3'
                text2 = pytesseract.image_to_string(processed_image, config=config2)
                text_results.append(text2)
                
                # Configuration 3: Sparse text
                config3 = '--psm 11 --oem 3'
                text3 = pytesseract.image_to_string(processed_image, config=config3)
                text_results.append(text3)
                
                # Choose best result
                best_text = self._select_best_text(text_results)
                
                if best_text.strip():
                    all_text.append(best_text.strip())
                    
                    # Get confidence
                    data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    if confidences:
                        total_confidence += sum(confidences) / len(confidences)
            
            # Advanced text cleaning and enhancement
            final_text = self._enhance_text('\n'.join(all_text))
            
            return {
                'text': final_text,
                'confidence': total_confidence / len(images) if images else 0,
                'page_count': len(images),
                'method_used': 'enhanced_ocr'
            }
            
        except Exception as e:
            logger.error(f"Enhanced OCR failed: {str(e)}")
            return {
                'text': '',
                'confidence': 0.0,
                'page_count': 0,
                'method_used': 'ocr_failed',
                'success': False,
                'error': str(e)
            }
    
    def _preprocess_image(self, image):
        """Advanced image preprocessing for perfect OCR with scanned documents"""
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        
        # 1. Deskewing (Fix rotation)
        coords = np.column_stack(np.where(gray < 255))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        # 2. Denoising
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # 3. Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # 4. Adaptive thresholding for varied lighting
        thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # 5. Morphological operations to thicken characters and remove noise
        kernel = np.ones((1,1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 6. Bilateral Filtering to preserve edges while removing noise
        final = cv2.bilateralFilter(cleaned, 9, 75, 75)
        
        return final
    
    def _select_best_text(self, text_results):
        """Select the best OCR result"""
        best_text = ""
        best_score = 0
        
        for text in text_results:
            score = self._calculate_text_quality(text)
            if score > best_score:
                best_score = score
                best_text = text
        
        return best_text
    
    def _calculate_text_quality(self, text):
        """Calculate quality score for extracted text"""
        if not text:
            return 0
        
        score = 0
        
        # Length score
        score += min(len(text) / 1000, 1) * 30
        
        # Word count score
        words = text.split()
        score += min(len(words) / 100, 1) * 30
        
        # Question detection score
        question_count = len(re.findall(r'\?', text))
        score += min(question_count / 10, 1) * 20
        
        # Sentence structure score
        sentences = re.split(r'[.!?]+', text)
        score += min(len([s for s in sentences if len(s.strip()) > 10]) / 20, 1) * 20
        
        return score
    
    def _enhance_text(self, text):
        """Enhance and clean extracted text"""
        if not text:
            return ""
        
        # Preserve line breaks because answer/question numbering often depends on them.
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Fix common OCR errors
        ocr_fixes = {
            'rn': 'm',
            'cl': 'd',
            'vv': 'w',
            'ii': 'n',
            'tl': 'h',
            'l1': 'll',
            '0o': 'oo',
            'O0': 'OO'
        }
        
        for wrong, correct in ocr_fixes.items():
            text = text.replace(wrong, correct)
        
        # Fix punctuation
        text = re.sub(r'\s*([,.!?])\s*', r'\1 ', text)
        
        # Fix question marks
        text = re.sub(r'([a-zA-Z])\s*\?', r'\1?', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\?.\-\,\!\:\;]', ' ', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([?.!,])', r'\1', text)
        
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
        return '\n'.join(line for line in lines if line).strip()
    
# Global instance
enhanced_ocr = EnhancedOCREngine()
