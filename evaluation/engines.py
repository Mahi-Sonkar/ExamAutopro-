import os
import re
from nltk.corpus import stopwords
import logging
import string
import time
from django.conf import settings
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)

class OCREngine:
    """OCR Engine for processing handwritten answer sheets"""
    
    def __init__(self):
        self.tesseract_config = r'--oem 3 --psm 6'
        
    def process_answer(self, answer):
        """Process OCR for a given answer (Supports Images and PDFs)"""
        import pytesseract
        from PIL import Image
        import cv2
        import numpy as np
        from pdf2image import convert_from_path
        
        start_time = time.time()
        
        try:
            from evaluation.models import OCREvaluation
            ocr_eval, created = OCREvaluation.objects.get_or_create(answer=answer)
            ocr_eval.status = 'processing'
            
            # Use uploaded_file from answer if not present in ocr_eval
            # OCREvaluation model doesn't have status or uploaded_file field based on models.py
            # Fixing based on available fields in models.py
            
            file_to_process = answer.uploaded_file
            if not file_to_process:
                return {'success': False, 'error': 'No file uploaded'}
                
            file_path = file_to_process.path
            file_extension = os.path.splitext(file_path)[1].lower()
            extracted_text = ""
            
            # Check if tesseract is available
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                # Fallback for demonstration: Use filename as content if OCR tools missing
                extracted_text = f"OCR Error: Tesseract not installed. Filename: {os.path.basename(file_path)}\n"
                extracted_text += "Please install Tesseract OCR on your system to enable text extraction."
                
                ocr_eval.extracted_text = extracted_text
                ocr_eval.confidence_score = 0.0
                ocr_eval.processing_time = time.time() - start_time
                ocr_eval.save()
                
                return {'success': False, 'error': 'Tesseract not installed', 'extracted_text': extracted_text}

            if file_extension == '.pdf':
                try:
                    # Set poppler path for Windows
                    import os
                    poppler_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'poppler-23.11.0', 'Library', 'bin')
                    if os.path.exists(poppler_path):
                        # Convert PDF to images with custom poppler path
                        images = convert_from_path(file_path, poppler_path=poppler_path)
                    else:
                        # Try default path
                        images = convert_from_path(file_path)
                    for i, image in enumerate(images):
                        # Process each page
                        open_cv_image = np.array(image)
                        # Convert RGB to BGR
                        open_cv_image = open_cv_image[:, :, ::-1].copy()
                        processed_page = self.preprocess_cv2_image(open_cv_image)
                        page_text = pytesseract.image_to_string(processed_page, config=self.tesseract_config)
                        extracted_text += page_text + "\n"
                except Exception as e:
                    extracted_text = f"Poppler/PDF Error: {str(e)}"
                    if "pdfinfo" in str(e).lower():
                        extracted_text = "Poppler not installed. Cannot process PDF files."
            else:
                # Process single image
                processed_image = self.preprocess_image(file_path)
                extracted_text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)
            
            # Clean extracted text
            cleaned_text = self.clean_text(extracted_text)
            
            # Update OCR evaluation
            ocr_eval.extracted_text = cleaned_text
            ocr_eval.confidence_score = self.calculate_confidence(extracted_text)
            ocr_eval.processing_time = time.time() - start_time
            ocr_eval.save()
            
            # Update answer with extracted text
            answer.answer_text = cleaned_text
            answer.save()
            
            return {
                'success': True,
                'extracted_text': cleaned_text,
                'confidence': ocr_eval.confidence_score,
                'processing_time': ocr_eval.processing_time
            }
            
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def preprocess_cv2_image(self, img):
        """Advanced Preprocessing for Noisy Handwritten Text"""
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Rescale for better OCR (DPI increase simulation)
        height, width = gray.shape
        gray = cv2.resize(gray, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
        
        # Denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Contrast Enhancement (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Adaptive Thresholding (Otsu + Gaussian)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to thicken text slightly (useful for light handwriting)
        kernel = np.ones((1,1), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        
        return dilated
    
    def preprocess_image(self, image_path):
        """Preprocess image for better OCR accuracy"""
        # Read image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Remove noise
        denoised = cv2.medianBlur(binary, 5)
        
        return denoised
    
    def clean_text(self, text):
        """Clean extracted text"""
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters except punctuation
        text = re.sub(r'[^\w\s\.,!?;:]', '', text)
        return text.strip()
    
    def calculate_confidence(self, text):
        """Calculate confidence score for OCR output"""
        if not text:
            return 0.0
        
        # Simple confidence calculation based on text quality
        word_count = len(text.split())
        if word_count < 5:
            return 0.3
        elif word_count < 20:
            return 0.6
        else:
            return 0.8

class AnswerSegmentationEngine:
    """Engine to segment full OCR text into individual answers based on QuestionPaper"""
    
    def __init__(self, question_paper):
        self.question_paper = question_paper
        self.questions = question_paper.questions.all().order_by('question_number')
        
    def segment_text(self, full_text):
        """
        Robust Segmentation using Fuzzy Markers
        Example: Q1, Ans 1, 1), .1.
        """
        segments = {}
        
        # Prepare markers for each question
        markers = []
        for q in self.questions:
            num = q.question_number
            # Patterns: Q1, Q.1, Question 1, 1., (1)
            patterns = [
                rf'(?i)\bQ\s*\.?\s*{num}[:\.\s\-]', 
                rf'(?i)\bQuestion\s*\.?\s*{num}[:\.\s\-]',
                rf'(?i)\bAns(?:wer)?\s*\.?\s*{num}[:\.\s\-]',
                rf'(?m)^\s*{num}[\.\)\-\s]'
            ]
            
            for pattern in patterns:
                for match in re.finditer(pattern, full_text):
                    markers.append({
                        'num': num,
                        'start': match.start(),
                        'end': match.end(),
                        'type': 'header'
                    })
        
        # Sort by occurrence
        markers.sort(key=lambda x: x['start'])
        
        # Segment extraction
        if not markers:
            # Fallback: try simple split by number only if text is structured
            lines = full_text.split('\n')
            current_q = None
            for line in lines:
                match = re.match(r'^\s*(\d+)[\.\)\-\s]', line)
                if match:
                    num = int(match.group(1))
                    if any(q.question_number == num for q in self.questions):
                        current_q = num
                        segments[current_q] = segments.get(current_q, "") + line + "\n"
                        continue
                if current_q:
                    segments[current_q] = segments.get(current_q, "") + line + "\n"
        else:
            for i in range(len(markers)):
                curr = markers[i]
                start = curr['end']
                end = markers[i+1]['start'] if i+1 < len(markers) else len(full_text)
                
                content = full_text[start:end].strip()
                if len(content) > 5: # Basic filter for noise
                    segments[curr['num']] = content
        
        return segments

class NLPEngine:
    """NLP Engine for evaluating descriptive answers"""
    
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        import nltk
        from nltk.stem import WordNetLemmatizer
        
        self.vectorizer = TfidfVectorizer(
            max_features=2000,
            stop_words='english',
            ngram_range=(1, 3) # Increased ngram range for better semantic matching
        )
        self.lemmatizer = WordNetLemmatizer()
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')
    
    def evaluate_answer_v2(self, student_answer, model_answer, max_marks, scoring_ranges=None):
        """
        Advanced Evaluation: Semantic Similarity + Keyword Weighting
        """
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        if not student_answer or not model_answer:
            return {'score': 0, 'similarity': 0, 'category': 'Poor', 'feedback': 'Missing student or model answer'}
            
        # Preprocess
        s_proc = self.preprocess_text(student_answer)
        m_proc = self.preprocess_text(model_answer)
        
        if not s_proc:
            return {'score': 0, 'similarity': 0, 'category': 'Poor', 'feedback': 'Student answer too short or invalid'}
            
        # 1. TF-IDF Cosine Similarity (Semantic overlap)
        try:
            tfidf_matrix = self.vectorizer.fit_transform([s_proc, m_proc])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            cosine_sim = 0
            
        # 2. Key Term Matching (Content Accuracy)
        # Extract unique words (simple keywords)
        m_words = set(m_proc.split())
        s_words = set(s_proc.split())
        
        # Intersection of words
        matched_words = s_words.intersection(m_words)
        # Calculate coverage
        keyword_coverage = len(matched_words) / len(m_words) if m_words else 0
        
        # 3. Weighted Score Calculation
        # Cosine Similarity shows overall semantic similarity
        # Keyword Coverage shows presence of required facts
        combined_sim = (cosine_sim * 0.6) + (keyword_coverage * 0.4)
        
        # 4. Length Penalty (Anti-Cheating)
        # If student answer is significantly shorter than model answer
        len_ratio = len(s_proc) / len(m_proc) if len(m_proc) > 0 else 1
        penalty = 1.0
        if len_ratio < 0.3:
            penalty = 0.5
        elif len_ratio < 0.6:
            penalty = 0.8
            
        combined_sim = combined_sim * penalty
        
        # 5. Apply Scoring Ranges
        final_score = 0
        category = "Average"
        
        if scoring_ranges:
            # Sort ranges by similarity descending to find the best match
            for r in scoring_ranges:
                if r.min_similarity <= combined_sim <= r.max_similarity:
                    final_score = (r.marks_percentage / 100.0) * max_marks
                    category = r.name
                    break
        else:
            final_score = combined_sim * max_marks
            
        return {
            'score': round(min(final_score, max_marks), 2),
            'similarity': round(combined_sim, 4),
            'category': category,
            'matched_keywords': list(matched_words)[:10],
            'feedback': f"Similarity: {round(combined_sim*100, 1)}%, Key terms found: {len(matched_words)}"
        }
    
    def evaluate_answer(self, answer):
        """Evaluate answer using NLP techniques with enhanced accuracy"""
        from sklearn.metrics.pairwise import cosine_similarity
        import nltk
        from nltk.tokenize import word_tokenize
        from evaluation.models import NLPEvaluation, ScoringRange
        from proctoring.models import ProctoringSession
        
        start_time = time.time()
        
        try:
            nlp_eval = NLPEvaluation.objects.get_or_create(answer=answer)[0]
            
            student_answer = answer.answer_text or ""
            model_answer = answer.question.model_answer or ""
            keywords = answer.question.keywords or ""
            
            if not model_answer:
                return {'score': 0, 'similarity': 0, 'confidence': 0}
            
            # Preprocess texts
            student_processed = self.preprocess_text(student_answer)
            model_processed = self.preprocess_text(model_answer)
            
            if not student_processed or not model_processed:
                # If either text is empty after preprocessing, similarity is 0
                similarity = 0.0
                keyword_score = 0.0
                matched_count = 0
                total_count = len(keywords.split(',')) if keywords else 0
            else:
                # Calculate TF-IDF vectors
                documents = [student_processed, model_processed]
                tfidf_matrix = self.vectorizer.fit_transform(documents)
                
                # Calculate cosine similarity
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                
                # Keyword matching with weightage
                keyword_score, matched_count, total_count = self.calculate_keyword_score_enhanced(student_processed, keywords)
            
            # Grammar and readability scores
            grammar_score = self.calculate_grammar_score(student_answer)
            readability_score = self.calculate_readability_score(student_answer)
            
            # Calculate base score
            similarity_weight = 0.5
            keyword_weight = 0.4
            grammar_weight = 0.1
            
            # --- CUSTOM SCORING RANGES LOGIC ---
            # Check if there are specific scoring ranges for this exam or globally
            matching_range = ScoringRange.objects.filter(
                (models.Q(exam=answer.submission.exam) | models.Q(exam__isnull=True)),
                min_similarity__lte=similarity,
                max_similarity__gte=similarity,
                is_active=True
            ).order_by('-exam').first()  # Exam-specific rules take priority
            
            if matching_range:
                # Use custom range to calculate marks
                base_score = (matching_range.marks_percentage / 100.0) * answer.question.marks
                logger.info(f"Applied scoring range '{matching_range.name}' for similarity {similarity}")
            else:
                # Default calculation if no range matches
                base_score = (
                    similarity * similarity_weight * answer.question.marks +
                    keyword_score * keyword_weight * answer.question.marks +
                    grammar_score * grammar_weight * answer.question.marks
                )
            
            # --- PROCTORING PENALTY LOGIC ---
            # Deduct marks if suspicious proctoring events occurred during this exam attempt
            proctoring_penalty = 0
            session = ProctoringSession.objects.filter(
                student=answer.submission.student,
                exam=answer.submission.exam,
                status__in=['active', 'completed']
            ).order_by('-start_time').first()
            
            if session:
                # Count high severity events like tab switching or focus loss
                critical_events = session.events.filter(
                    severity__in=['high', 'critical'],
                    event_type__in=['tab_switch', 'window_focus_lost', 'copy_paste']
                ).count()
                
                if critical_events > 0:
                    # Penalty: 5% of question marks per critical event, capped at 25%
                    penalty_factor = min(critical_events * 0.05, 0.25)
                    proctoring_penalty = base_score * penalty_factor
            
            final_score = max(0, base_score - proctoring_penalty)
            
            # Update NLP evaluation
            nlp_eval.text_similarity = similarity
            nlp_eval.semantic_similarity = similarity # Fallback
            nlp_eval.keyword_matches = self.get_keyword_matches(student_processed, keywords)
            nlp_eval.processing_time = time.time() - start_time
            nlp_eval.save()
            
            return {
                'score': int(final_score),
                'base_score': int(base_score),
                'penalty': int(proctoring_penalty),
                'similarity': float(similarity),
                'keyword_score': keyword_score,
                'grammar_score': grammar_score,
                'readability_score': readability_score,
                'matched_keywords': f"{matched_count}/{total_count}",
                'confidence': min(similarity + keyword_score, 1.0),
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"NLP evaluation failed: {str(e)}")
            return {
                'score': 0,
                'similarity': 0,
                'confidence': 0,
                'error': str(e)
            }

    def preprocess_text(self, text):
        """Preprocess text for NLP evaluation (tokenization, stopwords, lemmatization)"""
        if not text:
            return ""
            
        # Remove punctuation and lowercase
        text = text.lower().translate(str.maketrans('', '', string.punctuation))
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        stop_words = set(stopwords.words('english'))
        processed_tokens = [
            self.lemmatizer.lemmatize(token) 
            for token in tokens 
            if token not in stop_words
        ]
        
        return " ".join(processed_tokens)

    def calculate_keyword_score_enhanced(self, student_text, keywords):
        """Enhanced keyword matching with frequency and existence check"""
        if not keywords:
            return 0.0, 0, 0
        
        keyword_list = [kw.strip().lower() for kw in keywords.split(',')]
        student_tokens = student_text.lower().split()
        
        matched_keywords = [kw for kw in keyword_list if kw in student_tokens]
        
        if not keyword_list:
            return 0.0, 0, 0
            
        return len(matched_keywords) / len(keyword_list), len(matched_keywords), len(keyword_list)
    
    def get_keyword_matches(self, student_text, keywords):
        """Get list of matched keywords"""
        if not keywords:
            return []
        
        keyword_list = [kw.strip().lower() for kw in keywords.split(',')]
        student_tokens = set(student_text.lower().split())
        
        return [kw for kw in keyword_list if kw in student_tokens]
    
    def calculate_grammar_score(self, text):
        """Simple grammar score calculation"""
        # This is a simplified version - in production, use proper grammar checking
        sentences = text.split('.')
        if not sentences:
            return 0.0
        
        # Check for basic sentence structure
        valid_sentences = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence.split()) > 3:
                valid_sentences += 1
        
        return valid_sentences / len(sentences)
    
    def calculate_readability_score(self, text):
        """Calculate readability score"""
        words = text.split()
        sentences = text.split('.')
        
        if not sentences:
            return 0.0
        
        avg_words_per_sentence = len(words) / len(sentences)
        
        # Simple readability score based on average sentence length
        if avg_words_per_sentence < 10:
            return 0.9
        elif avg_words_per_sentence < 20:
            return 0.7
        elif avg_words_per_sentence < 30:
            return 0.5
        else:
            return 0.3

class GraceMarksEngine:
    """Engine for applying grace marks based on predefined rules"""
    
    def __init__(self):
        pass
    
    def apply_grace_marks(self, answer, nlp_result):
        """Apply grace marks based on evaluation rules"""
        try:
            from evaluation.models import GraceMarksRule, EvaluationResult
            
            initial_score = nlp_result.get('score', 0)
            similarity = nlp_result.get('similarity', 0)
            keyword_score = nlp_result.get('keyword_score', 0)
            grammar_score = nlp_result.get('grammar_score', 0)
            
            total_grace_marks = 0
            applied_rules = []
            feedback_parts = []
            
            # Check for active grace marks rules
            rules = GraceMarksRule.objects.filter(is_active=True)
            
            for rule in rules:
                grace_marks = self.evaluate_rule(rule, {
                    'similarity': similarity,
                    'keyword_score': keyword_score,
                    'grammar_score': grammar_score,
                    'answer_length': len(answer.answer_text or ''),
                    'initial_score': initial_score,
                    'max_marks': answer.question.marks
                })
                
                if grace_marks > 0:
                    # In this model, there's no max_grace_marks field
                    total_grace_marks += grace_marks
                    applied_rules.append(rule.name)
                    feedback_parts.append(f"Grace marks applied: {rule.name} (+{grace_marks})")
            
            final_score = min(initial_score + total_grace_marks, answer.question.marks)
            
            # Generate feedback
            feedback = self.generate_feedback(nlp_result, applied_rules, total_grace_marks)
            
            return {
                'final_score': final_score,
                'grace_marks': total_grace_marks,
                'applied_rules': applied_rules,
                'feedback': feedback,
                'analysis': {
                    'initial_score': initial_score,
                    'similarity': similarity,
                    'keyword_score': keyword_score,
                    'grammar_score': grammar_score,
                    'grace_rules_applied': applied_rules
                }
            }
            
        except Exception as e:
            logger.error(f"Grace marks application failed: {str(e)}")
            return {
                'final_score': nlp_result.get('score', 0),
                'grace_marks': 0,
                'feedback': 'Error in grace marks evaluation',
                'analysis': {}
            }
    
    def evaluate_rule(self, rule, evaluation_data):
        """Evaluate a single grace marks rule"""
        condition_type = rule.condition_type
        condition_value = rule.condition_value
        
        if condition_type == 'similarity_threshold':
            if evaluation_data['similarity'] >= condition_value:
                return rule.grace_marks
        
        elif condition_type == 'keyword_coverage':
            if evaluation_data['keyword_score'] >= condition_value:
                return rule.grace_marks
        
        elif condition_type == 'grammar_score':
            if evaluation_data['grammar_score'] >= condition_value:
                return rule.grace_marks
        
        elif condition_type == 'answer_length':
            if evaluation_data['answer_length'] >= condition_value:
                return rule.grace_marks
        
        elif condition_type == 'partial_match':
            # For answers that are close but not quite there
            if (evaluation_data['similarity'] >= condition_value and 
                evaluation_data['initial_score'] < evaluation_data['max_marks']):
                return rule.grace_marks
        
        return 0
    
    def generate_feedback(self, nlp_result, applied_rules, grace_marks):
        """Generate detailed feedback for the student"""
        feedback_parts = []
        
        # Similarity feedback
        similarity = nlp_result.get('similarity', 0)
        if similarity >= 0.8:
            feedback_parts.append("Excellent answer! Very close to the model answer.")
        elif similarity >= 0.6:
            feedback_parts.append("Good answer with some relevant content.")
        elif similarity >= 0.4:
            feedback_parts.append("Partially correct answer. More detail needed.")
        else:
            feedback_parts.append("Answer needs significant improvement.")
        
        # Keyword feedback
        keyword_score = nlp_result.get('keyword_score', 0)
        if keyword_score >= 0.8:
            feedback_parts.append("Great use of relevant keywords.")
        elif keyword_score >= 0.5:
            feedback_parts.append("Some keywords used, but more could be included.")
        else:
            feedback_parts.append("Consider including more relevant keywords.")
        
        # Grace marks feedback
        if grace_marks > 0:
            feedback_parts.append(f"Grace marks awarded: +{grace_marks}")
        
        return " | ".join(feedback_parts)
