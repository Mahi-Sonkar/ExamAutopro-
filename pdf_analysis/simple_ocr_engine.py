"""
Simple OCR Engine - Pytesseract + OpenCV Pipeline
PDF -> Image -> OCR -> Clean Text
"""

import fitz  # PyMuPDF
import io
import re
import pytesseract
from PIL import Image

class SimpleOCREngine:
    def __init__(self):
        # Automatically find tesseract path on Windows
        self._find_tesseract()
        
    def _find_tesseract(self):
        """Try to find tesseract executable in common Windows paths"""
        import os
        import platform
        
        if platform.system() == "Windows":
            common_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'D:\Tesseract-OCR\tesseract.exe',
                os.path.expanduser(r'~\AppData\Local\Tesseract-OCR\tesseract.exe')
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"DEBUG: Found Tesseract at {path}")
                    return True
            
            print("DEBUG: Tesseract not found in common paths. Please install it.")
        return False
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Simple Pipeline: PDF -> Image -> OCR -> Clean Text
        """
        try:
            print(f"Starting Simple OCR Pipeline for: {pdf_path}")
            
            # Step 1: PDF -> Images
            images = self._pdf_to_images(pdf_path)
            print(f"Converted PDF to {len(images)} images")
            
            # Step 2: Images -> OCR -> Clean Text
            all_text = ""
            for i, image in enumerate(images):
                print(f"Processing page {i+1}/{len(images)}")
                
                # Preprocess with OpenCV
                processed_image = self._preprocess_image(image)
                
                # Extract text with Pytesseract
                text = pytesseract.image_to_string(processed_image)
                
                # Clean text
                clean_text = self._clean_text(text)
                
                all_text += clean_text + "\n"
            
            final_text = self._final_cleanup(all_text)
            
            return {
                'text': final_text,
                'confidence': 85.0,
                'page_count': len(images),
                'method': 'simple_pipeline'
            }
            
        except Exception as e:
            print(f"Simple OCR Error: {str(e)}")
            return self._get_fallback_result(str(e))
    
    def _pdf_to_images(self, pdf_path):
        """Convert PDF to images using PyMuPDF"""
        try:
            images = []
            doc = fitz.open(pdf_path)
            
            for page in doc:
                # Convert page to image at 2x resolution
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                images.append(image)
            
            doc.close()
            return images
            
        except Exception as e:
            print(f"PDF to Image Error: {str(e)}")
            return []
    
    def _preprocess_image(self, image):
        """OpenCV preprocessing for better OCR accuracy"""
        try:
            import cv2
            import numpy as np
            
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_array
            
            # Noise reduction
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            
            # Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 15, 5
            )
            
            # Convert back to PIL
            return Image.fromarray(thresh)
            
        except Exception as e:
            print(f"Preprocessing Error: {str(e)}")
            return image
    
    def _clean_text(self, text):
        """Basic text cleaning"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common OCR errors
        text = re.sub(r'[^\w\s\.\,\?\!\;\:\-\(\)]', '', text)
        
        return text.strip()
    
    def _final_cleanup(self, text):
        """Final cleanup of complete text"""
        if not text:
            return ""
        
        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)
        
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        
        # Fix common issues
        text = text.replace('. ', '.\n')
        text = text.replace('? ', '?\n')
        text = text.replace('! ', '!\n')
        
        return text.strip()
    
    def _get_fallback_result(self, error_msg="Unknown error"):
        """Fallback result for errors - Hindi-English Mixed Instructions"""
        if "tesseract is not installed" in error_msg.lower() or "not recognized" in error_msg.lower():
            text = (
                "❌ Error: Tesseract OCR is not installed or not in your system path.\n\n"
                "👉 Solution (How to fix):\n"
                "1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "2. Install it in 'C:\\Program Files\\Tesseract-OCR'.\n"
                "3. If you install it elsewhere, update the path in 'simple_ocr_engine.py'.\n"
                "4. Restart your Django server.\n\n"
                "Hindi: Aapke system par Tesseract installed nahi hai. Kripya upar diye gaye link se install karein."
            )
        else:
            text = f"OCR processing failed. Error details: {error_msg}"
            
        return {
            'text': text,
            'confidence': 0.0,
            'page_count': 0,
            'method': 'error_fallback'
        }

# Create instance
simple_ocr = SimpleOCREngine()
