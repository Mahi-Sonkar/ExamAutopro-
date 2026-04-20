import logging
from .models import EvaluationResult, OCREvaluation, NLPEvaluation
from .engines import OCREngine, NLPEngine, GraceMarksEngine

logger = logging.getLogger(__name__)

def trigger_ai_evaluation(answer):
    """
    Utility function to trigger AI evaluation for a single answer.
    This can be called from multiple places (e.g., exams/views.py, evaluation/views.py).
    """
    try:
        # Get evaluation result or create new one
        result, created = EvaluationResult.objects.get_or_create(answer=answer)
        
        # Engines initialization
        ocr_engine = OCREngine()
        nlp_engine = NLPEngine()
        grace_engine = GraceMarksEngine()
        
        # OCR processing if needed (file uploaded but no text yet)
        if answer.uploaded_file and (not answer.answer_text or answer.answer_text.strip() == ""):
            ocr_result = ocr_engine.process_answer(answer)
            # Answer text is updated inside process_answer
            answer.refresh_from_db()
        
        nlp_result = {}
        # NLP evaluation if we have text
        if answer.answer_text and answer.answer_text.strip():
            nlp_result = nlp_engine.evaluate_answer(answer)
            result.similarity_score = nlp_result.get('similarity', 0.0)
            result.keyword_match_score = nlp_result.get('keyword_score', 0.0)
            result.confidence_score = nlp_result.get('confidence', 0.0)
            result.initial_score = float(nlp_result.get('base_score', 0.0))
            
            # Apply grace marks
            grace_result = grace_engine.apply_grace_marks(answer, nlp_result)
            result.grace_marks_applied = grace_result.get('grace_marks', 0.0)
            result.final_score = float(nlp_result.get('score', 0.0))
            result.feedback = grace_result.get('feedback', '')
            
            # Update Answer model as well
            answer.marks_obtained = int(result.final_score)
            answer.evaluated_by_ai = True
            answer.confidence_score = result.confidence_score
            answer.feedback = result.feedback
            answer.save()
            
            result.save()
            return {'success': True, 'result': result}
        else:
            return {'success': False, 'error': 'No answer text to evaluate'}
            
    except Exception as e:
        logger.error(f"Error in trigger_ai_evaluation for answer {answer.id}: {str(e)}")
        return {'success': False, 'error': str(e)}
