from google.cloud import vision
import io
from pdf2image import convert_from_path
import os
import tempfile

def extract_text_from_image(image_path):
    """Extract text from image using Google Vision API"""
    try:
        client = vision.ImageAnnotatorClient()

        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = client.document_text_detection(image=image)

        return response.full_text_annotation.text
        
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF by converting to images and using OCR"""
    try:
        images = convert_from_path(pdf_path)
        full_text = ""

        for i, img in enumerate(images):
            # Create temporary image file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
                img.save(temp_img.name, "PNG")
                
                # Extract text from image
                text = extract_text_from_image(temp_img.name)
                if text:
                    full_text += text + "\n"
                
                # Clean up temporary file
                os.unlink(temp_img.name)

        return full_text.strip()
        
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None


def extract_text_from_pdf_bytes(pdf_bytes):
    """Extract text from PDF bytes"""
    try:
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name

        # Extract text
        text = extract_text_from_pdf(temp_pdf_path)
        
        # Clean up temporary file
        os.unlink(temp_pdf_path)
        
        return text
        
    except Exception as e:
        print(f"Error extracting text from PDF bytes: {e}")
        return None


def extract_text_from_uploaded_file(uploaded_file):
    """Extract text from Django uploaded file"""
    try:
        # Read file content
        pdf_bytes = uploaded_file.read()
        
        # Extract text
        text = extract_text_from_pdf_bytes(pdf_bytes)
        
        return text
        
    except Exception as e:
        print(f"Error extracting text from uploaded file: {e}")
        return None


# Test function
def test_ocr():
    """Test OCR functionality with sample data"""
    print("Testing OCR functionality...")
    
    # Check if Google Vision API is working
    try:
        client = vision.ImageAnnotatorClient()
        print("Google Vision API client created successfully")
        return True
    except Exception as e:
        print(f"Error creating Google Vision API client: {e}")
        return False


if __name__ == "__main__":
    test_ocr()
