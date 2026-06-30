"""Central reasoning engine evaluating structured resumes without LLM calls or document parsing."""

import uuid
from typing import Dict, List, Optional

from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.resume.models import (
    Resume,
    SkillProfile,
    ATSReport,
    JDMatchReport,
    ResumeAnalysisReport
)
from backend.intelligence.resume.career_stage import CareerStageClassifier
from backend.intelligence.resume.strength_analyzer import StrengthAnalyzer
from backend.intelligence.resume.weakness_analyzer import WeaknessAnalyzer
from backend.intelligence.resume.readiness import ReadinessEvaluator
from backend.intelligence.resume.recommendations import AnalysisRecommendationEngine
from backend.intelligence.resume.validators import parse_date_safely


class ResumeAnalysisEngine:
    """Consolidates candidate structured attributes into explainable multi-point reports."""

    def __init__(self) -> None:
        self.stage_classifier = CareerStageClassifier()
        self.strength_analyzer = StrengthAnalyzer()
        self.weakness_analyzer = WeaknessAnalyzer()
        self.readiness_evaluator = ReadinessEvaluator()
        self.rec_engine = AnalysisRecommendationEngine()
        self.event_bus = EventBus()

    def analyze_resume_canonical(
        self,
        resume: Resume,
        skill_profile: Optional[SkillProfile] = None,
        ats_report: Optional[ATSReport] = None,
        jd_match: Optional[JDMatchReport] = None,
        workspace_id: str = "default-ws",
        document_id: str = ""
    ) -> ResumeAnalysisReport:
        """Runs reasoning evaluation across canonical candidate data.

        Args:
            resume: Canonical candidate resume.
            skill_profile: Optional extracted skill metadata profile.
            ats_report: Optional ATS compliance scoring report.
            jd_match: Optional Job Description suitability matching report.
            workspace_id: Current workspace context ID.
            document_id: Linked candidate document reference ID.

        Returns:
            ResumeAnalysisReport: Scored evaluation report.
        """
        # 1. Classify Stage and specialization
        stage, spec = self.stage_classifier.classify(resume)
        career_stage_str = f"{stage} {spec}"

        # 2. Extract strengths and weaknesses
        strengths = self.strength_analyzer.analyze_strengths(resume)
        weaknesses = self.weakness_analyzer.analyze_weaknesses(resume)

        # 3. Calculate 15 sub-scores
        scores = self._calculate_sub_scores(resume, skill_profile, strengths, weaknesses, stage)

        # 4. Evaluate Career Readiness
        readiness = self.readiness_evaluator.evaluate_readiness(resume, strengths, weaknesses, stage)

        # 5. Compile Recommendations
        recommendations = self.rec_engine.generate_analysis_recommendations(resume, weaknesses)

        # Compile final report
        report = ResumeAnalysisReport(
            report_id=f"rep-{str(uuid.uuid4())[:8]}",
            document_id=document_id or str(uuid.uuid4()),
            workspace_id=workspace_id,
            strengths=strengths,
            weaknesses=weaknesses,
            scores=scores,
            recommendations=recommendations,
            career_stage=career_stage_str,
            career_readiness=readiness,
            confidence=readiness.confidence
        )

        # Publish custom platform event: resume.analysis.completed
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ResumeAnalysisEngine",
            payload={
                "event": "resume.analysis.completed",
                "workspace_id": workspace_id,
                "document_id": document_id,
                "analysis_report": report.model_dump()
            }
        )
        self.event_bus.publish(event)

        return report

    def _calculate_sub_scores(
        self,
        resume: Resume,
        profile: Optional[SkillProfile],
        strengths: List[str],
        weaknesses: List[str],
        stage: str
    ) -> Dict[str, float]:
        """Runs rule-based calculations to output 0-100 metrics for the 15 target categories."""
        scores = {}

        # 1. Resume Completeness
        completeness = 0.0
        if resume.personal_info.email: completeness += 20.0
        if resume.personal_info.phone: completeness += 20.0
        if resume.education: completeness += 20.0
        if resume.experience or stage == "Student": completeness += 20.0
        if resume.skills: completeness += 20.0
        scores["Resume Completeness"] = completeness

        # 2. Technical Strength
        scores["Technical Strength"] = min(100.0, max(30.0, len(resume.skills) * 8.0))

        # 3. Project Quality
        proj_score = 0.0
        if resume.projects:
            for p in resume.projects:
                proj_score += 50.0
                if len(p.technologies) >= 3: proj_score += 20.0
                if len(p.contributions) >= 2: proj_score += 30.0
            proj_score = proj_score / len(resume.projects)
        else:
            proj_score = 40.0
        scores["Project Quality"] = min(100.0, proj_score)

        # 4. Experience Quality
        if resume.experience:
            has_impact = not any("Missing Impact" in w for w in weaknesses)
            exp_score = 70.0 + (30.0 if has_impact else 0.0)
        else:
            exp_score = 80.0 if stage == "Student" else 30.0
        scores["Experience Quality"] = exp_score

        # 5. Education Strength
        edu_score = 60.0
        for edu in resume.education:
            deg = (edu.degree or "").lower()
            if "phd" in deg or "doctor" in deg:
                edu_score = max(edu_score, 100.0)
            elif "master" in deg or "ms" in deg or "m.s" in deg:
                edu_score = max(edu_score, 90.0)
            elif "bachelor" in deg or "bs" in deg or "b.s" in deg:
                edu_score = max(edu_score, 80.0)
        scores["Education Strength"] = edu_score

        # 6. Certification Value
        scores["Certification Value"] = 100.0 if resume.certifications else 50.0

        # 7. Portfolio Quality
        has_portfolio = not any("Missing Portfolio" in w for w in weaknesses)
        scores["Portfolio Quality"] = 100.0 if has_portfolio else 40.0

        # 8. Open Source Contributions
        has_github = not any("Missing GitHub" in w for w in weaknesses)
        scores["Open Source Contributions"] = 100.0 if has_github else 30.0

        # 9. Leadership Indicators
        has_leadership = any("Leadership Indicators" in s for s in strengths)
        scores["Leadership Indicators"] = 100.0 if has_leadership else 60.0

        # 10. Career Growth
        if len(resume.experience) >= 2:
            scores["Career Growth"] = 100.0
        elif len(resume.experience) == 1:
            scores["Career Growth"] = 80.0
        else:
            scores["Career Growth"] = 50.0

        # 11. Learning Pattern
        has_learning = resume.certifications or resume.publications or len(resume.education) >= 2
        scores["Learning Pattern"] = 100.0 if has_learning else 70.0

        # 12. Technology Breadth
        # Compute breadth based on categories count in skill profile
        categories_count = 0
        if profile and profile.skills:
            cats = {s.category for s in profile.skills if s.category}
            categories_count = len(cats)
        else:
            # Fallback check taxonomy classifications
            from backend.intelligence.resume.skill_taxonomy import classify_skill_by_taxonomy
            cats = {classify_skill_by_taxonomy(s.name) for s in resume.skills if s.name}
            categories_count = len(cats)
        
        scores["Technology Breadth"] = min(100.0, max(40.0, categories_count * 20.0))

        # 13. Technology Depth
        # Compute based on Advanced/Expert level skills count
        depth_count = 0
        if profile and profile.skills:
            for s in profile.skills:
                if s.confidence_score >= 0.8 or s.frequency >= 2:
                    depth_count += 1
        else:
            # Heuristic default check skills list length
            depth_count = len(resume.skills) // 3
            
        scores["Technology Depth"] = min(100.0, max(50.0, 50.0 + depth_count * 15.0))

        # 14. Consistency
        has_gap = False
        sorted_exp = []
        for exp in resume.experience:
            start = parse_date_safely(exp.start_date)
            if start:
                sorted_exp.append((start, exp))
        sorted_exp.sort(key=lambda x: x[0], reverse=True)
        
        for i in range(len(sorted_exp) - 1):
            curr_end = parse_date_safely(sorted_exp[i][1].end_date)
            prev_start = sorted_exp[i+1][0]
            if curr_end and prev_start:
                # check gap greater than 1 year
                gap_days = (prev_start - curr_end).days
                if gap_days > 365:
                    has_gap = True
                    break
        scores["Consistency"] = 70.0 if has_gap else 100.0

        # 15. Resume Readability
        has_weak_kws = any("Weak Keywords" in w for w in weaknesses)
        has_short_desc = any("Generic Descriptions" in w for w in weaknesses)
        readability = 100.0
        if has_weak_kws: readability -= 20.0
        if has_short_desc: readability -= 30.0
        scores["Resume Readability"] = readability

        # Ensure all scores are rounded float
        return {k: round(v, 1) for k, v in scores.items()}
