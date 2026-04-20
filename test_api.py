#!/usr/bin/env python
"""
Test script for PDF Evaluation API with Google Vision integration
"""

import requests
import json
import os

def test_pdf_evaluation_api():
    """Test the PDF evaluation API endpoint"""
    
    # API endpoint
    url = "http://127.0.0.1:8000/core/api/evaluate-pdf/"
    
    # Test file (create if doesn't exist)
    test_file_path = "test.pdf"
    if not os.path.exists(test_file_path):
        print("Test PDF file not found. Creating one...")
        create_test_pdf()
    
    # Answer key for testing
    answer_key = {
        "Q1": "Machine learning is a subset of artificial intelligence that uses algorithms to learn from data",
        "Q2": "Neural networks are computing systems inspired by biological neural networks in the brain",
        "Q3": "Data is important because it trains machine learning models and improves accuracy"
    }
    
    # Prepare the request
    files = {
        'file': open(test_file_path, 'rb')
    }
    
    data = {
        'answer_key': json.dumps(answer_key)
    }
    
    try:
        print("Testing PDF Evaluation API...")
        print(f"URL: {url}")
        print(f"File: {test_file_path}")
        print(f"Answer Key: {answer_key}")
        print("-" * 50)
        
        # Make the request
        response = requests.post(url, files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("-" * 50)
        
        # Parse response
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS! API Response:")
            print(json.dumps(result, indent=2))
            
            # Check for Google Vision usage
            if 'processing_method' in result:
                print(f"\nProcessing Method: {result['processing_method']}")
            
            if 'engine_status' in result:
                print(f"Engine Status: {result['engine_status']}")
            
            if 'extracted_text' in result:
                print(f"\nExtracted Text Preview: {result['extracted_text'][:200]}...")
            
            # Check if Google Vision was used
            if result.get('processing_method') == 'google_vision':
                print("\nGoogle Vision API was successfully used!")
            elif result.get('processing_method') == 'ocr':
                print("\nOCR was used (Tesseract)")
            else:
                print("\nDirect text extraction was used")
                
        else:
            print(f"ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
    
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
    except Exception as e:
        print(f"General Error: {e}")
    finally:
        # Close the file
        files['file'].close()

def create_test_pdf():
    """Create a test PDF file"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a simple test PDF
        c = canvas.Canvas('test.pdf', pagesize=letter)
        c.drawString(100, 750, 'Q1. Machine learning is a subset of artificial intelligence.')
        c.drawString(100, 700, 'Q2. Neural networks are inspired by biological neural networks.')
        c.drawString(100, 650, 'Q3. Data is important for training machine learning models.')
        c.save()
        print("Test PDF created: test.pdf")
        
    except ImportError:
        print("ReportLab not installed. Creating simple text file instead...")
        with open('test.txt', 'w') as f:
            f.write('Q1. Machine learning is a subset of artificial intelligence.\n')
            f.write('Q2. Neural networks are inspired by biological neural networks.\n')
            f.write('Q3. Data is important for training machine learning models.\n')
        print("Test text file created: test.txt")

if __name__ == "__main__":
    test_pdf_evaluation_api()
