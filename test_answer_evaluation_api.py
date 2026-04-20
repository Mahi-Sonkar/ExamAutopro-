"""
Test Complete Answer Evaluation API Implementation
End-to-end testing of the new answer sheet evaluation system
"""

import requests
import json
import tempfile
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_test_answer_sheet():
    """Create a test answer sheet PDF"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_path = temp_file.name
    temp_file.close()
    
    doc = SimpleDocTemplate(temp_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = styles['Heading1']
    story.append(Paragraph("Answer Sheet", title_style))
    story.append(Spacer(1, 20))
    
    # Answers
    answer_style = styles['Normal']
    answer_style.fontSize = 14
    
    answers = [
        "1. Paris is the capital of France. It is located in the north-central part of the country and has been the political center since the 12th century.",
        
        "2. The chemical formula for water is H2O. It consists of two hydrogen atoms bonded to one oxygen atom through covalent bonds.",
        
        "3. True. The Earth is round and has a spherical shape, specifically an oblate spheroid.",
        
        "4. Machine Learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
        
        "5. The process of photosynthesis converts light energy into chemical energy through the reaction of carbon dioxide and water in the presence of chlorophyll."
    ]
    
    for answer in answers:
        story.append(Paragraph(answer, answer_style))
        story.append(Spacer(1, 15))
    
    doc.build(story)
    return temp_path

def create_test_question_paper():
    """Create a test question paper PDF"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_path = temp_file.name
    temp_file.close()
    
    doc = SimpleDocTemplate(temp_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = styles['Heading1']
    story.append(Paragraph("Test Question Paper", title_style))
    story.append(Spacer(1, 20))
    
    # Questions
    question_style = styles['Normal']
    question_style.fontSize = 14
    
    questions = [
        "1. What is the capital of France? (10 marks)",
        
        "2. What is the chemical formula for water? (10 marks)",
        
        "3. True or False: The Earth is round. (5 marks)",
        
        "4. What is Machine Learning? (15 marks)",
        
        "5. Explain the process of photosynthesis. (20 marks)"
    ]
    
    for question in questions:
        story.append(Paragraph(question, question_style))
        story.append(Spacer(1, 15))
    
    doc.build(story)
    return temp_path

def test_answer_evaluation_api():
    """Test the complete answer evaluation API"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("=== TESTING ANSWER EVALUATION API ===")
    print("Endpoint: POST /core/api/evaluate-answer-sheet/")
    print("=" * 60)
    
    try:
        # Create test PDFs
        print("Creating test PDF files...")
        answer_pdf_path = create_test_answer_sheet()
        question_pdf_path = create_test_question_paper()
        
        print(f"Answer sheet: {answer_pdf_path}")
        print(f"Question paper: {question_pdf_path}")
        print()
        
        # Test 1: Check API info (GET request)
        print("1. Testing API Info (GET)")
        print("-" * 30)
        
        response = requests.get(f"{base_url}/core/api/evaluate-answer-sheet/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: API info retrieved")
            print(f"API Name: {data.get('api_name', 'Unknown')}")
            print(f"Status: {data.get('status', 'Unknown')}")
            print(f"Scoring Rules Available: {len(data.get('scoring_rules', []))}")
        else:
            print(f"ERROR: {response.text}")
        
        print()
        
        # Test 2: Full evaluation (POST request)
        print("2. Testing Full Evaluation (POST)")
        print("-" * 30)
        
        with open(answer_pdf_path, 'rb') as answer_file, open(question_pdf_path, 'rb') as question_file:
            files = {
                'answer_pdf': ('answer_sheet.pdf', answer_file.read(), 'application/pdf'),
                'question_paper': ('question_paper.pdf', question_file.read(), 'application/pdf')
            }
            
            response = requests.post(
                f"{base_url}/core/api/evaluate-answer-sheet/",
                files=files,
                timeout=120
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("SUCCESS: Answer evaluation completed!")
                
                if data.get('success'):
                    print(f"Total Marks: {data.get('total_marks', 0)}")
                    print(f"Total Questions: {data.get('total_questions', 0)}")
                    print(f"Average Similarity: {data.get('average_similarity', 0):.3f}")
                    
                    processing_info = data.get('processing_info', {})
                    print(f"OCR Method: {processing_info.get('ocr_method', 'Unknown')}")
                    print(f"NLP Model: {processing_info.get('nlp_model', 'Unknown')}")
                    print(f"Scoring Rules Applied: {processing_info.get('scoring_rules_applied', 0)}")
                    
                    answers = data.get('answers', [])
                    print(f"\nDetailed Results ({len(answers)} answers):")
                    
                    for i, answer in enumerate(answers[:3]):  # Show first 3
                        print(f"  Q{i+1}: Similarity={answer.get('similarity', 0):.3f}, Marks={answer.get('marks', 0)}")
                        print(f"      Question: {answer.get('question', '')[:50]}...")
                        print(f"      Answer: {answer.get('answer', '')[:50]}...")
                        print(f"      Rule: {answer.get('applied_rule', 'default')}")
                        print()
                    
                    if len(answers) > 3:
                        print(f"  ... and {len(answers) - 3} more answers")
                else:
                    print(f"ERROR: {data.get('error', 'Unknown error')}")
            else:
                print(f"ERROR: {response.text}")
        
        print()
        
        # Test 3: Test with missing files
        print("3. Testing Validation (Missing Files)")
        print("-" * 30)
        
        files = {
            'answer_pdf': ('answer_sheet.pdf', b'test content', 'application/pdf')
            # Missing question_paper
        }
        
        response = requests.post(
            f"{base_url}/core/api/evaluate-answer-sheet/",
            files=files,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                print("SUCCESS: Validation working correctly")
                print(f"Error: {data.get('error', 'Unknown validation error')}")
        else:
            print(f"ERROR: {response.text}")
        
        print()
        
        # Test 4: Check scoring ranges in database
        print("4. Testing Scoring Ranges")
        print("-" * 30)
        
        response = requests.get(f"{base_url}/core/api/evaluate-answer-sheet/")
        
        if response.status_code == 200:
            data = response.json()
            scoring_rules = data.get('scoring_rules', [])
            
            print(f"Scoring Rules in Database: {len(scoring_rules)}")
            
            for rule in scoring_rules[:3]:  # Show first 3
                print(f"  - {rule.get('name', 'Unknown')}: {rule.get('min_score', 0):.2f}-{rule.get('max_score', 1):.2f} = {rule.get('marks', 0)} marks")
            
            if len(scoring_rules) == 0:
                print("WARNING: No scoring rules found in database")
                print("Create scoring ranges in Django admin for proper evaluation")
        
        print()
        print("=" * 60)
        print("API TESTING COMPLETE!")
        
        print("\nSUMMARY:")
        print("1. API Endpoint: POST /core/api/evaluate-answer-sheet/")
        print("2. Required Files: answer_pdf, question_paper")
        print("3. Response Format: JSON with total_marks, answers array")
        print("4. Scoring: Uses ScoringRange model from database")
        print("5. Processing: OCR -> NLP -> Scoring -> Results")
        
        print("\nNEXT STEPS:")
        print("1. Add scoring ranges in Django admin if needed")
        print("2. Test with real answer sheets")
        print("3. Integrate with frontend application")
        print("4. Add authentication if required")
        
    except Exception as e:
        print(f"TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary files
        try:
            if 'answer_pdf_path' in locals() and os.path.exists(answer_pdf_path):
                os.unlink(answer_pdf_path)
                print(f"Cleaned up: {answer_pdf_path}")
            if 'question_pdf_path' in locals() and os.path.exists(question_pdf_path):
                os.unlink(question_pdf_path)
                print(f"Cleaned up: {question_pdf_path}")
        except:
            pass

if __name__ == "__main__":
    test_answer_evaluation_api()
