"""
NLP Engine for Answer Evaluation
Advanced similarity calculation using sentence transformers
"""

from sentence_transformers import SentenceTransformer, util
import re
import logging

logger = logging.getLogger(__name__)

# Load the sentence transformer model
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Sentence transformer model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load sentence transformer model: {e}")
    model = None

def evaluate_answers(answer_text, question_text):
    """
    Evaluate answers against questions using semantic similarity with proper mapping
    
    Args:
        answer_text: Text containing student answers
        question_text: Text containing questions
    
    Returns:
        List of dictionaries with question, answer, and similarity scores
    """
    if not model:
        logger.error("Sentence transformer model not available")
        return []
    
    try:
        # Use enhanced question splitting
        questions = split_questions_enhanced(question_text)
        answers = split_answers(answer_text)
        
        logger.info(f"Found {len(questions)} questions and {len(answers)} answers")
        
        # Map questions to answers properly
        mapped_pairs = map_questions_to_answers(questions, answers)
        
        results = []
        
        # Evaluate each mapped question-answer pair
        for question, answer in mapped_pairs:
            if not question or not answer:
                continue
            
            # Calculate semantic similarity using real SentenceTransformer logic
            similarity = calculate_similarity(question, answer)
            
            results.append({
                "question": question,
                "answer": answer,
                "similarity": similarity
            })
        
        logger.info(f"Evaluated {len(results)} question-answer pairs with proper mapping")
        return results
        
    except Exception as e:
        logger.error(f"Error in evaluate_answers: {e}")
        import traceback
        traceback.print_exc()
        return []

def split_questions(text):
    """
    Split text into individual questions
    
    Args:
        text: Text containing questions
    
    Returns:
        List of question strings
    """
    try:
        # Common question patterns
        patterns = [
            r'\d+\.\s*(.+?)(?=\n\d+\.|\n\n|$)',  # Numbered questions: "1. Question text"
            r'[a-zA-Z]\)\s*(.+?)(?=\n[a-zA-Z]\)|\n\n|$)',  # Lettered: "a) Question text"
            r'Question\s*\d+:\s*(.+?)(?=Question|\n\n|$)',  # "Question 1: text"
            r'Q\d+\.\s*(.+?)(?=\nQ\d+\.|\n\n|$)',  # "Q1. text"
        ]
        
        questions = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    question_text = match[-1].strip()
                else:
                    question_text = match.strip()
                
                if len(question_text) > 10:  # Filter out very short matches
                    questions.append(question_text)
        
        # If no patterns found, split by newlines
        if not questions:
            lines = text.split('\n')
            questions = [line.strip() for line in lines if line.strip() and len(line.strip()) > 10]
        
        return questions
        
    except Exception as e:
        logger.error(f"Error splitting questions: {e}")
        return [text] if text.strip() else []

def split_answers(text):
    """
    Split text into individual answers using proper patterns
    
    Args:
        text: Text containing answers
    
    Returns:
        List of answer strings
    """
    try:
        # Enhanced patterns for answer splitting
        patterns = [
            r'\n\s*\d+[\.\)]\s*',  # Numbered: "1." or "1)"
            r'\n\s*Q\d+[\.\)]\s*',  # Questions: "Q1." or "Q1)"
            r'\n\s*Answer\s*\d+[\.\)]\s*',  # "Answer 1."
            r'\n\s*[a-zA-Z][\.\)]\s*',  # Lettered: "a." or "b)"
        ]
        
        # Try each pattern
        for pattern in patterns:
            parts = re.split(pattern, text)
            if len(parts) > 1:
                # Remove first empty element and clean up
                answers = []
                for part in parts[1:]:  # Skip first empty part
                    cleaned = part.strip()
                    if cleaned and len(cleaned) > 3:  # Filter very short parts
                        answers.append(cleaned)
                
                if answers:
                    logger.debug(f"Split answers using pattern {pattern}: {len(answers)} answers found")
                    return answers
        
        # Fallback: split by newlines with content filtering
        lines = text.split('\n')
        answers = []
        current_answer = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                # Empty line might indicate end of answer
                if current_answer:
                    answers.append(current_answer.strip())
                    current_answer = ""
                continue
            
            # Check if line starts a new answer (numbered pattern)
            if re.match(r'^\d+[\.\)]', line) or re.match(r'^[a-zA-Z][\.\)]', line):
                # Save previous answer if exists
                if current_answer:
                    answers.append(current_answer.strip())
                # Start new answer
                current_answer = line
            else:
                # Continue current answer
                current_answer += " " + line if current_answer else line
        
        # Don't forget the last answer
        if current_answer:
            answers.append(current_answer.strip())
        
        # Filter answers by minimum length
        filtered_answers = [ans for ans in answers if len(ans) > 5]
        
        logger.debug(f"Split answers using fallback: {len(filtered_answers)} answers found")
        return filtered_answers
        
    except Exception as e:
        logger.error(f"Error splitting answers: {e}")
        return [text] if text.strip() else []

def split_questions_enhanced(text):
    """
    Enhanced question splitting with proper pattern matching
    
    Args:
        text: Text containing questions
    
    Returns:
        List of question strings with numbers
    """
    try:
        questions = []
        
        # Pattern to match question beginnings with numbers
        question_pattern = r'(\d+[\.\)]\s*)(.+?)(?=\n\s*\d+[\.\)]|\n\n|$)'
        
        matches = re.findall(question_pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            question_num = match[0]  # "1. " or "2) "
            question_text = match[1].strip()  # The actual question
            
            if len(question_text) > 10:  # Filter out very short matches
                full_question = question_num + question_text
                questions.append(full_question)
        
        # Alternative pattern if above doesn't work
        if not questions:
            alt_pattern = r'(Q\d+[\.\)]\s*)(.+?)(?=\n\s*Q\d+[\.\)]|\n\n|$)'
            matches = re.findall(alt_pattern, text, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                question_num = match[0]
                question_text = match[1].strip()
                
                if len(question_text) > 10:
                    full_question = question_num + question_text
                    questions.append(full_question)
        
        logger.debug(f"Enhanced question splitting: {len(questions)} questions found")
        return questions
        
    except Exception as e:
        logger.error(f"Error in enhanced question splitting: {e}")
        return split_questions(text)  # Fallback to original function

def map_questions_to_answers(questions, answers):
    """
    Properly map questions to answers based on numbering
    
    Args:
        questions: List of question strings
        answers: List of answer strings
    
    Returns:
        List of (question, answer) tuples
    """
    try:
        mapped_pairs = []
        
        # Extract question numbers
        question_numbers = []
        for q in questions:
            # Try to extract question number
            match = re.search(r'(\d+)', q)
            if match:
                question_numbers.append(int(match.group(1)))
            else:
                question_numbers.append(len(question_numbers) + 1)
        
        # Create mapping
        for i, question in enumerate(questions):
            q_num = question_numbers[i]
            
            # Find corresponding answer
            answer = None
            if i < len(answers):
                answer = answers[i]
            else:
                # Try to find answer by number pattern
                for j, ans in enumerate(answers):
                    if re.search(rf'^{q_num}[\.\)]', ans) or re.search(rf'^Answer\s*{q_num}[\.\)]', ans):
                        answer = ans
                        break
                
                # If still not found, use the last available answer
                if not answer and answers:
                    answer = answers[-1]
            
            if question and answer:
                mapped_pairs.append((question.strip(), answer.strip()))
        
        logger.debug(f"Mapped {len(mapped_pairs)} question-answer pairs")
        return mapped_pairs
        
    except Exception as e:
        logger.error(f"Error mapping questions to answers: {e}")
        # Fallback: simple pairing
        return [(q.strip(), a.strip()) for q, a in zip(questions, answers)]

def calculate_similarity(text1, text2):
    """
    Calculate semantic similarity between two texts using SentenceTransformer
    
    Args:
        text1: First text string
        text2: Second text string
    
    Returns:
        Float similarity score between 0 and 1
    """
    try:
        if not model:
            logger.error("SentenceTransformer model not available")
            return 0.0
        
        # Clean and validate inputs
        text1 = str(text1).strip()
        text2 = str(text2).strip()
        
        if not text1 or not text2:
            logger.warning("Empty text provided for similarity calculation")
            return 0.0
        
        # Debug logging
        logger.debug(f"Calculating similarity between:")
        logger.debug(f"Text 1: {text1[:100]}...")
        logger.debug(f"Text 2: {text2[:100]}...")
        
        # Encode texts using SentenceTransformer
        embedding1 = model.encode(text1, convert_to_tensor=True)
        embedding2 = model.encode(text2, convert_to_tensor=True)
        
        # Calculate cosine similarity using sentence-transformers util
        similarity_tensor = util.cos_sim(embedding1, embedding2)
        similarity_score = float(similarity_tensor[0][0])
        
        # Ensure similarity is between 0 and 1
        similarity_score = max(0.0, min(1.0, similarity_score))
        
        logger.debug(f"Similarity calculated: {similarity_score:.4f}")
        
        return similarity_score
        
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        import traceback
        traceback.print_exc()
        return 0.0

def get_similarity_real(answer_text, expected_text):
    """
    Real similarity calculation using SentenceTransformer (as requested in fix)
    
    Args:
        answer_text: Student's answer
        expected_text: Expected/Model answer
    
    Returns:
        Float similarity score between 0 and 1
    """
    return calculate_similarity(answer_text, expected_text)

def advanced_similarity_calculation(student_answer, model_answer):
    """
    Advanced similarity calculation using multiple methods
    
    Args:
        student_answer: Student's answer
        model_answer: Model/expected answer
    
    Returns:
        Float similarity score
    """
    try:
        similarities = []
        
        # Clean texts
        student_clean = clean_text(student_answer)
        model_clean = clean_text(model_answer)
        
        # 1. Semantic similarity (sentence transformers)
        if model:
            semantic_sim = calculate_similarity(student_clean, model_clean)
            similarities.append(semantic_sim)
        
        # 2. Word overlap (Jaccard)
        jaccard_sim = jaccard_similarity(student_clean, model_clean)
        similarities.append(jaccard_sim)
        
        # 3. Cosine similarity on word frequencies
        cosine_sim = cosine_similarity_words(student_clean, model_clean)
        similarities.append(cosine_sim)
        
        # 4. Longest common subsequence
        lcs_sim = lcs_similarity(student_clean, model_clean)
        similarities.append(lcs_sim)
        
        # 5. Keyword matching
        keyword_sim = keyword_similarity(student_clean, model_clean)
        similarities.append(keyword_sim)
        
        # Weighted average
        weights = [0.4, 0.2, 0.15, 0.15, 0.1]  # Give more weight to semantic similarity
        final_similarity = sum(s * w for s, w in zip(similarities, weights))
        
        return max(0.0, min(1.0, final_similarity))
        
    except Exception as e:
        logger.error(f"Error in advanced similarity calculation: {e}")
        return 0.0

def clean_text(text):
    """Clean and normalize text"""
    try:
        # Convert to lowercase and remove extra whitespace
        text = str(text).lower().strip()
        
        # Remove special characters but keep spaces and punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error cleaning text: {e}")
        return str(text)

def jaccard_similarity(text1, text2):
    """Calculate Jaccard similarity between two texts"""
    try:
        words1 = set(clean_text(text1).split())
        words2 = set(clean_text(text2).split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
        
    except Exception as e:
        logger.error(f"Error calculating Jaccard similarity: {e}")
        return 0.0

def cosine_similarity_words(text1, text2):
    """Calculate cosine similarity between word frequency vectors"""
    try:
        from collections import Counter
        import math
        
        words1 = clean_text(text1).split()
        words2 = clean_text(text2).split()
        
        # Create word frequency vectors
        freq1 = Counter(words1)
        freq2 = Counter(words2)
        
        # Get union of words
        all_words = set(words1 + words2)
        
        # Create vectors
        vec1 = [freq1.get(word, 0) for word in all_words]
        vec2 = [freq2.get(word, 0) for word in all_words]
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0

def lcs_similarity(text1, text2):
    """Calculate similarity based on longest common subsequence"""
    try:
        text1 = clean_text(text1)
        text2 = clean_text(text2)
        
        def lcs_length(s1, s2):
            m, n = len(s1), len(s2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if s1[i-1] == s2[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            
            return dp[m][n]
        
        lcs_len = lcs_length(text1, text2)
        max_len = max(len(text1), len(text2))
        
        if max_len == 0:
            return 0.0
        
        return lcs_len / max_len
        
    except Exception as e:
        logger.error(f"Error calculating LCS similarity: {e}")
        return 0.0

def keyword_similarity(text1, text2):
    """Calculate similarity based on keyword matching"""
    try:
        # Extract keywords (words with length > 3)
        words1 = set(word for word in clean_text(text1).split() if len(word) > 3)
        words2 = set(word for word in clean_text(text2).split() if len(word) > 3)
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
        
    except Exception as e:
        logger.error(f"Error calculating keyword similarity: {e}")
        return 0.0

# Test function
def test_nlp():
    """Test NLP functionality"""
    print("Testing NLP functionality...")
    
    if not model:
        print("ERROR: Sentence transformer model not available")
        return False
    
    # Test similarity calculation
    text1 = "What is the capital of France?"
    text2 = "Paris is the capital city of France."
    
    similarity = calculate_similarity(text1, text2)
    print(f"Similarity test: {similarity:.3f}")
    
    # Test answer evaluation
    questions = "1. What is the capital of France?\n2. What is 2+2?"
    answers = "1. Paris is the capital of France.\n2. 2+2 equals 4."
    
    results = evaluate_answers(answers, questions)
    print(f"Evaluation test: {len(results)} results")
    
    return True

if __name__ == "__main__":
    test_nlp()
