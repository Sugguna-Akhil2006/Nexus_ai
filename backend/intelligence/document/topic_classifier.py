"""Automatically classifies texts into Technical, Legal, Cybersecurity, AI/ML, and other domains."""

import re
from typing import List, Dict, Any, Optional
from backend.intelligence.document.document_model import Topic


class TopicClassifier:
    """Classifies document texts into domain topics based on token counts."""

    def __init__(self) -> None:
        self.categories = {
            "Software Engineering": {"code", "architecture", "software", "repository", "class", "function", "git", "developer", "programming", "codebase", "compile", "design"},
            "AI/ML": {"ai", "machine learning", "deep learning", "neural", "model", "inference", "dataset", "training", "pytorch", "openai", "transformers", "llm", "predict"},
            "Cloud": {"docker", "kubernetes", "deployment", "aws", "gcp", "azure", "microservices", "cloud", "server", "hosting", "instance", "scaling"},
            "Technical": {"standards", "api", "json", "csv", "pdf", "xml", "binary", "database", "query", "parsing", "schema", "metadata"},
            "Business": {"product", "companies", "clients", "organization", "commercial", "marketing", "sales", "revenue", "strategy", "enterprise"},
            "Legal": {"agreement", "law", "legal", "policy", "compliance", "terms", "conditions", "copyright", "contract", "regulation", "appendix"},
            "Research": {"paper", "thesis", "method", "academic", "evaluation", "research", "experiment", "findings", "hypothesis", "citation", "reference"},
            "Meeting Notes": {"meeting", "minutes", "discussion", "attendees", "notes", "agenda", "action items", "notes", "schedule"},
            "Financial": {"transaction", "financial", "billing", "gateway", "payment", "cost", "invoice", "revenue", "price", "budget"},
            "Healthcare": {"patient", "clinical", "medical", "healthcare", "disease", "treatment", "doctor", "health", "hospital"},
            "Cybersecurity": {"security", "encryption", "secure", "vulnerability", "authentication", "cyber", "hack", "threat", "breach", "firewall"}
        }

    def classify_topics(self, text: str, custom_categories: Optional[List[str]] = None) -> List[Topic]:
        """Classifies text content and returns top matching topics with confidence weights.

        Args:
            text: Ingested document content string.
            custom_categories: Optional override keywords.

        Returns:
            List[Topic]: Classifed Topics.
        """
        text_lower = text.lower()
        scores = {}

        # 1. Standard categories scoring
        for category, keywords in self.categories.items():
            score = 0
            for kw in keywords:
                # Count keyword matches
                matches = len(re.findall(r'\b' + re.escape(kw) + r'\b', text_lower))
                score += matches
            if score > 0:
                scores[category] = score

        # 2. Custom categories if supplied
        if custom_categories:
            for cat in custom_categories:
                matches = len(re.findall(r'\b' + re.escape(cat.lower()) + r'\b', text_lower))
                if matches > 0:
                    scores[cat.title()] = matches

        # Sort classifications by score
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_cats:
            return [Topic(name="General", weight=0.5, description="General category classification.")]

        topics = []
        max_score = sorted_cats[0][1]
        
        for name, score in sorted_cats[:4]:
            weight = score / max_score
            topics.append(Topic(
                name=name,
                weight=round(weight, 2),
                description=f"Auto-classified theme based on keyword match occurrences ({score} hits)."
            ))
            
        return topics
