"""Entity Extraction Service Module."""

import json
import re
from typing import Any, Dict
from backend.services.intelligence import query_intelligence_agent

class EntityExtractionService:
    """Stateless service providing entity extraction capabilities."""

    def extract_entities(self, text: str, schema: Dict[str, Any], workspace_id: str, user_id: str = "admin") -> Dict[str, Any]:
        """Extracts structured entities conforming to specified schema."""
        prompt = (
            f"Extract entities matching the schema {json.dumps(schema)} from this text. "
            f"Return JSON only:\nText:\n{text}"
        )
        ans = query_intelligence_agent(prompt, workspace_id, user_id)
        if "Mock" in ans:
            # Fallback mock extraction
            return {
                "name": "Jane Doe",
                "email": "jane.doe@example.com"
            }
        
        try:
            match = re.search(r"\{.*\}", ans, re.DOTALL)
            return json.loads(match.group(0)) if match else {"raw": ans}
        except Exception:
            return {"raw": ans}
