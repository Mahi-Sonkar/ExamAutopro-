# ExamAutoPro - AI-Powered Automated Examination System

ExamAutoPro is a comprehensive AI-based examination evaluation system built with Django. It helps automate exam creation, student submissions, answer-sheet analysis, AI-assisted evaluation, result generation, and exam integrity workflows through proctoring and attempt restrictions.

## Key Features

### Exam Integrity & Proctoring

- Restricted exam attempts with support for configurable attempt limits.
- Proctoring workflows for monitoring exam activity.
- Student, teacher, and administrator roles with dedicated access flows.
- Secure exam-taking pages designed to reduce unfair assistance during online exams.

### AI-Powered Evaluation

- Hybrid scoring support using similarity analysis, keyword coverage, and configurable scoring ranges.
- Automated evaluation for MCQ and descriptive answers.
- PDF/image answer-sheet upload for scanned or handwritten submissions.
- OCR support with Tesseract, Google Vision, Gemini, and OCR.Space fallbacks where configured.
- Teacher exam selection during answer-sheet evaluation so saved questions, marks, model answers, and keywords can guide scoring.

### Role-Based Dashboards

- Student dashboard for available exams, submissions, and evaluated results.
- Teacher dashboard for managing exams, questions, scoring rules, and answer-sheet analysis.
- Admin dashboard for user, exam, and system-level oversight.
- Analytics and result views for reviewing student performance and evaluation outcomes.

### Scoring & Analysis Tools

- Configurable scoring ranges for evaluation rules.
- Scoring configuration import pages.
- Question-wise evaluation and feedback support.
- PDF analysis detail pages for reviewing extracted content and generated results.

## Tech Stack

- Backend: Django 4.2, Django REST Framework
- Database: SQLite for local development, configurable for production databases
- Frontend: HTML templates, Bootstrap-style UI, CSS, JavaScript
- AI/NLP/OCR: NLTK, scikit-learn, spaCy, OpenCV, pytesseract, pdfplumber, PyMuPDF
- Optional Providers: Google Vision, Gemini, Groq, OCR.Space

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Mahi-Sonkar/ExamAutopro-.git
cd ExamAutopro-
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

On Linux/macOS:

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure OCR

Install Tesseract OCR on your system if you want local OCR support.

- Windows: install a Tesseract build such as UB-Mannheim Tesseract.
- Make sure Tesseract is available on your system path.
- If needed, update the Tesseract command path in project settings.

### 5. Configure Environment Variables

Create a local `.env` file for API keys and local configuration. Do not commit this file.

```env
GEMINI_API_KEY=your_gemini_key
GOOGLE_API_KEY=your_google_key
GROQ_API_KEY=your_groq_key
OCR_SPACE_API_KEY=your_ocr_space_key
AI_PROVIDER_PRIORITY=gemini,groq
SQLITE_NAME=D:\ExamAutoPro\db.sqlite3
```

### 6. Apply Database Migrations

```bash
python manage.py migrate
```

### 7. Create an Admin User

```bash
python manage.py createsuperuser
```

### 8. Start the Development Server

```bash
python manage.py runserver
```

Open the app at:

```text
http://127.0.0.1:8000/
```

## Verification

Run Django checks before development or deployment:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

Run tests when available:

```bash
python manage.py test
```

## Teacher Workflow

1. Create an exam and add questions, marks, model answers, and keywords.
2. Configure global or exam-specific scoring ranges.
3. Upload a student's PDF/image answer sheet from the PDF analysis page.
4. Select the matching exam so the evaluator can use saved question data.
5. Review extracted answers, marks, feedback, percentages, and analytics.

## Project Structure

```text
ExamAutoPro/
├── accounts/        # Custom user accounts and authentication views
├── core/            # Shared evaluation, processing, and API utilities
├── dashboard/       # Role-based dashboard pages
├── evaluation/      # Scoring rules, evaluation models, and result workflows
├── exams/           # Exam, question, answer, and submission logic
├── pdf_analysis/    # PDF/image upload, OCR, NLP, and answer-sheet analysis
├── proctoring/      # Proctoring models, views, and monitoring helpers
├── static/          # CSS and JavaScript assets
├── templates/       # Shared and app-specific HTML templates
├── ExamAutoPro/     # Django project settings and URL configuration
├── manage.py        # Django management script
└── requirements.txt # Python dependencies
```

## Production Notes

Before production deployment:

- Configure a secure `SECRET_KEY`.
- Set `DEBUG=False`.
- Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
- Configure a production database.
- Configure static and media file hosting.
- Store API keys and credentials outside source control.

## Author

Mahi Sonkar - [GitHub](https://github.com/Mahi-Sonkar)

Developed as part of a major project for automated education evaluation.
