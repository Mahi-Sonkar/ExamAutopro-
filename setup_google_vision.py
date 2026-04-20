"""
Setup Google Vision API Configuration
Guide for setting up Google Vision API credentials
"""

import os
import json

def setup_google_vision_guide():
    """Provide step-by-step guide for Google Vision API setup"""
    
    print("=== GOOGLE VISION API SETUP GUIDE ===")
    print()
    
    print("STEP 1: Enable Google Vision API")
    print("=" * 40)
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a new project or select existing project")
    print("3. Go to 'APIs & Services' > 'Library'")
    print("4. Search for 'Cloud Vision API'")
    print("5. Click 'Enable'")
    print()
    
    print("STEP 2: Create Service Account")
    print("=" * 40)
    print("1. Go to 'APIs & Services' > 'Credentials'")
    print("2. Click 'Create Credentials' > 'Service Account'")
    print("3. Enter service account name (e.g., 'vision-api-service')")
    print("4. Click 'Create and Continue'")
    print("5. Skip roles (or add 'Vision AI User' role)")
    print("6. Click 'Done'")
    print()
    
    print("STEP 3: Generate JSON Key")
    print("=" * 40)
    print("1. Find your service account in the credentials list")
    print("2. Click on the service account email")
    print("3. Go to 'Keys' tab")
    print("4. Click 'Add Key' > 'Create new key'")
    print("5. Select 'JSON' as key type")
    print("6. Click 'Create'")
    print("7. Download the JSON file (save it as 'google-vision-key.json')")
    print()
    
    print("STEP 4: Set Environment Variable")
    print("=" * 40)
    print("Option A: Set environment variable (Recommended)")
    print("set GOOGLE_APPLICATION_CREDENTIALS=D:\\ExamAutoPro\\google-vision-key.json")
    print()
    print("Option B: Place credentials file in project")
    print("Create folder: D:\\ExamAutoPro\\credentials\\")
    print("Place JSON file: D:\\ExamAutoPro\\credentials\\google_vision_key.json")
    print()
    
    print("STEP 5: Test Configuration")
    print("=" * 40)
    print("Run this script again after setup to test the configuration")
    print()
    
    return False

def test_google_vision():
    """Test Google Vision API configuration"""
    
    print("=== TESTING GOOGLE VISION API ===")
    print()
    
    # Check environment variable
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not creds_path:
        print("Environment variable GOOGLE_APPLICATION_CREDENTIALS not set")
        
        # Try alternative paths
        alternative_paths = [
            r"D:\ExamAutoPro\google-vision-key.json",
            r"D:\ExamAutoPro\credentials\google_vision_key.json",
            r"D:\ExamAutoPro\ocr-key.json",
            "google-vision-key.json"
        ]
        
        for path in alternative_paths:
            if os.path.exists(path):
                print(f"Found credentials at: {path}")
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path
                creds_path = path
                break
        else:
            print("No Google Vision credentials found")
            return False
    
    print(f"Using credentials: {creds_path}")
    
    # Test Google Vision API
    try:
        from google.cloud import vision
        print("Google Vision library imported successfully")
        
        # Try to create client
        client = vision.ImageAnnotatorClient()
        print("Vision API client created successfully")
        
        # Test with a simple image (create a test image)
        from PIL import Image, ImageDraw
        import io
        
        # Create a test image
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Test", fill='black')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes = img_bytes.getvalue()
        
        # Test Vision API
        image = vision.Image(content=img_bytes)
        response = client.text_detection(image=image)
        
        if response.text_annotations:
            print("SUCCESS: Google Vision API working!")
            print(f"Detected text: '{response.text_annotations[0].description.strip()}'")
            return True
        else:
            print("Warning: No text detected (but API is working)")
            return True
            
    except ImportError:
        print("Google Vision library not installed")
        print("Install with: pip install google-cloud-vision")
        return False
    except Exception as e:
        print(f"Google Vision API test failed: {e}")
        return False

def create_credentials_placeholder():
    """Create placeholder credentials file for guidance"""
    
    placeholder_dir = "credentials"
    if not os.path.exists(placeholder_dir):
        os.makedirs(placeholder_dir)
    
    placeholder_file = os.path.join(placeholder_dir, "README.md")
    
    content = '''# Google Vision API Credentials

## Instructions:
1. Download your JSON key from Google Cloud Console
2. Save it as `google_vision_key.json` in this folder
3. Or set environment variable:
   ```
   set GOOGLE_APPLICATION_CREDENTIALS=D:\\ExamAutoPro\\credentials\\google_vision_key.json
   ```

## Alternative:
Place credentials file at project root: `D:\\ExamAutoPro\\google-vision-key.json`

## After setup:
Run `python setup_google_vision.py` to test configuration.
'''
    
    with open(placeholder_file, 'w') as f:
        f.write(content)
    
    print(f"Created credentials guide: {placeholder_file}")

if __name__ == "__main__":
    print("Google Vision API Setup")
    print("=" * 30)
    print()
    
    # Create credentials directory
    create_credentials_placeholder()
    
    # Test current configuration
    if test_google_vision():
        print("\nSUCCESS: Google Vision API is configured and working!")
    else:
        print("\nGoogle Vision API not configured")
        print("Please follow the setup guide:")
        setup_google_vision_guide()
