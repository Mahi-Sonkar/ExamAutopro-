from django import forms
from .models import Exam, Question, QuestionOption

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title', 'description', 'exam_type', 'duration', 'total_marks',
            'start_time', 'end_time', 'instructions', 'allow_multiple_attempts',
            'max_attempts', 'show_results_immediately', 'negative_marking',
            'negative_marks_percentage'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'instructions': forms.Textarea(attrs={'rows': 4}),
        }

class QuickExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'exam_type', 'duration', 'total_marks', 'start_time', 'end_time']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Untitled Exam'}),
            'exam_type': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': '60'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': '100'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control form-control-lg', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control form-control-lg', 'type': 'datetime-local'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'question_text', 'question_type', 'marks', 'required',
            'model_answer', 'keywords', 'has_image', 'question_image'
        ]
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Question text...'}),
            'model_answer': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'keywords': forms.TextInput(attrs={'placeholder': 'keyword1, keyword2, keyword3', 'class': 'form-control'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = ['option_text', 'is_correct']
        widgets = {
            'option_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter option text'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

QuestionOptionFormSet = forms.inlineformset_factory(
    Question,
    QuestionOption,
    form=QuestionOptionForm,
    extra=4,
    can_delete=True
)

# New FormSet for Questions inside Exam
ExamQuestionFormSet = forms.inlineformset_factory(
    Exam,
    Question,
    form=QuestionForm,
    extra=1,
    can_delete=True
)
