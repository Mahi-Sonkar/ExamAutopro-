import logging
from .models import EvaluationResult, OCREvaluation, NLPEvaluation
from .engines import OCREngine, NLPEngine, GraceMarksEngine

logger = logging.getLogger(__name__)


def _format_ai_feedback(ai_result):
    parts = []
    feedback = ai_result.get('feedback')
    score_reason = ai_result.get('score_reason')

    if feedback:
        parts.append(str(feedback).strip())
    if score_reason:
        parts.append(f"Reason: {str(score_reason).strip()}")

    labelled_lists = [
        ("Correct", ai_result.get('correct_points') or []),
        ("Missing", ai_result.get('missing_points') or []),
        ("Incorrect", ai_result.get('incorrect_points') or []),
    ]
    for label, values in labelled_lists:
        if values:
            clean_values = [str(value).strip() for value in values if str(value).strip()]
            if clean_values:
                parts.append(f"{label}: " + "; ".join(clean_values))

    return " | ".join(parts)

def trigger_ai_evaluation(answer):
    """
    Utility function to trigger AI evaluation for a single answer.
    This can be called from multiple places (e.g., exams/views.py, evaluation/views.py).
    """
    try:
        # Get evaluation result or create new one
        result, created = EvaluationResult.objects.get_or_create(
            answer=answer,
            defaults={
                'similarity_score': 0.0,
                'keyword_match_score': 0.0,
                'confidence_score': 0.0,
                'initial_score': 0.0,
                'grace_marks_applied': 0.0,
                'final_score': 0.0,
                'feedback': 'Evaluation pending',
                'evaluation_method': 'pending',
            }
        )
        
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
            ai_result = None
            try:
                from .ai_clients import FreeAIEvaluator
                ai_result = FreeAIEvaluator().evaluate(
                    student_answer=answer.answer_text,
                    model_answer=answer.question.model_answer or '',
                    question_text=answer.question.question_text,
                    max_marks=answer.question.marks,
                    keywords=answer.question.keywords or '',
                    question_type=answer.question.question_type,
                )
            except Exception as e:
                logger.warning(f"External AI evaluation skipped: {e}")

            if ai_result:
                nlp_result = {
                    'score': ai_result.get('score', 0.0),
                    'base_score': ai_result.get('score', 0.0),
                    'similarity': ai_result.get('similarity', 0.0),
                    'keyword_score': 0.0,
                    'confidence': ai_result.get('confidence', 0.0),
                }
                result.evaluation_method = ai_result.get('provider', 'free_ai_api')
                direct_feedback = _format_ai_feedback(ai_result)
            else:
                nlp_result = nlp_engine.evaluate_answer(answer)
                result.evaluation_method = 'local_nlp'
                direct_feedback = ''

            result.similarity_score = nlp_result.get('similarity', 0.0)
            result.keyword_match_score = nlp_result.get('keyword_score', 0.0)
            result.confidence_score = nlp_result.get('confidence', 0.0)
            result.initial_score = float(nlp_result.get('base_score', 0.0))
            
            # Apply grace marks
            grace_result = grace_engine.apply_grace_marks(answer, nlp_result)
            result.grace_marks_applied = grace_result.get('grace_marks', 0.0)
            result.final_score = float(grace_result.get('final_score', nlp_result.get('score', 0.0)))
            result.feedback = direct_feedback or grace_result.get('feedback', '')
            
            # Update Answer model as well
            answer.marks_obtained = int(round(result.final_score))
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
