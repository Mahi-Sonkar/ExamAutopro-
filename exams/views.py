from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q
import re
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


def _answer_has_content(answer):
    return bool(
        answer.selected_option_id
        or (answer.answer_text and answer.answer_text.strip())
        or answer.uploaded_file
    )


def _submission_has_answer_content(submission):
    return any(_answer_has_content(answer) for answer in submission.answers.all())


def _is_objective_question(question):
    return question.question_type in ['mcq', 'true_false']


def _get_total_possible_marks(exam):
    total = sum(question.marks for question in exam.questions.all())
    return total or exam.total_marks


def _normalize_choice_text(value):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', value or '').lower()).strip()


def _finalize_submission_result(submission, force_ai=False):
    """
    Recalculate every saved answer and persist the submission total.
    This keeps submit and result-page refreshes on the same grading logic.
    """
    evaluation_failures = []
    total_marks = 0
    try:
        from evaluation.ai_clients import FreeAIEvaluator
        external_ai_available = FreeAIEvaluator().available
    except Exception:
        external_ai_available = False

    answers = submission.answers.select_related('question', 'selected_option').all()
    for answer in answers:
        question = answer.question

        if _is_objective_question(question):
            correct_options = list(question.options.filter(is_correct=True))
            is_correct = bool(answer.selected_option and answer.selected_option.is_correct)
            evaluated_by_ai = False
            confidence_score = 1.0
            feedback = 'Correct answer.' if is_correct else 'Incorrect answer.'

            if answer.selected_option and not correct_options and external_ai_available:
                try:
                    from evaluation.ai_clients import FreeAIEvaluator
                    option_texts = [option.option_text for option in question.options.all()]
                    ai_result = FreeAIEvaluator().evaluate_objective(
                        question_text=question.question_text,
                        options=option_texts,
                        selected_option=answer.selected_option.option_text,
                        max_marks=question.marks,
                    )
                    if ai_result:
                        correct_answer = ai_result.get('correct_answer') or ''
                        ai_score = float(ai_result.get('score', 0.0))
                        if correct_answer:
                            selected_norm = _normalize_choice_text(answer.selected_option.option_text)
                            correct_norm = _normalize_choice_text(correct_answer)
                            is_correct = selected_norm == correct_norm or ai_score >= float(question.marks)
                        else:
                            is_correct = ai_score >= float(question.marks)
                        confidence_score = ai_result.get('confidence', 0.0)
                        reason = ai_result.get('score_reason') or ai_result.get('feedback') or ''
                        feedback = reason
                        if correct_answer:
                            feedback = f"{feedback} Correct answer: {correct_answer}".strip()
                        evaluated_by_ai = True
                except Exception as exc:
                    evaluation_failures.append(f"Question {question.order or question.id}: {exc}")

            answer.is_correct = is_correct
            answer.marks_obtained = question.marks if is_correct else 0
            answer.evaluated_by_ai = evaluated_by_ai
            answer.confidence_score = confidence_score
            answer.feedback = feedback
            answer.save(update_fields=[
                'is_correct',
                'marks_obtained',
                'evaluated_by_ai',
                'confidence_score',
                'feedback',
            ])
        elif answer.answer_text and answer.answer_text.strip():
            try:
                evaluation_method = answer.evaluationresult.evaluation_method
                has_evaluation = True
            except Exception:
                evaluation_method = ''
                has_evaluation = False

            needs_evaluation = (
                force_ai
                or not answer.evaluated_by_ai
                or not has_evaluation
                or (external_ai_available and evaluation_method == 'local_nlp')
            )
            if needs_evaluation:
                eval_result = trigger_ai_evaluation(answer)
                if not eval_result.get('success'):
                    evaluation_failures.append(
                        f"Question {question.order or question.id}: {eval_result.get('error', 'AI evaluation failed')}"
                    )
                answer.refresh_from_db()

        total_marks += answer.marks_obtained or 0

    total_possible = _get_total_possible_marks(submission.exam)
    submission.total_marks_obtained = total_marks
    submission.percentage = round((total_marks / total_possible) * 100, 1) if total_possible else 0.0
    if submission.status in ['submitted', 'evaluated']:
        submission.status = 'evaluated'
    submission.save(update_fields=['total_marks_obtained', 'percentage', 'status'])

    return {
        'failures': evaluation_failures,
        'total_possible': total_possible,
    }

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
        # Check if student already has reached max attempts. Blank auto-submits
        # should not block a student from starting the real attempt.
        attempts = ExamSubmission.objects.filter(
            student=request.user,
            exam=exam
        )
        counted_attempts = [
            attempt for attempt in attempts.exclude(status='in_progress').prefetch_related('answers')
            if _submission_has_answer_content(attempt)
        ]

        if not exam.allow_multiple_attempts and counted_attempts:
            messages.error(request, "You have already attempted this exam.")
            return redirect('exam_results', exam_id=exam.id)

        if len(counted_attempts) >= exam.max_attempts:
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
    expires_at = submission.started_at + timezone.timedelta(minutes=exam.duration)
    return render(request, 'exams/take_exam.html', {
        'exam': exam,
        'questions': questions,
        'submission': submission,
        'expires_at': expires_at,
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
        # Check for exam termination
        termination_reason = request.POST.get('termination_reason')
        if termination_reason:
            # Handle exam termination due to violation
            submission.status = 'cancelled'
            submission.submitted_at = timezone.now()
            submission.time_taken = (submission.submitted_at - submission.started_at).total_seconds()
            submission.save()

            # Log the termination
            from proctoring.models import ProctoringEvent, ProctoringSession
            # Find or create a proctoring session for this exam
            proctoring_session = ProctoringSession.objects.filter(
                student=request.user,
                exam=exam,
                status='active'
            ).first()

            if proctoring_session:
                ProctoringEvent.objects.create(
                    session=proctoring_session,
                    event_type='unusual_activity',  # Use existing event type
                    description=f'Exam terminated due to: {termination_reason}',
                    severity='critical',
                    metadata={
                        'termination_reason': termination_reason,
                        'timestamp': timezone.now().isoformat(),
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    }
                )

            messages.error(request, f'Exam terminated: {termination_reason}. You cannot attempt this exam again.')
            return redirect('exam_results', exam_id=exam.id)

        ocr_engine = OCREngine()
        evaluation_failures = []
        submitted_answer_count = 0

        # Process answers
        for question in exam.questions.all():
            answer_key = f'question_{question.id}'
            file_key = f'file_{question.id}'

            if question.question_type in ['mcq', 'true_false']:
                option_id = request.POST.get(answer_key)
                if option_id:
                    try:
                        option = QuestionOption.objects.get(id=option_id, question=question)
                        Answer.objects.update_or_create(
                            submission=submission,
                            question=question,
                            defaults={
                                'selected_option': option,
                                'is_correct': option.is_correct,
                                'marks_obtained': question.marks if option.is_correct else 0
                            }
                        )
                        submitted_answer_count += 1
                    except QuestionOption.DoesNotExist:
                        evaluation_failures.append(f"Invalid option selected for question {question.id}.")
            else:
                answer_text = request.POST.get(answer_key, '')
                uploaded_file = request.FILES.get(file_key)

                if not answer_text.strip() and not uploaded_file:
                    Answer.objects.filter(submission=submission, question=question).delete()
                    continue

                answer, created = Answer.objects.update_or_create(
                    submission=submission,
                    question=question,
                    defaults={
                        'answer_text': answer_text,
                        'uploaded_file': uploaded_file
                    }
                )
                submitted_answer_count += 1

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
                        eval_result = trigger_ai_evaluation(answer)
                        if not eval_result.get('success'):
                            evaluation_failures.append(
                                f"Question {question.order or question.id}: {eval_result.get('error', 'AI evaluation failed')}"
                            )
                    except Exception as e:
                        evaluation_failures.append(f"Question {question.order or question.id}: {str(e)}")

        if submitted_answer_count == 0:
            messages.error(request, "Please answer at least one question before submitting the exam.")
            return redirect('take_exam', exam_id=exam.id)

        submission.status = 'submitted'
        submission.submitted_at = timezone.now()
        submission.time_taken = int((submission.submitted_at - submission.started_at).total_seconds())
        submission.save()

        result_summary = _finalize_submission_result(submission)
        evaluation_failures.extend(result_summary['failures'])

        if evaluation_failures:
            messages.warning(
                request,
                'Exam submitted successfully, but some answers could not be evaluated automatically. '
                'They have been saved for review.'
            )
        else:
            messages.success(request, 'Exam submitted successfully! Your answers have been evaluated by AI.')
        return redirect('exam_results', exam_id=exam.id)

    return redirect('take_exam', exam_id=exam.id)

@login_required
def exam_results(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user.is_student:
        # Look for evaluated or submitted status
        submissions = ExamSubmission.objects.filter(
            student=request.user,
            exam=exam
        ).exclude(status='in_progress').prefetch_related('answers').order_by('-submitted_at')
        submission = next(
            (item for item in submissions if _submission_has_answer_content(item)),
            None
        )
    else:
        submission = None

    total_possible = _get_total_possible_marks(exam)
    if submission:
        force_ai = request.GET.get('refresh_ai') == '1'
        result_summary = _finalize_submission_result(submission, force_ai=force_ai)
        total_possible = result_summary['total_possible']
        submission.refresh_from_db()

    return render(request, 'exams/exam_results.html', {
        'exam': exam,
        'submission': submission,
        'total_possible': total_possible,
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
