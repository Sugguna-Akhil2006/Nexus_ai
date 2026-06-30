"""SWOT resume analyzer generating strengths, weaknesses, and interview questions."""

import json
from typing import Any, Dict
from backend.intelligence.resume.exceptions import ResumeIntelligenceError
from backend.intelligence.resume.models import ResumeAnalysis, ResumeData
from backend.intelligence.resume.parser import run_resume_llm_query
from backend.intelligence.resume.prompts import SWOT_SCHEMA


def clean_string_list(lst: Any) -> list[str]:
    res = []
    for item in (lst or []):
        if isinstance(item, dict):
            val = item.get("description") or item.get("question") or item.get("suggestion") or next(iter(item.values()), str(item))
            res.append(str(val))
        elif item is not None:
            res.append(str(item))
    return res


class ResumeAnalyzer:
    """Service to evaluate strengths, gaps, readiness, and interview preparation tips."""

    def analyze(self, resume_data: ResumeData, raw_text: str) -> ResumeAnalysis:
        """Evaluates candidate profiles, deduces SWOT metrics, and lists target questions.

        Args:
            resume_data: Structured ResumeData.
            raw_text: Full plain text of the resume.

        Returns:
            ResumeAnalysis: SWOT and career readiness results.

        Raises:
            ResumeIntelligenceError: On general analysis failures.
        """
        from typing import Any
        parsed_json = run_resume_llm_query("resume_general_analysis", raw_text, SWOT_SCHEMA)

        try:
            return ResumeAnalysis(
                strengths=clean_string_list(parsed_json.get("strengths")),
                weaknesses=clean_string_list(parsed_json.get("weaknesses")),
                improvement_suggestions=clean_string_list(parsed_json.get("improvement_suggestions")),
                career_readiness=str(parsed_json.get("career_readiness", "Mid-level Engineer")),
                interview_preparation_tips=clean_string_list(parsed_json.get("interview_preparation_tips"))
            )
        except Exception as e:
            raise ResumeIntelligenceError(f"Failed to map structured JSON payload to ResumeAnalysis: {e}") from e
