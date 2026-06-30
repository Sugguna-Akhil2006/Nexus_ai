"""System and user prompt templates registered for structured Resume Intelligence inference."""

import json
from backend.interfaces.prompt import PromptRegistry, PromptTemplate, PromptSection


# JSON structure schemas for parsing guides
EXTRACTION_SCHEMA = {
    "contact_info": {
        "name": "Candidate Name (or null)",
        "email": "Candidate Email (or null)",
        "phone": "Candidate Phone (or null)",
        "links": ["list", "of", "links"]
    },
    "education": [
        {
            "degree": "Degree (e.g. B.S.)",
            "institution": "University Name",
            "field_of_study": "Major name",
            "graduation_year": "Year (e.g. 2021)",
            "gpa": 3.8
        }
    ],
    "experience": [
        {
            "job_title": "Position",
            "company": "Company",
            "start_date": "Date",
            "end_date": "Date or Present",
            "description": "Responsibilities text description",
            "achievements": ["list", "of", "quantified", "achievements", "with", "numbers"]
        }
    ],
    "projects": [
        {
            "name": "Project Name",
            "description": "Project technical description",
            "role": "Role",
            "links": ["list", "of", "urls"]
        }
    ],
    "certifications": [
        {
            "name": "Cert Name",
            "issuing_organization": "Issuer",
            "issue_date": "Date",
            "expiration_date": "Date or No Expiration"
        }
    ],
    "skills": ["list", "of", "raw", "skills"]
}

SKILLS_SCHEMA = {
    "programming_languages": ["Python", "C++", "etc."],
    "frameworks": ["FastAPI", "React", "etc."],
    "databases": ["PostgreSQL", "MongoDB", "etc."],
    "cloud": ["AWS", "GCP", "etc."],
    "devops": ["Docker", "Kubernetes", "etc."],
    "ai_ml": ["LLMs", "PyTorch", "etc."],
    "tools": ["Git", "VSCode", "etc."],
    "soft_skills": ["Leadership", "Teamwork", "etc."],
    "explicit_skills": ["Skills explicitly written in the resume text"],
    "inferred_skills": ["Skills deduced semantically from projects or experience context"]
}

ATS_SCHEMA = {
    "score": 85,
    "section_completeness": {
        "education": True,
        "experience": True,
        "skills": True,
        "projects": False,
        "certifications": False
    },
    "keyword_density": {
        "python": 0.05,
        "fastapi": 0.02
    },
    "formatting_issues": ["Visual issue descriptions"],
    "missing_sections": ["Certifications"],
    "action_verb_usage": ["Led", "Managed", "Designed"],
    "quantified_achievements_count": 3,
    "resume_length_analysis": "Resume is appropriate length (1 page)."
}

MATCH_SCHEMA = {
    "match_percentage": 75,
    "missing_keywords": ["Kubernetes", "Go"],
    "matching_skills": ["Python", "FastAPI", "Docker"],
    "missing_skills": ["Go", "Kubernetes"],
    "recommendations": ["Add project details showing Kubernetes clusters", "Include Go language competency"],
    "section_specific_feedback": {
        "experience": "Try to quantify how you deployed services on GCP.",
        "skills": "Include missing keywords like Kubernetes in your technical stack segment."
    }
}

SWOT_SCHEMA = {
    "strengths": ["Strong FastAPI backend experience", "Quantified Google impact details"],
    "weaknesses": ["Lack of deployment orchestration toolsets details", "No SQL database references"],
    "improvement_suggestions": ["Detail docker container architectures used", "Add database scaling statistics"],
    "career_readiness": "Senior Software Engineer",
    "interview_preparation_tips": [
        "Be ready to explain RAG chunking layout designs.",
        "Prepare to describe Docker networking setups."
    ]
}


def register_resume_prompts() -> None:
    """Registers workflow-specific prompt templates in the global PromptRegistry."""
    registry = PromptRegistry()
    
    # 1. Extraction prompt template
    try:
        registry.register_template(PromptTemplate(
            template_id="resume_extraction",
            name="Resume Extraction Template",
            version="1.0.0",
            description="Extract candidate details from resume plain text",
            author="ResumeIntel",
            variables=[],
            sections=[
                PromptSection(
                    section_id="sys",
                    title="System Instruction",
                    content=(
                        "You are an expert Resume Parser agent. Analyze the provided resume plaintext and extract structured attributes. "
                        "Do NOT write any descriptions, introductions, explanations, or codeblocks wrapper tags (like ```json). "
                        "Respond ONLY with a valid JSON matching this schema format:\n"
                        f"{json.dumps(EXTRACTION_SCHEMA, indent=2)}\n"
                        "Never fabricate info. If a section or field is missing, set its value to null or empty list."
                    ),
                    priority=1.0,
                    required=True,
                    metadata={"role": "system"}
                ),
                PromptSection(
                    section_id="usr",
                    title="User Resume Text",
                    content="Resume Plaintext:\n{query}",
                    priority=2.0,
                    required=True,
                    metadata={"role": "user"}
                )
            ]
        ))
    except Exception:
        pass

    # 2. Skill Categorizer prompt template
    try:
        registry.register_template(PromptTemplate(
            template_id="resume_skill_categorizer",
            name="Resume Skill Categorizer Template",
            version="1.0.0",
            description="Categorizes skills into specific taxonomies and infers implicit skills",
            author="ResumeIntel",
            variables=[],
            sections=[
                PromptSection(
                    section_id="sys",
                    title="System Instruction",
                    content=(
                        "You are an expert technical recruiter. Categorize the input candidate's flat skills list into specialized classes "
                        "and deduce inferred implicit skills based on candidate project contexts. "
                        "Respond ONLY with a valid JSON matching this schema format:\n"
                        f"{json.dumps(SKILLS_SCHEMA, indent=2)}\n"
                        "Do not include any wrapper markup or markdown backticks."
                    ),
                    priority=1.0,
                    required=True,
                    metadata={"role": "system"}
                ),
                PromptSection(
                    section_id="usr",
                    title="User Skills Data",
                    content="Flat Skills List & Candidate Context:\n{query}",
                    priority=2.0,
                    required=True,
                    metadata={"role": "user"}
                )
            ]
        ))
    except Exception:
        pass

    # 3. ATS Analysis prompt template
    try:
        registry.register_template(PromptTemplate(
            template_id="resume_ats_analysis",
            name="Resume ATS Analysis Template",
            version="1.0.0",
            description="Analyzes formatting issues, action verbs, sections completeness, and keyword density",
            author="ResumeIntel",
            variables=[],
            sections=[
                PromptSection(
                    section_id="sys",
                    title="System Instruction",
                    content=(
                        "You are an expert ATS (Applicant Tracking System) parser simulator. Evaluate the candidate's resume "
                        "on formatting checklist, missing sections, strong action verb usage, quantified achievements containing numbers, and length. "
                        "Respond ONLY with a valid JSON matching this schema format:\n"
                        f"{json.dumps(ATS_SCHEMA, indent=2)}\n"
                        "Do not write conversational text or wrapper blocks."
                    ),
                    priority=1.0,
                    required=True,
                    metadata={"role": "system"}
                ),
                PromptSection(
                    section_id="usr",
                    title="User Resume Content",
                    content="Resume Content:\n{query}",
                    priority=2.0,
                    required=True,
                    metadata={"role": "user"}
                )
            ]
        ))
    except Exception:
        pass

    # 4. JD Matcher prompt template
    try:
        registry.register_template(PromptTemplate(
            template_id="resume_jd_matcher",
            name="Resume Job Description Matcher Template",
            version="1.0.0",
            description="Calculates match alignment percentage and skill gaps against a JD",
            author="ResumeIntel",
            variables=[],
            sections=[
                PromptSection(
                    section_id="sys",
                    title="System Instruction",
                    content=(
                        "You are an expert HR Recruiter matching candidate resumes to Job Descriptions. "
                        "Determine match percentage, missing keywords, matching skills, missing skills, and detailed section recommendations. "
                        "Respond ONLY with a valid JSON matching this schema format:\n"
                        f"{json.dumps(MATCH_SCHEMA, indent=2)}\n"
                        "Output must be raw JSON only."
                    ),
                    priority=1.0,
                    required=True,
                    metadata={"role": "system"}
                ),
                PromptSection(
                    section_id="usr",
                    title="Resume & Job Description text",
                    content="Compare the following candidate resume and JD details:\n{query}",
                    priority=2.0,
                    required=True,
                    metadata={"role": "user"}
                )
            ]
        ))
    except Exception:
        pass

    # 5. General SWOT Analysis prompt template
    try:
        registry.register_template(PromptTemplate(
            template_id="resume_general_analysis",
            name="Resume General SWOT Analysis Template",
            version="1.0.0",
            description="Evaluates strengths, weaknesses, readiness levels, and interview prep questions",
            author="ResumeIntel",
            variables=[],
            sections=[
                PromptSection(
                    section_id="sys",
                    title="System Instruction",
                    content=(
                        "You are an expert Career Counselor. Generate SWOT profile details (Strengths, Weaknesses, Gaps), "
                        "improvement updates, career readiness alignment tier, and interview questions. "
                        "Respond ONLY with a valid JSON matching this schema format:\n"
                        f"{json.dumps(SWOT_SCHEMA, indent=2)}\n"
                        "Strictly output JSON only."
                    ),
                    priority=1.0,
                    required=True,
                    metadata={"role": "system"}
                ),
                PromptSection(
                    section_id="usr",
                    title="User Resume Details",
                    content="Candidate Resume:\n{query}",
                    priority=2.0,
                    required=True,
                    metadata={"role": "user"}
                )
            ]
        ))
    except Exception:
        pass


JD_SCHEMA = {
    "job_title": "String title",
    "company": "Company name or null",
    "experience_required": "Years of experience required, or null",
    "education_requirements": ["List", "of", "education", "requirements"],
    "required_skills": ["List", "of", "required", "skills"],
    "preferred_skills": ["List", "of", "preferred", "skills"],
    "responsibilities": ["List", "of", "responsibilities"],
    "technologies": ["List", "of", "technologies"],
    "certifications": ["List", "of", "certifications"],
    "soft_skills": ["List", "of", "soft", "skills"],
    "location": "Location or null",
    "employment_type": "Employment type or null"
}

# 6. Job Description Parser prompt template
try:
    registry.register_template(PromptTemplate(
        template_id="resume_jd_parser",
        name="Job Description Parser Template",
        version="1.0.0",
        description="Parses job description into structured properties",
        author="ResumeIntel",
        variables=[],
        sections=[
            PromptSection(
                section_id="sys",
                title="System Instruction",
                content=(
                    "You are an expert Talent Acquisition / ATS Parser. "
                    "Extract details from the job description and output ONLY a valid JSON conforming to this schema:\n"
                    f"{json.dumps(JD_SCHEMA, indent=2)}\n"
                    "Do not fabricate missing details. Strictly output JSON only."
                ),
                priority=1.0,
                required=True,
                metadata={"role": "system"}
            ),
            PromptSection(
                section_id="usr",
                title="User JD Details",
                content="Job Description:\n{query}",
                priority=2.0,
                required=True,
                metadata={"role": "user"}
            )
        ]
    ))
except Exception:
    pass
