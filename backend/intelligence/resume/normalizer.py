"""Normalization dictionary and standardizer for technology keywords/skill aliases."""

from typing import Dict

# Reusable normalization mapping dictionary
SKILL_ALIASES: Dict[str, str] = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "py": "Python",
    "python": "Python",
    "py3": "Python",
    "python3": "Python",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "tensor flow": "TensorFlow",
    "tensorflow": "TensorFlow",
    "llm": "Large Language Models",
    "llms": "Large Language Models",
    "large language models": "Large Language Models",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "kube": "Kubernetes",
    "docker-compose": "Docker",
    "dockercompose": "Docker",
    "docker": "Docker",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "golang": "Go",
    "go lang": "Go",
    "go": "Go",
    "html": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "html5": "HTML",
    "generative ai": "Generative AI",
    "genai": "Generative AI",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "fastapi": "FastAPI",
    "langchain": "LangChain",
    "llamaindex": "LlamaIndex",
    "pinecone": "Pinecone",
    "chromadb": "ChromaDB",
    "chroma": "ChromaDB",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "rest apis": "REST APIs",
    "api development": "API Development",
    "api design": "API Design",
    "large language models": "Large Language Models",
    "android studio": "Android Studio",
    "git actions": "GitHub Actions",
    "github actions": "GitHub Actions",
    "react native": "React Native",
    "spring boot": "Spring Boot",
    "next.js": "Next.js",
    "vue.js": "Vue.js",
    "express.js": "Express.js",
    "nest.js": "Nest.js"
}


def normalize_skill_name(name: str) -> str:
    """Normalizes raw skill name casing and aliases to their standard format.

    Args:
        name: The raw input name.

    Returns:
        str: Standardized name, e.g. "React", "JavaScript", "Python".
    """
    if not name:
        return ""
    clean = name.strip().lower()
    
    # Try exact match first
    if clean in SKILL_ALIASES:
        return SKILL_ALIASES[clean]
        
    # Remove hyphens and try matching
    clean_split = clean.replace("-", " ")
    clean_split = " ".join(clean_split.split())
    if clean_split in SKILL_ALIASES:
        return SKILL_ALIASES[clean_split]
        
    # Standard Title Case Fallback (replace hyphens first)
    clean_fallback = name.strip().replace("-", " ")
    words = clean_fallback.split()
    return " ".join(w.capitalize() for w in words)
