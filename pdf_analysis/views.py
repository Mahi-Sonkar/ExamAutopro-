"""
PDF Analysis Views - Simple and Working
Basic PDF upload and analysis functionality
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
import os
import json

@login_required
def pdf_upload_view(request):
    """PDF upload page"""
    from .forms import PDFUploadForm
    from exams.models import Exam
    
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the PDF document
            pdf_doc = form.save(commit=False)
            pdf_doc.uploaded_by = request.user
            pdf_doc.save()
            
            messages.success(request, f'PDF "{pdf_doc.title}" uploaded successfully!')
            return redirect('pdf_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PDFUploadForm()
    
    teacher_exams = Exam.objects.none()
    if getattr(request.user, 'role', None) == 'teacher':
        teacher_exams = Exam.objects.filter(teacher=request.user).prefetch_related('questions').order_by('-created_at')

    return render(request, 'pdf_analysis/pdf_upload.html', {
        'form': form,
        'teacher_exams': teacher_exams,
    })

@login_required
def pdf_list_view(request):
    """Show all uploaded PDFs with statistics, search and filtering"""
    from .models import PDFDocument
    from django.db.models import Q
    
    # Get all PDFs
    pdf_documents = PDFDocument.objects.all().order_by('-uploaded_at')
    
    # Apply filters
    query = request.GET.get('query')
    doc_type = request.GET.get('document_type')
    status = request.GET.get('analysis_status')
    
    if query:
        pdf_documents = pdf_documents.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    
    if doc_type:
        pdf_documents = pdf_documents.filter(document_type=doc_type)
        
    if status:
        pdf_documents = pdf_documents.filter(analysis_status=status)
    
    # Calculate statistics (based on filtered results or all? Usually all is better for overview)
    all_pdfs = PDFDocument.objects.all()
    completed_docs = all_pdfs.filter(analysis_status='completed').count()
    processing_docs = all_pdfs.filter(analysis_status='processing').count()
    pending_docs = all_pdfs.filter(analysis_status='pending').count()
    failed_docs = all_pdfs.filter(analysis_status='failed').count()
    
    context = {
        'pdf_documents': pdf_documents,
        'pdfs': pdf_documents,  # For compatibility
        'completed_docs': completed_docs,
        'processing_docs': processing_docs,
        'pending_docs': pending_docs,
        'failed_docs': failed_docs,
    }
    
    return render(request, 'pdf_analysis/pdf_list.html', context)

@login_required
def pdf_detail_view(request, pk):
    """Show PDF document details with analysis generation"""
    from .models import PDFDocument, PDFAnalysisResult
    from django.shortcuts import get_object_or_404
    import os
    import json
    
    pdf_document = get_object_or_404(PDFDocument, pk=pk)
    
    # Get or create analysis result
    analysis_result = None
    try:
        analysis_result = pdf_document.analysis_result
    except PDFAnalysisResult.DoesNotExist:
        analysis_result = None
    
    # If no analysis exists or status is pending/failed, trigger analysis
    if not analysis_result or pdf_document.analysis_status in ['pending', 'failed']:
        if pdf_document.pdf_file and os.path.exists(pdf_document.pdf_file.path):
            try:
                # Import our enhanced OCR/NLP engines
                from .enhanced_ocr_engine import enhanced_ocr
                from .enhanced_nlp_engine import EnhancedNLPEngine
                from .models import PDFProcessingLog, PDFQuestion
                from evaluation.models import ScoringRange
                import time
                
                # Fetch scoring ranges from database
                scoring_ranges = ScoringRange.objects.filter(is_active=True).order_by('-min_similarity')
                custom_rules = {}
                if scoring_ranges.exists():
                    for sr in scoring_ranges:
                        custom_rules[sr.name.lower()] = {
                            'range': (sr.min_similarity * 100, sr.max_similarity * 100),
                            'marks_percentage': sr.marks_percentage,
                            'criteria': [sr.description or sr.name]
                        }
                
                # Initialize engine with custom rules if available
                engine = EnhancedNLPEngine(custom_rules=custom_rules if custom_rules else None)
                
                # Update status to processing
                pdf_document.analysis_status = 'processing'
                pdf_document.save()
                
                PDFProcessingLog.objects.create(
                    pdf_document=pdf_document,
                    log_level='info',
                    message='Starting automatic PDF analysis with custom scoring rules'
                )
                
                # Perform analysis
                start_time = time.time()
                ocr_result = enhanced_ocr.extract_text_from_pdf(pdf_document.pdf_file.path)
                
                if ocr_result.get('text') and len(ocr_result.get('text', '').strip()) > 0:
                    extracted_text = ocr_result['text']
                    
                    # NLP analysis using the engine with custom rules
                    nlp_result = engine.analyze_text_comprehensive(extracted_text)
                    processing_time = time.time() - start_time
                    
                    # Prepare detected_questions for the template (list of dicts)
                    template_questions = []
                    for q in nlp_result.get('question_analysis', []):
                        template_questions.append({
                            'text': q.get('question', ''),
                            'type': q.get('type', 'Unknown'),
                            'confidence': q.get('score', 0.0) / 100.0
                        })
                    
                    # Create or update analysis result
                    analysis_result, created = PDFAnalysisResult.objects.update_or_create(
                        pdf_document=pdf_document,
                        defaults={
                            'extracted_text': extracted_text,
                            'ocr_confidence': ocr_result.get('confidence', 0.0),
                            'processing_time': processing_time,
                            'word_count': nlp_result.get('text_statistics', {}).get('word_count', 0),
                            'sentence_count': nlp_result.get('text_statistics', {}).get('sentence_count', 0),
                            'detected_questions': template_questions,
                            'question_count': len(template_questions),
                            'overall_score': nlp_result.get('overall_score', 0.0),
                            'score_category': nlp_result.get('score_category', 'average'),
                            'summary': nlp_result.get('recommendations', ["Analysis complete"])[0],
                            'content_analysis': nlp_result.get('content_analysis', {}),
                            'complexity_analysis': nlp_result.get('complexity_analysis', {}),
                            'question_analysis': nlp_result.get('question_analysis', []),
                            'recommendations': nlp_result.get('recommendations', [])
                        }
                    )
                    
                    # Save individual questions
                    PDFQuestion.objects.filter(pdf_document=pdf_document).delete()
                    for q_data in nlp_result.get('question_analysis', []):
                        PDFQuestion.objects.create(
                            pdf_document=pdf_document,
                            question_text=q_data.get('question', ''),
                            question_type=q_data.get('type', 'unknown'),
                            marks=int(q_data.get('weight', 1) * 10),
                            confidence_score=q_data.get('score', 0.0) / 100.0
                        )
                    
                    # Update PDF document status
                    pdf_document.analysis_status = 'completed'
                    pdf_document.save()
                    
                else:
                    # OCR failed
                    pdf_document.analysis_status = 'failed'
                    pdf_document.save()
                    
            except Exception as e:
                # Analysis failed
                pdf_document.analysis_status = 'failed'
                pdf_document.save()
                print(f"Analysis failed for {pdf_document.title}: {e}")
    
    context = {
        'pdf_document': pdf_document,
        'pdf': pdf_document,  # For backward compatibility
        'analysis_result': analysis_result,
        'processing_logs': pdf_document.processing_logs.all()[:10],
    }
    
    return render(request, 'pdf_analysis/pdf_detail.html', context)

@login_required
def pdf_delete_view(request, pk):
    """Delete a PDF document"""
    from .models import PDFDocument
    from django.shortcuts import get_object_or_404
    
    try:
        pdf = get_object_or_404(PDFDocument, pk=pk)
        title = pdf.title
        
        # Try to delete with proper error handling
        try:
            pdf.delete()
            messages.success(request, f'PDF "{title}" has been deleted.')
        except Exception as e:
            # If there's a database schema issue, try to handle it gracefully
            if "no such table" in str(e).lower():
                # Manually delete related objects if cascade delete fails
                try:
                    # Delete analysis results manually if they exist
                    if hasattr(pdf, 'analysis_result'):
                        pdf.analysis_result.delete()
                    # Delete processing logs manually if they exist
                    if hasattr(pdf, 'processing_logs'):
                        pdf.processing_logs.all().delete()
                    # Delete extracted questions manually if they exist
                    if hasattr(pdf, 'extracted_questions'):
                        pdf.extracted_questions.all().delete()
                    
                    # Finally delete the PDF document
                    pdf.delete()
                    messages.success(request, f'PDF "{title}" has been deleted.')
                except Exception as inner_e:
                    messages.error(request, f'Error deleting PDF: {str(inner_e)}')
            else:
                messages.error(request, f'Error deleting PDF: {str(e)}')
        
        return redirect('pdf_list')
    except Exception as e:
        messages.error(request, f'PDF not found or error occurred: {str(e)}')
        return redirect('pdf_list')

@login_required
def pdf_export_view(request, pk):
    """Export PDF analysis result"""
    from django.http import HttpResponse, JsonResponse
    from django.shortcuts import get_object_or_404
    from .models import PDFDocument, PDFAnalysisResult, PDFQuestion
    import json
    import csv
    from io import StringIO
    from datetime import datetime
    
    pdf = get_object_or_404(PDFDocument, pk=pk)
    export_format = request.GET.get('format', 'json')
    
    try:
        if export_format == 'json':
            # Export as JSON
            export_data = {
                'document_info': {
                    'id': str(pdf.id),
                    'title': pdf.title,
                    'description': pdf.description,
                    'document_type': pdf.document_type,
                    'uploaded_at': pdf.uploaded_at.isoformat(),
                    'uploaded_by': pdf.uploaded_by.email if pdf.uploaded_by else None,
                    'analysis_status': pdf.analysis_status,
                    'file_size': pdf.file_size,
                    'page_count': pdf.page_count
                },
                'analysis_results': [],
                'questions': []
            }
            
            # Get analysis results if they exist
            try:
                if hasattr(pdf, 'analysis_result') and pdf.analysis_result:
                    result = pdf.analysis_result
                    export_data['analysis_results'].append({
                        'extracted_text': result.extracted_text,
                        'ocr_confidence': result.ocr_confidence,
                        'processing_time': result.processing_time,
                        'word_count': result.word_count,
                        'sentence_count': result.sentence_count,
                        'paragraph_count': result.paragraph_count,
                        'language_detected': result.language_detected,
                        'readability_score': result.readability_score,
                        'complexity_score': result.complexity_score,
                        'main_topics': result.main_topics,
                        'keywords': result.keywords,
                        'detected_questions': result.detected_questions,
                        'question_count': result.question_count,
                        'overall_score': result.overall_score,
                        'score_category': result.score_category,
                        'summary': result.summary,
                        'content_analysis': result.content_analysis,
                        'complexity_analysis': result.complexity_analysis,
                        'question_analysis': result.question_analysis,
                        'recommendations': result.recommendations,
                        'sentiment_score': result.sentiment_score,
                        'sentiment_label': result.sentiment_label,
                        'auto_summary': result.auto_summary,
                        'key_points': result.key_points,
                        'analyzed_at': result.analyzed_at.isoformat() if result.analyzed_at else None,
                        'analysis_version': result.analysis_version
                    })
            except Exception as e:
                export_data['analysis_results'].append({
                    'error': f'Analysis results not available: {str(e)}'
                })
            
            # Get questions if they exist
            try:
                if hasattr(pdf, 'extracted_questions'):
                    for question in pdf.extracted_questions.all():
                        export_data['questions'].append({
                            'question_number': question.page_number,
                            'question_text': question.question_text,
                            'question_type': question.question_type,
                            'options': question.options,
                            'correct_answer': question.correct_answer,
                            'marks': question.marks,
                            'confidence_score': question.confidence_score,
                            'created_at': question.created_at.isoformat() if question.created_at else None
                        })
            except Exception as e:
                export_data['questions'].append({
                    'error': f'Questions not available: {str(e)}'
                })
            
            response = HttpResponse(
                json.dumps(export_data, indent=2),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{pdf.title}_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
            return response
            
        elif export_format == 'csv':
            # Export as CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Document ID', 'Title', 'Document Type', 'Status', 
                'Question Number', 'Question Text', 'Extracted Answer', 
                'Confidence Score', 'Processing Time', 'Created At'
            ])
            
            # Write analysis results
            if hasattr(pdf, 'analysis_results'):
                for result in pdf.analysis_results.all():
                    writer.writerow([
                        str(pdf.id),
                        pdf.title,
                        pdf.document_type,
                        pdf.analysis_status,
                        result.question_number,
                        result.question_text,
                        result.extracted_answer,
                        result.confidence_score,
                        result.processing_time,
                        result.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    ])
            
            response = HttpResponse(
                output.getvalue(),
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename="{pdf.title}_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            return response
            
        elif export_format == 'pdf':
            # Export analysis as PDF report
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            import io
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Center
            )
            story.append(Paragraph(f"Analysis Report: {pdf.title}", title_style))
            story.append(Spacer(1, 12))
            
            # Document Info
            doc_info_data = [
                ['Document ID', str(pdf.id)],
                ['Title', pdf.title],
                ['Document Type', pdf.document_type],
                ['Status', pdf.analysis_status],
                ['Uploaded By', pdf.uploaded_by.email if pdf.uploaded_by else 'N/A'],
                ['Uploaded At', pdf.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")]
            ]
            
            doc_info_table = Table(doc_info_data, colWidths=[2*inch, 4*inch])
            doc_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ]))
            
            story.append(doc_info_table)
            story.append(Spacer(1, 20))
            
            # Analysis Results
            if hasattr(pdf, 'analysis_results') and pdf.analysis_results.exists():
                story.append(Paragraph("Analysis Results", styles['Heading2']))
                story.append(Spacer(1, 12))
                
                results_data = [['Question #', 'Question Text', 'Extracted Answer', 'Confidence']]
                
                for result in pdf.analysis_results.all():
                    # Truncate long text for table
                    question_text = result.question_text[:100] + '...' if len(result.question_text) > 100 else result.question_text
                    answer_text = result.extracted_answer[:100] + '...' if len(result.extracted_answer) > 100 else result.extracted_answer
                    
                    results_data.append([
                        result.question_number,
                        question_text,
                        answer_text,
                        f"{result.confidence_score:.2f}%"
                    ])
                
                results_table = Table(results_data, colWidths=[0.8*inch, 2.5*inch, 2.5*inch, 1.2*inch])
                results_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(results_table)
            
            doc.build(story)
            
            response = HttpResponse(
                buffer.getvalue(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{pdf.title}_analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            return response
            
        else:
            # Return list of available formats
            formats = {
                'json': 'JSON format - Complete analysis data',
                'csv': 'CSV format - Analysis results only',
                'pdf': 'PDF format - Analysis report'
            }
            
            return JsonResponse({
                'available_formats': formats,
                'current_format': export_format,
                'usage': f'Add ?format=json|csv|pdf to the URL to specify export format'
            })
            
    except Exception as e:
        return JsonResponse({
            'error': f'Export failed: {str(e)}',
            'available_formats': ['json', 'csv', 'pdf']
        }, status=500)

@login_required
def pdf_analysis_view(request):
    """PDF analysis page"""
    return render(request, 'pdf_analysis/pdf_analysis.html')

@login_required
def pdf_analysis_detail_view(request, pk):
    """Show PDF analysis results for a specific document and handle analysis trigger"""
    from .models import PDFDocument, PDFAnalysisResult, PDFQuestion, PDFProcessingLog
    from django.shortcuts import get_object_or_404, render, redirect
    from .enhanced_ocr_engine import enhanced_ocr
    from .enhanced_nlp_engine import EnhancedNLPEngine
    from evaluation.models import ScoringRange
    import os
    import time
    
    pdf_document = get_object_or_404(PDFDocument, pk=pk)
    
    # Handle POST request to start analysis
    if request.method == 'POST':
        try:
            # Fetch scoring ranges from database
            scoring_ranges = ScoringRange.objects.filter(is_active=True).order_by('-min_similarity')
            custom_rules = {}
            if scoring_ranges.exists():
                for sr in scoring_ranges:
                    custom_rules[sr.name.lower()] = {
                        'range': (sr.min_similarity * 100, sr.max_similarity * 100),
                        'marks_percentage': sr.marks_percentage,
                        'criteria': [sr.description or sr.name]
                    }
            
            # Initialize engine with custom rules if available
            engine = EnhancedNLPEngine(custom_rules=custom_rules if custom_rules else None)

            # Update status to processing
            pdf_document.analysis_status = 'processing'
            pdf_document.save()
            
            PDFProcessingLog.objects.create(
                pdf_document=pdf_document,
                log_level='info',
                message='Started manual analysis trigger with custom scoring rules'
            )
            
            # Step 1: OCR Extraction
            PDFProcessingLog.objects.create(
                pdf_document=pdf_document,
                log_level='info',
                message='Running Enhanced OCR (Handwriting optimized)...'
            )
            
            start_time = time.time()
            ocr_result = enhanced_ocr.extract_text_from_pdf(pdf_document.pdf_file.path)
            
            if not ocr_result.get('text') or len(ocr_result['text'].strip()) < 10:
                raise Exception("OCR failed to extract meaningful text from the document.")
            
            # Step 2: NLP Analysis
            PDFProcessingLog.objects.create(
                pdf_document=pdf_document,
                log_level='info',
                message=f"OCR successful using {ocr_result.get('method_used', 'unknown')}. Starting NLP analysis..."
            )
            
            nlp_result = engine.analyze_text_comprehensive(ocr_result['text'])
            processing_time = time.time() - start_time
            
            # Step 3: Save Results
            # Prepare detected_questions for the template (list of dicts)
            template_questions = []
            for q in nlp_result.get('question_analysis', []):
                template_questions.append({
                    'text': q.get('question', ''),
                    'type': q.get('type', 'Unknown'),
                    'confidence': q.get('score', 0.0) / 100.0
                })

            analysis_result, created = PDFAnalysisResult.objects.update_or_create(
                pdf_document=pdf_document,
                defaults={
                    'extracted_text': ocr_result['text'],
                    'ocr_confidence': ocr_result.get('confidence', 0.0),
                    'processing_time': processing_time,
                    'word_count': nlp_result.get('text_statistics', {}).get('word_count', 0),
                    'sentence_count': nlp_result.get('text_statistics', {}).get('sentence_count', 0),
                    'detected_questions': template_questions,
                    'question_count': len(template_questions),
                    'overall_score': nlp_result.get('overall_score', 0.0),
                    'score_category': nlp_result.get('score_category', 'average'),
                    'summary': nlp_result.get('recommendations', ["Analysis complete"])[0],
                    'content_analysis': nlp_result.get('content_analysis', {}),
                    'complexity_analysis': nlp_result.get('complexity_analysis', {}),
                    'question_analysis': nlp_result.get('question_analysis', []),
                    'recommendations': nlp_result.get('recommendations', [])
                }
            )
            
            # Save individual questions for detail views
            PDFQuestion.objects.filter(pdf_document=pdf_document).delete()
            for q_data in nlp_result.get('question_analysis', []):
                PDFQuestion.objects.create(
                    pdf_document=pdf_document,
                    question_text=q_data.get('question', ''),
                    question_type=q_data.get('type', 'unknown'),
                    marks=int(q_data.get('weight', 1) * 10),
                    confidence_score=q_data.get('score', 0.0) / 100.0
                )
            
            # Finalize status
            pdf_document.analysis_status = 'completed'
            pdf_document.save()
            
            PDFProcessingLog.objects.create(
                pdf_document=pdf_document,
                log_level='info',
                message='Analysis completed successfully'
            )
            
            messages.success(request, "Analysis completed successfully!")
            return redirect('pdf_detail', pk=pk)
            
        except Exception as e:
            pdf_document.analysis_status = 'failed'
            pdf_document.save()
            
            PDFProcessingLog.objects.create(
                pdf_document=pdf_document,
                log_level='error',
                message=f'Analysis failed: {str(e)}'
            )
            
            messages.error(request, f"Analysis failed: {str(e)}")
            return redirect('pdf_detail', pk=pk)

    # GET request: Show existing results
    analysis_result = None
    try:
        analysis_result = pdf_document.analysis_result
    except PDFAnalysisResult.DoesNotExist:
        analysis_result = None
    
    context = {
        'pdf_document': pdf_document,
        'pdf': pdf_document,
        'analysis_result': analysis_result,
        'processing_logs': pdf_document.processing_logs.all()[:10]
    }
    
    return render(request, 'pdf_analysis/pdf_analysis_detail.html', context)

@login_required
def pdf_retry_view(request, pk):
    """Retry PDF analysis for a specific document"""
    from .models import PDFDocument
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    import os
    
    pdf = get_object_or_404(PDFDocument, pk=pk)
    
    try:
        # Check if poppler is available for PDF processing
        import subprocess
        try:
            subprocess.run(['pdfinfo', '--version'], capture_output=True, check=True)
            poppler_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            poppler_available = False
        
        if not poppler_available:
            messages.error(request, 'PDF processing requires Poppler utility. Please install Poppler and add it to system PATH.')
            return redirect('pdf_detail', pk=pk)
        
        # Reset analysis status to pending
        pdf.analysis_status = 'pending'
        pdf.error_message = None
        pdf.save()
        
        # Trigger reprocessing
        try:
            from evaluation.engines import OCREngine
            ocr_engine = OCREngine()
            
            # Process the PDF file
            if pdf.file_path and os.path.exists(pdf.file_path.path):
                ocr_engine.process_pdf(pdf)
                messages.success(request, f'Analysis for "{pdf.title}" has been restarted successfully.')
            else:
                messages.error(request, 'PDF file not found. Please upload the file again.')
                
        except Exception as e:
            pdf.analysis_status = 'failed'
            pdf.error_message = str(e)
            pdf.save()
            messages.error(request, f'Failed to process PDF: {str(e)}')
            
    except Exception as e:
        messages.error(request, f'Error during retry: {str(e)}')
    
    return redirect('pdf_detail', pk=pk)

@csrf_exempt
@require_http_methods(["POST"])
def upload_pdf_api(request):
    """API endpoint for PDF upload"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        file = request.FILES['file']
        if not file.name.lower().endswith('.pdf'):
            return JsonResponse({'error': 'Only PDF files are supported'}, status=400)
        
        # Save the PDF document
        from .models import PDFDocument
        from .forms import PDFUploadForm
        
        form = PDFUploadForm({'title': file.name}, {'pdf_file': file})
        if form.is_valid():
            pdf_doc = form.save(commit=False)
            pdf_doc.uploaded_by = request.user if request.user.is_authenticated else None
            pdf_doc.save()
            
            return JsonResponse({
                'success': True,
                'message': 'PDF uploaded successfully',
                'document_id': str(pdf_doc.id),
                'title': pdf_doc.title
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Form validation failed',
                'errors': form.errors
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def evaluate_answer_sheet_api(request):
    """
    API endpoint for complete answer sheet evaluation
    Handles OCR extraction, question detection, and automatic scoring
    """
    try:
        # Validate required files
        if 'answer_sheet' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Answer sheet file is required'
            }, status=400)
        
        answer_sheet = request.FILES['answer_sheet']
        question_paper = request.FILES.get('question_paper', None)
        exam_id = request.POST.get('exam_id', '').strip()
        marking_scheme_text = request.POST.get('marking_scheme', '').strip()
        total_marks = request.POST.get('total_marks', '').strip()
        total_marks = float(total_marks) if total_marks else None
        selected_exam = None
        question_specs = []
        
        # Validate file types
        if not answer_sheet.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            return JsonResponse({
                'success': False,
                'error': 'Answer sheet must be PDF or image file'
            }, status=400)
        
        if question_paper and not question_paper.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            return JsonResponse({
                'success': False,
                'error': 'Question paper must be PDF or image file'
            }, status=400)

        if exam_id:
            from django.shortcuts import get_object_or_404
            from exams.models import Exam

            selected_exam = get_object_or_404(
                Exam.objects.prefetch_related('questions'),
                id=exam_id,
                teacher=request.user
            )
            question_specs = [
                {
                    'question_number': index + 1,
                    'question': question.question_text,
                    'type': question.question_type,
                    'marks': float(question.marks),
                    'weight': float(question.marks) / 10.0,
                    'model_answer': question.model_answer or '',
                    'keywords': question.keywords or '',
                }
                for index, question in enumerate(selected_exam.questions.all())
            ]
            if total_marks is None:
                total_marks = float(selected_exam.total_marks)
        
        # Parse scoring rules from request
        scoring_rules = {}
        try:
            if 'scoring_rules' in request.POST:
                scoring_rules = json.loads(request.POST['scoring_rules'])
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Fetch scoring ranges from database if not provided
        if not scoring_rules:
            from evaluation.models import ScoringRange
            from django.db.models import Q

            scoring_ranges = ScoringRange.objects.filter(is_active=True)
            if request.user.is_authenticated and getattr(request.user, 'role', None) == 'teacher':
                scoring_ranges = scoring_ranges.filter(created_by=request.user)
            if selected_exam:
                scoring_ranges = scoring_ranges.filter(Q(exam=selected_exam) | Q(exam__isnull=True))
            scoring_ranges = scoring_ranges.order_by('-min_similarity')
            for sr in scoring_ranges:
                scoring_rules[sr.name.lower()] = {
                    'range': (sr.min_similarity * 100, sr.max_similarity * 100),
                    'marks_percentage': sr.marks_percentage,
                    'criteria': [sr.description or sr.name],
                    'total_questions': sr.total_questions,
                    'total_marks': sr.total_marks,
                    'marks_per_question': sr.marks_per_question,
                }
            if total_marks is None:
                marks_source = scoring_ranges.exclude(total_marks=0).first()
                if marks_source:
                    total_marks = float(marks_source.total_marks)
        
        # Initialize evaluation engine
        from .answer_evaluation_engine import AnswerEvaluationEngine
        engine = AnswerEvaluationEngine(custom_scoring_rules=scoring_rules)
        
        # Save uploaded files temporarily
        import tempfile
        import os
        
        answer_sheet_path = None
        question_paper_path = None
        
        try:
            # Save answer sheet
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(answer_sheet.name)[1]) as temp_answer:
                for chunk in answer_sheet.chunks():
                    temp_answer.write(chunk)
                answer_sheet_path = temp_answer.name
            
            # Save question paper if provided
            if question_paper:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(question_paper.name)[1]) as temp_question:
                    for chunk in question_paper.chunks():
                        temp_question.write(chunk)
                    question_paper_path = temp_question.name
            
            # Perform complete evaluation
            evaluation_result = engine.evaluate_complete_paper(
                answer_sheet_path=answer_sheet_path,
                question_paper_path=question_paper_path,
                scoring_rules=scoring_rules,
                question_specs=question_specs,
                marking_scheme_text=marking_scheme_text,
                total_marks=total_marks
            )
            
            if evaluation_result['success']:
                # Save results to database if user is authenticated
                if request.user.is_authenticated:
                    answer_sheet.seek(0)
                    if question_paper:
                        question_paper.seek(0)
                    _save_evaluation_results(request.user, evaluation_result, answer_sheet, question_paper)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Answer sheet evaluated successfully',
                    'results': evaluation_result
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Evaluation failed: {evaluation_result.get("error", "Unknown error")}'
                }, status=500)
                
        finally:
            # Clean up temporary files
            if answer_sheet_path and os.path.exists(answer_sheet_path):
                os.unlink(answer_sheet_path)
            if question_paper_path and os.path.exists(question_paper_path):
                os.unlink(question_paper_path)
                
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Evaluation failed: {str(e)}'
        }, status=500)

def _save_evaluation_results(user, evaluation_result, answer_sheet_file, question_paper_file=None):
    """
    Save evaluation results to database
    """
    try:
        from .models import PDFDocument, PDFAnalysisResult
        
        # Create PDF document for answer sheet
        answer_doc = PDFDocument.objects.create(
            title=f"Answer Sheet - {answer_sheet_file.name}",
            description="Automatically evaluated answer sheet",
            pdf_file=answer_sheet_file,
            document_type='answer_sheet',
            uploaded_by=user,
            analysis_status='completed'
        )
        
        # Create analysis result
        PDFAnalysisResult.objects.create(
            pdf_document=answer_doc,
            extracted_text=evaluation_result['answer_extraction']['text'],
            ocr_confidence=evaluation_result['answer_extraction']['confidence'],
            processing_time=evaluation_result['final_results']['processing_time'],
            word_count=len(evaluation_result['answer_extraction']['text'].split()),
            overall_score=evaluation_result['final_results']['percentage'],
            score_category=evaluation_result['final_results']['grade'],
            summary=f"Automatic evaluation: {evaluation_result['final_results']['percentage']:.1f}% - {evaluation_result['final_results']['grade']}",
            content_analysis=evaluation_result['evaluation'],
            question_analysis=evaluation_result['evaluation']['evaluation_results']
        )
        return answer_doc
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to save evaluation results: {e}")

@csrf_exempt
@require_http_methods(["POST"])
def quick_evaluate_api(request):
    """
    Quick evaluation API - only answer sheet, auto-detect questions
    """
    try:
        if 'answer_sheet' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Answer sheet file is required'
            }, status=400)
        
        answer_sheet = request.FILES['answer_sheet']
        
        if not answer_sheet.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            return JsonResponse({
                'success': False,
                'error': 'Answer sheet must be PDF or image file'
            }, status=400)
        
        # Initialize evaluation engine
        from .answer_evaluation_engine import AnswerEvaluationEngine
        engine = AnswerEvaluationEngine()
        
        # Save file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(answer_sheet.name)[1]) as temp_file:
            for chunk in answer_sheet.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        try:
            # Perform evaluation without question paper
            result = engine.evaluate_complete_paper(answer_sheet_path=temp_path)
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Quick evaluation completed successfully',
                    'results': result
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Evaluation failed: {result.get("error", "Unknown error")}'
                }, status=500)
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Quick evaluation failed: {str(e)}'
        }, status=500)
