import requests
import json

# Test the PDF analysis URL
try:
    url = 'http://127.0.0.1:8000/pdf/2594fcea-6af1-486a-a071-8425f219794c/'
    response = requests.get(url, timeout=10)
    
    print(f'URL: {url}')
    print(f'Status Code: {response.status_code}')
    print(f'Content-Type: {response.headers.get("Content-Type", "Unknown")}')
    print(f'Content Length: {len(response.text)} characters')
    
    if response.status_code == 200:
        print('SUCCESS: URL is accessible')
        # Check if it's HTML or JSON
        if 'application/json' in response.headers.get('Content-Type', ''):
            data = response.json()
            print('Response Type: JSON')
            print('Keys:', list(data.keys()) if isinstance(data, dict) else 'Not a dict')
        else:
            print('Response Type: HTML')
            # Look for key indicators in HTML
            if 'analysis' in response.text.lower():
                print('Analysis content found in HTML')
            elif 'error' in response.text.lower():
                print('Error found in HTML')
            elif 'not found' in response.text.lower():
                print('Not found message in HTML')
            else:
                print('No clear indicators in HTML')
        print('Response preview:')
        print(response.text[:1000])
    else:
        print(f'HTTP Error: {response.status_code}')
        print('Response preview:', response.text[:500])
        
except Exception as e:
    print(f'Test Error: {e}')
    import traceback
    traceback.print_exc()
