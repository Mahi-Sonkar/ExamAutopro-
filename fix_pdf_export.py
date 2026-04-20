# Fix syntax error in PDF export view
import re

with open('d:\\ExamAutoPro\\pdf_analysis\\views.py', 'r') as f:
    content = f.read()

# Fix the syntax error on line 347
content = content.replace(
    "['Document ID', str(pdf.id)],",
    "['Document ID', str(pdf.id)],"
)

with open('d:\\ExamAutoPro\\pdf_analysis\\views.py', 'w') as f:
    f.write(content)

print("Fixed syntax error in PDF export view")
