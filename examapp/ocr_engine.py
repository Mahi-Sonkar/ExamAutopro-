"""
OCR Engine - Tab 3 Implementation
Handles PDF text extraction using multiple OCR methods
"""

import os
import tempfile
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not available")

try:
    import pytesseract
    import cv2
    import numpy as np
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract not available")

try:
    from google.cloud import vision
    import io
    from pdf_analysis.google_vision_engine import google_vision
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    logger.warning("Google Vision not available")

try:
    import pdf2image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("pdf2image not available")


class OCREngine:
    """Main OCR Engine class with multiple extraction methods"""
    
    def __init__(self):
        self.method = "auto"  # auto, pymupdf, tesseract, vision
        
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF using available OCR methods
        Returns: {'text': str, 'method': str, 'confidence': float}
        """
        
        # Try PyMuPDF first (fastest)
        if PYMUPDF_AVAILABLE and self.method in ["auto", "pymupdf"]:
            result = self._extract_with_pymupdf(pdf_path)
            if result['text'] and len(result['text'].strip()) > 50:
                return result
        
        # Try Google Vision API
        if VISION_AVAILABLE and self.method in ["auto", "vision"]:
            result = self._extract_with_vision(pdf_path)
            if result['text'] and len(result['text'].strip()) > 50:
                return result
        
        # Try Tesseract OCR
        if TESSERACT_AVAILABLE and self.method in ["auto", "tesseract"]:
            result = self._extract_with_tesseract(pdf_path)
            if result['text'] and len(result['text'].strip()) > 50:
                return result
        
        return {
            'text': '',
            'method': 'none',
            'confidence': 0.0,
            'error': 'All OCR methods failed'
        }
    
    def _extract_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text using PyMuPDF (fastest method)"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            
            return {
                'text': text.strip(),
                'method': 'PyMuPDF',
                'confidence': 0.95,
                'pages': len(doc)
            }
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return {'text': '', 'method': 'PyMuPDF', 'confidence': 0.0, 'error': str(e)}
    
    def _extract_with_vision(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text using Google Vision API (Handwriting Optimized)"""
        try:
            if not VISION_AVAILABLE:
                return {'text': '', 'method': 'Vision', 'confidence': 0.0, 'error': 'Vision libraries not available'}
            
            # Use the specialized GoogleVisionEngine for best results (handles document_text_detection)
            if google_vision.is_active():
                logger.info(f"Using GoogleVisionEngine for {pdf_path}")
                result = google_vision.extract_text_from_pdf(pdf_path)
                return {
                    'text': result.get('text', ''),
                    'method': 'Google Vision (Handwriting)',
                    'confidence': result.get('confidence', 0.98),
                    'pages': result.get('page_count', 0)
                }
            
            # Fallback if google_vision is not active but VISION_AVAILABLE (e.g. key missing)
            if not PDF2IMAGE_AVAILABLE:
                return {'text': '', 'method': 'Vision', 'confidence': 0.0, 'error': 'pdf2image not available'}
            
            # Convert PDF to images
            images = pdf2image.convert_from_path(pdf_path)
            full_text = ""
            
            # Try default initialization
            client = vision.ImageAnnotatorClient()
            
            for i, img in enumerate(images):
                # Save image temporarily
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
                    img.save(temp_img.name, "PNG")
                    
                    # Extract text from image
                    with io.open(temp_img.name, 'rb') as image_file:
                        content = image_file.read()
                    
                    image = vision.Image(content=content)
                    # Use document_text_detection for better handwriting support
                    response = client.document_text_detection(image=image)
                    
                    if response.full_text_annotation:
                        full_text += response.full_text_annotation.text + "\n"
                    
                    # Clean up
                    os.unlink(temp_img.name)
            
            return {
                'text': full_text.strip(),
                'method': 'Google Vision',
                'confidence': 0.98,
                'pages': len(images)
            }
            
        except Exception as e:
            logger.error(f"Google Vision extraction failed: {e}")
            return {'text': '', 'method': 'Vision', 'confidence': 0.0, 'error': str(e)}
    
    def _extract_with_tesseract(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text using Tesseract OCR"""
        try:
            if not PDF2IMAGE_AVAILABLE:
                return {'text': '', 'method': 'Tesseract', 'confidence': 0.0, 'error': 'pdf2image not available'}
            
            # Convert PDF to images
            images = pdf2image.convert_from_path(pdf_path)
            full_text = ""
            
            for i, img in enumerate(images):
                # Convert to OpenCV format
                img_array = np.array(img)
                
                # Preprocessing
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                
                # Extract text
                text = pytesseract.image_to_string(gray)
                full_text += text + "\n"
            
            return {
                'text': full_text.strip(),
                'method': 'Tesseract',
                'confidence': 0.85,
                'pages': len(images)
            }
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return {'text': '', 'method': 'Tesseract', 'confidence': 0.0, 'error': str(e)}
    
    def get_available_methods(self) -> list:
        """Get list of available OCR methods"""
        methods = []
        if PYMUPDF_AVAILABLE:
            methods.append('PyMuPDF')
        if VISION_AVAILABLE:
            methods.append('Google Vision')
        if TESSERACT_AVAILABLE:
            methods.append('Tesseract')
        return methods
    
    def set_method(self, method: str):
        """Set preferred OCR method"""
        if method in ['auto', 'pymupdf', 'tesseract', 'vision']:
            self.method = method
        else:
            raise ValueError(f"Invalid method: {method}")


# Singleton instance
ocr_engine = OCREngine()


def extract_text_from_pdf(pdf_path: str, method: str = "auto") -> Dict[str, Any]:
    """
    Convenience function to extract text from PDF
    """
    ocr_engine.set_method(method)
    return ocr_engine.extract_text_from_pdf(pdf_path)


def extract_text_from_pdf_bytes(pdf_bytes: bytes, method: str = "auto") -> Dict[str, Any]:
    """
    Extract text from PDF bytes
    """
    try:
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name
        
        # Extract text
        result = extract_text_from_pdf(temp_pdf_path, method)
        
        # Clean up
        os.unlink(temp_pdf_path)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF bytes: {e}")
        return {'text': '', 'method': 'none', 'confidence': 0.0, 'error': str(e)}


if __name__ == "__main__":
    # Test OCR engine
    print("Available OCR methods:", ocr_engine.get_available_methods())
    
    # Test with a sample PDF path (if exists)
    test_pdf = "sample.pdf"
    if os.path.exists(test_pdf):
        result = extract_text_from_pdf(test_pdf)
        print(f"Extraction result: {result}")
    else:
        print(f"Test file {test_pdf} not found")
