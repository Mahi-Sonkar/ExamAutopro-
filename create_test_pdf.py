"""
Create Test PDF Files for Evaluation Pipeline
Generate proper PDF files for testing answer sheet evaluation
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import tempfile
import os

def create_answer_sheet_pdf():
    """Create a test answer sheet PDF"""
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_path = temp_file.name
    temp_file.close()
    
    # Create PDF
    doc = SimpleDocTemplate(temp_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = styles['Heading1']
    title_style.fontSize = 18
    title_style.spaceAfter = 30
    story.append(Paragraph("Answer Sheet", title_style))
    
    # Instructions
    instructions_style = styles['Normal']
    instructions_style.fontSize = 12
    instructions_style.spaceAfter = 20
    story.append(Paragraph("Answer all questions in the space provided:", instructions_style))
    
    # Answers
    answer_style = styles['Normal']
    answer_style.fontSize = 14
    answer_style.leftIndent = 20
    
    answers = [
        "1. Paris is the capital of France. It is located in the north-central part of the country and has been the political center since the 12th century. The city is known for its iconic landmarks including the Eiffel Tower and Louvre Museum.",
        
        "2. The chemical formula for water is H2O. It consists of two hydrogen atoms bonded to one oxygen atom through covalent bonds. Water is essential for all known forms of life and covers approximately 71% of Earth's surface.",
        
        "3. True. The Earth is round and has a spherical shape, specifically an oblate spheroid. This means it is slightly flattened at the poles and bulges at the equator due to its rotation."
    ]
    
    for answer in answers:
        story.append(Paragraph(answer, answer_style))
        story.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story)
    return temp_path

def create_question_paper_pdf():
    """Create a test question paper PDF"""
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_path = temp_file.name
    temp_file.close()
    
    # Create PDF
    doc = SimpleDocTemplate(temp_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = styles['Heading1']
    title_style.fontSize = 18
    title_style.spaceAfter = 30
    story.append(Paragraph("Test Question Paper", title_style))
    
    # Instructions
    instructions_style = styles['Normal']
    instructions_style.fontSize = 12
    instructions_style.spaceAfter = 20
    story.append(Paragraph("Answer all questions:", instructions_style))
    
    # Questions
    question_style = styles['Normal']
    question_style.fontSize = 14
    question_style.spaceAfter = 25
    
    questions = [
        "1. What is the capital of France? (10 marks)",
        
        "2. What is the chemical formula for water? (10 marks)",
        
        "3. True or False: The Earth is round. (10 marks)"
    ]
    
    for question in questions:
        story.append(Paragraph(question, question_style))
    
    # Build PDF
    doc.build(story)
    return temp_path

if __name__ == "__main__":
    print("Creating test PDF files for evaluation pipeline...")
    
    try:
        # Create answer sheet
        answer_pdf_path = create_answer_sheet_pdf()
        print(f"✅ Answer sheet PDF created: {answer_pdf_path}")
        
        # Create question paper
        question_pdf_path = create_question_paper_pdf()
        print(f"✅ Question paper PDF created: {question_pdf_path}")
        
        print("\n📁 Test files ready for evaluation!")
        print(f"Answer Sheet: {answer_pdf_path}")
        print(f"Question Paper: {question_pdf_path}")
        
        # Keep files open for manual testing
        input("\nPress Enter to delete temporary files...")
        
    except Exception as e:
        print(f"❌ Error creating PDF files: {e}")
    
    finally:
        # Clean up
        try:
            if 'answer_pdf_path' in locals() and os.path.exists(answer_pdf_path):
                os.unlink(answer_pdf_path)
                print("🗑️  Answer sheet PDF deleted")
            if 'question_pdf_path' in locals() and os.path.exists(question_pdf_path):
                os.unlink(question_pdf_path)
                print("🗑️  Question paper PDF deleted")
        except:
            pass
