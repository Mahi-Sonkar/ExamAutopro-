from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q
from .models import Exam, Question, Answer, ExamSubmission, QuestionOption
from .forms import ExamForm, QuickExamForm, QuestionForm, QuestionOptionFormSet
from evaluation.utils import trigger_ai_evaluation

# Import OCR Engine
try:
    from pdf_analysis.simple_ocr_engine import SimpleOCREngine as OCREngine
except ImportError:
    # Fallback if OCR engine is not available
    class OCREngine:
        def process_answer(self, answer):
            return {'success': False, 'error': 'OCR Engine not available'}

class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 10
    
    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return Exam.objects.filter(teacher=user).order_by('-created_at')
        elif user.is_student:
            return Exam.objects.filter(status='published').order_by('-start_time')
        else:
            return Exam.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Calculate statistics
        context['total_exams'] = queryset.count()
        context['published_exams'] = queryset.filter(status='published').count()
        context['ongoing_exams'] = queryset.filter(status='ongoing').count()
        context['completed_exams'] = queryset.filter(status='completed').count()
        
        return context

class ExamCreateView(LoginRequiredMixin, CreateView):
    model = Exam
    form_class = QuickExamForm
    template_name = 'exams/exam_form.html'
    
    def get_success_url(self):
        return reverse_lazy('exam_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Create instance without saving to DB yet
        self.object = form.save(commit=False)
        self.object.teacher = self.request.user
        
        # Provide defaults for required fields not in QuickExamForm
        if not self.object.start_time:
            self.object.start_time = timezone.now()
        if not self.object.end_time:
            self.object.end_time = timezone.now() + timezone.timedelta(hours=24)
            
        # Save to DB
        self.object.save()
        
        messages.success(self.request, 'Exam basic details saved! Now you can add questions.')
        return redirect(self.get_success_url())
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_teacher:
            return HttpResponseForbidden("Only teachers can create exams.")
        return super().dispatch(request, *args, **kwargs)

class ExamDetailView(LoginRequiredMixin, DetailView):
    model = Exam
    template_name = 'exams/exam_detail.html'
    context_object_name = 'exam'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()
        context['submissions'] = ExamSubmission.objects.filter(exam=self.object)
        # Add question creation forms for Google Forms style interface
        context['question_form'] = QuestionForm()
        context['option_formset'] = QuestionOptionFormSet()
        return context

class ExamUpdateView(LoginRequiredMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exam_list')
    
    def dispatch(self, request, *args, **kwargs):
        exam = self.get_object()
        if request.user != exam.teacher and not request.user.is_admin_user:
            return HttpResponseForbidden("Only exam creator can edit exams.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Exam'
        context['submit_text'] = 'Update Exam'
        return context

@login_required
def create_question(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.user != exam.teacher:
        return HttpResponseForbidden("Only exam creator can add questions.")
    
    form = QuestionForm(request.POST or None, request.FILES or None)
    formset = QuestionOptionFormSet(request.POST or None, request.FILES or None)
    
    if request.method == 'POST':
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            
            if question.question_type in ['mcq', 'true_false']:
                formset = QuestionOptionFormSet(request.POST, request.FILES, instance=question)
                if formset.is_valid():
                    question.save()
                    formset.save()
                    messages.success(request, 'Question and options added successfully!')
                    return redirect('exam_detail', pk=exam.id)
            else:
                question.save()
                messages.success(request, 'Question added successfully!')
                return redirect('exam_detail', pk=exam.id)
        
        # If we are here, something was invalid
        messages.error(request, 'There were errors in your question. Please check the form below.')
    
    return render(request, 'exams/question_form.html', {
        'form': form,
        'formset': formset,
        'exam': exam
    })

@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Allow students, teachers (for testing), and admins (for testing) to take exams
    # if not request.user.is_student:
    #    return HttpResponseForbidden("Only students can take exams.")
    
    if not exam.is_active and not (request.user.is_teacher or request.user.is_admin_user):
        messages.error(request, "This exam is not currently active.")
        return redirect('exam_list')
    
    # Check if student already has an active submission
    submission = ExamSubmission.objects.filter(
        student=request.user,
        exam=exam,
        status='in_progress'
    ).first()
    
    if not submission:
        # Check if student already has reached max attempts
        attempts = ExamSubmission.objects.filter(
            student=request.user,
            exam=exam
        )
        
        if not exam.allow_multiple_attempts and attempts.exists():
            messages.error(request, "You have already attempted this exam.")
            return redirect('exam_results', exam_id=exam.id)
            
        if attempts.count() >= exam.max_attempts:
            messages.error(request, f"You have reached the maximum number of attempts ({exam.max_attempts}).")
            return redirect('exam_results', exam_id=exam.id)
            
        # Get the next attempt number
        last_attempt = attempts.order_by('-attempt_number').first()
        next_attempt = (last_attempt.attempt_number + 1) if last_attempt else 1
        
        submission = ExamSubmission.objects.create(
            student=request.user,
            exam=exam,
            attempt_number=next_attempt,
            started_at=timezone.now()
        )
    
    questions = exam.questions.all()
    return render(request, 'exams/take_exam.html', {
        'exam': exam,
        'questions': questions,
        'submission': submission
    })

@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    submission = ExamSubmission.objects.filter(
        student=request.user, 
        exam=exam, 
        status='in_progress'
    ).first()
    
    if not submission:
        messages.error(request, "No active exam submission found. Please start the exam first.")
        return redirect('take_exam', exam_id=exam_id)
    
    if request.method == 'POST':
        submission.status = 'submitted'
        submission.submitted_at = timezone.now()
        submission.time_taken = (submission.submitted_at - submission.started_at).total_seconds()
        submission.save()
        
        ocr_engine = OCREngine()
        
        # Process answers
        for question in exam.questions.all():
            answer_key = f'question_{question.id}'
            file_key = f'file_{question.id}'
            
            if question.question_type in ['mcq', 'true_false']:
                option_id = request.POST.get(answer_key)
                if option_id:
                    try:
                        option = QuestionOption.objects.get(id=option_id)
                        Answer.objects.update_or_create(
                            submission=submission,
                            question=question,
                            defaults={
                                'selected_option': option,
                                'is_correct': option.is_correct,
                                'marks_obtained': question.marks if option.is_correct else 0
                            }
                        )
                    except QuestionOption.DoesNotExist:
                        pass
            else:
                answer_text = request.POST.get(answer_key, '')
                uploaded_file = request.FILES.get(file_key)
                
                answer, created = Answer.objects.update_or_create(
                    submission=submission,
                    question=question,
                    defaults={
                        'answer_text': answer_text,
                        'uploaded_file': uploaded_file
                    }
                )
                
                # If a file was uploaded, trigger OCR
                if uploaded_file:
                    try:
                        ocr_result = ocr_engine.process_answer(answer)
                        if ocr_result.get('success'):
                            # After OCR, answer.answer_text is updated
                            answer.refresh_from_db()
                    except Exception as e:
                        print(f"OCR processing failed for answer {answer.id}: {str(e)}")
                
                # Trigger AI evaluation for descriptive answers (either typed or OCR-ed)
                if answer.answer_text and answer.answer_text.strip():
                    try:
                        trigger_ai_evaluation(answer)
                    except Exception as e:
                        print(f"AI evaluation failed for answer {answer.id}: {str(e)}")
        
        # Calculate total marks for the submission after all evaluations
        total_marks = 0
        # Refresh submission to get updated answers
        submission.refresh_from_db()
        for answer in submission.answers.all():
            total_marks += answer.marks_obtained or 0
        submission.total_marks_obtained = total_marks
        
        # Calculate percentage
        if exam.total_marks > 0:
            submission.percentage = round((total_marks / exam.total_marks) * 100, 1)
        
        # Mark submission as evaluated
        submission.status = 'evaluated'
        submission.save()
        
        messages.success(request, 'Exam submitted successfully! Your answers have been evaluated by AI.')
        return redirect('exam_results', exam_id=exam.id)
    
    return redirect('take_exam', exam_id=exam.id)

@login_required
def exam_results(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.user.is_student:
        # Look for evaluated or submitted status
        submission = ExamSubmission.objects.filter(
            student=request.user,
            exam=exam
        ).exclude(status='in_progress').order_by('-submitted_at').first()
    else:
        submission = None
    
    return render(request, 'exams/exam_results.html', {
        'exam': exam,
        'submission': submission
    })

@login_required
def publish_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.user != exam.teacher:
        return HttpResponseForbidden("Only exam creator can publish.")
    
    if exam.questions.count() == 0:
        messages.error(request, "Cannot publish an exam without questions.")
        return redirect('exam_detail', pk=pk)
    
    exam.status = 'published'
    # Automatically set end_time if not set
    if not exam.end_time:
        exam.end_time = timezone.now() + timezone.timedelta(hours=24)
    exam.save()
    
    messages.success(request, f"Exam '{exam.title}' has been published! You can now share the link with students.")
    return redirect('exam_detail', pk=pk)

def search_exams(request):
    query = request.GET.get('q', '')
    exams = Exam.objects.filter(
        Q(title__icontains=query) | 
        Q(description__icontains=query) |
        Q(teacher__email__icontains=query)
    )
    
    return render(request, 'exams/search_results.html', {
        'exams': exams,
        'query': query
    })
