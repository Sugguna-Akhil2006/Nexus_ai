"""Confidence Service Module."""

import json
import re
from typing import Any, Dict
from backend.services.intelligence import query_intelligence_agent

class ConfidenceService:
    """Stateless service providing confidence scoring and explanations."""

    def evaluate_confidence(self, text: str, context: str, workspace_id: str, user_id: str = "admin") -> Dict[str, Any]:
        """Evaluates confidence score and logic explanations for generated texts."""
        prompt = (
            "Analyze the reliability and confidence level of this text based on the provided context.\n"
            "Return JSON only: {confidence_score: float, explanation: str}\n"
            f"Generated Text:\n{text}\n\nSource Context:\n{context}"
        )
        ans = query_intelligence_agent(prompt, workspace_id, user_id)
        if "Mock" in ans:
            return {
                "confidence_score": 0.95,
                "explanation": "No hallucination detected, direct alignment with source context sentences."
            }
        
        try:
            match = re.search(r"\{.*\}", ans, re.DOTALL)
            return json.loads(match.group(0)) if match else {"raw": ans}
        except Exception:
            return {"raw": ans}
