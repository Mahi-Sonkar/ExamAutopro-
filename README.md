# ExamAutoPro

ExamAutoPro is a Django-based examination automation platform for creating exams, collecting submissions, evaluating answers, processing uploaded answer sheets, and supporting proctoring workflows.

## Features

- User accounts for students, teachers, and administrators
- Exam creation, question management, and online exam taking
- AI-assisted descriptive answer evaluation
- PDF/image answer-sheet upload and analysis
- Teacher exam selection for answer-sheet evaluation using stored questions and model answers
- OCR support with Tesseract, Google Vision, Gemini, and OCR.Space fallbacks where configured
- Scoring ranges, scoring configuration import, evaluation dashboards, analytics, and result views
- Basic proctoring workflows and dashboard pages

## Tech Stack

- Python 3.8+
- Django 4.2
- Django REST Framework
- SQLite for local development
- OpenCV, pytesseract, scikit-learn, NLTK, spaCy, pdfplumber, PyMuPDF, and related OCR/NLP tools

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Apply database migrations:

   ```bash
   python manage.py migrate
   ```

4. Optional: use a custom SQLite database path for local testing:

   ```bash
   set SQLITE_NAME=D:\ExamAutoPro\local.sqlite3
   python manage.py migrate
   ```

5. Create an admin user:

   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:

   ```bash
   python manage.py runserver
   ```

7. Open the app:

   ```text
   http://127.0.0.1:8000/
   ```

## Optional Configuration

Create a local `.env` file for API keys and provider preferences. Do not commit this file.

```env
GEMINI_API_KEY=your_gemini_key
GOOGLE_API_KEY=your_google_key
GROQ_API_KEY=your_groq_key
OCR_SPACE_API_KEY=your_ocr_space_key
AI_PROVIDER_PRIORITY=gemini,groq
SQLITE_NAME=D:\ExamAutoPro\db.sqlite3
```

For local OCR, install Tesseract OCR separately and make sure it is available on your system path.

## Useful Commands

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic
```

## Project Structure

- `accounts/` - custom user accounts and authentication views
- `exams/` - exam, question, submission, and answer workflows
- `evaluation/` - scoring, evaluation engines, and evaluation results
- `pdf_analysis/` - PDF upload, OCR, NLP, and answer-sheet analysis
- `proctoring/` - proctoring models and views
- `dashboard/` - role-based dashboard pages
- `templates/` - shared and app-specific HTML templates
- `static/` - CSS and JavaScript assets

## Teacher Workflow

1. Create an exam and add questions, marks, model answers, and keywords.
2. Configure scoring ranges globally or for the selected exam.
3. Upload a student's answer sheet from the PDF analysis page.
4. Select the matching exam so the evaluator can use the saved questions and model answers.
5. Review extracted answers, marks, feedback, and analytics from the result and dashboard pages.

## Notes

The project defaults to SQLite and development-friendly settings. Before production deployment, configure a secure `SECRET_KEY`, set `DEBUG=False`, update `ALLOWED_HOSTS`, configure a production database, and use proper static/media file hosting.
