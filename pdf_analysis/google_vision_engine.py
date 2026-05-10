"""
Vision OCR engine for handwritten answer sheets.

Provider order:
1. Google Cloud Vision, when GOOGLE_APPLICATION_CREDENTIALS is configured.
2. Gemini Vision, when GEMINI_API_KEY / GOOGLE_API_KEY is configured.
3. The caller falls back to local Tesseract when neither provider returns text.
"""

import base64
import io
import logging
import os
from typing import Any, Dict, List

import fitz
import requests
from PIL import Image

try:
    from google.cloud import vision
except Exception:
    vision = None

logger = logging.getLogger(__name__)


class GoogleVisionEngine:
    def __init__(self):
        self.credentials_path = os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS",
            "credentials/google_vision_key.json",
        )
        self.gemini_key = (
            os.environ.get("GEMINI_API_KEY", "").strip()
            or os.environ.get("GOOGLE_API_KEY", "").strip()
            or os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY", "").strip()
        )
        self.ocr_space_key = os.environ.get("OCR_SPACE_API_KEY", "").strip()
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Google Cloud Vision if the library and credentials exist."""
        if vision is None:
            logger.warning("google-cloud-vision is not installed; Gemini/Tesseract OCR fallback will be used.")
            return

        try:
            if os.path.exists(self.credentials_path):
                self.client = vision.ImageAnnotatorClient.from_service_account_json(self.credentials_path)
                logger.info("Google Vision client initialized from %s", self.credentials_path)
                return

            env_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if env_creds and os.path.exists(env_creds):
                self.client = vision.ImageAnnotatorClient()
                logger.info("Google Vision client initialized from GOOGLE_APPLICATION_CREDENTIALS")
                return

            logger.warning("Google Vision credentials not found; Gemini/Tesseract OCR fallback will be used.")
        except Exception as exc:
            logger.error("Failed to initialize Google Vision client: %s", exc)
            self.client = None

    def is_active(self) -> bool:
        return self.client is not None or bool(self.gemini_key or self.ocr_space_key)

    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        if self.client:
            result = self._extract_with_google_vision(pdf_path)
            if result.get("success") and result.get("text", "").strip():
                return result
            logger.warning("Google Vision OCR failed; trying Gemini Vision fallback.")

        if self.gemini_key:
            result = self._extract_with_gemini_vision(pdf_path)
            if result.get("success") and result.get("text", "").strip():
                return result
            logger.warning("Gemini Vision OCR failed; trying OCR.space fallback.")

        if self.ocr_space_key:
            return self._extract_with_ocr_space(pdf_path)

        return self._get_error_result("No cloud vision OCR provider is configured.")

    def _extract_with_google_vision(self, pdf_path: str) -> Dict[str, Any]:
        try:
            images = self._pdf_to_images(pdf_path)
            all_text = []
            total_confidence = 0.0

            for image in images:
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="PNG")
                vision_image = vision.Image(content=img_byte_arr.getvalue())
                response = self.client.document_text_detection(image=vision_image)

                if response.error.message:
                    raise Exception(f"Google Vision Error: {response.error.message}")

                page_text = response.full_text_annotation.text.strip()
                if page_text:
                    all_text.append(page_text)

                if response.full_text_annotation.pages:
                    total_confidence += response.full_text_annotation.pages[0].confidence

            text = "\n\n".join(all_text).strip()
            avg_confidence = (total_confidence / len(images)) * 100 if images else 0.0
            return {
                "text": text,
                "confidence": avg_confidence,
                "page_count": len(images),
                "method": "google_vision_ocr",
                "success": bool(text),
            }
        except Exception as exc:
            logger.error("Google Vision OCR error: %s", exc)
            return self._get_error_result(str(exc))

    def _extract_with_gemini_vision(self, pdf_path: str) -> Dict[str, Any]:
        try:
            images = self._pdf_to_images(pdf_path)
            if not images:
                return self._get_error_result("Could not convert file to images for Gemini OCR.")

            model = os.environ.get("GEMINI_OCR_MODEL", os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            prompt = (
                "Extract all readable text from this exam answer sheet or question paper. "
                "Preserve question numbering, line breaks, marks like [5 marks], and handwritten answers. "
                "Return only the extracted text, no explanation."
            )
            all_text = []

            for image in images:
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="PNG")
                encoded = base64.b64encode(img_byte_arr.getvalue()).decode("ascii")
                response = requests.post(
                    endpoint,
                    params={"key": self.gemini_key},
                    json={
                        "contents": [{
                            "parts": [
                                {"text": prompt},
                                {"inline_data": {"mime_type": "image/png", "data": encoded}},
                            ]
                        }],
                        "generationConfig": {"temperature": 0.0},
                    },
                    timeout=45,
                )
                response.raise_for_status()
                parts = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
                page_text = "".join(part.get("text", "") for part in parts).strip()
                if page_text:
                    all_text.append(page_text)

            text = "\n\n".join(all_text).strip()
            return {
                "text": text,
                "confidence": 85.0 if text else 0.0,
                "page_count": len(images),
                "method": "gemini_vision_ocr",
                "success": bool(text),
            }
        except Exception as exc:
            logger.error("Gemini Vision OCR error: %s", exc)
            return self._get_error_result(str(exc))

    def _extract_with_ocr_space(self, pdf_path: str) -> Dict[str, Any]:
        try:
            with open(pdf_path, "rb") as upload:
                response = requests.post(
                    "https://api.ocr.space/parse/image",
                    files={"file": upload},
                    data={
                        "apikey": self.ocr_space_key,
                        "language": os.environ.get("OCR_SPACE_LANGUAGE", "eng"),
                        "isOverlayRequired": "false",
                        "OCREngine": os.environ.get("OCR_SPACE_ENGINE", "2"),
                        "scale": "true",
                    },
                    timeout=60,
                )
            response.raise_for_status()
            payload = response.json()
            if payload.get("IsErroredOnProcessing"):
                errors = payload.get("ErrorMessage") or payload.get("ErrorDetails") or "OCR.space failed"
                if isinstance(errors, list):
                    errors = "; ".join(str(error) for error in errors)
                raise Exception(errors)

            parsed_results = payload.get("ParsedResults") or []
            text = "\n\n".join(
                item.get("ParsedText", "").strip()
                for item in parsed_results
                if item.get("ParsedText", "").strip()
            ).strip()
            return {
                "text": text,
                "confidence": 65.0 if text else 0.0,
                "page_count": len(parsed_results) or 1,
                "method": "ocr_space",
                "success": bool(text),
            }
        except Exception as exc:
            logger.error("OCR.space OCR error: %s", exc)
            return self._get_error_result(str(exc))

    def _pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        images = []
        try:
            ext = os.path.splitext(pdf_path)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]:
                return [Image.open(pdf_path).convert("RGB")]

            doc = fitz.open(pdf_path)
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                images.append(image)
            doc.close()
        except Exception as exc:
            logger.error("PDF/image conversion error: %s", exc)
        return images

    def _get_error_result(self, error_msg: str) -> Dict[str, Any]:
        return {
            "text": "",
            "confidence": 0.0,
            "page_count": 0,
            "method": "vision_ocr_error",
            "success": False,
            "error": error_msg,
        }


google_vision = GoogleVisionEngine()
