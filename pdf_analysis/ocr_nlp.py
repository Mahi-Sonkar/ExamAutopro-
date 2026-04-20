"""
OCR + NLP Integration for Answer Evaluation
Working solution for answer segmentation and question matching
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class OCRNLPEvaluator:
    """Main class for evaluating OCR-extracted answers against question paper"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.model_answers = []
        self.question_marks = []
    
    def split_answers(self, text):
        """
        STEP 1: Answer Extract + Split
        Split OCR text by question numbers
        """
        try:
            # Split by Q1, Q2, Q3 patterns
            answers = re.split(r'Q\d+\.?', text, flags=re.IGNORECASE)
            answers = [a.strip() for a in answers if len(a.strip()) > 20]
            
            logger.info(f"Found {len(answers)} answers after splitting")
            return answers
            
        except Exception as e:
            logger.error(f"Answer splitting failed: {e}")
            return []
    
    def set_question_paper(self, questions_data):
        """
        STEP 2: Question Paper Store karo
        Store question paper in memory
        """
        try:
            self.model_answers = []
            self.question_marks = []
            
            for q_data in questions_data:
                self.model_answers.append(q_data['question_text'])
                self.question_marks.append(q_data['marks'])
                
            logger.info(f"Loaded {len(self.model_answers)} questions with marks")
            
        except Exception as e:
            logger.error(f"Question paper loading failed: {e}")
    
    def evaluate_answer(self, student_answer, model_answer):
        """
        STEP 3: Matching Logic (IMPORTANT)
        Answer vs Model Answer comparison using TF-IDF
        """
        try:
            if not student_answer or not model_answer:
                return 0.0
            
            # Create TF-IDF vectors
            documents = [student_answer, model_answer]
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            logger.info(f"Similarity score: {similarity:.3f}")
            return similarity
            
        except Exception as e:
            logger.error(f"Answer evaluation failed: {e}")
            return 0.0
    
    def calculate_marks(self, similarity, max_marks):
        """
        STEP 4: Marks Calculation
        Convert similarity score to marks
        """
        try:
            if similarity > 0.7:
                return max_marks
            elif similarity > 0.4:
                return max_marks * 0.7
            else:
                return max_marks * 0.3
                
        except Exception as e:
            logger.error(f"Marks calculation failed: {e}")
            return 0.0
    
    def evaluate_all_answers(self, student_answers_text):
        """
        STEP 5: Full Pipeline
        Complete evaluation pipeline
        """
        try:
            # Split student answers
            student_answers = self.split_answers(student_answers_text)
            
            if not student_answers:
                logger.warning("No student answers found")
                return {
                    'total_marks': 0,
                    'max_marks': sum(self.question_marks),
                    'percentage': 0.0,
                    'answer_details': []
                }
            
            # Evaluate each answer
            answer_details = []
            total_marks = 0
            
            for i, student_answer in enumerate(student_answers):
                if i < len(self.model_answers):
                    similarity = self.evaluate_answer(student_answer, self.model_answers[i])
                    marks = self.calculate_marks(similarity, self.question_marks[i])
                    
                    answer_details.append({
                        'question_number': i + 1,
                        'student_answer': student_answer[:100] + '...' if len(student_answer) > 100 else student_answer,
                        'model_answer': self.model_answers[i][:100] + '...' if len(self.model_answers[i]) > 100 else self.model_answers[i],
                        'similarity': similarity,
                        'marks_obtained': marks,
                        'max_marks': self.question_marks[i],
                        'percentage': (marks / self.question_marks[i]) * 100 if self.question_marks[i] > 0 else 0
                    })
                    
                    total_marks += marks
                else:
                    # Extra answer without corresponding question
                    answer_details.append({
                        'question_number': i + 1,
                        'student_answer': student_answer[:100] + '...' if len(student_answer) > 100 else student_answer,
                        'model_answer': 'No corresponding question',
                        'similarity': 0.0,
                        'marks_obtained': 0,
                        'max_marks': 0,
                        'percentage': 0
                    })
            
            max_marks = sum(self.question_marks)
            percentage = (total_marks / max_marks) * 100 if max_marks > 0 else 0
            
            result = {
                'total_marks': total_marks,
                'max_marks': max_marks,
                'percentage': percentage,
                'answer_details': answer_details,
                'questions_evaluated': len([d for d in answer_details if d['max_marks'] > 0]),
                'total_questions': len(self.model_answers)
            }
            
            logger.info(f"Evaluation completed: {result['total_marks']}/{result['max_marks']} ({result['percentage']:.1f}%)")
            return result
            
        except Exception as e:
            logger.error(f"Full evaluation pipeline failed: {e}")
            return {
                'total_marks': 0,
                'max_marks': 0,
                'percentage': 0.0,
                'answer_details': [],
                'error': str(e)
            }


# Quick test function
def test_evaluation_system():
    """Test the complete evaluation system"""
    print("=== TESTING COMPLETE EVALUATION SYSTEM ===")
    
    evaluator = OCRNLPEvaluator()
    
    # Set up question paper
    questions_data = [
        {'question_text': 'What is Machine Learning?', 'marks': 10},
        {'question_text': 'Explain the process of photosynthesis', 'marks': 15},
        {'question_text': 'Define artificial intelligence', 'marks': 5}
    ]
    
    evaluator.set_question_paper(questions_data)
    
    # Test student answers
    student_text = """
    Q1. Machine Learning is a subset of artificial intelligence that uses algorithms to learn from data.
    Q2. Photosynthesis is the process by which plants convert sunlight into energy.
    Q3. AI is the simulation of human intelligence in machines.
    """
    
    result = evaluator.evaluate_all_answers(student_text)
    
    print(f"Total Marks: {result['total_marks']}")
    print(f"Max Marks: {result['max_marks']}")
    print(f"Percentage: {result['percentage']:.1f}%")
    
    for detail in result['answer_details']:
        print(f"Q{detail['question_number']}: {detail['marks_obtained']}/{detail['max_marks']} ({detail['similarity']:.2f} similarity)")


if __name__ == "__main__":
    test_evaluation_system()
