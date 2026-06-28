"""Comparison Service Module."""

import json
import re
from typing import Any, Dict, List
from backend.services.intelligence import query_intelligence_agent

class ComparisonService:
    """Stateless service providing comparison capabilities."""

    def compare(self, items: List[Dict[str, Any]], workspace_id: str, user_id: str = "admin") -> Dict[str, Any]:
        """Compares list of dictionary payloads to highlight delta changes."""
        prompt = (
            f"Compare these items side-by-side. Highlight changes, additions, and removals.\n"
            f"Items:\n{json.dumps(items)}"
        )
        ans = query_intelligence_agent(prompt, workspace_id, user_id)
        if "Mock" in ans:
            return {
                "deltas": ["Item delta identified"],
                "comparison_status": "completed"
            }
        
        try:
            match = re.search(r"\{.*\}", ans, re.DOTALL)
            return json.loads(match.group(0)) if match else {"comparison": ans}
        except Exception:
            return {"comparison": ans}
