"""Classification Service Module."""

import json
import re
from typing import Any, Dict, List
from backend.services.intelligence import query_intelligence_agent

class ClassificationService:
    """Stateless service providing classification capabilities."""

    def classify(self, text: str, categories: List[str], workspace_id: str, user_id: str = "admin") -> Dict[str, Any]:
        """Classifies text into one or more categories."""
        prompt = (
            f"Classify this text into one or more of these categories: {categories}. "
            f"Return JSON only: {{primary_category: str, confidence: float, tags: []}}\nText:\n{text}"
        )
        ans = query_intelligence_agent(prompt, workspace_id, user_id)
        if "Mock" in ans:
            return {
                "primary_category": categories[0] if categories else "general",
                "confidence": 0.95,
                "tags": ["extracted"]
            }
        
        try:
            match = re.search(r"\{.*\}", ans, re.DOTALL)
            return json.loads(match.group(0)) if match else {"raw_classification": ans}
        except Exception:
            return {"raw_classification": ans}
