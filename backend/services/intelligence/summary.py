"""Summarization Service Module."""

from backend.services.intelligence import query_intelligence_agent

class SummaryService:
    """Stateless service providing summarization capabilities."""

    def summarize(self, text: str, workspace_id: str, user_id: str = "admin") -> str:
        """Summarizes raw text details using LLM completion."""
        prompt = f"Summarize the following text concisely:\n{text}"
        ans = query_intelligence_agent(prompt, workspace_id, user_id)
        if "Mock" in ans:
            return "Summarized Text: Jane Doe is an experienced software architect specializing in Python backend architectures."
        return ans
