"""Weakness evaluation analyzer identifying content deficiencies and profile omissions."""

import re
from typing import List
from backend.intelligence.resume.models import Resume


class WeaknessAnalyzer:
    """Identifies formatting, structural, and content gaps in canonical resume profiles."""

    def analyze_weaknesses(self, resume: Resume) -> List[str]:
        """Scans structured fields for areas of weakness.

        Args:
            resume: Normalized canonical candidate profile.

        Returns:
            List[str]: Identified weaknesses.
        """
        weaknesses = []

        # Compile text corpus from experience descriptions
        exp_texts = " ".join(" ".join(e.responsibilities + e.achievements).lower() for e in resume.experience)
        proj_texts = " ".join((p.description or "").lower() for p in resume.projects)
        corpus = f"{exp_texts} {proj_texts}"

        # 1. Weak Projects
        has_weak_proj = False
        if resume.projects:
            for proj in resume.projects:
                desc = proj.description or ""
                if len(desc.strip()) < 20 or not proj.technologies:
                    has_weak_proj = True
                    break
        if has_weak_proj:
            weaknesses.append("Weak Projects: Projects section includes items with minimal description or missing technology tags.")

        # 2. Missing Impact
        # Check if experience descriptions contain numeric values (quantification)
        has_numbers = False
        for exp in resume.experience:
            for bullet in exp.responsibilities + exp.achievements:
                if re.search(r"\b\d+\b", bullet):
                    has_numbers = True
                    break
        if resume.experience and not has_numbers:
            weaknesses.append("Missing Impact: Work experience descriptions lack quantified metrics (e.g. revenue, percentages, speedups).")

        # 3. Generic Descriptions
        has_short_exp = False
        for exp in resume.experience:
            desc = " ".join(exp.responsibilities)
            if len(desc.strip()) < 40 and len(exp.responsibilities) < 2:
                has_short_exp = True
                break
        if has_short_exp:
            weaknesses.append("Generic Descriptions: Work roles contain overly brief responsibilities that do not outline unique achievements.")

        # 4. Technology Gaps
        if len(resume.skills) < 5:
            weaknesses.append("Technology Gaps: Skills list includes very few competencies, which may fail ATS keyword screening.")

        # 5. Weak Experience
        # Not a student, but has empty experience
        if not resume.experience:
            has_edu = bool(resume.education)
            if not has_edu:
                weaknesses.append("Weak Experience: Work history section is completely empty.")

        # 6. Incomplete Sections
        info = resume.personal_info
        if not info.email or not info.phone:
            weaknesses.append("Incomplete Sections: Essential contact information (email or phone) is missing from the profile.")

        # 7. Weak Keywords
        weak_words = ["assisted", "helped", "responsible for", "participated"]
        if any(w in corpus for w in weak_words):
            weaknesses.append("Weak Keywords: Passive verbs (e.g., 'helped', 'assisted', 'responsible for') dilute the impact of achievements.")

        # 8. Duplicate Skills
        skills = [s.name.lower() for s in resume.skills if s.name]
        if len(skills) != len(set(skills)):
            weaknesses.append("Duplicate Skills: Redundant skills or duplicate keywords were found in the competency list.")

        # 9 & 10. Links: Portfolio & GitHub
        cand_links = []
        if info.linkedin: cand_links.append(info.linkedin)
        if info.github: cand_links.append(info.github)
        if info.portfolio: cand_links.append(info.portfolio)
        if info.website: cand_links.append(info.website)
        for sl in info.social_links:
            if sl.url: cand_links.append(sl.url)

        links = [l.lower() for l in cand_links]
        has_portfolio = any("portfolio" in l or "personal" in l or "github.io" in l or "site" in l for l in links)
        has_github = any("github.com" in l for l in links)

        if not has_portfolio:
            weaknesses.append("Missing Portfolio: No personal portfolio URL or project site link was found.")
        if not has_github:
            weaknesses.append("Missing GitHub: No active GitHub repository link is listed in contact information.")

        return weaknesses
