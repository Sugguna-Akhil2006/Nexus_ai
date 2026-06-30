"""Career Stage and specialization classification heuristics for structured candidate profiles."""

from typing import Tuple
from backend.intelligence.resume.models import Resume
from backend.intelligence.resume.validators import parse_date_safely


class CareerStageClassifier:
    """Classifies the candidate's career stage and engineering specialization."""

    def classify(self, resume: Resume) -> Tuple[str, str]:
        """Runs rule-based heuristics on experience duration and skills to classify stage and track.

        Args:
            resume: Normalized canonical candidate profile.

        Returns:
            Tuple[str, str]: (career_stage, specialization)
        """
        # Calculate experience tenure in months
        total_months = 0.0
        has_non_intern_role = False
        
        for exp in resume.experience:
            start = parse_date_safely(exp.start_date)
            end = parse_date_safely(exp.end_date)
            if start and end:
                months = (end.year - start.year) * 12 + (end.month - start.month)
                total_months += max(1.0, float(months))
            
            role_title = (exp.role or "").lower()
            if "intern" not in role_title and "trainee" not in role_title:
                has_non_intern_role = True

        total_years = total_months / 12.0

        # 1. Deduce Career Stage
        if not resume.experience:
            # Check if student
            if resume.education:
                stage = "Student"
            else:
                stage = "Junior"
        elif not has_non_intern_role:
            stage = "Intern"
        else:
            if total_years < 2.0:
                stage = "Junior"
            elif total_years < 5.0:
                stage = "Mid-Level"
            elif total_years < 8.0:
                stage = "Senior"
            else:
                stage = "Lead"

        # 2. Deduce Specialization
        # Compile a search corpus from skills, projects, and role descriptions
        skills_set = {s.name.lower() for s in resume.skills if s.name}
        
        corpus_parts = list(skills_set)
        for proj in resume.projects:
            corpus_parts.append((proj.project_name or "").lower())
            corpus_parts.append((proj.description or "").lower())
            corpus_parts.extend(t.lower() for t in proj.technologies)
        for exp in resume.experience:
            corpus_parts.append((exp.role or "").lower())
            corpus_parts.append(" ".join(exp.responsibilities + exp.achievements).lower())
            
        corpus = " ".join(corpus_parts)

        # Heuristic keywords lists
        ai_kws = ["pytorch", "tensorflow", "keras", "generative ai", "llm", "openai", "pinecone", "chromadb", "nlp", "transformers", "deep learning", "machine learning"]
        research_kws = ["research", "publication", "paper", "journal", "academic", "scientific"]
        ds_kws = ["data science", "statistics", "pandas", "numpy", "scikit-learn", "tableau", "jupyter", "data analysis", "data analyst"]
        fe_kws = ["react", "angular", "vue", "css", "html", "svelte", "frontend", "javascript", "typescript"]
        be_kws = ["fastapi", "django", "postgresql", "flask", "databases", "go", "golang", "node.js", "backend", "sql", "redis"]

        has_ai = any(kw in corpus for kw in ai_kws)
        has_research = any(kw in corpus for kw in research_kws) or bool(resume.publications)
        has_ds = any(kw in corpus for kw in ds_kws)
        has_fe = any(kw in corpus for kw in fe_kws)
        has_be = any(kw in corpus for kw in be_kws)

        if has_research:
            specialization = "Research Engineer"
        elif has_ai:
            specialization = "AI Engineer"
        elif has_ds:
            specialization = "Data Scientist"
        elif has_fe and has_be:
            specialization = "Full Stack Engineer"
        elif has_fe:
            specialization = "Frontend Engineer"
        else:
            # Default fallback
            specialization = "Backend Engineer"

        return stage, specialization
