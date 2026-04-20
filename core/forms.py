"""
Scoring Configuration Forms for ExamAutoPro
Main motive: Teacher scoring configuration forms
"""

from django import forms
from django.forms import formset_factory
from .models import (
    ScoringConfiguration, QuestionWiseScoring, EvaluationTemplate, 
    ScoringRule, BulkQuestionUpload
)
from exams.models import Exam

class ScoringConfigurationForm(forms.ModelForm):
    """Scoring configuration form"""
    
    class Meta:
        model = ScoringConfiguration
        fields = [
            'exam', 'full_marks_threshold', 'partial_marks_threshold', 'minimum_marks_threshold',
            'full_marks_percentage', 'partial_marks_percentage', 'minimum_marks_percentage',
            'keyword_weight', 'concept_weight', 'structure_weight',
            'enable_grace_marks', 'grace_marks_percentage', 'borderline_threshold'
        ]
        widgets = {
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'full_marks_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'partial_marks_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'minimum_marks_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'full_marks_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1', 
                'min': '0', 
                'max': '100'
            }),
            'partial_marks_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1', 
                'min': '0', 
                'max': '100'
            }),
            'minimum_marks_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1', 
                'min': '0', 
                'max': '100'
            }),
            'keyword_weight': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'concept_weight': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'structure_weight': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'grace_marks_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1', 
                'min': '0', 
                'max': '100'
            }),
            'borderline_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1', 
                'min': '0', 
                'max': '100'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['exam'].queryset = Exam.objects.filter(teacher=user)
        
        # Add help text
        self.fields['full_marks_threshold'].help_text = "Minimum similarity for full marks (0.0-1.0)"
        self.fields['partial_marks_threshold'].help_text = "Minimum similarity for partial marks (0.0-1.0)"
        self.fields['minimum_marks_threshold'].help_text = "Minimum similarity for minimum marks (0.0-1.0)"
    
    def clean(self):
        cleaned_data = super().clean()
        
        full_threshold = cleaned_data.get('full_marks_threshold', 0)
        partial_threshold = cleaned_data.get('partial_marks_threshold', 0)
        minimum_threshold = cleaned_data.get('minimum_marks_threshold', 0)
        
        # Validate threshold logic
        if full_threshold <= partial_threshold:
            raise forms.ValidationError("Full marks threshold must be greater than partial marks threshold")
        
        if partial_threshold <= minimum_threshold:
            raise forms.ValidationError("Partial marks threshold must be greater than minimum marks threshold")
        
        # Validate weight sum
        keyword_weight = cleaned_data.get('keyword_weight', 0)
        concept_weight = cleaned_data.get('concept_weight', 0)
        structure_weight = cleaned_data.get('structure_weight', 0)
        
        total_weight = keyword_weight + concept_weight + structure_weight
        if abs(total_weight - 1.0) > 0.01:
            raise forms.ValidationError(f"Total weight must be 1.0 (current: {total_weight})")
        
        return cleaned_data

class QuestionWiseScoringForm(forms.ModelForm):
    """Question-wise scoring form"""
    
    class Meta:
        model = QuestionWiseScoring
        fields = [
            'question_number', 'question_text', 'max_marks', 'question_type',
            'custom_full_threshold', 'custom_partial_threshold', 'custom_minimum_threshold',
            'required_keywords', 'evaluation_method'
        ]
        widgets = {
            'question_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'custom_full_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'custom_partial_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'custom_minimum_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'required_keywords': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'keyword1, keyword2, keyword3'
            }),
            'evaluation_method': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['question_text'].help_text = "Enter the question text"
        self.fields['required_keywords'].help_text = "Comma-separated keywords required for full marks"
        self.fields['custom_full_threshold'].help_text = "Leave blank to use global threshold"
        self.fields['custom_partial_threshold'].help_text = "Leave blank to use global threshold"
        self.fields['custom_minimum_threshold'].help_text = "Leave blank to use global threshold"

class BulkQuestionSetupForm(forms.Form):
    """Bulk question setup form"""
    
    start_question = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    end_question = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    marks_per_question = forms.FloatField(
        min_value=0.5,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'})
    )
    question_type = forms.ChoiceField(
        choices=QuestionWiseScoring._meta.get_field('question_type').choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class SimilarityRangeForm(forms.ModelForm):
    """Similarity range configuration form"""
    
    class Meta:
        model = ScoringConfiguration
        fields = [
            'full_marks_threshold', 'partial_marks_threshold', 'minimum_marks_threshold',
            'full_marks_percentage', 'partial_marks_percentage', 'minimum_marks_percentage'
        ]
        widgets = {
            'full_marks_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'partial_marks_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'minimum_marks_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '1'
            }),
            'full_marks_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1', 
                'min': '0', 
                'max': '100'
            }),
            'partial_marks_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1', 
                'min': '0', 
                'max': '100'
            }),
            'minimum_marks_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1', 
                'min': '0', 
                'max': '100'
            }),
        }

class EvaluationTemplateForm(forms.ModelForm):
    """Evaluation template form"""
    
    class Meta:
        model = EvaluationTemplate
        fields = ['name', 'description', 'configuration', 'question_template', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'configuration': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'question_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['configuration'].help_text = "JSON configuration for scoring"
        self.fields['question_template'].help_text = "JSON template for question-wise scoring"

class ScoringRuleForm(forms.ModelForm):
    """Scoring rule form"""
    
    class Meta:
        model = ScoringRule
        fields = [
            'rule_name', 'rule_type', 'conditions', 'action_type', 'action_value', 'priority'
        ]
        widgets = {
            'rule_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'action_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['conditions'].help_text = "JSON format conditions"
        self.fields['priority'].help_text = "Higher priority rules are executed first"

class BulkQuestionUploadForm(forms.ModelForm):
    """Bulk question upload form"""
    
    class Meta:
        model = BulkQuestionUpload
        fields = ['exam', 'upload_file', 'file_type']
        widgets = {
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'upload_file': forms.FileInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['exam'].queryset = Exam.objects.filter(teacher=user)

# Formsets
QuestionWiseScoringFormSet = formset_factory(
    QuestionWiseScoringForm,
    extra=5,
    can_delete=True
)

class ScoringRangeCalculatorForm(forms.Form):
    """Form to calculate scoring ranges"""
    
    similarity_score = forms.FloatField(
        min_value=0,
        max_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Enter similarity score (0.0-1.0)'
        })
    )
    max_marks = forms.FloatField(
        min_value=0.5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5',
            'placeholder': 'Enter maximum marks'
        })
    )

class QuestionRangeSetupForm(forms.Form):
    """Form for setting up question ranges"""
    
    range_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    start_question = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    end_question = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    marks_per_question = forms.FloatField(
        min_value=0.5,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'})
    )
    question_type = forms.ChoiceField(
        choices=QuestionWiseScoring._meta.get_field('question_type').choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    evaluation_method = forms.ChoiceField(
        choices=QuestionWiseScoring._meta.get_field('evaluation_method').choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        start_question = cleaned_data.get('start_question')
        end_question = cleaned_data.get('end_question')
        
        if start_question and end_question:
            if start_question > end_question:
                raise forms.ValidationError("Start question cannot be greater than end question")
        
        return cleaned_data
