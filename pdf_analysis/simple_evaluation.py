"""
Simple Evaluation Logic
STEP 9: Simple evaluation logic
"""

import re
from typing import List, Dict, Tuple

def evaluate_answer(student_answer: str, keywords: List[str]) -> Dict:
    """
    STEP 9: Simple evaluation logic
    Evaluate student answer based on keywords
    """
    if not student_answer or not keywords:
        return {
            'score': 0,
            'matched_keywords': [],
            'total_keywords': len(keywords),
            'percentage': 0.0
        }
    
    # Clean student answer
    cleaned_answer = student_answer.lower()
    
    # Find matched keywords
    matched_keywords = []
    for keyword in keywords:
        keyword_lower = keyword.lower().strip()
        if keyword_lower in cleaned_answer:
            matched_keywords.append(keyword)
    
    # Calculate score
    total_keywords = len(keywords)
    matched_count = len(matched_keywords)
    score = matched_count
    percentage = (matched_count / total_keywords) * 100 if total_keywords > 0 else 0
    
    return {
        'score': score,
        'matched_keywords': matched_keywords,
        'total_keywords': total_keywords,
        'percentage': percentage
    }

def evaluate_multiple_choice(student_answer: str, correct_answer: str) -> Dict:
    """Evaluate multiple choice answer"""
    student_clean = student_answer.lower().strip()
    correct_clean = correct_answer.lower().strip()
    
    is_correct = student_clean == correct_clean
    
    return {
        'score': 1 if is_correct else 0,
        'is_correct': is_correct,
        'student_answer': student_clean,
        'correct_answer': correct_clean
    }

def evaluate_descriptive(student_answer: str, model_answer: str, keywords: List[str] = None) -> Dict:
    """Evaluate descriptive answer with multiple criteria"""
    if not student_answer or not model_answer:
        return {
            'score': 0,
            'content_score': 0,
            'keyword_score': 0,
            'length_score': 0,
            'total_score': 0
        }
    
    # Content similarity (basic word overlap)
    student_words = set(student_answer.lower().split())
    model_words = set(model_answer.lower().split())
    
    common_words = student_words.intersection(model_words)
    content_score = len(common_words) / len(model_words) if model_words else 0
    
    # Keyword matching
    keyword_score = 0
    matched_keywords = []
    if keywords:
        for keyword in keywords:
            if keyword.lower() in student_answer.lower():
                keyword_score += 1
                matched_keywords.append(keyword)
        keyword_score = keyword_score / len(keywords) if keywords else 0
    
    # Length appropriateness
    student_length = len(student_answer.split())
    model_length = len(model_answer.split())
    
    if student_length >= model_length * 0.5 and student_length <= model_length * 2:
        length_score = 1.0
    elif student_length >= model_length * 0.3 and student_length <= model_length * 3:
        length_score = 0.7
    else:
        length_score = 0.3
    
    # Calculate total score
    total_score = (content_score * 0.5 + keyword_score * 0.3 + length_score * 0.2) * 100
    
    return {
        'score': total_score,
        'content_score': content_score * 100,
        'keyword_score': keyword_score * 100,
        'length_score': length_score * 100,
        'matched_keywords': matched_keywords,
        'word_overlap': len(common_words),
        'total_model_words': len(model_words)
    }

def batch_evaluate_answers(student_answers: List[Dict], model_answers: List[Dict]) -> List[Dict]:
    """Batch evaluate multiple answers"""
    results = []
    
    for i, student_ans in enumerate(student_answers):
        if i < len(model_answers):
            model_ans = model_answers[i]
            
            # Determine question type and evaluate accordingly
            question_type = student_ans.get('type', 'descriptive')
            
            if question_type == 'multiple_choice':
                result = evaluate_multiple_choice(
                    student_ans.get('answer', ''),
                    model_ans.get('correct_answer', '')
                )
            elif question_type == 'keywords':
                result = evaluate_answer(
                    student_ans.get('answer', ''),
                    model_ans.get('keywords', [])
                )
            else:
                result = evaluate_descriptive(
                    student_ans.get('answer', ''),
                    model_ans.get('model_answer', ''),
                    model_ans.get('keywords', [])
                )
            
            result['question_id'] = student_ans.get('id', i)
            result['question_type'] = question_type
            results.append(result)
    
    return results

def generate_evaluation_report(results: List[Dict]) -> Dict:
    """Generate comprehensive evaluation report"""
    if not results:
        return {
            'total_questions': 0,
            'total_score': 0,
            'average_score': 0,
            'performance_breakdown': {}
        }
    
    total_questions = len(results)
    total_score = sum(r.get('score', 0) for r in results)
    average_score = total_score / total_questions if total_questions > 0 else 0
    
    # Performance breakdown by question type
    performance_breakdown = {}
    for result in results:
        q_type = result.get('question_type', 'unknown')
        if q_type not in performance_breakdown:
            performance_breakdown[q_type] = {
                'count': 0,
                'total_score': 0,
                'average_score': 0
            }
        
        performance_breakdown[q_type]['count'] += 1
        performance_breakdown[q_type]['total_score'] += result.get('score', 0)
    
    # Calculate averages for each type
    for q_type, data in performance_breakdown.items():
        if data['count'] > 0:
            data['average_score'] = data['total_score'] / data['count']
    
    return {
        'total_questions': total_questions,
        'total_score': total_score,
        'average_score': average_score,
        'performance_breakdown': performance_breakdown,
        'individual_results': results
    }
