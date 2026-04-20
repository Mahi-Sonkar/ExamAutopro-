# Create evaluation result for each answer
            EvaluationResult.objects.create(
                answer=answer,
                similarity_score=q_data.get('similarity', 0.0),
                keyword_match_score=0.0,
                confidence_score=q_data.get('confidence', 0.0),
                initial_score=q_data.get('score', 0.0),
                grace_marks_applied=0.0,
                final_score=q_data.get('score', 0.0),
                feedback=q_data.get('feedback', 'Auto-generated from PDF analysis'),
                evaluation_method='pdf_ocr'
            )
