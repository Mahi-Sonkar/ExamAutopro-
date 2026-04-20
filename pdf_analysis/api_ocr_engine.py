"""
Local OCR Engine using Pytesseract and OpenCV
"""

import os
import cv2
import numpy as np
from PIL import Image
import io
import pytesseract
import re

class LocalOCREngine:
    def __init__(self):
        # For Windows, you might need to set the tesseract path:
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
        
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF using Local OCR (Pytesseract + OpenCV)"""
        try:
            # 1. Try to extract text directly from PDF first
            text = self._extract_text_from_pdf_direct(pdf_path)
            
            page_count = self._get_page_count(pdf_path)
            words = text.split()
            
            # Smart scanned detection
            is_scanned = not text or len(text.strip()) < 50 or (len(words) / max(1, page_count)) < 5
            
            if not is_scanned:
                return {
                    'text': text.strip(),
                    'confidence': 95.0,
                    'page_count': page_count,
                    'method': 'direct_extraction'
                }
            
            # 2. Local OCR for scanned PDFs
            print(f"Scanned PDF detected. Triggering Local OCR (Pytesseract) for {pdf_path}")
            return self._extract_text_via_local_ocr(pdf_path)
            
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return self._get_fallback_result()

    def _extract_text_via_local_ocr(self, pdf_path):
        """Extract text using Local Pytesseract with OpenCV preprocessing"""
        try:
            images = self._pdf_to_images(pdf_path)
            all_text = ""
            
            for image in images:
                # Preprocess for better accuracy
                processed_image = self._preprocess_image(image)
                
                # Perform Local OCR
                text = pytesseract.image_to_string(processed_image)
                all_text += text + "\n"
            
            final_text = self._enhance_text(all_text.strip())
            
            return {
                'text': final_text,
                'confidence': 85.0,
                'page_count': len(images),
                'method': 'local_pytesseract'
            }
        except Exception as e:
            print(f"Local OCR Error: {str(e)}")
            return self._get_fallback_result()

    def _extract_text_from_pdf_direct(self, pdf_path):
        """Extract text directly from PDF using PyMuPDF (fitz)"""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"Direct extraction error: {str(e)}")
            return ""

    def _preprocess_image(self, image):
        """Advanced image preprocessing optimized for Handwritten/Scanned PDFs"""
        try:
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_array

            # Noise Reduction
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            
            # Deskewing
            coords = np.column_stack(np.where(denoised < 255))
            if coords.size > 0:
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45: angle = -(90 + angle)
                else: angle = -angle
                (h, w) = denoised.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                denoised = cv2.warpAffine(denoised, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

            # Contrast enhancement (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Adaptive Thresholding
            thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 15, 5)
            
            return Image.fromarray(thresh)
        except Exception as e:
            print(f"Preprocessing error: {str(e)}")
            return image

    def _enhance_text(self, text):
        """Clean OCR output"""
        if not text: return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _pdf_to_images(self, pdf_path):
        """Convert PDF to images using PyMuPDF"""
        try:
            import fitz
            images = []
            doc = fitz.open(pdf_path)
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            doc.close()
            return images
        except:
            return []

    def _get_page_count(self, pdf_path):
        try:
            import fitz
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except:
            return 1

    def _get_fallback_result(self):
        return {
            'text': "Fallback text for analysis.",
            'confidence': 70.0,
            'page_count': 1,
            'method': 'fallback'
        }

# Create instance compatible with existing code
api_ocr = LocalOCREngine()
