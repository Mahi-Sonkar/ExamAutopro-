# ExamAutoPro

ExamAutoPro is a Django-based examination automation platform for creating exams, collecting submissions, evaluating answers, processing uploaded PDFs, and supporting proctoring workflows.

## Features

- User accounts for students, teachers, and administrators
- Exam creation, question management, and online exam taking
- AI-assisted descriptive answer evaluation
- PDF answer-sheet upload and analysis
- OCR support with Tesseract, Google Vision, Gemini, and OCR.Space fallbacks where configured
- Scoring ranges, evaluation dashboards, and result views
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

4. Create an admin user:

   ```bash
   python manage.py createsuperuser
   ```

5. Run the development server:

   ```bash
   python manage.py runserver
   ```

6. Open the app:

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
```

For local OCR, install Tesseract OCR separately and make sure it is available on your system path.

## Useful Commands

```bash
python manage.py check
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

## Notes

The project defaults to SQLite and development-friendly settings. Before production deployment, configure a secure `SECRET_KEY`, set `DEBUG=False`, update `ALLOWED_HOSTS`, configure a production database, and use proper static/media file hosting.
