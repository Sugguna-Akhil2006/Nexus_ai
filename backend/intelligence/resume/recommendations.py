"""Actionable Recommendation engine deriving evidence-based improvement steps from gaps."""

from typing import List
from backend.intelligence.resume.models import JDCategoryMatch, Resume, AnalysisRecommendation


class RecommendationEngine:
    """Translates evaluation gaps into clear improvement tasks."""

    def generate_recommendations(self, category_matches: List[JDCategoryMatch]) -> List[str]:
        """Translates missing attributes into evidence-based action items.

        Args:
            category_matches: Category match scores and evidences.

        Returns:
            List[str]: Set of recommendations.
        """
        recommendations = []

        # Sort categories by weight descending to recommend highest value tasks first
        sorted_matches = sorted(category_matches, key=lambda m: m.weight, reverse=True)

        for match in sorted_matches:
            if not match.missing_evidence:
                continue

            cat = match.category_name
            for miss in match.missing_evidence:
                clean_val = miss.replace("Missing target:", "").replace("Missing certification:", "").strip()
                
                # Check category type to tailor recommendation text
                if cat in ["Programming Languages", "Technical Skills"]:
                    recommendations.append(f"Learn Programming Language/Tech: Acquire proficiency in '{clean_val}' through courses or hands-on tutorials.")
                elif cat in ["Frameworks", "Databases", "Cloud Platforms", "AI/ML Skills", "DevOps"]:
                    recommendations.append(f"Master Technology Stack: Build small sandbox applications using '{clean_val}' to understand framework architecture.")
                elif cat == "Certifications":
                    recommendations.append(f"Pursue Professional Certification: Obtain '{clean_val}' to validate expertise and satisfy ATS screening constraints.")
                elif cat == "Project Relevance":
                    recommendations.append("Strengthen Engineering Portfolio: Create at least one full-scale project utilizing target job description technologies.")
                elif cat == "Experience":
                    recommendations.append("Expand Work History Details: Document freelance tasks, contracting, or open-source code contributions to offset tenure gaps.")
                elif cat == "Soft Skills":
                    recommendations.append(f"Showcase Soft Skills: Mention situations in past experience where you demonstrated '{clean_val}' (e.g. leadership, agile).")

        # Generic truthful keywords suggestion
        missing_skills = []
        for m in category_matches:
            if m.category_name in ["Programming Languages", "Frameworks", "Databases", "Cloud Platforms", "DevOps", "AI/ML Skills", "Technical Skills"]:
                for miss in m.missing_evidence:
                    clean = miss.replace("Missing target:", "").strip()
                    if clean:
                        missing_skills.append(clean)
                        
        if missing_skills:
            recommendations.append(
                f"Optimize Resume Keywords (Truthful Only): If you possess prior familiarity with {', '.join(f'({s})' for s in missing_skills[:4])}, "
                "ensure they are explicitly listed in your Skills or Experience bullets."
            )

        if not recommendations:
            recommendations.append("Excellent job! Your profile closely matches all job description requirements.")

        return recommendations


class AnalysisRecommendationEngine:
    """Translates profile weaknesses and omissions into prioritized, evidence-based suggestions."""

    def generate_analysis_recommendations(
        self,
        resume: Resume,
        weaknesses: List[str]
    ) -> List["AnalysisRecommendation"]:
        """Compiles prioritized recommendations with direct resume references.

        Args:
            resume: Canonical candidate profile.
            weaknesses: Extracted weakness strings.

        Returns:
            List[AnalysisRecommendation]: Structured recommendations list.
        """
        from backend.intelligence.resume.models import AnalysisRecommendation
        
        recs = []

        # Map weakness tags to prioritized suggestions
        for w in weaknesses:
            if "Incomplete Sections" in w:
                recs.append(AnalysisRecommendation(
                    priority="Critical",
                    description="Populate missing contact info (email and phone) immediately to ensure hiring managers can reach you.",
                    evidence="Email or phone fields in personal_info are empty."
                ))
            elif "Missing GitHub" in w:
                recs.append(AnalysisRecommendation(
                    priority="Critical",
                    description="Provide an active link referencing 'github.com' to showcase your coding activity.",
                    evidence="Candidate's personal links do not contain a link referencing github.com."
                ))
            elif "Missing Impact" in w:
                recs.append(AnalysisRecommendation(
                    priority="Important",
                    description="Quantify accomplishments in your experience bullets (e.g. speedups, cost reduction, scale).",
                    evidence="No numeric metrics or percentages were found in work history bullet points."
                ))
            elif "Technology Gaps" in w:
                recs.append(AnalysisRecommendation(
                    priority="Important",
                    description="Expand your core skills list with a wider range of modern technologies and methodologies.",
                    evidence="Candidate has listed fewer than 5 unique tech skills."
                ))
            elif "Generic Descriptions" in w:
                recs.append(AnalysisRecommendation(
                    priority="Important",
                    description="Elaborate on job responsibilities using descriptive action verbs and detailed bullet points.",
                    evidence="Some role descriptions contain fewer than 40 characters."
                ))
            elif "Weak Projects" in w:
                recs.append(AnalysisRecommendation(
                    priority="Important",
                    description="Provide more technical detail and technology stacks on your projects.",
                    evidence="Projects are present but have short descriptions or missing technology tags."
                ))
            elif "Missing Portfolio" in w:
                recs.append(AnalysisRecommendation(
                    priority="Optional",
                    description="Add a link to a personal website or online project catalog.",
                    evidence="Candidate's personal links do not contain a reference to a personal website or portfolio."
                ))
            elif "Duplicate Skills" in w:
                recs.append(AnalysisRecommendation(
                    priority="Optional",
                    description="De-duplicate skills list to avoid keyword redundancy.",
                    evidence="Case-insensitive duplicate keywords found in the skills list."
                ))
            elif "Weak Keywords" in w:
                recs.append(AnalysisRecommendation(
                    priority="Optional",
                    description="Replace passive verbs like 'helped' or 'assisted' with active accomplishments.",
                    evidence="Found passive wording in work history or project details."
                ))

        if not recs:
            recs.append(AnalysisRecommendation(
                priority="Optional",
                description="Maintain high-quality standards; verify keywords are regularly updated.",
                evidence="No significant weaknesses identified in candidate profile."
            ))

        return recs
