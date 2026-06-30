"""Validation and normalization engine for canonical Resume Data Models."""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.intelligence.resume.exceptions import ResumeValidationError, ResumeNormalizationError
from backend.intelligence.resume.models import (
    Resume,
    PersonalInformation,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Skill,
    CertificationEntry,
    Language,
    Award,
    Publication,
    VolunteerExperience,
    SocialLink,
    CustomSection,
)

# Standard Degree Canonical Normalizations
DEGREE_MAPPING: Dict[str, str] = {
    "b.s.": "Bachelor of Science",
    "bs": "Bachelor of Science",
    "bachelor of science": "Bachelor of Science",
    "b.tech": "Bachelor of Technology",
    "btech": "Bachelor of Technology",
    "bachelor of technology": "Bachelor of Technology",
    "b.a.": "Bachelor of Arts",
    "ba": "Bachelor of Arts",
    "bachelor of arts": "Bachelor of Arts",
    "m.s.": "Master of Science",
    "ms": "Master of Science",
    "master of science": "Master of Science",
    "m.tech": "Master of Technology",
    "mtech": "Master of Technology",
    "master of technology": "Master of Technology",
    "ph.d.": "Doctor of Philosophy",
    "phd": "Doctor of Philosophy",
    "doctor of philosophy": "Doctor of Philosophy",
    "m.b.a.": "Master of Business Administration",
    "mba": "Master of Business Administration",
    "master of business administration": "Master of Business Administration",
}

# Technology and Skill aliases standardizations
TECH_ALIASES: Dict[str, str] = {
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "k8s": "Kubernetes",
    "kube": "Kubernetes",
    "docker-compose": "Docker",
    "dockercompose": "Docker",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "python": "Python",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "react": "React",
    "reactjs": "React",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "golang": "Go",
    "go lang": "Go",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "sqlite": "SQLite",
    "mysql": "MySQL",
    "html": "HTML",
    "css": "CSS",
    "sass": "Sass",
    "scss": "SCSS",
    "nodejs": "Node.js",
    "node": "Node.js"
}


def parse_date_safely(date_str: Optional[str]) -> Optional[datetime]:
    """Tries parsing raw date strings using standard formats for date validation checks."""
    if not date_str:
        return None
    date_clean = date_str.strip().lower()
    if date_clean in ["present", "current", "now", "today", ""]:
        return datetime.utcnow()
    
    # Try year only
    if re.match(r"^\d{4}$", date_clean):
        return datetime(int(date_clean), 1, 1)
        
    # Try common formats
    formats = [
        "%Y-%m-%d", "%Y-%m", "%m/%Y", "%d/%m/%Y",
        "%B %Y", "%b %Y", "%B, %Y", "%b, %Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
            
    # Regex fallback for year extraction
    year_match = re.search(r"\b(19|20)\d{2}\b", date_clean)
    if year_match:
        return datetime(int(year_match.group(0)), 1, 1)
        
    return None


class ResumeValidator:
    """Validator class implementing validation rules across canonical Resume models."""

    @staticmethod
    def validate_email(email: Optional[str]) -> None:
        """Validates format of candidate email."""
        if not email:
            return
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email.strip()):
            raise ResumeValidationError(f"Invalid email address format: {email}")

    @staticmethod
    def validate_url(url: Optional[str], field_name: str) -> None:
        """Validates syntax and protocol format of platform links."""
        if not url:
            return
        url_clean = url.strip()
        pattern = r"^(https?://)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"
        if not re.match(pattern, url_clean, re.IGNORECASE):
            raise ResumeValidationError(f"Invalid URL link format on field '{field_name}': {url}")

    @staticmethod
    def validate_date_range(start: Optional[str], end: Optional[str], context: str) -> None:
        """Ensures start year or start date precedes or equals end date constraint."""
        if not start or not end:
            return
        dt_start = parse_date_safely(start)
        dt_end = parse_date_safely(end)
        
        if dt_start and dt_end:
            if dt_start > dt_end:
                raise ResumeValidationError(f"Date consistency mismatch in '{context}': Start '{start}' is after End '{end}'.")

    def validate(self, resume: Resume) -> List[str]:
        """Runs full validation sweep and checks all models fields limits constraints.

        Args:
            resume: Top-level Resume canonical model.

        Returns:
            List[str]: List of non-critical warnings encountered.

        Raises:
            ResumeValidationError: For critical schema validation failures.
        """
        warnings: List[str] = []
        info = resume.personal_info
        
        # 1. Check Required Fields
        if not info.full_name or not info.full_name.strip():
            raise ResumeValidationError("Candidate full_name is a required field and cannot be missing or empty.")

        # 2. Validate Emails & URLs
        self.validate_email(info.email)
        self.validate_url(info.linkedin, "linkedin")
        self.validate_url(info.github, "github")
        self.validate_url(info.portfolio, "portfolio")
        self.validate_url(info.website, "website")

        for idx, link in enumerate(info.social_links):
            self.validate_url(link.url, f"social_links[{idx}]")

        # 3. Date Ranges validations
        # Education dates
        for idx, edu in enumerate(resume.education):
            self.validate_date_range(edu.start_year, edu.end_year, f"education[{idx}] - {edu.institution or 'Unknown'}")
            
        # Work Experience dates
        for idx, exp in enumerate(resume.experience):
            self.validate_date_range(exp.start_date, exp.end_date, f"experience[{idx}] - {exp.company or 'Unknown'}")

        # Volunteer dates
        for idx, vol in enumerate(resume.volunteer):
            self.validate_date_range(vol.start_date, vol.end_date, f"volunteer[{idx}] - {vol.organization or 'Unknown'}")

        # Certifications URLs
        for idx, cert in enumerate(resume.certifications):
            self.validate_url(cert.verification_url, f"certifications[{idx}]")

        # Publications URLs
        for idx, pub in enumerate(resume.publications):
            self.validate_url(pub.url, f"publications[{idx}]")

        return warnings


class ResumeNormalizer:
    """Normalizer class processing casing, technology aliases, and absolute URLs."""

    @staticmethod
    def normalize_company(company: Optional[str]) -> Optional[str]:
        """Strips standard suffixes (Inc., LLC) from company names."""
        if not company:
            return company
        suffixes = [
            r"\binc\b\.?", r"\bllc\b\.?", r"\bcorp\b\.?", r"\bcorporation\b\.?",
            r"\bco\b\.?", r"\bltd\b\.?", r"\bpty\b\.?", r"\bprivate\b\.?",
            r"\bs\.a\b\.?", r"\bsa\b\.?", r"\bgmbh\b\.?", r"\bag\b\.?"
        ]
        name = company.strip()
        for suff in suffixes:
            name = re.sub(suff, "", name, flags=re.IGNORECASE).strip()
        name = re.sub(r"[\s,.]+$", "", name).strip()
        return name or company.strip()

    @staticmethod
    def normalize_degree(degree: Optional[str]) -> Optional[str]:
        """Standardizes degree name variations to standard forms."""
        if not degree:
            return degree
        clean = degree.strip().lower().replace(",", "")
        return DEGREE_MAPPING.get(clean, degree.strip())

    @staticmethod
    def normalize_url(url: Optional[str]) -> Optional[str]:
        """Ensures absolute http/https protocol is prepended if absent."""
        if not url:
            return url
        url_clean = url.strip()
        if not re.match(r"^https?://", url_clean, re.IGNORECASE):
            url_clean = "https://" + url_clean
        return url_clean

    @staticmethod
    def normalize_tech(tech_name: str) -> str:
        """Standardizes technology keywords aliases and spelling casings."""
        clean = tech_name.strip().lower()
        return TECH_ALIASES.get(clean, tech_name.strip())

    def normalize(self, resume: Resume) -> Resume:
        """Applies normalizations and filters duplicates from list categories.

        Args:
            resume: Top-level Resume canonical model.

        Returns:
            Resume: Normalized clone of the input model.
        """
        # 1. Personal Information Normalizations
        info = resume.personal_info
        normalized_info = PersonalInformation(
            full_name=info.full_name.strip() if info.full_name else None,
            email=info.email.strip().lower() if info.email else None,
            phone=info.phone.strip() if info.phone else None,
            location=info.location.strip() if info.location else None,
            address=info.address.strip() if info.address else None,
            linkedin=self.normalize_url(info.linkedin),
            github=self.normalize_url(info.github),
            portfolio=self.normalize_url(info.portfolio),
            website=self.normalize_url(info.website),
            social_links=[
                SocialLink(platform=s.platform.strip(), url=self.normalize_url(s.url))
                for s in info.social_links if s.platform and s.url
            ]
        )

        # 2. Education Normalizations
        normalized_edu = []
        for edu in resume.education:
            normalized_edu.append(EducationEntry(
                institution=edu.institution.strip() if edu.institution else None,
                degree=self.normalize_degree(edu.degree),
                branch=edu.branch.strip() if edu.branch else None,
                gpa_cgpa=edu.gpa_cgpa.strip() if edu.gpa_cgpa else None,
                start_year=edu.start_year.strip() if edu.start_year else None,
                end_year=edu.end_year.strip() if edu.end_year else None,
                graduation_year=edu.graduation_year.strip() if edu.graduation_year else None,
                description=edu.description.strip() if edu.description else None
            ))

        # 3. Experience Normalizations
        normalized_exp = []
        for exp in resume.experience:
            normalized_exp.append(ExperienceEntry(
                company=self.normalize_company(exp.company),
                role=exp.role.strip() if exp.role else None,
                location=exp.location.strip() if exp.location else None,
                start_date=exp.start_date.strip() if exp.start_date else None,
                end_date=exp.end_date.strip() if exp.end_date else None,
                duration=exp.duration.strip() if exp.duration else None,
                responsibilities=[resp.strip() for resp in exp.responsibilities if resp.strip()],
                technologies_used=[self.normalize_tech(t) for t in exp.technologies_used if t.strip()],
                achievements=[ach.strip() for ach in exp.achievements if ach.strip()]
            ))

        # 4. Project Normalizations
        normalized_proj = []
        for proj in resume.projects:
            normalized_proj.append(ProjectEntry(
                project_name=proj.project_name.strip() if proj.project_name else None,
                name=proj.name.strip() if proj.name else (proj.project_name.strip() if proj.project_name else None),
                description=proj.description.strip() if proj.description else None,
                technologies=[self.normalize_tech(t) for t in proj.technologies if t.strip()],
                github_url=self.normalize_url(proj.github_url),
                live_url=self.normalize_url(proj.live_url),
                github_link=self.normalize_url(proj.github_link or proj.github_url),
                live_demo=self.normalize_url(proj.live_demo or proj.live_url),
                duration=proj.duration.strip() if proj.duration else None,
                contributions=[c.strip() for c in proj.contributions if c.strip()],
                team_size=proj.team_size
            ))

        # 5. Skills Normalizations & Duplicate Removal
        seen_skills: Set[Tuple[str, str]] = set()
        normalized_skills = []
        for sk in resume.skills:
            if not sk.name or not sk.name.strip():
                continue
            norm_name = self.normalize_tech(sk.name)
            key = (norm_name.lower(), sk.category.strip().lower())
            if key not in seen_skills:
                seen_skills.add(key)
                normalized_skills.append(Skill(
                    name=norm_name,
                    category=sk.category.strip(),
                    confidence_score=max(0.0, min(1.0, sk.confidence_score)),
                    explicit_or_inferred=sk.explicit_or_inferred,
                    years_of_experience=sk.years_of_experience
                ))

        # 6. Certifications Normalizations & Duplicate Removal
        seen_certs: Set[str] = set()
        normalized_certs = []
        for cert in resume.certifications:
            cname = cert.certification_name or ""
            if not cname.strip():
                continue
            key = cname.strip().lower()
            if key not in seen_certs:
                seen_certs.add(key)
                normalized_certs.append(CertificationEntry(
                    certification_name=cname.strip(),
                    organization=self.normalize_company(cert.organization),
                    year=cert.year.strip() if cert.year else None,
                    issuer=self.normalize_company(cert.issuer or cert.organization),
                    credential_id=cert.credential_id.strip() if cert.credential_id else None,
                    verification_url=self.normalize_url(cert.verification_url)
                ))

        # 7. Languages Normalizations & Duplicate Removal
        seen_langs: Set[str] = set()
        normalized_langs = []
        for lang in resume.languages:
            if not lang.name or not lang.name.strip():
                continue
            key = lang.name.strip().lower()
            if key not in seen_langs:
                seen_langs.add(key)
                normalized_langs.append(Language(
                    name=lang.name.strip(),
                    proficiency=lang.proficiency.strip() if lang.proficiency else None
                ))

        # 8. Awards Normalizations
        normalized_awards = []
        for aw in resume.awards:
            if not aw.title or not aw.title.strip():
                continue
            normalized_awards.append(Award(
                title=aw.title.strip(),
                issuer=self.normalize_company(aw.issuer),
                date=aw.date.strip() if aw.date else None,
                description=aw.description.strip() if aw.description else None
            ))

        # 9. Publications Normalizations
        normalized_pubs = []
        for pub in resume.publications:
            if not pub.title or not pub.title.strip():
                continue
            normalized_pubs.append(Publication(
                title=pub.title.strip(),
                publisher=self.normalize_company(pub.publisher),
                date=pub.date.strip() if pub.date else None,
                url=self.normalize_url(pub.url),
                description=pub.description.strip() if pub.description else None
            ))

        # 10. Volunteer Experience Normalizations
        normalized_vol = []
        for vol in resume.volunteer:
            if not vol.organization or not vol.organization.strip():
                continue
            normalized_vol.append(VolunteerExperience(
                organization=self.normalize_company(vol.organization),
                role=vol.role.strip() if vol.role else None,
                start_date=vol.start_date.strip() if vol.start_date else None,
                end_date=vol.end_date.strip() if vol.end_date else None,
                description=vol.description.strip() if vol.description else None
            ))

        # 11. Custom Sections Normalizations
        normalized_custom = []
        for cs in resume.custom_sections:
            if not cs.title or not cs.title.strip():
                continue
            normalized_custom.append(CustomSection(
                title=cs.title.strip(),
                content=[line.strip() for line in cs.content if line.strip()]
            ))

        return Resume(
            personal_info=normalized_info,
            education=normalized_edu,
            experience=normalized_exp,
            projects=normalized_proj,
            skills=normalized_skills,
            certifications=normalized_certs,
            languages=normalized_langs,
            awards=normalized_awards,
            publications=normalized_pubs,
            volunteer=normalized_vol,
            custom_sections=normalized_custom
        )
