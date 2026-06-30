"""Strength evaluation analyzer scanning candidate profile attributes for key technical highlights."""

from typing import List
from backend.intelligence.resume.models import Resume


class StrengthAnalyzer:
    """Detects candidate technical strengths and soft highlights from canonical profiles."""

    def analyze_strengths(self, resume: Resume) -> List[str]:
        """Scans structured fields for strengths.

        Args:
            resume: Normalized canonical candidate profile.

        Returns:
            List[str]: Identified strengths.
        """
        strengths = []
        
        # Compile skills list & description text corpus
        skills = [s.name.lower() for s in resume.skills if s.name]
        proj_texts = " ".join((p.description or "").lower() for p in resume.projects)
        exp_texts = " ".join(" ".join(e.responsibilities + e.achievements).lower() for e in resume.experience)
        corpus = f"{proj_texts} {exp_texts}"

        # 1. Strong Projects
        has_strong_proj = False
        for proj in resume.projects:
            if len(proj.technologies) >= 3 and len(proj.contributions) >= 2:
                has_strong_proj = True
                break
        if has_strong_proj:
            strengths.append("Strong Projects: Possesses detailed project records highlighting multiple technologies and detailed contributions.")

        # 2. Modern Technologies
        modern_techs = ["fastapi", "rust", "go", "golang", "typescript", "docker", "kubernetes", "k8s", "react", "next.js"]
        if any(tech in skills for tech in modern_techs):
            strengths.append("Modern Technologies: Familiar with contemporary cloud-native stacks (e.g. FastAPI, Go, Docker, React).")

        # 3. Leadership
        is_leader = False
        leader_titles = ["lead", "principal", "manager", "director", "architect", "senior", "head", "lead"]
        leader_verbs = ["led", "managed", "designed", "mentored", "architected", "supervised", "spearheaded", "directed"]
        for exp in resume.experience:
            role = (exp.role or "").lower()
            desc = " ".join(exp.responsibilities + exp.achievements).lower()
            if any(title in role for title in leader_titles) or any(verb in desc for verb in leader_verbs):
                is_leader = True
                break
        if is_leader:
            strengths.append("Leadership Indicators: Experience includes mentoring, spearheading systems architecture, or senior leadership roles.")

        # 4. Open Source
        has_os = "open source" in corpus or "open-source" in corpus
        
        # Build candidate links list safely
        cand_links = []
        info = resume.personal_info
        if info.linkedin: cand_links.append(info.linkedin)
        if info.github: cand_links.append(info.github)
        if info.portfolio: cand_links.append(info.portfolio)
        if info.website: cand_links.append(info.website)
        for sl in info.social_links:
            if sl.url: cand_links.append(sl.url)
            
        for link in cand_links:
            if "github.com" in link.lower():
                has_os = True
        for proj in resume.projects:
            for link in [proj.github_url, proj.live_url]:
                if link and "github.com" in link.lower():
                    has_os = True
        if has_os:
            strengths.append("Open Source: Demonstrates public coding involvement or open-source collaboration.")

        # 5. Research
        if resume.publications or "research" in corpus or "academic" in corpus:
            strengths.append("Research & Publications: Experience includes technical publications or scientific research projects.")

        # 6. Hackathons
        has_hack = "hackathon" in corpus
        for aw in resume.awards:
            if "hackathon" in (aw.title or "").lower():
                has_hack = True
        if has_hack:
            strengths.append("Hackathons: Active participation in competitive development events and coding hackathons.")

        # 7. Certifications
        if resume.certifications:
            strengths.append(f"Certifications: Validated credentials including: {', '.join(c.certification_name for c in resume.certifications[:2])}.")

        # 8. Cloud Experience
        cloud_keywords = ["aws", "gcp", "azure", "cloud", "terraform", "s3", "ec2", "lambda"]
        if any(kw in skills or kw in corpus for kw in cloud_keywords):
            strengths.append("Cloud Platforms: Practical cloud experience deploying scalable systems (e.g., AWS, Azure, GCP).")

        # 9. AI Experience
        ai_keywords = ["pytorch", "tensorflow", "generative ai", "llm", "rag", "langchain", "openai", "machine learning"]
        if any(kw in skills or kw in corpus for kw in ai_keywords):
            strengths.append("AI/ML Systems: Experience building artificial intelligence models, LLM agents, or analytics networks.")

        # 10. Backend Experience
        backend_keywords = ["fastapi", "django", "postgresql", "databases", "go", "golang", "backend", "apis", "flask", "sql"]
        if any(kw in skills or kw in corpus for kw in backend_keywords):
            strengths.append("Backend Engineering: Competency in creating REST APIs, configuring databases, and optimizing backend logic.")

        # 11. Frontend Experience
        frontend_keywords = ["react", "angular", "vue", "frontend", "html", "css", "javascript", "typescript", "bootstrap"]
        if any(kw in skills or kw in corpus for kw in frontend_keywords):
            strengths.append("Frontend Development: Competency in UI components, responsive layout systems, and javascript frameworks.")

        if not strengths:
            strengths.append("Standard Core: Profile presents standard structural components with solid foundations.")

        return strengths
