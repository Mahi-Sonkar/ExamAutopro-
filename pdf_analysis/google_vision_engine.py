"""
Google Cloud Vision OCR Engine - Advanced Handwritten Recognition
Addresses Problem: Handwritten text recognition (Google Lens style)
"""

import io
import os
import re
from typing import Dict, List, Any
from google.cloud import vision
from PIL import Image
import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

class GoogleVisionEngine:
    def __init__(self):
        # Service account key ka path environment variable se ya default path se uthayega
        self.credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'credentials/google_vision_key.json')
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Google Vision Client initialize karein agar key मौजूद hai"""
        try:
            # First check if credentials path exists
            if os.path.exists(self.credentials_path):
                # JSON key file mil gayi, client set karein
                self.client = vision.ImageAnnotatorClient.from_service_account_json(self.credentials_path)
                logger.info(f"✅ Google Vision Client initialized using {self.credentials_path}")
            else:
                # If not in specific path, try environment variable (Standard GCP way)
                env_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                if env_creds and os.path.exists(env_creds):
                    self.client = vision.ImageAnnotatorClient()
                    logger.info(f"✅ Google Vision Client initialized using environment variable: {env_creds}")
                else:
                    # Key nahi mili, fallback mode active rahega
                    logger.warning(f"⚠️ Google Vision credentials NOT FOUND. Please ensure '{self.credentials_path}' exists or set GOOGLE_APPLICATION_CREDENTIALS environment variable.")
                    self.client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Vision Client: {str(e)}")
            self.client = None

    def is_active(self) -> bool:
        """Check karein ki Google Vision active hai ya nahi"""
        return self.client is not None

    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDF se handwritten text extract karein using Google Vision API
        """
        if not self.client:
            return self._get_error_result("Google Vision API not initialized. Credentials check karein.")

        try:
            print(f"Starting Google Vision OCR for: {pdf_path}")
            
            # PDF ko images mein convert karein
            images = self._pdf_to_images(pdf_path)
            all_text = ""
            total_confidence = 0
            
            for i, image in enumerate(images):
                print(f"Processing page {i+1}/{len(images)} with Google Vision")
                
                # Image ko bytes mein convert karein
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                content = img_byte_arr.getvalue()
                
                vision_image = vision.Image(content=content)
                
                # DOCUMENT_TEXT_DETECTION use karein (dense/handwritten text ke liye best)
                response = self.client.document_text_detection(image=vision_image)
                
                if response.error.message:
                    raise Exception(f"Google Vision Error: {response.error.message}")
                
                page_text = response.full_text_annotation.text
                all_text += page_text + "\n"
                
                # Confidence calculate karein (optional)
                # Google Vision pages[0].confidence deta hai
                if response.full_text_annotation.pages:
                    total_confidence += response.full_text_annotation.pages[0].confidence
            
            avg_confidence = (total_confidence / len(images)) * 100 if images else 0
            
            return {
                'text': all_text.strip(),
                'confidence': avg_confidence,
                'page_count': len(images),
                'method': 'google_vision_ocr'
            }
            
        except Exception as e:
            logger.error(f"Google Vision OCR Error: {str(e)}")
            return self._get_error_result(str(e))

    def _pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Convert PDF to images using PyMuPDF"""
        images = []
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x resolution for better OCR
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                images.append(image)
            doc.close()
        except Exception as e:
            logger.error(f"PDF to Image Conversion Error: {str(e)}")
        return images

    def _get_error_result(self, error_msg: str) -> Dict[str, Any]:
        return {
            'text': f"Google Vision OCR Failed: {error_msg}",
            'confidence': 0.0,
            'page_count': 0,
            'method': 'google_vision_error'
        }

# Global instance
google_vision = GoogleVisionEngine()
