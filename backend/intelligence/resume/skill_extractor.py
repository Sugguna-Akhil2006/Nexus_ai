"""Skill categorizer classifying explicit and inferred skills across tech categories."""

import re
from typing import Dict, List, Set, Tuple

from backend.intelligence.resume.exceptions import SkillExtractionError
from backend.intelligence.resume.models import (
    CategorizedSkills,
    ResumeData,
    Resume,
    Skill,
    SkillEvidence,
    ExtractedSkill,
    SkillProfile,
)
from backend.intelligence.resume.parser import run_resume_llm_query
from backend.intelligence.resume.prompts import SKILLS_SCHEMA
from backend.intelligence.resume.skill_taxonomy import TAXONOMY_PATTERNS, classify_skill_by_taxonomy
from backend.intelligence.resume.normalizer import normalize_skill_name
from backend.intelligence.resume.confidence import calculate_confidence

# Inferences dictionary mapping trigger technology to implied parent/dependent skills
INFERENCE_RULES: Dict[str, List[str]] = {
    "FastAPI": ["REST APIs", "Python Backend", "API Development"],
    "React": ["Frontend", "JavaScript", "Web Development"],
    "Docker": ["Containerization", "DevOps"],
    "PyTorch": ["Deep Learning", "Machine Learning", "Generative AI"],
    "TensorFlow": ["Deep Learning", "Machine Learning", "Generative AI"],
    "Kubernetes": ["Container Orchestration", "DevOps"],
    "AWS": ["Cloud Computing"],
    "Git": ["Version Control"],
    "Django": ["Backend", "Python Backend", "Web Development"],
    "Flask": ["Backend", "Python Backend", "Web Development"],
    "TypeScript": ["JavaScript", "Frontend"],
    "GPT-4": ["Generative AI", "Large Language Models"],
    "LangChain": ["Generative AI", "LLM Frameworks"],
    "LlamaIndex": ["Generative AI", "LLM Frameworks"],
    "Pinecone": ["Vector Databases", "Generative AI"]
}


def search_skills_in_text(text: str) -> List[str]:
    """Scans text block for keyword matches in TAXONOMY_PATTERNS using word boundaries.

    Args:
        text: Source text snippet.

    Returns:
        List[str]: Matched taxonomy keywords.
    """
    if not text:
        return []
    # Replace common punctuation with spaces to prevent word boundary issues
    clean = re.sub(r"[.,;():\-/]", " ", text.lower())
    clean = " ".join(clean.split())
    
    found = []
    for cat, keywords in TAXONOMY_PATTERNS.items():
        for kw in keywords:
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, clean):
                found.append(kw)
    return found


class SkillExtractor:
    """Service to categorize skills and infer implicit technologies from candidate experiences."""

    def extract_and_categorize(self, resume_data: ResumeData) -> CategorizedSkills:
        """Categorizes raw skills list and infers implicit skills.

        Args:
            resume_data: Parsed ResumeData.

        Returns:
            CategorizedSkills: Taxonomy-grouped skills model.

        Raises:
            SkillExtractionError: On failure to parse or categorize skills.
        """
        # Build query text for the categorizer containing raw skills, experience bullet points, and project descriptions
        experience_bullets = []
        for exp in resume_data.experience:
            if exp.description:
                experience_bullets.append(exp.description)
            experience_bullets.extend(exp.achievements)
            
        project_details = []
        for proj in resume_data.projects:
            if proj.name and proj.description:
                project_details.append(f"{proj.name}: {proj.description}")

        query_text = (
            f"Explicit Skills List:\n{', '.join(resume_data.skills)}\n\n"
            f"Work Experience Context:\n{'\n'.join(experience_bullets)}\n\n"
            f"Project Context:\n{'\n'.join(project_details)}"
        )

        parsed_json = run_resume_llm_query("resume_skill_categorizer", query_text, SKILLS_SCHEMA)

        try:
            return CategorizedSkills(
                programming_languages=parsed_json.get("programming_languages", []) or [],
                frameworks=parsed_json.get("frameworks", []) or [],
                databases=parsed_json.get("databases", []) or [],
                cloud=parsed_json.get("cloud", []) or [],
                devops=parsed_json.get("devops", []) or [],
                ai_ml=parsed_json.get("ai_ml", []) or [],
                tools=parsed_json.get("tools", []) or [],
                soft_skills=parsed_json.get("soft_skills", []) or [],
                explicit_skills=parsed_json.get("explicit_skills", []) or [],
                inferred_skills=parsed_json.get("inferred_skills", []) or []
            )
        except Exception as e:
            raise SkillExtractionError(f"Failed to map structured JSON payload to CategorizedSkills: {e}") from e

    def extract_skills_profile(self, resume: Resume) -> SkillProfile:
        """Extracts, normalizes, categorizes, scores, infers, and deduplicates skills from Resume.

        Args:
            resume: The canonical Resume model.

        Returns:
            SkillProfile: Consolidated structured profile containing all skills.
        """
        all_skills: List[ExtractedSkill] = []

        # Helper to safely append or construct an extracted skill
        def add_extracted_skill(name: str, source: str, context: str, evidence_text: str, explicit: bool = True) -> None:
            norm_name = normalize_skill_name(name)
            if not norm_name:
                return
            category = classify_skill_by_taxonomy(norm_name)
            status = "Explicit" if explicit else "Inferred"
            
            evidence = SkillEvidence(
                source=source,
                context=context,
                evidence_text=evidence_text.strip()
            )
            
            all_skills.append(ExtractedSkill(
                name=norm_name,
                category=category,
                confidence_score=0.0,  # will be computed after deduplication/merging
                explicit_or_inferred=status,
                frequency=1,
                evidence=[evidence]
            ))

        # 1. Extract from Explicit Skills Section
        for sk in resume.skills:
            if sk.name:
                add_extracted_skill(
                    name=sk.name,
                    source="Explicit Skills",
                    context="Skills Section",
                    evidence_text=f"Explicitly listed: {sk.name}",
                    explicit=True
                )

        # 2. Extract from Education
        for edu in resume.education:
            inst = edu.institution or "Education Section"
            fields_to_scan = [edu.degree, edu.branch, edu.description]
            for val in fields_to_scan:
                if val:
                    for keyword in search_skills_in_text(val):
                        add_extracted_skill(
                            name=keyword,
                            source="Education",
                            context=inst,
                            evidence_text=f"Found in education record ({inst}): '{val}'",
                            explicit=True
                        )

        # 3. Extract from Work Experience
        for exp in resume.experience:
            comp = exp.company or "Work Experience Section"
            # Explicit technologies listed on the experience model
            for tech in exp.technologies_used:
                add_extracted_skill(
                    name=tech,
                    source="Work Experience",
                    context=f"Role: {exp.role} at {comp}",
                    evidence_text=f"Explicitly listed as technology used at {comp}",
                    explicit=True
                )
            # Scan text responsibilities/achievements
            text_blocks = [exp.role] + exp.responsibilities + exp.achievements
            for val in text_blocks:
                if val:
                    for keyword in search_skills_in_text(val):
                        add_extracted_skill(
                            name=keyword,
                            source="Work Experience",
                            context=f"Role: {exp.role} at {comp}",
                            evidence_text=f"Found in job description details at {comp}: '{val}'",
                            explicit=True
                        )

        # 4. Extract from Projects
        for proj in resume.projects:
            pname = proj.name or proj.project_name or "Project"
            # Explicit project technologies list
            for tech in proj.technologies:
                add_extracted_skill(
                    name=tech,
                    source="Projects",
                    context=pname,
                    evidence_text=f"Explicitly listed as technology used in project: {pname}",
                    explicit=True
                )
            # Scan descriptions/contributions
            text_blocks = [pname, proj.description] + proj.contributions
            for val in text_blocks:
                if val:
                    for keyword in search_skills_in_text(val):
                        add_extracted_skill(
                            name=keyword,
                            source="Projects",
                            context=pname,
                            evidence_text=f"Found in project details of {pname}: '{val}'",
                            explicit=True
                        )

        # 5. Extract from Certifications
        for cert in resume.certifications:
            cname = cert.certification_name or ""
            if cname:
                for keyword in search_skills_in_text(cname):
                    add_extracted_skill(
                        name=keyword,
                        source="Certifications",
                        context=cname,
                        evidence_text=f"Extracted from certification title: '{cname}'",
                        explicit=True
                    )

        # 6. Extract from Publications
        for pub in resume.publications:
            pname = pub.title or "Publication"
            text_blocks = [pub.title, pub.publisher, pub.description]
            for val in text_blocks:
                if val:
                    for keyword in search_skills_in_text(val):
                        add_extracted_skill(
                            name=keyword,
                            source="Publications",
                            context=pname,
                            evidence_text=f"Found in publication description ({pname}): '{val}'",
                            explicit=True
                        )

        # 7. Apply Inference Rules
        inferred_skills: List[ExtractedSkill] = []
        for sk in all_skills:
            if sk.name in INFERENCE_RULES:
                for target in INFERENCE_RULES[sk.name]:
                    inferred_skills.append(ExtractedSkill(
                        name=normalize_skill_name(target),
                        category=classify_skill_by_taxonomy(target),
                        confidence_score=0.0,
                        explicit_or_inferred="Inferred",
                        frequency=1,
                        evidence=[SkillEvidence(
                            source="Inference",
                            context=f"Inferred from {sk.name}",
                            evidence_text=f"Logically inferred because the candidate has demonstrated skill in: '{sk.name}'"
                        )]
                    ))
        all_skills.extend(inferred_skills)

        # 8. Deduplicate and Merge Skills
        merged_skills: Dict[Tuple[str, str], ExtractedSkill] = {}
        for sk in all_skills:
            key = (sk.name, sk.category)
            if key not in merged_skills:
                merged_skills[key] = sk
            else:
                existing = merged_skills[key]
                # If either is Explicit, canonical skill is Explicit
                if sk.explicit_or_inferred == "Explicit":
                    existing.explicit_or_inferred = "Explicit"
                
                # Increment frequency
                existing.frequency += sk.frequency
                
                # Consolidate evidence citations
                existing_ev_keys = {(ev.source, ev.evidence_text) for ev in existing.evidence}
                for ev in sk.evidence:
                    ev_key = (ev.source, ev.evidence_text)
                    if ev_key not in existing_ev_keys:
                        existing.evidence.append(ev)
                        existing_ev_keys.add(ev_key)

        # 9. Recalculate Final Confidence Scores
        from backend.intelligence.resume.confidence import SOURCE_BASE_CONFIDENCE
        for sk in merged_skills.values():
            # Find the strongest source among the evidence citations
            strongest_source = "Inference"
            max_weight = -1.0
            for ev in sk.evidence:
                weight = SOURCE_BASE_CONFIDENCE.get(ev.source, 0.50)
                if weight > max_weight:
                    max_weight = weight
                    strongest_source = ev.source
            
            sk.confidence_score = calculate_confidence(
                source=strongest_source,
                explicit_or_inferred=sk.explicit_or_inferred,
                frequency=sk.frequency
            )

        # Sort skills by category and name for clean output formatting
        sorted_skills = sorted(merged_skills.values(), key=lambda x: (x.category, x.name))
        return SkillProfile(skills=sorted_skills)
