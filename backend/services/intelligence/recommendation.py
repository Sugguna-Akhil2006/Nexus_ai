"""Recommendation Service Module."""

import json
import re
from typing import Any, Dict, List
from backend.services.intelligence import query_intelligence_agent

class RecommendationService:
    """Stateless service providing recommendations generation capabilities."""

    def generate_recommendations(self, context_text: str, goals: List[str], workspace_id: str, user_id: str = "admin") -> List[Dict[str, Any]]:
        """Generates structured recommended items based on context text and goals."""
        prompt = (
            f"Generate recommendations aligned with these goals: {goals}.\n"
            f"Context:\n{context_text}"
        )
        ans = query_intelligence_agent(prompt, workspace_id, user_id)
        if "Mock" in ans:
            return [
                {
                    "recommendation": "Incorporate numeric indicators",
                    "priority": "HIGH",
                    "rationale": "Improves readability and ATS rating checklist"
                }
            ]
        
        try:
            match = re.search(r"\[.*\]", ans, re.DOTALL)
            return json.loads(match.group(0)) if match else [{"raw": ans}]
        except Exception:
            return [{"raw": ans}]
