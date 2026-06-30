"""Vocabulary checklists, action verbs alternatives, and keywords for ATS scanning."""

from typing import Dict, List

# Core industry keywords expected by technical ATS screeners
HIGH_VALUE_KEYWORDS: List[str] = [
    "python", "go", "golang", "java", "typescript", "javascript",
    "docker", "kubernetes", "k8s", "aws", "gcp", "azure",
    "fastapi", "django", "react", "pytorch", "tensorflow",
    "ci/cd", "microservices", "system design", "distributed systems",
    "sql", "postgresql", "mongodb", "redis", "rest api", "graphql"
]

# Emerging technologies indicators
EMERGING_TECHNOLOGIES: List[str] = [
    "generative ai", "genai", "llm", "llms", "large language models",
    "vector databases", "pinecone", "chromadb", "weaviate", "qdrant",
    "langchain", "llamaindex", "rag", "retrieval augmented generation",
    "transformers", "prompt engineering"
]

# Strong Action Verbs alternatives mapping
ACTION_VERB_ALTERNATIVES: Dict[str, List[str]] = {
    "built": ["constructed", "forged", "implemented", "engineered"],
    "designed": ["architected", "engineered", "conceptualized", "devised"],
    "implemented": ["executed", "deployed", "enforced", "established"],
    "optimized": ["maximised", "streamlined", "refined", "boosted"],
    "developed": ["engineered", "formulated", "authored", "pioneered"],
    "architected": ["orchestrated", "engineered", "conceptualized"],
    "automated": ["streamlined", "orchestrated", "systematized"],
    "integrated": ["consolidated", "harmoniesed", "fused", "unified"],
    "created": ["pioneered", "devised", "initiated", "founded"],
    "generated": ["produced", "yielded", "attained", "secured"]
}

# Weak phrasing indicators which reduce impact
WEAK_WORDS: List[str] = [
    "helped with", "assisted", "responsible for", "participated in",
    "worked on", "handled", "helped", "assisted in", "involved in"
]

# Core document sections required on standard technical resumes
CORE_SECTIONS: List[str] = [
    "Personal Information",
    "Education",
    "Experience",
    "Projects",
    "Skills"
]

# Optional/Supporting sections that add extra score weights
SUPPORTING_SECTIONS: List[str] = [
    "Certifications",
    "Languages",
    "Awards",
    "Volunteer Experience",
    "Custom Sections"
]
