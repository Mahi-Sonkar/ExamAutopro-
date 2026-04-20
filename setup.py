#!/usr/bin/env python
"""
ExamAutoPro Setup Script
AI-Powered Examination Evaluation System
"""

import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version: {sys.version}")

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def setup_database():
    """Setup database and run migrations"""
    print("Setting up database...")
    try:
        # Create migrations if they don't exist
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        # Apply migrations
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✓ Database setup completed")
    except Exception as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)

def create_superuser():
    """Create superuser account"""
    print("Creating superuser...")
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            execute_from_command_line([
                'manage.py', 'createsuperuser',
                '--username', 'admin',
                '--email', 'admin@examautopro.com'
            ])
            print("✓ Superuser created successfully")
        else:
            print("✓ Superuser already exists")
    except Exception as e:
        print(f"Error creating superuser: {e}")

def setup_directories():
    """Create necessary directories"""
    directories = [
        'media',
        'media/profile_pics',
        'media/question_images',
        'media/handwritten_answers',
        'media/proctoring_screenshots',
        'media/proctoring_camera',
        'staticfiles',
        'logs',
        'ai_models',
        'ai_models/face_detection'
    ]
    
    print("Creating directories...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✓ Directories created successfully")

def download_nltk_data():
    """Download required NLTK data"""
    print("Downloading NLTK data...")
    try:
        import nltk
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('averaged_perceptron_tagger')
        print("✓ NLTK data downloaded successfully")
    except Exception as e:
        print(f"Error downloading NLTK data: {e}")

def setup_tesseract():
    """Check if Tesseract OCR is installed"""
    print("Checking Tesseract OCR...")
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✓ Tesseract OCR is available")
    except Exception as e:
        print("⚠ Tesseract OCR not found. Please install Tesseract OCR:")
        print("  - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("  - macOS: brew install tesseract")
        print("  - Ubuntu: sudo apt install tesseract-ocr")

def setup_opencv():
    """Check if OpenCV is properly installed"""
    print("Checking OpenCV...")
    try:
        import cv2
        print(f"✓ OpenCV version: {cv2.__version__}")
    except Exception as e:
        print(f"Error with OpenCV: {e}")

def collect_static_files():
    """Collect static files"""
    print("Collecting static files...")
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✓ Static files collected")
    except Exception as e:
        print(f"Error collecting static files: {e}")

def create_sample_data():
    """Create sample data for testing"""
    print("Creating sample data...")
    try:
        from django.core.management import call_command
        call_command('loaddata', 'sample_data.json', verbosity=0)
        print("✓ Sample data created")
    except Exception as e:
        print(f"Note: Sample data not created (this is normal): {e}")

def run_tests():
    """Run basic tests to verify installation"""
    print("Running tests...")
    try:
        execute_from_command_line(['manage.py', 'test', '--verbosity=2'])
        print("✓ Tests completed successfully")
    except Exception as e:
        print(f"⚠ Some tests failed: {e}")

def main():
    """Main setup function"""
    print("=" * 60)
    print("ExamAutoPro Setup Script")
    print("AI-Powered Examination Evaluation System")
    print("=" * 60)
    
    # Set up Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ExamAutoPro.settings')
    
    try:
        django.setup()
    except Exception as e:
        print(f"Error setting up Django: {e}")
        sys.exit(1)
    
    # Run setup steps
    check_python_version()
    setup_directories()
    install_dependencies()
    setup_database()
    download_nltk_data()
    setup_tesseract()
    setup_opencv()
    collect_static_files()
    create_superuser()
    create_sample_data()
    
    print("\n" + "=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Start the development server:")
    print("   python manage.py runserver")
    print("\n2. Open your browser and navigate to:")
    print("   http://localhost:8000")
    print("\n3. Login with the superuser account you created")
    print("\n4. For production deployment, remember to:")
    print("   - Set DEBUG=False in settings.py")
    print("   - Configure proper database settings")
    print("   - Set up secure SECRET_KEY")
    print("   - Configure email settings")
    print("   - Set up proper file serving")
    
    print("\nOptional:")
    print("- Run tests: python manage.py test")
    print("- Create sample data: python manage.py loaddata sample_data.json")
    print("- Access admin panel: http://localhost:8000/admin")

if __name__ == '__main__':
    main()
