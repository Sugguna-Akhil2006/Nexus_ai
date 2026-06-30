"""Confidence scoring utilities and source weighting models for extracted skills."""

from typing import Dict

# Source baseline confidence weights
SOURCE_BASE_CONFIDENCE: Dict[str, float] = {
    "Explicit Skills": 0.95,
    "Certifications": 0.90,
    "Work Experience": 0.85,
    "Projects": 0.80,
    "Publications": 0.80,
    "Education": 0.70,
    "Inference": 0.60
}


def calculate_confidence(source: str, explicit_or_inferred: str, frequency: int) -> float:
    """Calculates confidence score based on source weights and appearance frequency.

    Args:
        source: Origin of extraction ("Explicit Skills", "Projects", etc.).
        explicit_or_inferred: Status string ("Explicit" or "Inferred").
        frequency: Number of occurrences found.

    Returns:
        float: Calculated score between 0.0 and 1.0.
    """
    base = SOURCE_BASE_CONFIDENCE.get(source, 0.50)
    
    # Inferred skills are slightly penalized if frequency is 1
    if explicit_or_inferred == "Inferred" and source == "Inference":
        base = 0.80  # Default high confidence inference base as required by prompt
        
    # Boost confidence based on frequency
    boost = max(0, (frequency - 1) * 0.05)
    
    score = base + boost
    return min(1.0, max(0.0, score))
