"""Scoring algorithms evaluating the 11 quality categories of structured Resume models."""

import re
from typing import Any, Dict, List, Tuple

from backend.intelligence.resume.models import Resume, ATSCategoryScore
from backend.intelligence.resume.metrics import (
    HIGH_VALUE_KEYWORDS,
    EMERGING_TECHNOLOGIES,
    ACTION_VERB_ALTERNATIVES,
    WEAK_WORDS,
    CORE_SECTIONS,
    SUPPORTING_SECTIONS,
)
from backend.intelligence.resume.rules import SCORING_CATEGORIES
from backend.intelligence.resume.validators import parse_date_safely


class ResumeScoringEngine:
    """Computes category scores, detects quality gaps, and compiles feedback points."""

    def score_contact_info(self, resume: Resume) -> Tuple[float, str, List[str]]:
        """Scores completeness of contact information details."""
        info = resume.personal_info
        missing = []
        suggestions = []
        score = 100.0

        if not info.full_name or not info.full_name.strip():
            missing.append("Full Name")
            score -= 20.0
        if not info.email or not info.email.strip():
            missing.append("Email")
            score -= 20.0
        if not info.phone or not info.phone.strip():
            missing.append("Phone Number")
            score -= 20.0
        if not info.location or not info.location.strip():
            missing.append("Location (City/State)")
            score -= 20.0
        if not info.address or not info.address.strip():
            missing.append("Address")
            score -= 20.0

        score = max(0.0, score)
        if score == 100.0:
            reason = "All standard contact fields (Name, Email, Phone, Location, Address) are present."
        else:
            reason = f"Missing the following contact details: {', '.join(missing)}."
            for m in missing:
                suggestions.append(f"Add your {m} to the personal details header section.")
                
        return score, reason, suggestions

    def score_links(self, resume: Resume) -> Tuple[float, str, List[str]]:
        """Scores presence and validity of profile and repository links."""
        info = resume.personal_info
        suggestions = []
        score = 0.0
        found = []

        # Enforce link validations
        if info.linkedin and info.linkedin.strip().startswith("http"):
            score += 40.0
            found.append("LinkedIn")
        if info.github and info.github.strip().startswith("http"):
            score += 30.0
            found.append("GitHub")
        if (info.portfolio and info.portfolio.strip().startswith("http")) or (info.website and info.website.strip().startswith("http")):
            score += 20.0
            found.append("Portfolio")
        if info.social_links:
            score += 10.0
            found.append("Other Social links")

        score = min(100.0, score)
        if score == 100.0 or (found and score >= 90.0):
            reason = f"Excellent online footprint with links found for: {', '.join(found)}."
        elif not found:
            reason = "No valid professional links (LinkedIn, GitHub, Portfolio) were found."
            suggestions.append("Add your LinkedIn profile link to help recruiters find you.")
            suggestions.append("Include your GitHub profile link to showcase code repositories.")
            suggestions.append("Provide a personal portfolio or blog website link to display achievements.")
        else:
            reason = f"Partial professional profile links found: {', '.join(found)}."
            if "LinkedIn" not in found:
                suggestions.append("Add a valid LinkedIn profile URL.")
            if "GitHub" not in found:
                suggestions.append("Include your GitHub URL link to demonstrate technical contributions.")
            if "Portfolio" not in found:
                suggestions.append("Link a portfolio website or professional blog URL.")

        return score, reason, suggestions

    def score_sections(self, resume: Resume) -> Tuple[float, str, List[str]]:
        """Scores document structure completeness based on core and supporting sections."""
        missing_core = []
        incomplete_core = []
        present_supporting = []
        score = 100.0
        suggestions = []

        # 1. Evaluate Core Sections
        # Personal Information
        if not resume.personal_info.full_name:
            missing_core.append("Personal Information")
            score -= 20.0
            
        # Education
        if not resume.education:
            missing_core.append("Education")
            score -= 20.0
        else:
            # Check fields
            for edu in resume.education:
                if not edu.degree or not edu.institution:
                    incomplete_core.append("Education")
                    score -= 5.0
                    break

        # Experience
        if not resume.experience:
            missing_core.append("Experience")
            score -= 20.0
        else:
            for exp in resume.experience:
                if not exp.role or not exp.company:
                    incomplete_core.append("Experience")
                    score -= 5.0
                    break

        # Projects
        if not resume.projects:
            missing_core.append("Projects")
            score -= 20.0
        else:
            for proj in resume.projects:
                if not proj.description or not (proj.name or proj.project_name):
                    incomplete_core.append("Projects")
                    score -= 5.0
                    break

        # Skills
        if not resume.skills:
            missing_core.append("Skills")
            score -= 20.0

        # 2. Add points for supporting optional sections (max 20)
        supporting_bonus = 0.0
        if resume.certifications:
            present_supporting.append("Certifications")
            supporting_bonus += 5.0
        if resume.languages:
            present_supporting.append("Languages")
            supporting_bonus += 5.0
        if resume.awards:
            present_supporting.append("Awards")
            supporting_bonus += 5.0
        if resume.volunteer:
            present_supporting.append("Volunteer Experience")
            supporting_bonus += 5.0
            
        score = min(100.0, max(0.0, score + supporting_bonus))

        if not missing_core and not incomplete_core:
            reason = f"All core sections are fully complete. Supporting sections present: {', '.join(present_supporting)}."
        else:
            parts = []
            if missing_core:
                parts.append(f"Missing core: {', '.join(missing_core)}")
                for m in missing_core:
                    suggestions.append(f"Add a dedicated section for '{m}' to structured resume layout.")
            if incomplete_core:
                parts.append(f"Incomplete details in: {', '.join(set(incomplete_core))}")
                for ic in set(incomplete_core):
                    suggestions.append(f"Fill in all missing attributes (roles, dates, institutions) in '{ic}' section.")
            reason = "; ".join(parts)

        return score, reason, suggestions

    def score_keywords(self, resume: Resume) -> Tuple[float, str, List[str], List[str]]:
        """Evaluates high-value keyword density and reports missing keywords."""
        text_corpus = []
        suggestions = []
        
        # Consolidate all resume text fields to look for keywords
        if resume.personal_info.location:
            text_corpus.append(resume.personal_info.location)
        for edu in resume.education:
            if edu.branch: text_corpus.append(edu.branch)
            if edu.description: text_corpus.append(edu.description)
        for exp in resume.experience:
            if exp.role: text_corpus.append(exp.role)
            text_corpus.extend(exp.responsibilities)
            text_corpus.extend(exp.achievements)
            text_corpus.extend(exp.technologies_used)
        for proj in resume.projects:
            if proj.name: text_corpus.append(proj.name)
            if proj.description: text_corpus.append(proj.description)
            text_corpus.extend(proj.technologies)
            text_corpus.extend(proj.contributions)
        for sk in resume.skills:
            if sk.name: text_corpus.append(sk.name)
        for cert in resume.certifications:
            if cert.certification_name: text_corpus.append(cert.certification_name)
            
        full_text = " ".join(text_corpus).lower()
        
        # Clean special chars
        full_text = re.sub(r"[.,;():\-/]", " ", full_text)
        
        found = []
        missing = []
        for kw in HIGH_VALUE_KEYWORDS:
            if f" {kw} " in f" {full_text} ":
                found.append(kw)
            else:
                missing.append(kw)

        # Benchmark: target at least 8 matching keywords
        benchmark = 8
        score = (len(found) / benchmark) * 100.0
        score = min(100.0, score)

        if score >= 90.0:
            reason = f"Excellent keyword alignment matching {len(found)} key terms: {', '.join(found)}."
        elif not found:
            reason = "No high-value industry keywords were found in your resume text."
            suggestions.append(f"Incorporate standard industry keywords (e.g. {', '.join(HIGH_VALUE_KEYWORDS[:5])}) based on your expertise.")
        else:
            reason = f"Moderate keyword coverage. Found: {', '.join(found)}."
            suggestions.append(f"Add missing target industry keywords: {', '.join(missing[:5])} to increase ATS compliance.")

        return score, reason, suggestions, missing

    def score_skill_diversity(self, resume: Resume) -> Tuple[float, str, List[str]]:
        """Scores category balance across the skills taxonomy, rewarding emerging tech."""
        suggestions = []
        if not resume.skills:
            return 0.0, "No skills found in the resume.", ["Create a structured Skills section containing specialized tech categories."]

        categories = set(sk.category for sk in resume.skills if sk.category and sk.category != "Other")
        
        # Check emerging technologies
        emerging_found = []
        for sk in resume.skills:
            name_clean = sk.name.lower()
            for tech in EMERGING_TECHNOLOGIES:
                if name_clean == tech or tech in name_clean:
                    emerging_found.append(sk.name)
                    break
        emerging_found = list(set(emerging_found))

        # Scoring: categories coverage (benchmark 4 non-other categories = 80 points)
        score = (len(categories) / 4) * 80.0
        
        # Emerging tech bonus (10 points per tech, max 20)
        score += min(20.0, len(emerging_found) * 10.0)
        score = min(100.0, score)

        if score >= 85.0:
            reason = f"High skill diversity across {len(categories)} categories. Emerging skills found: {', '.join(emerging_found) or 'None'}."
        else:
            reason = f"Skills are clustered in few categories ({len(categories)} categories found). Emerging tech count: {len(emerging_found)}."
            suggestions.append("Distribute skills into specialized categories (e.g. Programming Languages, Frameworks, DevOps, Databases).")
            if not emerging_found:
                suggestions.append(f"Add skills in emerging technology fields (e.g. {', '.join(EMERGING_TECHNOLOGIES[:3])}) to make your profile modern.")

        return score, reason, suggestions

    def score_experience_quality(self, resume: Resume) -> Tuple[float, str, List[str]]:
        """Evaluates duration, career progression, quantifiable impact, and leadership."""
        suggestions = []
        if not resume.experience:
            # Entry level/Student profile
            return 50.0, "No work experience history was found.", ["Add internships, freelance work, or academic leadership roles to the experience section."]

        score = 50.0
        reasons_list = []

        # 1. Total Tenure Duration (in Years)
        total_months = 0.0
        for exp in resume.experience:
            start = parse_date_safely(exp.start_date)
            end = parse_date_safely(exp.end_date)
            if start and end:
                months = (end.year - start.year) * 12 + (end.month - start.month)
                total_months += max(1.0, float(months))
                
        years = total_months / 12.0
        if years >= 5.0:
            score += 20.0
            reasons_list.append(f"Strong professional history ({years:.1f} years)")
        elif years >= 2.0:
            score += 15.0
            reasons_list.append(f"Solid tenure history ({years:.1f} years)")
        else:
            score += 5.0
            reasons_list.append(f"Short tenure history ({years:.1f} years)")
            suggestions.append("Accumulate more professional tenure or detailed freelance experiences.")

        # 2. Progression
        has_progression = False
        roles = [exp.role.lower() for exp in resume.experience if exp.role]
        senior_keywords = ["senior", "sr", "lead", "principal", "manager", "director", "architect"]
        # Check if later role has senior keyword while early one did not
        if len(roles) >= 2:
            early_senior = any(k in roles[-1] for k in senior_keywords)
            later_senior = any(k in roles[0] for k in senior_keywords)
            if later_senior and not early_senior:
                has_progression = True
                
        if has_progression:
            score += 10.0
            reasons_list.append("Career role progression detected")

        # 3. Achievements Quantification
        quantified_bullets = 0
        total_bullets = 0
        for exp in resume.experience:
            bullets = exp.responsibilities + exp.achievements
            total_bullets += len(bullets)
            for b in bullets:
                # Look for numbers, percentages, or dollar values
                if re.search(r"\b\d+%\b|\b\d+\b|\$\b\d+", b):
                    quantified_bullets += 1
                    
        ratio = (quantified_bullets / total_bullets) if total_bullets > 0 else 0.0
        if ratio >= 0.30:
            score += 10.0
            reasons_list.append(f"Excellent quantified achievements ({quantified_bullets} bullets)")
        elif ratio > 0.0:
            score += 5.0
            reasons_list.append(f"Some quantified achievements ({quantified_bullets} bullets)")
            suggestions.append("Incorporate more metrics (percentages, revenues, load speed) to quantify achievements.")
        else:
            suggestions.append("Quantify your impact. Use metrics, percentages, and absolute values to justify achievements.")

        # 4. Leadership & Action Verbs
        has_leadership = False
        leadership_verbs = ["led", "managed", "directed", "orchestrated", "supervised", "spearheaded"]
        for exp in resume.experience:
            for b in (exp.responsibilities + exp.achievements):
                if any(f" {lv} " in f" {b.lower()} " for lv in leadership_verbs):
                    has_leadership = True
                    break
        if has_leadership:
            score += 10.0
            reasons_list.append("Leadership verbs detected")
        else:
            suggestions.append("Use leadership verbs (e.g., Led, Spearheaded, Orchestrated) to highlight ownership.")

        score = min(100.0, score)
        reason = ", ".join(reasons_list)
        return score, reason, suggestions

    def score_projects(self, resume: Resume) -> Tuple[float, str, List[str]]:
        """Evaluates project counts, descriptions length, tech stack usage, and project urls."""
        suggestions = []
        if not resume.projects:
            return 0.0, "No projects section was found.", ["Create a Projects section to showcase hands-on work and tech complexity."]

        score = 40.0
        reasons_list = []

        # 1. Project Count
        count = len(resume.projects)
        if count >= 3:
            score += 20.0
            reasons_list.append(f"Good project count ({count} projects)")
        elif count == 2:
            score += 15.0
            reasons_list.append(f"Moderate project count ({count} projects)")
        else:
            score += 5.0
            reasons_list.append(f"Low project count ({count} project)")
            suggestions.append("Add at least 2-3 engineering projects matching target domain skills.")

        # 2. Description Quality
        total_words = 0
        has_tech = False
        has_links = False
        for proj in resume.projects:
            desc = proj.description or ""
            total_words += len(desc.split())
            if proj.technologies:
                has_tech = True
            if (proj.github_url or proj.github_link) or (proj.live_url or proj.live_demo):
                has_links = True
                
        avg_words = (total_words / count) if count > 0 else 0
        if avg_words >= 20:
            score += 15.0
            reasons_list.append(f"Detailed descriptions (avg {avg_words:.0f} words)")
        else:
            suggestions.append("Add detailed descriptions of accomplishments to the projects.")

        # 3. Technologies
        if has_tech:
            score += 15.0
            reasons_list.append("Project tech stacks explicitly specified")
        else:
            suggestions.append("Specify the tech stack list utilized in each project.")

        # 4. Repositories / Demos
        if has_links:
            score += 10.0
            reasons_list.append("Repository/live demo URLs present")
        else:
            suggestions.append("Provide GitHub repository links or live demo URLs for your projects.")

        score = min(100.0, score)
        reason = ", ".join(reasons_list)
        return score, reason, suggestions

    def score_education(self, resume: Resume) -> Tuple[float, str, List[str]]:
        """Scores educational background completeness."""
        suggestions = []
        if not resume.education:
            return 0.0, "No educational credentials found.", ["Add an Education section to declare degree titles and institutions."]

        score = 100.0
        missing_fields = []
        for edu in resume.education:
            if not edu.institution:
                missing_fields.append("Institution")
                score -= 15.0
            if not edu.degree:
                missing_fields.append("Degree")
                score -= 15.0
            if not edu.branch:
                missing_fields.append("Field of Study")
                score -= 15.0
            if not edu.graduation_year and not edu.end_year:
                missing_fields.append("Graduation Year")
                score -= 10.0
            if not edu.gpa_cgpa:
                missing_fields.append("GPA/CGPA")
                score -= 5.0

        score = min(100.0, max(0.0, score))
        if score == 100.0:
            reason = "Education credentials are fully complete."
        else:
            reason = f"Missing educational elements: {', '.join(set(missing_fields))}."
            for mf in set(missing_fields):
                suggestions.append(f"Include the '{mf}' detail in your education list items.")

        return score, reason, suggestions

    def score_certifications(self, resume: Resume) -> Tuple[float, str, List[str]]:
        """Scores certifications section (defaulting gracefully as optional)."""
        suggestions = []
        if not resume.certifications:
            # Optional section default
            return 75.0, "No professional certifications are listed.", ["Consider earning and adding industry certifications (e.g. AWS Solutions Architect, GCP, Kubernetes)."]

        score = 100.0
        missing = []
        for cert in resume.certifications:
            if not cert.certification_name:
                missing.append("Name")
                score -= 20.0
            if not (cert.organization or cert.issuer):
                missing.append("Issuer")
                score -= 20.0
            if not cert.year:
                missing.append("Year")
                score -= 10.0

        score = min(100.0, max(0.0, score))
        if score == 100.0:
            reason = "Certifications listed are complete with Name, Issuer, and Year."
        else:
            reason = f"Missing certification details: {', '.join(set(missing))}."
            for m in set(missing):
                suggestions.append(f"Add missing '{m}' details to your certifications section.")

        return score, reason, suggestions

    def score_formatting(self, resume: Resume) -> Tuple[float, str, List[str]]:
        """Detects overlapping/duplicate companies, weak phrasing, or sizing issues."""
        suggestions = []
        score = 100.0
        issues = []

        # 1. Weak wording penalty
        weak_count = 0
        for exp in resume.experience:
            bullets = exp.responsibilities + exp.achievements
            for b in bullets:
                for ww in WEAK_WORDS:
                    if f" {ww} " in f" {b.lower()} ":
                        weak_count += 1
                        
        if weak_count > 0:
            penalty = min(20.0, weak_count * 5.0)
            score -= penalty
            issues.append(f"Found {weak_count} weak words (e.g., 'responsible for')")
            suggestions.append("Replace passive phrases like 'responsible for' with active accomplishments.")

        # 2. Overlapping duplicate company names check
        seen_companies = []
        has_overlap = False
        for exp in resume.experience:
            if exp.company:
                comp = exp.company.lower().strip()
                if comp in seen_companies:
                    has_overlap = True
                seen_companies.append(comp)
        if has_overlap:
            score -= 10.0
            issues.append("Duplicate company occurrences detected")
            suggestions.append("Consolidate multiple roles at the same company into a single work experience entry.")

        # 3. Document sizing/length check
        total_word_count = 0
        for exp in resume.experience:
            total_word_count += len(" ".join(exp.responsibilities).split())
        for proj in resume.projects:
            if proj.description:
                total_word_count += len(proj.description.split())
                
        if total_word_count < 100 and resume.experience:
            score -= 15.0
            issues.append("Resume content length is very short")
            suggestions.append("Elaborate on experience responsibilities to meet the target word count (150-500 words).")

        score = min(100.0, max(0.0, score))
        if score == 100.0:
            reason = "No major formatting, weak wording, or layout spacing issues were detected."
        else:
            reason = f"Formatting issues found: {', '.join(issues)}."

        return score, reason, suggestions

    def score_readability(self, resume: Resume) -> Tuple[float, str, List[str]]:
        """Evaluates sentence lengths, action verbs ratio, and weak wording ratio."""
        suggestions = []
        score = 80.0
        reasons = []

        # 1. Action Verbs Usage
        strong_verbs_count = 0
        total_bullets = 0
        for exp in resume.experience:
            bullets = exp.responsibilities + exp.achievements
            total_bullets += len(bullets)
            for b in bullets:
                # Look if first word is a verb
                first_word = b.strip().lower().split()[0] if b.strip() else ""
                # Check match against action verb alternatives trigger keys
                if first_word in ACTION_VERB_ALTERNATIVES:
                    strong_verbs_count += 1
                elif any(first_word.endswith(suf) for suf in ["ed", "t", "d"]):
                    # Simple past tense heuristic
                    strong_verbs_count += 1

        if total_bullets > 0:
            ratio = strong_verbs_count / total_bullets
            if ratio >= 0.50:
                score += 20.0
                reasons.append("High action verb usage (>= 50% of bullets)")
            else:
                score += 10.0
                reasons.append(f"Moderate action verb usage ({ratio:.0%})")
                suggestions.append("Start every work responsibility bullet point with a strong past-tense action verb.")
        else:
            suggestions.append("Add work experience details beginning with active past-tense accomplishments.")

        # 2. Sentence Length check
        too_long = 0
        for exp in resume.experience:
            for b in (exp.responsibilities + exp.achievements):
                if len(b.split()) > 30:
                    too_long += 1
        if too_long > 2:
            score -= 10.0
            reasons.append(f"Found {too_long} long sentences (>30 words)")
            suggestions.append("Break up long bullet points into concise 1-2 sentence lines.")

        score = min(100.0, max(0.0, score))
        reason = ", ".join(reasons) or "Standard readability metrics."
        return score, reason, suggestions
