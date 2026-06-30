"""Core matching algorithms comparing structured Resumes against Job Descriptions."""

import re
from typing import Dict, List, Set, Tuple

from backend.intelligence.resume.models import Resume, JobDescription, JDCategoryMatch
from backend.intelligence.resume.skill_taxonomy import classify_skill_by_taxonomy
from backend.intelligence.resume.validators import parse_date_safely


class MatchingEvaluator:
    """Compares Resume properties against Job Description targets, scoring each category."""

    # Category weights configuration
    WEIGHTS: Dict[str, float] = {
        "Technical Skills": 0.15,
        "Programming Languages": 0.15,
        "Frameworks": 0.10,
        "Databases": 0.05,
        "Cloud Platforms": 0.10,
        "AI/ML Skills": 0.10,
        "DevOps": 0.05,
        "Experience": 0.10,
        "Education": 0.05,
        "Certifications": 0.05,
        "Soft Skills": 0.05,
        "Project Relevance": 0.05
    }

    def evaluate_match(self, resume: Resume, jd: JobDescription) -> List[JDCategoryMatch]:
        """Runs segment-by-segment comparisons and yields scored matches with evidence.

        Args:
            resume: Normalized canonical candidate profile.
            jd: Structured target job description.

        Returns:
            List[JDCategoryMatch]: Evaluations for the 12 target categories.
        """
        category_matches: List[JDCategoryMatch] = []

        # Gather all skills & tech from Job Description
        jd_skills = set(jd.required_skills + jd.preferred_skills)
        jd_techs = set(jd.technologies)
        jd_all_skills = jd_skills.union(jd_techs)

        # Categorize JD skills using taxonomy classifier
        jd_categorized: Dict[str, List[str]] = {cat: [] for cat in self.WEIGHTS}
        for sk in jd_all_skills:
            tax = classify_skill_by_taxonomy(sk)
            # Map taxonomy categories to match categories
            if tax == "Programming Languages":
                jd_categorized["Programming Languages"].append(sk)
            elif tax in ["Frameworks", "Libraries"]:
                jd_categorized["Frameworks"].append(sk)
            elif tax == "Databases":
                jd_categorized["Databases"].append(sk)
            elif tax == "Cloud Platforms":
                jd_categorized["Cloud Platforms"].append(sk)
            elif tax in ["DevOps", "Version Control"]:
                jd_categorized["DevOps"].append(sk)
            elif tax in ["Generative AI", "LLM Frameworks", "Vector Databases", "Deep Learning", "Machine Learning", "Data Science"]:
                jd_categorized["AI/ML Skills"].append(sk)
            elif tax == "Soft Skills":
                jd_categorized["Soft Skills"].append(sk)
            else:
                jd_categorized["Technical Skills"].append(sk)

        # Also explicit soft skills list from JD
        for ss in jd.soft_skills:
            if ss not in jd_categorized["Soft Skills"]:
                jd_categorized["Soft Skills"].append(ss)

        # Map candidate skills by category
        cand_categorized: Dict[str, List[str]] = {cat: [] for cat in self.WEIGHTS}
        for sk in resume.skills:
            tax = classify_skill_by_taxonomy(sk.name)
            if tax == "Programming Languages":
                cand_categorized["Programming Languages"].append(sk.name)
            elif tax in ["Frameworks", "Libraries"]:
                cand_categorized["Frameworks"].append(sk.name)
            elif tax == "Databases":
                cand_categorized["Databases"].append(sk.name)
            elif tax == "Cloud Platforms":
                cand_categorized["Cloud Platforms"].append(sk.name)
            elif tax in ["DevOps", "Version Control"]:
                cand_categorized["DevOps"].append(sk.name)
            elif tax in ["Generative AI", "LLM Frameworks", "Vector Databases", "Deep Learning", "Machine Learning", "Data Science"]:
                cand_categorized["AI/ML Skills"].append(sk.name)
            elif tax == "Soft Skills":
                cand_categorized["Soft Skills"].append(sk.name)
            else:
                cand_categorized["Technical Skills"].append(sk.name)

        # 1. Score Skill Categories
        skill_cats = [
            "Technical Skills", "Programming Languages", "Frameworks",
            "Databases", "Cloud Platforms", "AI/ML Skills", "DevOps", "Soft Skills"
        ]
        for cat in skill_cats:
            jd_reqs = jd_categorized[cat]
            cand_has = cand_categorized[cat]
            
            if not jd_reqs:
                # Default score if no requirement specified
                category_matches.append(JDCategoryMatch(
                    category_name=cat,
                    score=100.0,
                    weight=self.WEIGHTS[cat],
                    confidence=1.0,
                    matching_evidence=["No specific target requirements were defined in the job description."],
                    missing_evidence=[]
                ))
            else:
                matching = []
                missing = []
                for req in jd_reqs:
                    # Look for exact or case-insensitive match in candidate's skills list
                    if any(req.lower() == c.lower() or c.lower() in req.lower() or req.lower() in c.lower() for c in cand_has):
                        matching.append(req)
                    else:
                        missing.append(req)
                        
                score = (len(matching) / len(jd_reqs)) * 100.0
                category_matches.append(JDCategoryMatch(
                    category_name=cat,
                    score=round(score, 1),
                    weight=self.WEIGHTS[cat],
                    confidence=0.9,
                    matching_evidence=[f"Found matching: {m}" for m in matching] if matching else ["No matching skills found."],
                    missing_evidence=[f"Missing target: {ms}" for ms in missing]
                ))

        # 2. Score Experience
        exp_score, exp_match_ev, exp_miss_ev, exp_conf = self._evaluate_experience(resume, jd)
        category_matches.append(JDCategoryMatch(
            category_name="Experience",
            score=exp_score,
            weight=self.WEIGHTS["Experience"],
            confidence=exp_conf,
            matching_evidence=exp_match_ev,
            missing_evidence=exp_miss_ev
        ))

        # 3. Score Education
        edu_score, edu_match_ev, edu_miss_ev, edu_conf = self._evaluate_education(resume, jd)
        category_matches.append(JDCategoryMatch(
            category_name="Education",
            score=edu_score,
            weight=self.WEIGHTS["Education"],
            confidence=edu_conf,
            matching_evidence=edu_match_ev,
            missing_evidence=edu_miss_ev
        ))

        # 4. Score Certifications
        cert_score, cert_match_ev, cert_miss_ev, cert_conf = self._evaluate_certifications(resume, jd)
        category_matches.append(JDCategoryMatch(
            category_name="Certifications",
            score=cert_score,
            weight=self.WEIGHTS["Certifications"],
            confidence=cert_conf,
            matching_evidence=cert_match_ev,
            missing_evidence=cert_miss_ev
        ))

        # 5. Score Project Relevance
        proj_score, proj_match_ev, proj_miss_ev, proj_conf = self._evaluate_projects(resume, jd_all_skills)
        category_matches.append(JDCategoryMatch(
            category_name="Project Relevance",
            score=proj_score,
            weight=self.WEIGHTS["Project Relevance"],
            confidence=proj_conf,
            matching_evidence=proj_match_ev,
            missing_evidence=proj_miss_ev
        ))

        return category_matches

    def _evaluate_experience(self, resume: Resume, jd: JobDescription) -> Tuple[float, List[str], List[str], float]:
        matching = []
        missing = []
        score = 100.0

        # Parse years requirement from JD (e.g. "5+ years", "3 years")
        target_years = 0.0
        req_str = jd.experience_required or ""
        match = re.search(r"(\d+)\s*-\s*(\d+)|\b(\d+)\b", req_str)
        if match:
            # Take max or direct number
            vals = [int(v) for v in match.groups() if v is not None]
            target_years = float(max(vals)) if vals else 0.0
        else:
            # Heuristic checks on job title
            title = jd.job_title.lower()
            if "senior" in title or "sr" in title:
                target_years = 5.0
            elif "lead" in title or "principal" in title or "manager" in title:
                target_years = 7.0
            elif "junior" in title or "jr" in title or "associate" in title:
                target_years = 1.0

        # Calculate candidate tenure
        total_months = 0.0
        for exp in resume.experience:
            start = parse_date_safely(exp.start_date)
            end = parse_date_safely(exp.end_date)
            if start and end:
                months = (end.year - start.year) * 12 + (end.month - start.month)
                total_months += max(1.0, float(months))
        cand_years = total_months / 12.0

        if target_years > 0:
            if cand_years >= target_years:
                matching.append(f"Tenure requirements satisfied: Target is {target_years} years, Candidate has {cand_years:.1f} years.")
            else:
                score = (cand_years / target_years) * 100.0
                missing.append(f"Short tenure experience: Job requires {target_years} years, candidate possesses only {cand_years:.1f} years.")
        else:
            matching.append(f"No specific tenure requirements declared. Candidate possesses {cand_years:.1f} years.")

        # Title matching helper
        title_matched = False
        jd_title_words = set(jd.job_title.lower().split())
        for exp in resume.experience:
            if exp.role:
                exp_words = set(exp.role.lower().split())
                if jd_title_words.intersection(exp_words):
                    title_matched = True
                    matching.append(f"Role title alignment: Candidate previously worked as '{exp.role}'.")
                    break
        if not title_matched and resume.experience:
            score -= 10.0
            missing.append(f"No direct past role matched job title '{jd.job_title}'.")

        score = min(100.0, max(0.0, score))
        return round(score, 1), matching, missing, 0.85

    def _evaluate_education(self, resume: Resume, jd: JobDescription) -> Tuple[float, List[str], List[str], float]:
        matching = []
        missing = []
        score = 100.0

        if not jd.education_requirements:
            return 100.0, ["No educational requirements listed in job description."], [], 1.0

        # Gather degree requirements (e.g. Master, PhD, Bachelor, BS, MS)
        has_phd_req = any("phd" in r.lower() or "doctorate" in r.lower() for r in jd.education_requirements)
        has_ms_req = any("master" in r.lower() or "ms" in r.lower() or "m.s." in r.lower() for r in jd.education_requirements)
        has_bs_req = any("bachelor" in r.lower() or "bs" in r.lower() or "b.s." in r.lower() or "degree" in r.lower() for r in jd.education_requirements)

        # Check candidate degree levels
        cand_phd = False
        cand_ms = False
        cand_bs = False
        for edu in resume.education:
            deg = (edu.degree or "").lower()
            if "phd" in deg or "doctor" in deg or "ph.d" in deg:
                cand_phd = True
            elif "master" in deg or "ms" in deg or "m.s" in deg:
                cand_ms = True
            elif "bachelor" in deg or "bs" in deg or "b.s" in deg:
                cand_bs = True

        if has_phd_req:
            if cand_phd:
                matching.append("PhD requirement fully satisfied.")
            elif cand_ms:
                score = 70.0
                missing.append("Candidate holds a Master's degree, which is below the target PhD requirement.")
            else:
                score = 40.0
                missing.append("Candidate holds no graduate degree matching the target PhD requirement.")
        elif has_ms_req:
            if cand_phd or cand_ms:
                matching.append("Master's requirement satisfied.")
            elif cand_bs:
                score = 70.0
                missing.append("Candidate holds a Bachelor's degree, below target Master's requirement.")
            else:
                score = 30.0
                missing.append("Candidate holds no degree matching the target Master's requirement.")
        elif has_bs_req:
            if cand_phd or cand_ms or cand_bs:
                matching.append("Bachelor's requirement satisfied.")
            else:
                score = 50.0
                missing.append("Candidate holds no college degree matching target Bachelor's requirement.")
        else:
            matching.append("Education matches standard requirements.")

        return score, matching, missing, 0.9

    def _evaluate_certifications(self, resume: Resume, jd: JobDescription) -> Tuple[float, List[str], List[str], float]:
        matching = []
        missing = []

        if not jd.certifications:
            return 100.0, ["No specific certifications required in job description."], [], 1.0

        cand_certs = [c.certification_name.lower() for c in resume.certifications if c.certification_name]
        for req in jd.certifications:
            req_clean = req.lower()
            matched = False
            for cc in cand_certs:
                if req_clean in cc or cc in req_clean:
                    matching.append(f"Certification matched: {req}")
                    matched = True
                    break
            if not matched:
                missing.append(f"Missing certification: {req}")

        score = (len(matching) / len(jd.certifications)) * 100.0
        return round(score, 1), matching, missing, 0.9

    def _evaluate_projects(self, resume: Resume, jd_skills: Set[str]) -> Tuple[float, List[str], List[str], float]:
        matching = []
        missing = []

        if not resume.projects:
            return 0.0, [], ["No projects section to compare relevance against requirements."], 0.8

        # Check how many projects mention any of the JD requirements
        relevant_projects_count = 0
        for proj in resume.projects:
            desc = (proj.description or "").lower()
            techs = [t.lower() for t in proj.technologies]
            conts = [c.lower() for c in proj.contributions]
            
            project_corpus = " ".join([desc] + techs + conts)
            matched_keywords = []
            for skill in jd_skills:
                if f" {skill.lower()} " in f" {project_corpus} ":
                    matched_keywords.append(skill)
                    
            if matched_keywords:
                relevant_projects_count += 1
                matching.append(f"Project '{proj.project_name or proj.name}' relates via: {', '.join(matched_keywords[:3])}")

        # Benchmark: target at least 2 relevant projects for a full score
        benchmark = 2
        score = (relevant_projects_count / benchmark) * 100.0
        score = min(100.0, score)

        if score < 100.0:
            missing.append(f"Low project portfolio relevance: only {relevant_projects_count} relevant projects found (benchmark: {benchmark}).")

        return round(score, 1), matching, missing, 0.8
