"""
Setup Tesseract OCR Path Configuration
Configure Tesseract for Windows environment
"""

import os
import sys
import subprocess

def setup_tesseract_path():
    """Setup Tesseract OCR path for Windows"""
    
    print("=== TESSERACT OCR SETUP ===")
    print()
    
    # Check if Tesseract is already installed
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("SUCCESS: Tesseract is already installed and accessible")
            print(f"Version: {result.stdout.split()[1]}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("Tesseract not found in PATH")
    
    print()
    print("MANUAL INSTALLATION REQUIRED:")
    print("=" * 40)
    print()
    print("1. Download Tesseract from:")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print("2. Install Tesseract (usually to: C:\\Program Files\\Tesseract-OCR)")
    print()
    print("3. Add Tesseract to system PATH OR set environment variable:")
    print("   setx TESSERACT_CMD \"C:\\Program Files\\Tesseract-OCR\\tesseract.exe\"")
    print()
    print("4. Restart your terminal/command prompt")
    print()
    
    # Try to detect common installation paths
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe"
    ]
    
    print("Checking common installation paths...")
    for path in common_paths:
        if os.path.exists(path):
            print(f"FOUND: {path}")
            print(f"Setting TESSERACT_CMD to: {path}")
            
            # Set environment variable for current session
            os.environ['TESSERACT_CMD'] = path
            
            # Create Python configuration
            config_content = f'''"""
Tesseract OCR Configuration
Auto-generated configuration for Windows
"""

import pytesseract

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r"{path}"

print(f"Tesseract configured: {{pytesseract.pytesseract.tesseract_cmd}}")
'''
            
            config_file = "tesseract_config.py"
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            print(f"Configuration saved to: {config_file}")
            print("Import this file before using pytesseract")
            return True
    
    print("Tesseract not found in common locations")
    print("Please install Tesseract manually first")
    return False

def test_tesseract():
    """Test Tesseract functionality"""
    try:
        import pytesseract
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a test image with text
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use a default font
            draw.text((10, 10), "Test 123", fill='black')
        except:
            # If font fails, just continue
            pass
        
        # Test OCR
        text = pytesseract.image_to_string(img)
        print(f"Tesseract test result: '{text.strip()}'")
        return True
        
    except Exception as e:
        print(f"Tesseract test failed: {e}")
        return False

if __name__ == "__main__":
    if setup_tesseract_path():
        print("\nTesting Tesseract...")
        test_tesseract()
    else:
        print("\nPlease install Tesseract first, then run this script again")
