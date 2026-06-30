"""ATS compliance scoring and resume quality analyzer engine."""

import json
from typing import Dict, List, Optional
import uuid

from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.resume.exceptions import ATSAnalysisError
from backend.intelligence.resume.models import (
    ATSResult, 
    ResumeData, 
    Resume, 
    ATSReport, 
    ATSCategoryScore,
    PersonalInformation,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Skill,
    CertificationEntry,
    SocialLink
)
from backend.intelligence.resume.scoring import ResumeScoringEngine
from backend.intelligence.resume.feedback import FeedbackCompiler
from backend.intelligence.resume.rules import SCORING_CATEGORIES


class ATSEngine:
    """Service to run Applicant Tracking System checks on resume context."""

    def __init__(self) -> None:
        self.scoring_engine = ResumeScoringEngine()
        self.feedback_compiler = FeedbackCompiler()
        self.event_bus = EventBus()

    def evaluate_resume(self, resume: Resume) -> ATSReport:
        """Evaluates a structured canonical Resume model against ATS criteria.

        Args:
            resume: The structured Resume model.

        Returns:
            ATSReport: Strongly typed report detailing scores and recommendations.

        Raises:
            ATSAnalysisError: If evaluation fails.
        """
        try:
            category_scores: List[ATSCategoryScore] = []

            # 1. Contact Information Completeness (Weight: 0.05)
            c_score, c_reason, c_sug = self.scoring_engine.score_contact_info(resume)
            category_scores.append(ATSCategoryScore(
                name="Contact Information Completeness",
                weight=SCORING_CATEGORIES["Contact Information Completeness"]["weight"],
                max_score=SCORING_CATEGORIES["Contact Information Completeness"]["max_score"],
                current_score=c_score,
                reason=c_reason,
                improvement_suggestions=c_sug
            ))

            # 2. Link Validation (Weight: 0.10)
            l_score, l_reason, l_sug = self.scoring_engine.score_links(resume)
            category_scores.append(ATSCategoryScore(
                name="Link Validation",
                weight=SCORING_CATEGORIES["Link Validation"]["weight"],
                max_score=SCORING_CATEGORIES["Link Validation"]["max_score"],
                current_score=l_score,
                reason=l_reason,
                improvement_suggestions=l_sug
            ))

            # 3. Section Completeness (Weight: 0.15)
            s_score, s_reason, s_sug = self.scoring_engine.score_sections(resume)
            category_scores.append(ATSCategoryScore(
                name="Section Completeness",
                weight=SCORING_CATEGORIES["Section Completeness"]["weight"],
                max_score=SCORING_CATEGORIES["Section Completeness"]["max_score"],
                current_score=s_score,
                reason=s_reason,
                improvement_suggestions=s_sug
            ))

            # 4. Keyword Coverage (Weight: 0.15)
            k_score, k_reason, k_sug, missing_keywords = self.scoring_engine.score_keywords(resume)
            category_scores.append(ATSCategoryScore(
                name="Keyword Coverage",
                weight=SCORING_CATEGORIES["Keyword Coverage"]["weight"],
                max_score=SCORING_CATEGORIES["Keyword Coverage"]["max_score"],
                current_score=k_score,
                reason=k_reason,
                improvement_suggestions=k_sug
            ))

            # 5. Skill Diversity (Weight: 0.10)
            sd_score, sd_reason, sd_sug = self.scoring_engine.score_skill_diversity(resume)
            category_scores.append(ATSCategoryScore(
                name="Skill Diversity",
                weight=SCORING_CATEGORIES["Skill Diversity"]["weight"],
                max_score=SCORING_CATEGORIES["Skill Diversity"]["max_score"],
                current_score=sd_score,
                reason=sd_reason,
                improvement_suggestions=sd_sug
            ))

            # 6. Experience Quality (Weight: 0.10)
            eq_score, eq_reason, eq_sug = self.scoring_engine.score_experience_quality(resume)
            category_scores.append(ATSCategoryScore(
                name="Experience Quality",
                weight=SCORING_CATEGORIES["Experience Quality"]["weight"],
                max_score=SCORING_CATEGORIES["Experience Quality"]["max_score"],
                current_score=eq_score,
                reason=eq_reason,
                improvement_suggestions=eq_sug
            ))

            # 7. Project Quality (Weight: 0.10)
            pq_score, pq_reason, pq_sug = self.scoring_engine.score_projects(resume)
            category_scores.append(ATSCategoryScore(
                name="Project Quality",
                weight=SCORING_CATEGORIES["Project Quality"]["weight"],
                max_score=SCORING_CATEGORIES["Project Quality"]["max_score"],
                current_score=pq_score,
                reason=pq_reason,
                improvement_suggestions=pq_sug
            ))

            # 8. Education Completeness (Weight: 0.05)
            ed_score, ed_reason, ed_sug = self.scoring_engine.score_education(resume)
            category_scores.append(ATSCategoryScore(
                name="Education Completeness",
                weight=SCORING_CATEGORIES["Education Completeness"]["weight"],
                max_score=SCORING_CATEGORIES["Education Completeness"]["max_score"],
                current_score=ed_score,
                reason=ed_reason,
                improvement_suggestions=ed_sug
            ))

            # 9. Certification Quality (Weight: 0.05)
            cq_score, cq_reason, cq_sug = self.scoring_engine.score_certifications(resume)
            category_scores.append(ATSCategoryScore(
                name="Certification Quality",
                weight=SCORING_CATEGORIES["Certification Quality"]["weight"],
                max_score=SCORING_CATEGORIES["Certification Quality"]["max_score"],
                current_score=cq_score,
                reason=cq_reason,
                improvement_suggestions=cq_sug
            ))

            # 10. Formatting Quality (Weight: 0.10)
            fq_score, fq_reason, fq_sug = self.scoring_engine.score_formatting(resume)
            category_scores.append(ATSCategoryScore(
                name="Formatting Quality",
                weight=SCORING_CATEGORIES["Formatting Quality"]["weight"],
                max_score=SCORING_CATEGORIES["Formatting Quality"]["max_score"],
                current_score=fq_score,
                reason=fq_reason,
                improvement_suggestions=fq_sug
            ))

            # 11. Readability (Weight: 0.05)
            r_score, r_reason, r_sug = self.scoring_engine.score_readability(resume)
            category_scores.append(ATSCategoryScore(
                name="Readability",
                weight=SCORING_CATEGORIES["Readability"]["weight"],
                max_score=SCORING_CATEGORIES["Readability"]["max_score"],
                current_score=r_score,
                reason=r_reason,
                improvement_suggestions=r_sug
            ))

            # Calculate Overall Score
            overall = sum(c.current_score * c.weight for c in category_scores)
            overall_score = round(overall, 1)

            # Compile strengths, weaknesses, priority improvements
            strengths, weaknesses, priorities, recommendations = self.feedback_compiler.compile_feedback(category_scores)

            return ATSReport(
                overall_score=overall_score,
                category_scores=category_scores,
                strengths=strengths,
                weaknesses=weaknesses,
                priority_improvements=priorities,
                detailed_recommendations=recommendations
            )
        except Exception as e:
            raise ATSAnalysisError(f"Failed to score resume: {e}") from e

    def analyze_ats(self, resume_data: ResumeData, raw_text: str) -> ATSResult:
        """Runs compliance checks, computes density/scoring, and flags format gaps.

        Args:
            resume_data: Structured ResumeData.
            raw_text: Full plain text of the resume.

        Returns:
            ATSResult: Computations of ATS compliance (backwards-compatible schema).

        Raises:
            ATSAnalysisError: On failure to parse compliance metrics.
        """
        try:
            # Map ResumeData to canonical Resume model
            resume = self._map_data_to_canonical(resume_data)
            
            # Run the new engine
            report = self.evaluate_resume(resume)
            
            # Map ATSReport back to ATSResult compatibility structure
            completeness = 70.0
            formatting = 70.0
            keyword = 70.0
            readability = 70.0
            quantification = 70.0
            
            for cat in report.category_scores:
                if cat.name == "Section Completeness":
                    completeness = cat.current_score
                elif cat.name == "Formatting Quality":
                    formatting = cat.current_score
                elif cat.name == "Keyword Coverage":
                    keyword = cat.current_score
                elif cat.name == "Readability":
                    readability = cat.current_score
                elif cat.name == "Experience Quality":
                    quantification = cat.current_score

            # Check action verbs
            action_verbs_found = []
            for exp in resume.experience:
                for b in (exp.responsibilities + exp.achievements):
                    words = b.lower().split()
                    if words:
                        first = words[0]
                        if first in ["built", "designed", "implemented", "optimized", "developed", "architected", "automated", "integrated", "created", "generated"]:
                            action_verbs_found.append(first.capitalize())

            # Missing sections mapping
            missing_sections = []
            core_names = ["personal_info", "education", "experience", "projects", "skills"]
            if not resume_data.education:
                missing_sections.append("Education")
            if not resume_data.experience:
                missing_sections.append("Experience")
            if not resume_data.projects:
                missing_sections.append("Projects")
            if not resume_data.skills:
                missing_sections.append("Skills")

            readability_level = "Standard"
            if readability >= 85.0:
                readability_level = "High"
            elif readability < 65.0:
                readability_level = "Low"

            # Parse missing keywords
            _, _, _, missing_kws = self.scoring_engine.score_keywords(resume)

            return ATSResult(
                score=report.overall_score,
                completeness_score=completeness,
                formatting_score=formatting,
                keyword_density_score=keyword,
                verb_metric_score=readability,
                quantification_score=quantification,
                missing_keywords=missing_kws,
                action_verbs_found=list(set(action_verbs_found)),
                missing_sections=missing_sections,
                readability_level=readability_level
            )
        except Exception as e:
            raise ATSAnalysisError(f"Failed to map structured JSON payload to ATSResult: {e}") from e

    def _map_data_to_canonical(self, resume_data: ResumeData) -> Resume:
        """Helper to convert MVP ResumeData object to canonical Resume model."""
        info = resume_data.contact_info
        
        linkedin = getattr(info, "linkedin", "") or ""
        github = getattr(info, "github", "") or ""
        portfolio = getattr(info, "portfolio", "") or ""
        social_links = []
        
        # Parse links list for profiles
        for link in getattr(info, "links", []) or []:
            if "linkedin.com" in link.lower():
                linkedin = link
            elif "github.com" in link.lower():
                github = link
            else:
                if not portfolio:
                    portfolio = link
                social_links.append(SocialLink(platform="Website", url=link))
                
        personal_info = PersonalInformation(
            full_name=info.name or "",
            email=info.email or "",
            phone=info.phone or "",
            linkedin=linkedin,
            github=github,
            portfolio=portfolio,
            location=None,
            address=None,
            website=portfolio,
            social_links=social_links
        )

        education = []
        for edu in resume_data.education:
            gpa_cgpa = getattr(edu, "gpa", None)
            gpa_str = str(gpa_cgpa) if gpa_cgpa is not None else ""
            if not gpa_str and hasattr(edu, "gpa_cgpa"):
                gpa_str = str(getattr(edu, "gpa_cgpa", ""))
            education.append(EducationEntry(
                institution=getattr(edu, "institution", "") or "",
                degree=getattr(edu, "degree", "") or "",
                branch=getattr(edu, "field_of_study", "") or getattr(edu, "branch", "") or "",
                gpa_cgpa=gpa_str,
                graduation_year=getattr(edu, "graduation_year", "") or getattr(edu, "end_year", "") or "",
                start_year=None,
                end_year=getattr(edu, "graduation_year", "") or getattr(edu, "end_year", "") or "",
                description=None
            ))

        experience = []
        for exp in resume_data.experience:
            role_str = getattr(exp, "role", "") or getattr(exp, "job_title", "") or ""
            experience.append(ExperienceEntry(
                company=getattr(exp, "company", "") or "",
                role=role_str,
                start_date=getattr(exp, "start_date", "") or "",
                end_date=getattr(exp, "end_date", "") or "",
                duration=getattr(exp, "duration", None),
                responsibilities=getattr(exp, "responsibilities", []) or [],
                location=None,
                technologies_used=[],
                achievements=getattr(exp, "achievements", []) or []
            ))

        projects = []
        for proj in resume_data.projects:
            proj_name = getattr(proj, "project_name", "") or getattr(proj, "name", "") or ""
            
            github_url = getattr(proj, "github_url", "") or ""
            live_url = getattr(proj, "live_url", "") or ""
            for l in getattr(proj, "links", []) or []:
                if "github.com" in l.lower():
                    github_url = l
                else:
                    live_url = l

            projects.append(ProjectEntry(
                project_name=proj_name,
                name=proj_name,
                description=getattr(proj, "description", "") or "",
                technologies=getattr(proj, "technologies", []) or [],
                github_url=github_url,
                live_url=live_url,
                github_link=github_url,
                live_demo=live_url,
                duration=None,
                contributions=getattr(proj, "contributions", []) or [],
                team_size=None
            ))

        skills = []
        for sk in resume_data.skills:
            skills.append(Skill(
                name=sk,
                category="Other",
                proficiency="Intermediate"
            ))

        certifications = []
        for cert in resume_data.certifications:
            certifications.append(CertificationEntry(
                certification_name=cert.name or "",
                organization=cert.issuing_organization or "",
                year=cert.issue_date or "",
                credential_id=None,
                verification_url=None
            ))

        return Resume(
            personal_info=personal_info,
            education=education,
            experience=experience,
            projects=projects,
            skills=skills,
            certifications=certifications,
            languages=[],
            awards=[],
            publications=[],
            volunteer=[],
            custom_sections=[]
        )
