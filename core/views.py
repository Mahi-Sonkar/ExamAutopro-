"""
Scoring Configuration Views for ExamAutoPro
Main motive: Teacher scoring configuration and evaluation settings
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
import json
from io import BytesIO

# Try to import pandas, fallback to basic implementation if not available
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from .models import (
    ScoringConfiguration, QuestionWiseScoring, EvaluationTemplate, 
    ScoringRule, BulkQuestionUpload
)
from .forms import (
    ScoringConfigurationForm, QuestionWiseScoringForm, EvaluationTemplateForm,
    ScoringRuleForm, BulkQuestionUploadForm
)
from exams.models import Exam

@login_required
def scoring_dashboard(request):
    """Main scoring configuration dashboard"""
    
    # Get teacher's scoring configurations
    scoring_configs = ScoringConfiguration.objects.filter(
        teacher=request.user, is_active=True
    ).select_related('exam')
    
    # Get recent uploads
    recent_uploads = BulkQuestionUpload.objects.filter(
        teacher=request.user
    ).order_by('-created_at')[:5]
    
    # Get templates
    templates = EvaluationTemplate.objects.filter(
        teacher=request.user
    ).order_by('-updated_at')[:5]
    
    context = {
        'scoring_configs': scoring_configs,
        'recent_uploads': recent_uploads,
        'templates': templates,
        'title': 'Scoring Configuration Dashboard'
    }
    
    return render(request, 'core/scoring_dashboard.html', context)

class ScoringConfigurationCreateView(LoginRequiredMixin, CreateView):
    """Create new scoring configuration"""
    
    model = ScoringConfiguration
    form_class = ScoringConfigurationForm
    template_name = 'core/scoring_config_form.html'
    success_url = reverse_lazy('core:scoring_dashboard')
    
    def form_valid(self, form):
        form.instance.teacher = self.request.user
        messages.success(self.request, 'Scoring configuration created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Scoring Configuration'
        context['exams'] = Exam.objects.filter(teacher=self.request.user)
        return context

class ScoringConfigurationUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing scoring configuration"""
    
    model = ScoringConfiguration
    form_class = ScoringConfigurationForm
    template_name = 'core/scoring_config_form.html'
    success_url = reverse_lazy('core:scoring_dashboard')
    
    def get_queryset(self):
        return ScoringConfiguration.objects.filter(teacher=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Scoring configuration updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Scoring Configuration'
        context['exams'] = Exam.objects.filter(teacher=self.request.user)
        return context

@login_required
def question_wise_scoring(request, config_id):
    """Question-wise scoring setup"""
    
    scoring_config = get_object_or_404(
        ScoringConfiguration, 
        id=config_id, 
        teacher=request.user
    )
    
    if request.method == 'POST':
        # Handle bulk question setup
        if 'bulk_setup' in request.POST:
            return handle_bulk_question_setup(request, scoring_config)
        
        # Handle individual question setup
        elif 'save_question' in request.POST:
            return handle_individual_question_setup(request, scoring_config)
    
    # Get existing questions
    questions = QuestionWiseScoring.objects.filter(
        scoring_config=scoring_config
    ).order_by('question_number')
    
    context = {
        'scoring_config': scoring_config,
        'questions': questions,
        'title': f'Question-wise Scoring - {scoring_config.exam.title if scoring_config.exam else "Default"}'
    }
    
    return render(request, 'core/question_wise_scoring.html', context)

@login_required
def similarity_range_settings(request, config_id):
    """Similarity range configuration page"""
    
    scoring_config = get_object_or_404(
        ScoringConfiguration, 
        id=config_id, 
        teacher=request.user
    )
    
    if request.method == 'POST':
        # Update similarity ranges
        scoring_config.full_marks_threshold = float(request.POST.get('full_marks_threshold', 0.8))
        scoring_config.partial_marks_threshold = float(request.POST.get('partial_marks_threshold', 0.6))
        scoring_config.minimum_marks_threshold = float(request.POST.get('minimum_marks_threshold', 0.4))
        
        scoring_config.full_marks_percentage = float(request.POST.get('full_marks_percentage', 100.0))
        scoring_config.partial_marks_percentage = float(request.POST.get('partial_marks_percentage', 50.0))
        scoring_config.minimum_marks_percentage = float(request.POST.get('minimum_marks_percentage', 25.0))
        
        scoring_config.save()
        messages.success(request, 'Similarity ranges updated successfully!')
        return redirect('core:question_wise_scoring', config_id=config_id)
    
    # Get existing questions and group them by ranges
    questions = QuestionWiseScoring.objects.filter(
        scoring_config=scoring_config
    ).order_by('question_number')
    
    # Calculate question ranges
    question_ranges = []
    if questions:
        current_range = None
        
        for question in questions:
            if (current_range is None or 
                question.question_number != current_range['end'] + 1 or
                question.max_marks != current_range['marks_per_question'] or
                question.question_type != current_range['question_type']):
                
                # Start new range
                if current_range:
                    question_ranges.append(current_range)
                
                current_range = {
                    'start': question.question_number,
                    'end': question.question_number,
                    'marks_per_question': question.max_marks,
                    'question_type': question.question_type,
                    'question_count': 1,
                    'total_marks': question.max_marks
                }
            else:
                # Continue current range
                current_range['end'] = question.question_number
                current_range['question_count'] += 1
                current_range['total_marks'] += question.max_marks
        
        # Add the last range
        if current_range:
            question_ranges.append(current_range)
    
    # Calculate statistics
    total_questions = questions.count()
    total_marks = sum(q.max_marks for q in questions)
    question_types = set(q.question_type for q in questions)
    custom_settings_count = sum(1 for q in questions 
                              if q.custom_full_threshold or 
                              q.custom_partial_threshold or 
                              q.custom_minimum_threshold)
    
    context = {
        'scoring_config': scoring_config,
        'question_ranges': question_ranges,
        'total_questions': total_questions,
        'total_marks': total_marks,
        'question_count': len(question_types),
        'custom_settings_count': custom_settings_count,
        'title': f'Similarity Range Settings - {scoring_config.exam.title if scoring_config.exam else "Default"}'
    }
    
    return render(request, 'core/similarity_range_settings.html', context)

@login_required
def evaluation_templates(request):
    """Manage evaluation templates"""
    
    templates = EvaluationTemplate.objects.filter(
        teacher=request.user
    ).order_by('-updated_at')
    
    if request.method == 'POST':
        form = EvaluationTemplateForm(request.POST)
        if form.is_valid():
            form.instance.teacher = request.user
            form.save()
            messages.success(request, 'Template created successfully!')
            return redirect('core:evaluation_templates')
    else:
        form = EvaluationTemplateForm()
    
    context = {
        'templates': templates,
        'form': form,
        'title': 'Evaluation Templates'
    }
    
    return render(request, 'core/evaluation_templates.html', context)

@login_required
def bulk_question_upload(request):
    """Bulk question upload and scoring setup"""
    
    if request.method == 'POST':
        form = BulkQuestionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.teacher = request.user
            form.instance.status = 'pending'
            form.save()
            
            # Process the upload
            process_bulk_upload(form.instance)
            
            messages.success(request, 'Questions uploaded successfully!')
            return redirect('core:scoring_dashboard')
    else:
        form = BulkQuestionUploadForm()
    
    # Get teacher's exams
    exams = Exam.objects.filter(teacher=request.user)
    
    context = {
        'form': form,
        'exams': exams,
        'title': 'Bulk Question Upload'
    }
    
    return render(request, 'core/bulk_question_upload.html', context)

@login_required
def scoring_preview(request, config_id):
    """Preview scoring configuration"""
    
    scoring_config = get_object_or_404(
        ScoringConfiguration, 
        id=config_id, 
        teacher=request.user
    )
    
    questions = QuestionWiseScoring.objects.filter(
        scoring_config=scoring_config
    ).order_by('question_number')
    
    context = {
        'scoring_config': scoring_config,
        'questions': questions,
        'title': 'Scoring Preview'
    }
    
    return render(request, 'core/scoring_preview.html', context)

@login_required
def export_scoring_config(request, config_id):
    """Export scoring configuration as Excel"""
    
    scoring_config = get_object_or_404(
        ScoringConfiguration, 
        id=config_id, 
        teacher=request.user
    )
    
    questions = QuestionWiseScoring.objects.filter(
        scoring_config=scoring_config
    ).order_by('question_number')
    
    if PANDAS_AVAILABLE:
        # Create Excel file with pandas
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Configuration sheet
            config_data = {
                'Setting': ['Full Marks Threshold', 'Partial Marks Threshold', 'Minimum Marks Threshold',
                           'Full Marks Percentage', 'Partial Marks Percentage', 'Minimum Marks Percentage',
                           'Keyword Weight', 'Concept Weight', 'Structure Weight'],
                'Value': [
                    scoring_config.full_marks_threshold,
                    scoring_config.partial_marks_threshold,
                    scoring_config.minimum_marks_threshold,
                    scoring_config.full_marks_percentage,
                    scoring_config.partial_marks_percentage,
                    scoring_config.minimum_marks_percentage,
                    scoring_config.keyword_weight,
                    scoring_config.concept_weight,
                    scoring_config.structure_weight
                ]
            }
            
            pd.DataFrame(config_data).to_excel(writer, sheet_name='Configuration', index=False)
            
            # Questions sheet
            questions_data = []
            for q in questions:
                questions_data.append({
                    'Question Number': q.question_number,
                    'Question Text': q.question_text,
                    'Max Marks': q.max_marks,
                    'Question Type': q.question_type,
                    'Required Keywords': q.required_keywords,
                    'Evaluation Method': q.evaluation_method
                })
            
            pd.DataFrame(questions_data).to_excel(writer, sheet_name='Questions', index=False)
        
        output.seek(0)
        
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=scoring_config_{config_id}.xlsx'
        
        return response
    else:
        # Fallback to CSV export if pandas is not available
        import csv
        from django.utils.http import urlquote
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=scoring_config_{config_id}.csv'
        
        writer = csv.writer(response)
        
        # Write configuration
        writer.writerow(['Configuration'])
        writer.writerow(['Setting', 'Value'])
        writer.writerow(['Full Marks Threshold', scoring_config.full_marks_threshold])
        writer.writerow(['Partial Marks Threshold', scoring_config.partial_marks_threshold])
        writer.writerow(['Minimum Marks Threshold', scoring_config.minimum_marks_threshold])
        writer.writerow(['Full Marks Percentage', scoring_config.full_marks_percentage])
        writer.writerow(['Partial Marks Percentage', scoring_config.partial_marks_percentage])
        writer.writerow(['Minimum Marks Percentage', scoring_config.minimum_marks_percentage])
        writer.writerow(['Keyword Weight', scoring_config.keyword_weight])
        writer.writerow(['Concept Weight', scoring_config.concept_weight])
        writer.writerow(['Structure Weight', scoring_config.structure_weight])
        
        writer.writerow([])  # Empty row
        writer.writerow(['Questions'])
        writer.writerow(['Question Number', 'Question Text', 'Max Marks', 'Question Type', 'Required Keywords', 'Evaluation Method'])
        
        for q in questions:
            writer.writerow([
                q.question_number,
                q.question_text,
                q.max_marks,
                q.question_type,
                q.required_keywords,
                q.evaluation_method
            ])
        
        return response

@login_required
def import_scoring_config(request):
    """Import scoring configuration from Excel"""
    
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        
        if excel_file:
            try:
                if PANDAS_AVAILABLE:
                    # Read Excel file with pandas
                    df_config = pd.read_excel(excel_file, sheet_name='Configuration')
                    df_questions = pd.read_excel(excel_file, sheet_name='Questions')
                    
                    # Create scoring configuration
                    scoring_config = ScoringConfiguration.objects.create(
                        teacher=request.user,
                        full_marks_threshold=df_config.loc[df_config['Setting'] == 'Full Marks Threshold', 'Value'].iloc[0],
                        partial_marks_threshold=df_config.loc[df_config['Setting'] == 'Partial Marks Threshold', 'Value'].iloc[0],
                        minimum_marks_threshold=df_config.loc[df_config['Setting'] == 'Minimum Marks Threshold', 'Value'].iloc[0],
                        full_marks_percentage=df_config.loc[df_config['Setting'] == 'Full Marks Percentage', 'Value'].iloc[0],
                        partial_marks_percentage=df_config.loc[df_config['Setting'] == 'Partial Marks Percentage', 'Value'].iloc[0],
                        minimum_marks_percentage=df_config.loc[df_config['Setting'] == 'Minimum Marks Percentage', 'Value'].iloc[0]
                )
                
                # Create questions
                for _, row in df_questions.iterrows():
                    QuestionWiseScoring.objects.create(
                        scoring_config=scoring_config,
                        question_number=row['Question Number'],
                        question_text=row['Question Text'],
                        max_marks=row['Max Marks'],
                        question_type=row['Question Type'],
                        required_keywords=row['Required Keywords'],
                        evaluation_method=row['Evaluation Method']
                    )
                
                messages.success(request, 'Scoring configuration imported successfully!')
                return redirect('core:scoring_dashboard')
                
            except Exception as e:
                messages.error(request, f'Error importing configuration: {str(e)}')
    
    return render(request, 'core/import_scoring_config.html', {
        'title': 'Import Scoring Configuration'
    })

@login_required
def bulk_question_setup(request, config_id):
    """View to handle bulk question marks setup from question ranges"""
    
    scoring_config = get_object_or_404(
        ScoringConfiguration, 
        id=config_id, 
        teacher=request.user
    )
    
    if request.method == 'POST':
        return handle_bulk_question_setup(request, scoring_config)
    
    return redirect('core:question_wise_scoring', config_id=config_id)

@login_required
def delete_question_range(request, config_id):
    """Delete a range of questions"""
    
    scoring_config = get_object_or_404(
        ScoringConfiguration, 
        id=config_id, 
        teacher=request.user
    )
    
    if request.method == 'POST':
        start_q = int(request.POST.get('start_q', 0))
        end_q = int(request.POST.get('end_q', 0))
        
        if start_q and end_q:
            QuestionWiseScoring.objects.filter(
                scoring_config=scoring_config,
                question_number__range=(start_q, end_q)
            ).delete()
            messages.success(request, f'Questions {start_q} to {end_q} deleted successfully.')
        
    return redirect(request.META.get('HTTP_REFERER', 'core:similarity_range_settings'))

# Helper functions
def handle_bulk_question_setup(request, scoring_config):
    """Handle bulk question setup"""
    
    start_question = int(request.POST.get('start_question', 1))
    end_question = int(request.POST.get('end_question', 10))
    marks_per_question = float(request.POST.get('marks_per_question', 1.0))
    question_type = request.POST.get('question_type', 'short_answer')
    
    # Create or update questions in bulk
    for q_num in range(start_question, end_question + 1):
        QuestionWiseScoring.objects.update_or_create(
            scoring_config=scoring_config,
            question_number=q_num,
            defaults={
                'max_marks': marks_per_question,
                'question_type': question_type
            }
        )
    
    messages.success(request, f'Marks updated for Questions {start_question} to {end_question}: {marks_per_question} marks each.')
    
    # Redirect based on where the request came from
    redirect_to = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if redirect_to:
        return redirect(redirect_to)
    
    return redirect('core:question_wise_scoring', config_id=scoring_config.id)

def handle_individual_question_setup(request, scoring_config):
    """Handle individual question setup"""
    
    question_number = int(request.POST.get('question_number'))
    max_marks = float(request.POST.get('max_marks', 1.0))
    question_text = request.POST.get('question_text', '')
    question_type = request.POST.get('question_type', 'short_answer')
    required_keywords = request.POST.get('required_keywords', '')
    
    question, created = QuestionWiseScoring.objects.update_or_create(
        scoring_config=scoring_config,
        question_number=question_number,
        defaults={
            'question_text': question_text,
            'max_marks': max_marks,
            'question_type': question_type,
            'required_keywords': required_keywords
        }
    )
    
    if created:
        messages.success(request, f'Question {question_number} created successfully!')
    else:
        messages.success(request, f'Question {question_number} updated successfully!')
    
    return redirect('core:question_wise_scoring', config_id=scoring_config.id)

def process_bulk_upload(bulk_upload):
    """Process bulk question upload"""
    
    try:
        bulk_upload.status = 'processing'
        bulk_upload.save()
        
        # Read the uploaded file
        if bulk_upload.file_type == 'excel':
            df = pd.read_excel(bulk_upload.upload_file)
        elif bulk_upload.file_type == 'csv':
            df = pd.read_csv(bulk_upload.upload_file)
        elif bulk_upload.file_type == 'json':
            with open(bulk_upload.upload_file.path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        
        # Process questions
        scoring_config = ScoringConfiguration.objects.create(
            teacher=bulk_upload.teacher,
            exam=bulk_upload.exam
        )
        
        for index, row in df.iterrows():
            try:
                QuestionWiseScoring.objects.create(
                    scoring_config=scoring_config,
                    question_number=row.get('question_number', index + 1),
                    question_text=row.get('question_text', ''),
                    max_marks=row.get('max_marks', 1.0),
                    question_type=row.get('question_type', 'short_answer'),
                    required_keywords=row.get('required_keywords', ''),
                    evaluation_method=row.get('evaluation_method', 'automatic')
                )
                bulk_upload.processed_questions += 1
            except Exception as e:
                bulk_upload.failed_questions += 1
                bulk_upload.error_log += f"Error in row {index + 1}: {str(e)}\n"
        
        bulk_upload.total_questions = len(df)
        bulk_upload.mark_completed()
        
    except Exception as e:
        bulk_upload.status = 'failed'
        bulk_upload.error_log = str(e)
        bulk_upload.save()
