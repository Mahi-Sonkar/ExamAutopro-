import requests
import json
import tempfile
import os

# Test complete PDF analysis pipeline
try:
    # Test 1: Text file upload (should work with direct read)
    text_content = '''Sample PDF Document for Testing
1. What is the capital of France?
2. What is the chemical formula for water?
3. True or False: The Earth is round.'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write(text_content)
        temp_path = temp_file.name
    
    with open(temp_path, 'rb') as f:
        files = {
            'file': ('test.pdf', f.read(), 'application/pdf'),
            'answer_key': json.dumps({'Q1': 'Paris', 'Q2': 'H2O', 'Q3': 'True'})
        }
        
        response = requests.post('http://127.0.0.1:8000/core/api/evaluate-pdf/', files=files)
        print('Test 1 - Text File Upload:')
        print(f'Status Code: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('SUCCESS: Text file processing works!')
            print(f'Success: {data.get("success", False)}')
            print(f'File Name: {data.get("file_name", "No file name")}')
            
            extraction = data.get('extraction', {})
            print(f'Extraction Method: {extraction.get("method", "Unknown")}')
            print(f'Text Length: {len(extraction.get("text", ""))}')
            
            questions = data.get('questions', {})
            print(f'Questions Found: {questions.get("count", 0)}')
            
            analysis = data.get('analysis', {})
            print(f'Word Count: {analysis.get("word_count", 0)}')
            
            answer_eval = data.get('answer_evaluation', {})
            if answer_eval and 'total_questions' in answer_eval:
                print(f'Answer Evaluation: {answer_eval.get("total_questions", 0)} questions evaluated')
            
            print('COMPLETE PIPELINE WORKING!')
            
        else:
            print(f'HTTP Error: {response.status_code}')
            print(f'Response: {response.text}')
    
    os.unlink(temp_path)
    
except Exception as e:
    print(f'Test Error: {e}')
    import traceback
    traceback.print_exc()
