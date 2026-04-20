import requests
import json

# Test the PDF analysis endpoint directly
try:
    # Test the analysis API endpoint we created earlier
    url = 'http://127.0.0.1:8000/core/api/evaluate-pdf/'
    
    # Create a test PDF content
    test_content = '''Sample PDF Document for Testing
1. What is the capital of France?
2. What is the chemical formula for water?
3. True or False: The Earth is round.'''
    
    files = {
        'file': ('test.pdf', test_content.encode('utf-8'), 'application/pdf'),
        'answer_key': json.dumps({'Q1': 'Paris', 'Q2': 'H2O', 'Q3': 'True'})
    }
    
    response = requests.post(url, files=files, timeout=30)
    
    print(f'API Endpoint: {url}')
    print(f'Status Code: {response.status_code}')
    print(f'Content-Type: {response.headers.get("Content-Type", "Unknown")}')
    
    if response.status_code == 200:
        data = response.json()
        print('SUCCESS: API analysis working!')
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
        
        print('\n=== ANALYSIS RESULTS ===')
        print(f'Extracted Text Preview: {extraction.get("text", "")[:200]}...')
        print(f'Questions List: {questions.get("list", [])}')
        print(f'Processing Steps: {data.get("processing_steps", [])}')
        
    else:
        print(f'HTTP Error: {response.status_code}')
        print('Response:', response.text)
        
except Exception as e:
    print(f'Test Error: {e}')
    import traceback
    traceback.print_exc()

# Now test the specific UUID URL to see what's happening
print('\n' + '='*50)
print('Testing UUID URL directly...')

try:
    uuid_url = 'http://127.0.0.1:8000/pdf/2594fcea-6af1-486a-a071-8425f219794c/'
    response = requests.get(uuid_url, timeout=10)
    
    print(f'UUID URL: {uuid_url}')
    print(f'Status Code: {response.status_code}')
    
    if response.status_code == 200:
        # Check if it's redirecting to login or showing PDF details
        if 'login' in response.text.lower():
            print('ISSUE: Redirected to login page - authentication required')
        elif 'not found' in response.text.lower():
            print('ISSUE: PDF document not found with this UUID')
        elif 'pdf' in response.text.lower() and 'detail' in response.text.lower():
            print('SUCCESS: PDF detail page loaded')
        else:
            print('UNCLEAR: Check the HTML content manually')
            print('First 500 chars:', response.text[:500])
    else:
        print(f'HTTP Error: {response.status_code}')
        
except Exception as e:
    print(f'UUID URL Test Error: {e}')
