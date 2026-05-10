from django import forms
from django.core.validators import FileExtensionValidator
from .models import PDFDocument
import logging

logger = logging.getLogger(__name__)

class PDFUploadForm(forms.ModelForm):
    """Form for uploading PDF documents"""
    
    class Meta:
        model = PDFDocument
        fields = ['title', 'description', 'pdf_file', 'document_type']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter document title',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter document description (optional)'
            }),
            'pdf_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
                'required': True
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pdf_file'].validators = [
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])
        ]
        self.fields['pdf_file'].help_text = "Upload a PDF or image file (max 50MB)"
    
    def clean_pdf_file(self):
        """Validate PDF file"""
        pdf_file = self.cleaned_data.get('pdf_file')
        
        if pdf_file:
            # Check file size (50MB limit)
            if pdf_file.size > 50 * 1024 * 1024:
                raise forms.ValidationError("PDF file size cannot exceed 50MB.")
            
            allowed_extensions = ('.pdf', '.jpg', '.jpeg', '.png')
            if not pdf_file.name.lower().endswith(allowed_extensions):
                raise forms.ValidationError("Please upload a valid PDF or image file.")
            
            # Check MIME type (more lenient)
            allowed_mime_types = [
                'application/pdf', 'application/x-pdf', 'application/octet-stream',
                'image/jpeg', 'image/png'
            ]
            if pdf_file.content_type not in allowed_mime_types:
                # Log the mismatch but allow if extension is .pdf
                logger.warning(f"Lenient PDF upload: Unexpected content type {pdf_file.content_type} for {pdf_file.name}")
            
            # Double check extension just in case
            if not pdf_file.name.lower().endswith(allowed_extensions):
                raise forms.ValidationError("Only PDF, JPG, JPEG, and PNG files are allowed.")
        
        return pdf_file
    
    def clean_title(self):
        """Clean title field"""
        title = self.cleaned_data.get('title')
        if title:
            return title.strip().title()
        return title

class PDFSearchForm(forms.Form):
    """Form for searching PDF documents"""
    
    search_query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Search PDF documents...'
        })
    )
    
    document_type = forms.ChoiceField(
        choices=[('', 'All Types')] + PDFDocument.DOCUMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    
    analysis_status = forms.ChoiceField(
        choices=[('', 'All Status')] + PDFDocument.ANALYSIS_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

class PDFAnalysisSettingsForm(forms.Form):
    """Form for configuring PDF analysis settings"""
    
    ocr_method = forms.ChoiceField(
        choices=[
            ('auto', 'Automatic (Best Available)'),
            ('pdfplumber', 'PDFPlumber (Text-based PDFs)'),
            ('pymupdf', 'PyMuPDF (Fast Extraction)'),
            ('pytesseract', 'Tesseract OCR (Scanned PDFs)')
        ],
        initial='auto',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    extract_questions = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    generate_summary = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    analyze_sentiment = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    extract_entities = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    confidence_threshold = forms.FloatField(
        min_value=0.0,
        max_value=1.0,
        initial=0.5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'min': '0',
            'max': '1'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ocr_method'].help_text = "Choose the OCR method for text extraction"
        self.fields['confidence_threshold'].help_text = "Minimum confidence threshold for results"
