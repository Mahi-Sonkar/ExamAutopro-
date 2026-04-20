"""
Fixed PDF Analysis Views with Enhanced OCR + NLP
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
import logging
import threading

from .models import PDFDocument, PDFAnalysisResult, PDFProcessingLog
from .forms import PDFUploadForm, PDFSearchForm

logger = logging.getLogger(__name__)

class PDFListView(LoginRequiredMixin, ListView):
    """List view for PDF documents"""
    model = PDFDocument
    template_name = 'pdf_analysis/pdf_list.html'
    context_object_name = 'pdf_documents'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = PDFDocument.objects.filter(uploaded_by=self.request.user)
        
        # Filter by document type
        document_type = self.request.GET.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        # Filter by analysis status
        analysis_status = self.request.GET.get('analysis_status')
        if analysis_status:
            queryset = queryset.filter(analysis_status=analysis_status)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)
        
        return queryset.order_by('-uploaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PDFSearchForm(self.request.GET)
        context['total_count'] = self.get_queryset().count()
        return context

@login_required
def pdf_detail(request, pk):
    pdf_document = get_object_or_404(PDFDocument, pk=pk, uploaded_by=request.user)
    analysis_result = PDFAnalysisResult.objects.filter(pdf_document=pdf_document).first()
    questions = pdf_document.extracted_questions.all()
    
    return render(request, 'pdf_analysis/pdf_detail.html', {
        'pdf_document': pdf_document,
        'analysis_result': analysis_result,
        'questions': questions
    })

class PDFUploadView(LoginRequiredMixin, CreateView):
    """View for uploading PDF documents with Enhanced OCR + NLP"""
    model = PDFDocument
    form_class = PDFUploadForm
    template_name = 'pdf_analysis/pdf_upload.html'
    
    def get_success_url(self):
        return reverse_lazy('pdf_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        response = super().form_valid(form)
        
        # Start enhanced analysis in background
        try:
            self.analyze_pdf_enhanced(form.instance)
            messages.success(self.request, 'PDF uploaded successfully! Enhanced analysis started.')
        except Exception as e:
            logger.error(f"Error starting enhanced PDF analysis: {str(e)}")
            messages.warning(self.request, 'PDF uploaded but enhanced analysis failed to start.')
        
        return response

    def form_invalid(self, form):
        """Log form errors for debugging"""
        print(f"DEBUG: Form invalid: {form.errors}")
        logger.warning(f"PDF upload form invalid: {form.errors}")
        return super().form_invalid(form)
    
    def analyze_pdf_enhanced(self, pdf_document):
        """Analyze PDF with Enhanced OCR + NLP"""
        print(f"DEBUG: Starting enhanced analysis for {pdf_document.title}")
        
        import threading
        
        def run_enhanced_analysis():
            try:
                # Update status to processing
                pdf_document.analysis_status = 'processing'
                pdf_document.save()
                
                # Log start
                PDFProcessingLog.objects.create(
                    pdf_document=pdf_document,
                    log_level='info',
                    message='Starting Enhanced PDF analysis'
                )
                
                # Enhanced OCR text extraction
                print(f"DEBUG: Enhanced OCR extraction from {pdf_document.pdf_file.path}")
                from .enhanced_ocr_engine import enhanced_ocr
                ocr_result = enhanced_ocr.extract_text_from_pdf(pdf_document.pdf_file.path)
                
                print(f"DEBUG: Enhanced OCR extracted {len(ocr_result['text'])} characters")
                
                # Update document with OCR results
                pdf_document.page_count = ocr_result.get('page_count')
                pdf_document.save()
                
                # Enhanced NLP analysis with score range evaluation
                print("DEBUG: Performing Enhanced NLP analysis")
                try:
                    from .enhanced_nlp_engine import enhanced_nlp
                    nlp_result = enhanced_nlp.analyze_text_comprehensive(ocr_result['text'])
                    
                    # Extract questions for storage
                    questions = nlp_result.get('question_analysis', [])
                    
                    # Save analysis result with enhanced data
                    PDFAnalysisResult.objects.update_or_create(
                        pdf_document=pdf_document,
                        defaults={
                            'extracted_text': ocr_result['text'],
                            'ocr_confidence': ocr_result.get('confidence', 0.0),
                            'processing_time': 0.0,
                            'word_count': nlp_result.get('text_statistics', {}).get('word_count', 0),
                            'sentence_count': nlp_result.get('text_statistics', {}).get('sentence_count', 0),
                            'paragraph_count': nlp_result.get('text_statistics', {}).get('char_count', 0) // 100,
                            'language_detected': 'en',
                            'readability_score': nlp_result.get('overall_score', 0.0),
                            'complexity_score': nlp_result.get('complexity_analysis', {}).get('technical_terms_ratio', 0.0) * 100,
                            'main_topics': nlp_result.get('content_analysis', {}).get('domain_scores', {}).keys(),
                            'keywords': list(nlp_result.get('content_analysis', {}).get('domain_scores', {}).keys()),
                            'entities': {},
                            'detected_questions': [q['question'] for q in questions],
                            'question_count': len(questions),
                            'question_types': {},
                            'sentiment_score': 0.5,
                            'sentiment_label': 'neutral',
                            'summary': f"Analysis complete with {len(questions)} questions detected",
                            'key_points': nlp_result.get('recommendations', []),
                            'overall_score': nlp_result.get('overall_score', 0.0),
                            'score_category': nlp_result.get('score_category', 'average'),
                            'content_analysis': nlp_result.get('content_analysis', {}),
                            'complexity_analysis': nlp_result.get('complexity_analysis', {}),
                            'question_analysis': questions,
                            'recommendations': nlp_result.get('recommendations', [])
                        }
                    )
                    
                    # Update status to completed
                    pdf_document.analysis_status = 'completed'
                    pdf_document.save()
                    
                    print("DEBUG: Enhanced analysis completed successfully")
                    
                except Exception as nlp_err:
                    logger.error(f"Enhanced NLP analysis failed: {str(nlp_err)}")
                    pdf_document.analysis_status = 'failed'
                    pdf_document.save()
                    
            except Exception as e:
                logger.error(f"Enhanced analysis failed: {str(e)}")
                pdf_document.analysis_status = 'failed'
                pdf_document.save()
        
        # Start analysis in background thread
        thread = threading.Thread(target=run_enhanced_analysis)
        thread.daemon = True
        thread.start()

@login_required
def retry_analysis(request, pk):
    """Retry PDF analysis"""
    pdf_document = get_object_or_404(PDFDocument, pk=pk, uploaded_by=request.user)
    
    try:
        # Reset status
        pdf_document.analysis_status = 'pending'
        pdf_document.save()
        
        # Start analysis
        upload_view = PDFUploadView()
        upload_view.analyze_pdf_enhanced(pdf_document)
        
        messages.success(request, 'Analysis restarted successfully!')
    except Exception as e:
        logger.error(f"Error restarting analysis: {str(e)}")
        messages.error(request, 'Failed to restart analysis.')
    
    return redirect('pdf_detail', pk=pk)
