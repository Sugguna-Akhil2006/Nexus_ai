"""Job Description Parser using LLM query schema extraction and skill normalization."""

from typing import List, Optional
import json

from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.resume.exceptions import JDParserError
from backend.intelligence.resume.models import JobDescription
from backend.intelligence.resume.parser import run_resume_llm_query
from backend.intelligence.resume.prompts import JD_SCHEMA
from backend.intelligence.resume.normalizer import normalize_skill_name


class JobDescriptionParser:
    """Parses raw text of Job Descriptions into canonical JobDescription models."""

    def parse_jd(
        self,
        jd_text: str,
        workspace_id: str = "default-ws",
        document_id: Optional[str] = None
    ) -> JobDescription:
        """Extracts structured fields from job description plaintext and normalizes names.

        Args:
            jd_text: Job Description plaintext content.
            workspace_id: Associated workspace context ID.
            document_id: Optional linked candidate document ID.

        Returns:
            JobDescription: Structured, normalized job description.

        Raises:
            JDParserError: On extraction failure.
        """
        if not jd_text or not jd_text.strip():
            raise JDParserError("Job Description plaintext cannot be empty.")

        try:
            # Query local LLM registry template
            parsed_json = run_resume_llm_query("resume_jd_parser", jd_text, JD_SCHEMA)
            
            # Extract lists
            req_skills = parsed_json.get("required_skills", []) or []
            pref_skills = parsed_json.get("preferred_skills", []) or []
            techs = parsed_json.get("technologies", []) or []
            certs = parsed_json.get("certifications", []) or []
            soft = parsed_json.get("soft_skills", []) or []
            
            # Normalize and deduplicate helper
            def clean_and_normalize(items: List[str]) -> List[str]:
                seen = set()
                result = []
                for item in items:
                    if item:
                        norm = normalize_skill_name(str(item))
                        if norm and norm.lower() not in seen:
                            seen.add(norm.lower())
                            result.append(norm)
                return result

            # Populate JobDescription
            jd = JobDescription(
                job_title=parsed_json.get("job_title", "Unknown Role") or "Unknown Role",
                company=parsed_json.get("company"),
                experience_required=parsed_json.get("experience_required"),
                education_requirements=parsed_json.get("education_requirements", []) or [],
                required_skills=clean_and_normalize(req_skills),
                preferred_skills=clean_and_normalize(pref_skills),
                responsibilities=parsed_json.get("responsibilities", []) or [],
                technologies=clean_and_normalize(techs),
                certifications=clean_and_normalize(certs),
                soft_skills=clean_and_normalize(soft),
                location=parsed_json.get("location"),
                employment_type=parsed_json.get("employment_type")
            )

            # Publish event: resume.jd.parsed
            bus = EventBus()
            event = Event(
                event_type=EventType.CUSTOM_EVENT,
                source="JobDescriptionParser",
                payload={
                    "event": "resume.jd.parsed",
                    "workspace_id": workspace_id,
                    "document_id": document_id,
                    "job_description": jd.model_dump()
                }
            )
            bus.publish(event)

            return jd
        except Exception as e:
            raise JDParserError(f"Failed to parse and normalize Job Description: {e}") from e
