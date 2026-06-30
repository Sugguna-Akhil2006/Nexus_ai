"""Job Description matcher comparing resume attributes against core requirements."""

import json
from typing import Dict, List, Optional
import uuid

from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.resume.exceptions import JDMatchingError
from backend.intelligence.resume.models import (
    JDMatchResult,
    ResumeData,
    Resume,
    JobDescription,
    JDMatchReport,
    JDCategoryMatch
)
from backend.intelligence.resume.jd_parser import JobDescriptionParser
from backend.intelligence.resume.matching import MatchingEvaluator
from backend.intelligence.resume.gap_analysis import GapAnalyzer
from backend.intelligence.resume.recommendations import RecommendationEngine
from backend.intelligence.resume.ats_engine import ATSEngine


class JDMatcher:
    """Service to compare candidate profiles against Job Descriptions."""

    def __init__(self) -> None:
        self.parser = JobDescriptionParser()
        self.evaluator = MatchingEvaluator()
        self.gap_analyzer = GapAnalyzer()
        self.rec_engine = RecommendationEngine()
        self.event_bus = EventBus()

    def match_resume_to_jd(
        self,
        resume: Resume,
        jd: JobDescription,
        workspace_id: str = "default-ws",
        document_id: Optional[str] = None
    ) -> JDMatchReport:
        """Compares structured Resume against normalized JobDescription, producing suitability metrics.

        Args:
            resume: Normalized canonical candidate profile.
            jd: Structured target job description.
            workspace_id: Current workspace context ID.
            document_id: Linked document reference ID.

        Returns:
            JDMatchReport: Explainable suitability scoring, gaps, and recommendations.

        Raises:
            JDMatchingError: If calculation fails.
        """
        try:
            # 1. Run detailed category comparison
            category_scores = self.evaluator.evaluate_match(resume, jd)

            # 2. Calculate overall weighted score
            overall = sum(cat.score * cat.weight for cat in category_scores)
            overall_score = round(overall, 1)

            # 3. Extract missing and matching skills list
            missing_skills = []
            matching_skills = []
            skill_cats = ["Technical Skills", "Programming Languages", "Frameworks", "Databases", "Cloud Platforms", "AI/ML Skills", "DevOps", "Soft Skills"]
            for cat in category_scores:
                if cat.category_name in skill_cats:
                    for ev in cat.matching_evidence:
                        clean = ev.replace("Found matching:", "").strip()
                        if clean and clean != "No matching skills found.":
                            matching_skills.append(clean)
                    for ev in cat.missing_evidence:
                        clean = ev.replace("Missing target:", "").strip()
                        if clean:
                            missing_skills.append(clean)

            # 4. Perform gap analysis
            gap_analysis = self.gap_analyzer.analyze_gaps(category_scores)

            # 5. Formulate recommendations
            recommendations = self.rec_engine.generate_recommendations(category_scores)

            # 6. Confidence score (simple average of category confidences)
            confidences = [cat.confidence for cat in category_scores]
            avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 1.0

            report = JDMatchReport(
                overall_score=overall_score,
                category_scores=category_scores,
                missing_skills=list(set(missing_skills)),
                matching_skills=list(set(matching_skills)),
                gap_analysis=gap_analysis,
                recommendations=recommendations,
                confidence=avg_confidence
            )

            # Publish event: resume.jd.matched
            event = Event(
                event_type=EventType.CUSTOM_EVENT,
                source="JDMatcher",
                payload={
                    "event": "resume.jd.matched",
                    "workspace_id": workspace_id,
                    "document_id": document_id,
                    "match_report": report.model_dump()
                }
            )
            self.event_bus.publish(event)

            return report
        except Exception as e:
            raise JDMatchingError(f"Failed to match candidate against Job Description: {e}") from e

    def match(self, resume_data: ResumeData, raw_text: str, job_description: str) -> JDMatchResult:
        """Computes matching percentage, missing skills, and detailed gap suggestions (backwards compatible).

        Args:
            resume_data: Structured ResumeData.
            raw_text: Full plain text of the resume.
            job_description: Plain text of the job description.

        Returns:
            JDMatchResult: Detailed JD match metrics.

        Raises:
            JDMatchingError: On failure to match.
        """
        try:
            # 1. Parse Job Description dynamically using LLM parser
            jd = self.parser.parse_jd(job_description)

            # 2. Map legacy ResumeData to canonical Resume model
            ats_helper = ATSEngine()
            resume = ats_helper._map_data_to_canonical(resume_data)

            # 3. Perform canonical match
            report = self.match_resume_to_jd(resume, jd)

            # 4. Map report findings back to legacy JDMatchResult
            gap_str = "\n".join(report.gap_analysis)
            
            section_feedback = {}
            for cat in report.category_scores:
                section_feedback[cat.category_name] = "; ".join(cat.matching_evidence + cat.missing_evidence)

            missing_kws = report.missing_skills
            # Add missing techs and certs if not in missing_skills
            for cat in report.category_scores:
                if cat.category_name in ["Certifications", "Technical Skills"]:
                    for ev in cat.missing_evidence:
                        clean = ev.replace("Missing target:", "").replace("Missing certification:", "").strip()
                        if clean and clean not in missing_kws:
                            missing_kws.append(clean)

            return JDMatchResult(
                match_percentage=report.overall_score,
                matching_skills=report.matching_skills,
                missing_skills=report.missing_skills,
                missing_keywords=missing_kws,
                gap_analysis=gap_str,
                recommendations=report.recommendations,
                section_specific_feedback=section_feedback
            )
        except Exception as e:
            raise JDMatchingError(f"Failed to map structured JSON payload to JDMatchResult: {e}") from e
