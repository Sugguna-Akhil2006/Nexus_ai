"""Scoring rules, categories configuration, and weights for ATS analysis."""

from typing import Dict, TypedDict

class CategoryConfig(TypedDict):
    weight: float
    max_score: int

# Configuration for the 11 evaluation categories
SCORING_CATEGORIES: Dict[str, CategoryConfig] = {
    "Contact Information Completeness": {"weight": 0.05, "max_score": 100},
    "Link Validation": {"weight": 0.10, "max_score": 100},
    "Section Completeness": {"weight": 0.15, "max_score": 100},
    "Keyword Coverage": {"weight": 0.15, "max_score": 100},
    "Skill Diversity": {"weight": 0.10, "max_score": 100},
    "Experience Quality": {"weight": 0.10, "max_score": 100},
    "Project Quality": {"weight": 0.10, "max_score": 100},
    "Education Completeness": {"weight": 0.05, "max_score": 100},
    "Certification Quality": {"weight": 0.05, "max_score": 100},
    "Formatting Quality": {"weight": 0.10, "max_score": 100},
    "Readability": {"weight": 0.05, "max_score": 100}
}
