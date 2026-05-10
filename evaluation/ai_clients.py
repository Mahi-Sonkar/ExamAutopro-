import json
import logging
import os
import re
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


class FreeAIEvaluator:
    """
    Optional free-tier API evaluator.

    Keys must be supplied through environment variables:
    - GROQ_API_KEY for Groq chat completions
    - GEMINI_API_KEY or GOOGLE_API_KEY for Google Generative AI
    """

    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_key = (
            os.getenv("GEMINI_API_KEY", "").strip()
            or os.getenv("GOOGLE_API_KEY", "").strip()
            or os.getenv("GOOGLE_GENERATIVE_AI_API_KEY", "").strip()
        )

    @property
    def available(self) -> bool:
        return bool(self.groq_key or self.gemini_key)

    def evaluate(
        self,
        student_answer: str,
        model_answer: str,
        question_text: str,
        max_marks: float,
        keywords: str = "",
        question_type: str = "descriptive",
    ) -> Optional[Dict]:
        if not student_answer or not self.available:
            return None

        prompt = self._build_prompt(
            student_answer=student_answer,
            model_answer=model_answer,
            question_text=question_text,
            max_marks=max_marks,
            keywords=keywords,
            question_type=question_type,
        )

        providers = {
            "groq": self._evaluate_with_groq,
            "gemini": self._evaluate_with_gemini,
        }
        priority = [
            item.strip().lower()
            for item in os.getenv("AI_PROVIDER_PRIORITY", "gemini,groq").split(",")
            if item.strip().lower() in providers
        ]

        for provider_name in priority:
            try:
                result = providers[provider_name](prompt)
                if result:
                    result["score"] = max(0.0, min(float(result.get("score", 0.0)), float(max_marks)))
                    result["similarity"] = max(0.0, min(float(result.get("similarity", 0.0)), 1.0))
                    result["confidence"] = max(0.0, min(float(result.get("confidence", 0.0)), 1.0))
                    return result
            except Exception as exc:
                logger.warning("AI provider evaluation failed: %s", exc)

        return None

    def evaluate_objective(
        self,
        question_text: str,
        options,
        selected_option: str,
        max_marks: float,
    ) -> Optional[Dict]:
        if not question_text or not selected_option or not self.available:
            return None

        option_lines = "\n".join(f"- {option}" for option in options)
        prompt = f"""
You are an exam evaluator. Determine whether the selected option correctly answers the question.
Use standard academic knowledge. If the question wording is ambiguous, choose the best available option.

Return only JSON with these keys:
score, similarity, confidence, correct_answer, score_reason, feedback

Max marks: {max_marks}
Question: {question_text}
Options:
{option_lines}
Selected option: {selected_option}

Scoring rules:
- score is {max_marks} if selected option is correct, otherwise 0
- similarity is 1 for correct and 0 for incorrect
- confidence must be from 0 to 1
- correct_answer must be the best correct option text
- score_reason must briefly explain why the selected option is right or wrong
- feedback must be a short student-facing explanation
""".strip()

        providers = {
            "groq": self._evaluate_with_groq,
            "gemini": self._evaluate_with_gemini,
        }
        priority = [
            item.strip().lower()
            for item in os.getenv("AI_PROVIDER_PRIORITY", "gemini,groq").split(",")
            if item.strip().lower() in providers
        ]

        for provider_name in priority:
            try:
                result = providers[provider_name](prompt)
                if result:
                    result["score"] = max(0.0, min(float(result.get("score", 0.0)), float(max_marks)))
                    result["similarity"] = max(0.0, min(float(result.get("similarity", 0.0)), 1.0))
                    result["confidence"] = max(0.0, min(float(result.get("confidence", 0.0)), 1.0))
                    return result
            except Exception as exc:
                logger.warning("AI objective evaluation failed: %s", exc)

        return None

    def _build_prompt(
        self,
        student_answer: str,
        model_answer: str,
        question_text: str,
        max_marks: float,
        keywords: str,
        question_type: str,
    ) -> str:
        return f"""
You are an exam evaluator. Grade only against the question, model answer, and keywords.
Be strict, fair, and do not award marks for unrelated text.

Return only JSON with these keys:
score, similarity, confidence, correct_points, missing_points, incorrect_points, score_reason, feedback

Max marks: {max_marks}
Question type: {question_type}
Question: {question_text}
Model answer: {model_answer or "not provided; use the question text and standard academic knowledge as the rubric"}
Important keywords: {keywords or "not provided"}
Student answer: {student_answer}

Scoring rules:
- score must be a number from 0 to {max_marks}
- similarity must be from 0 to 1
- confidence must be from 0 to 1
- correct_points must list what the student got right
- missing_points must list important expected points that are absent
- incorrect_points must list inaccurate or irrelevant claims
- score_reason must explain why this exact score was awarded
- feedback must be a short student-facing summary
""".strip()

    def _evaluate_with_groq(self, prompt: str) -> Optional[Dict]:
        if not self.groq_key:
            return None

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            },
            timeout=20,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return self._parse_json(content, "groq")

    def _evaluate_with_gemini(self, prompt: str) -> Optional[Dict]:
        if not self.gemini_key:
            return None

        preferred_model = os.getenv("GEMINI_MODEL", "").strip()
        models = [preferred_model] if preferred_model else []
        models.extend([
            "gemini-2.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.5-flash",
        ])

        last_error = None
        for model in dict.fromkeys(item for item in models if item):
            try:
                response = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={"x-goog-api-key": self.gemini_key},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.1,
                            "responseMimeType": "application/json",
                        },
                    },
                    timeout=20,
                )
                response.raise_for_status()
                parts = response.json()["candidates"][0]["content"]["parts"]
                content = "".join(part.get("text", "") for part in parts)
                return self._parse_json(content, "gemini")
            except requests.HTTPError as exc:
                last_error = exc
                if exc.response is None or exc.response.status_code not in (404, 429, 503):
                    raise

        if last_error:
            raise last_error
        return None

    def _parse_json(self, content: str, provider: str) -> Dict:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        data = json.loads(match.group(0) if match else content)
        return {
            "score": data.get("score", 0),
            "similarity": data.get("similarity", data.get("confidence", 0)),
            "confidence": data.get("confidence", 0.8),
            "feedback": data.get("feedback", f"Evaluated with {provider}"),
            "correct_points": self._as_list(data.get("correct_points")),
            "missing_points": self._as_list(data.get("missing_points")),
            "incorrect_points": self._as_list(data.get("incorrect_points")),
            "score_reason": data.get("score_reason", ""),
            "correct_answer": data.get("correct_answer", ""),
            "provider": provider,
        }

    def _as_list(self, value):
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []
