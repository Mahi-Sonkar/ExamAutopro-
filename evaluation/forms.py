from django import forms
from .models import ScoringRange

class ScoringRangeForm(forms.ModelForm):
    class Meta:
        model = ScoringRange
        fields = [
            'name', 
            'description', 
            'min_similarity', 
            'max_similarity', 
            'marks_percentage', 
            'total_questions',
            'total_marks',
            'marks_per_question',
            'exam', 
            'pdf_document', 
            'paper_image',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter rule name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe when this rule applies'
            }),
            'min_similarity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.0',
                'max': '1.0'
            }),
            'max_similarity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.0',
                'max': '1.0'
            }),
            'marks_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '100'
            }),
            'total_questions': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Enter total number of questions'
            }),
            'total_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Enter total marks'
            }),
            'marks_per_question': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Enter marks per question'
            }),
            'exam': forms.Select(attrs={
                'class': 'form-select'
            }),
            'pdf_document': forms.Select(attrs={
                'class': 'form-select'
            }),
            'paper_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        min_similarity = cleaned_data.get('min_similarity')
        max_similarity = cleaned_data.get('max_similarity')
        marks_percentage = cleaned_data.get('marks_percentage')

        # Validate similarity range
        if min_similarity is not None and max_similarity is not None:
            if min_similarity > max_similarity:
                raise forms.ValidationError("Minimum similarity cannot be greater than maximum similarity.")
            
            if min_similarity < 0 or min_similarity > 1:
                raise forms.ValidationError("Minimum similarity must be between 0.0 and 1.0.")
            
            if max_similarity < 0 or max_similarity > 1:
                raise forms.ValidationError("Maximum similarity must be between 0.0 and 1.0.")

        # Validate marks percentage
        if marks_percentage is not None:
            if marks_percentage < 0 or marks_percentage > 100:
                raise forms.ValidationError("Marks percentage must be between 0 and 100.")

        # Validate new fields
        total_questions = cleaned_data.get('total_questions')
        total_marks = cleaned_data.get('total_marks')
        marks_per_question = cleaned_data.get('marks_per_question')

        if total_questions is not None and total_questions < 0:
            raise forms.ValidationError("Total questions cannot be negative.")

        if total_marks is not None and total_marks < 0:
            raise forms.ValidationError("Total marks cannot be negative.")

        if marks_per_question is not None and marks_per_question < 0:
            raise forms.ValidationError("Marks per question cannot be negative.")

        # Validate logical consistency
        if total_questions and total_marks and marks_per_question:
            calculated_marks_per_question = total_marks / total_questions
            if abs(calculated_marks_per_question - marks_per_question) > 0.01:
                raise forms.ValidationError(
                    f"Marks per question ({marks_per_question}) doesn't match "
                    f"total marks ({total_marks}) divided by questions ({total_questions}). "
                    f"Expected: {calculated_marks_per_question:.2f}"
                )

        return cleaned_data

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter exams by teacher
            self.fields['exam'].queryset = user.exam_set.all()
            
            # Filter PDF documents by user
            from pdf_analysis.models import PDFDocument
            self.fields['pdf_document'].queryset = PDFDocument.objects.filter(uploaded_by=user)
        
        # Add help texts
        self.fields['min_similarity'].help_text = "Minimum similarity score (0.0 to 1.0)"
        self.fields['max_similarity'].help_text = "Maximum similarity score (0.0 to 1.0)"
        self.fields['marks_percentage'].help_text = "Percentage of total marks to award for this range (0 to 100)"
        self.fields['total_questions'].help_text = "Total number of questions in this evaluation"
        self.fields['total_marks'].help_text = "Total marks allocated for all questions"
        self.fields['marks_per_question'].help_text = "Marks allocated per individual question"
        self.fields['exam'].help_text = "If selected, rule applies only to this exam"
        self.fields['pdf_document'].help_text = "If selected, rule applies only to this PDF"
        self.fields['is_active'].help_text = "Enable this scoring rule"
