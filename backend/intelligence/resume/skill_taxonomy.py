"""Taxonomy definition and helper matching utilities for categorizing skills."""

from typing import Dict, List, Optional

CATEGORIES: List[str] = [
    "Programming Languages",
    "Frameworks",
    "Libraries",
    "Databases",
    "Cloud Platforms",
    "DevOps",
    "Operating Systems",
    "Networking",
    "Cybersecurity",
    "Machine Learning",
    "Deep Learning",
    "Generative AI",
    "LLM Frameworks",
    "Vector Databases",
    "Data Science",
    "Mobile Development",
    "Frontend",
    "Backend",
    "Testing",
    "Version Control",
    "Soft Skills",
    "Other"
]

# Taxonomy mapping rules (case-insensitive keyword matching)
TAXONOMY_PATTERNS: Dict[str, List[str]] = {
    "Generative AI": [
        "gpt-4", "gpt-3.5", "claude", "stable diffusion", "midjourney", "dall-e",
        "llm", "llms", "large language models", "prompt engineering", "retrieval augmented generation",
        "rag", "text-to-image", "copilot", "generative ai", "genai", "openai", "anthropic"
    ],
    "LLM Frameworks": [
        "langchain", "llamaindex", "huggingface", "hugging face", "semantic kernel", "autogen", "crewai"
    ],
    "Vector Databases": [
        "pinecone", "milvus", "chroma", "chromadb", "weaviate", "qdrant", "faiss"
    ],
    "Deep Learning": [
        "pytorch", "tensorflow", "keras", "neural networks", "cnn", "rnn", "lstm",
        "transformers", "backpropagation", "gan", "autoencoders", "deep learning"
    ],
    "Machine Learning": [
        "scikit-learn", "sklearn", "regression", "classification", "clustering", "random forest",
        "xgboost", "gradient boosting", "svm", "knn", "dimensionality reduction", "pca", "decision trees",
        "machine learning", "ml", "nlp", "natural language processing", "computer vision", "cv"
    ],
    "DevOps": [
        "docker", "kubernetes", "k8s", "jenkins", "ansible", "terraform", "github actions",
        "ci/cd", "circleci", "prometheus", "grafana", "helm", "nginx", "apache", "vagrant",
        "containerization", "monitoring", "infrastructure as code", "iac"
    ],
    "Cloud Platforms": [
        "aws", "amazon web services", "gcp", "google cloud platform", "google cloud", "azure",
        "microsoft azure", "heroku", "digitalocean", "vercel", "netlify", "cloud computing"
    ],
    "Databases": [
        "postgresql", "postgres", "mongodb", "redis", "mysql", "sqlite", "cassandra",
        "dynamodb", "neo4j", "elasticsearch", "oracle", "mariadb", "firestore", "nosql", "rdbms"
    ],
    "Frameworks": [
        "fastapi", "django", "flask", "react", "react.js", "reactjs", "vue", "vue.js", "vuejs",
        "angular", "next.js", "nextjs", "spring boot", "springboot", "rails", "laravel",
        "express", "express.js", "flutter", "react native", "svelte", "django rest framework", "drf"
    ],
    "Libraries": [
        "numpy", "pandas", "scipy", "matplotlib", "seaborn", "spacy", "nltk", "requests",
        "beautifulsoup", "sqlalchemy", "pydantic", "redux", "rxjs", "gunicorn", "uvicorn"
    ],
    "Programming Languages": [
        "python", "go", "javascript", "typescript", "c++", "c#", "java", "ruby", "rust", "php",
        "swift", "kotlin", "scala", "clojure", "haskell", "r", "perl", "bash", "shell", "sql",
        "objective-c", "dart", "c language", "golang"
    ],
    "Cybersecurity": [
        "oauth", "jwt", "saml", "encryption", "decryption", "hashing", "cryptography", "firewall",
        "penetration testing", "vulnerability assessment", "iam", "active directory", "cybersecurity", "security"
    ],
    "Networking": [
        "tcp/ip", "dns", "http", "https", "grpc", "graphql", "websockets", "ssl/tls", "ftp",
        "ssh", "dhcp", "ipsec", "vpn", "networking", "routing", "load balancer"
    ],
    "Operating Systems": [
        "linux", "ubuntu", "debian", "centos", "redhat", "unix", "macos", "os x", "windows",
        "ios", "android", "operating system", "os"
    ],
    "Testing": [
        "pytest", "unittest", "junit", "selenium", "cypress", "jest", "mocha", "chai",
        "playwright", "postman", "integration testing", "unit testing", "e2e testing", "mocking", "testing"
    ],
    "Version Control": [
        "git", "github", "gitlab", "bitbucket", "svn", "mercurial", "version control"
    ],
    "Frontend": [
        "html", "css", "html5", "css3", "sass", "scss", "tailwind", "tailwind css", "bootstrap",
        "webpack", "babel", "vite", "npm", "yarn", "dom", "seo", "frontend", "web design"
    ],
    "Backend": [
        "node.js", "nodejs", "microservices", "rest api", "restful api", "soap", "mvc",
        "backend", "api design", "api development", "server-side"
    ],
    "Mobile Development": [
        "android studio", "xcode", "ionic", "xamarin", "mobile app", "ios development", "android development"
    ],
    "Data Science": [
        "statistics", "data analysis", "data visualization", "jupyter notebook", "tableau",
        "power bi", "feature engineering", "a/b testing", "data science", "data analytics"
    ],
    "Soft Skills": [
        "leadership", "communication", "teamwork", "collaboration", "problem solving",
        "time management", "mentoring", "public speaking", "negotiation", "agile", "scrum",
        "project management", "critical thinking", "creativity"
    ]
}

# Specific category matching priorities to resolve overlaps
CATEGORY_PRIORITY: List[str] = [
    "Generative AI",
    "LLM Frameworks",
    "Vector Databases",
    "Deep Learning",
    "Machine Learning",
    "DevOps",
    "Cloud Platforms",
    "Databases",
    "Frameworks",
    "Libraries",
    "Programming Languages",
    "Cybersecurity",
    "Networking",
    "Operating Systems",
    "Testing",
    "Version Control",
    "Frontend",
    "Backend",
    "Mobile Development",
    "Data Science",
    "Soft Skills"
]


def classify_skill_by_taxonomy(skill_name: str) -> str:
    """Classifies a standardized skill name into the most specific taxonomy category.

    Args:
        skill_name: The normalized name of the technology/skill.

    Returns:
        str: Category name matching CATEGORIES, defaulting to "Other".
    """
    clean_name = skill_name.strip().lower()
    
    # 1. First look for exact match across all categories
    for cat in CATEGORY_PRIORITY:
        keywords = TAXONOMY_PATTERNS.get(cat, [])
        if clean_name in keywords:
            return cat
            
    # 2. Substring matching if exact match not found
    for cat in CATEGORY_PRIORITY:
        keywords = TAXONOMY_PATTERNS.get(cat, [])
        for kw in keywords:
            if f" {clean_name} " in f" {kw} " or f" {kw} " in f" {clean_name} ":
                return cat
                
    return "Other"
