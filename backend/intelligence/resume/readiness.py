"""Career Readiness scoring engine calculating readiness levels, confidence, and improvement zones."""

from typing import List
from backend.intelligence.resume.models import Resume, ATSReport, CareerReadiness


class ReadinessEvaluator:
    """Evaluates composite readiness scores, confidence bounds, and reasoning descriptors."""

    def evaluate_readiness(
        self,
        resume: Resume,
        strengths: List[str],
        weaknesses: List[str],
        stage: str
    ) -> CareerReadiness:
        """Calculates readiness properties using rule-based metrics.

        Args:
            resume: Normalized canonical candidate profile.
            strengths: Extracted candidate strengths.
            weaknesses: Extracted candidate weaknesses.
            stage: Classified career stage string.

        Returns:
            CareerReadiness: Readiness profile.
        """
        # 1. Base Score calculation
        score = 70.0

        # Adjust by strengths and weaknesses counts
        score += len(strengths) * 3.0
        score -= len(weaknesses) * 4.0

        # Adjust based on career stage experience levels
        stage_adjustments = {
            "Student": 2.0,
            "Intern": 4.0,
            "Junior": 6.0,
            "Mid-Level": 12.0,
            "Senior": 16.0,
            "Lead": 20.0
        }
        score += stage_adjustments.get(stage, 5.0)

        # Cap score between 0.0 and 100.0
        score = round(min(100.0, max(0.0, score)), 1)

        # 2. Confidence score calculation
        confidence = 0.95
        if not resume.experience:
            confidence -= 0.10
        if not resume.skills:
            confidence -= 0.15
        if not resume.education:
            confidence -= 0.05
        confidence = round(max(0.5, confidence), 2)

        # 3. Create reasoning summary
        strengths_brief = [s.split(":")[0] for s in strengths[:3]]
        weaknesses_brief = [w.split(":")[0] for w in weaknesses[:3]]
        
        reasoning = (
            f"The candidate is classified at the '{stage}' career stage with an overall readiness score of {score}. "
            f"Core strengths include: {', '.join(strengths_brief) if strengths_brief else 'standard core profile'}. "
            f"Key optimization points include resolving gaps such as: {', '.join(weaknesses_brief) if weaknesses_brief else 'none identified'}."
        )

        # 4. Extract improvement areas directly from weaknesses list
        improvement_areas = []
        for w in weaknesses:
            clean = w.split(":")[0].strip()
            if "Missing Impact" in w:
                improvement_areas.append("Quantify work experience bullet points with metrics (percentages, numbers, or scale).")
            elif "Missing GitHub" in w:
                improvement_areas.append("Provide a link to an active GitHub profile in the contact details.")
            elif "Missing Portfolio" in w:
                improvement_areas.append("Add a link to a personal website or online portfolio project catalog.")
            elif "Technology Gaps" in w:
                improvement_areas.append("Add more technical keywords and framework stacks to satisfy ATS filters.")
            elif "Generic Descriptions" in w:
                improvement_areas.append("Expand on role descriptions using action-oriented bullet points outlining specific achievements.")
            else:
                improvement_areas.append(f"Resolve issue: {clean}.")

        if not improvement_areas:
            improvement_areas.append("Maintain high-quality standards; ensure tech tags are updated regularly.")

        return CareerReadiness(
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            improvement_areas=improvement_areas
        )
