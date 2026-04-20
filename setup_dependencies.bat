@echo off
echo ========================================
echo ExamAutoPro Dependencies Setup
echo ========================================
echo.

echo [1] Installing Tesseract OCR...
echo Please download and install Tesseract OCR from:
echo https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo After installation, please note the installation path
echo Usually: C:\Program Files\Tesseract-OCR\tesseract.exe
echo.

echo [2] Google Vision API Setup...
echo 1. Go to: https://console.cloud.google.com/
echo 2. Create Project: ExamAutoPro OCR
echo 3. Enable Vision API
echo 4. Create Service Account: ocr-service
echo 5. Download JSON key and save as: D:\ExamAutoPro\ocr-key.json
echo.

echo [3] Claude API Setup...
echo 1. Get API key from: https://console.anthropic.com/
echo 2. Add to .env file: ANTHROPIC_API_KEY=your_key_here
echo.

echo [4] Testing Dependencies...
echo Run: python manage.py runserver
echo Then test: http://127.0.0.1:8000/core/api/evaluate-pdf/
echo.

echo ========================================
echo Setup Complete!
echo ========================================
pause
