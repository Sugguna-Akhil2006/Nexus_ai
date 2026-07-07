"""Detects user query intents and maps them to required intelligence modules."""

import re
from typing import List


class RequestAnalyzer:
    """Analyzes natural language queries to resolve module dependency intents."""

    def analyze_request_intent(self, query: str) -> List[str]:
        """Scans the query for keywords and resolves which engines must run.

        Mappings:
        - "Resume": resume, cv, career, experience, job, background, education.
        - "GitHub": github, repo, repository, commit, coding, contributor.
        - "Document": document, file, pdf, docx, txt, summarize, summary.
        - "Research": paper, research, literature, scientific, bibliography, reading, whitepaper.
        """
        q_lower = query.lower()
        intents = []

        if any(w in q_lower for w in ("resume", "cv", "career", "experience", "job", "background", "education")):
            intents.append("Resume")
            
        if any(w in q_lower for w in ("github", "repo", "repository", "commit", "coding", "contributor")):
            intents.append("GitHub")

        if any(w in q_lower for w in ("document", "file", "pdf", "docx", "txt", "summarize", "summary")):
            # If research paper is also mentioned, prefer Research over generic Document
            if not any(w in q_lower for w in ("paper", "research", "literature", "scientific", "whitepaper")):
                intents.append("Document")

        if any(w in q_lower for w in ("paper", "research", "literature", "scientific", "bibliography", "reading", "whitepaper")):
            intents.append("Research")

        # Fallback: if nothing is matched, check if general profile queries
        if not intents:
            if "profile" in q_lower or "skill" in q_lower or "technology" in q_lower or "project" in q_lower:
                # Direct everything to Resume and GitHub
                intents.extend(["Resume", "GitHub"])
            else:
                # Default fallback
                intents.append("Document")

        return list(set(intents))
