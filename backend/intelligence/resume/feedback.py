"""Feedback compiler, strengths extractor, and recommendation generator for ATS reports."""

from typing import List, Tuple
from backend.intelligence.resume.models import ATSCategoryScore

class FeedbackCompiler:
    """Consolidates category-specific findings into overall qualitative feedback arrays."""

    def compile_feedback(
        self, 
        categories: List[ATSCategoryScore]
    ) -> Tuple[List[str], List[str], List[str], List[str]]:
        """Extracts strengths, weaknesses, priority improvements, and detailed recommendations.

        Args:
            categories: List of scored categories.

        Returns:
            Tuple: (strengths, weaknesses, priority_improvements, detailed_recommendations).
        """
        strengths = []
        weaknesses = []
        priority_improvements = []
        detailed_recommendations = []

        # Sort categories by score to identify priorities
        sorted_categories = sorted(categories, key=lambda c: c.current_score)

        for cat in categories:
            # 1. Strengths (Scores >= 85)
            if cat.current_score >= 85.0:
                strengths.append(f"[{cat.name}]: {cat.reason}")
            # 2. Weaknesses (Scores < 75)
            elif cat.current_score < 75.0:
                weaknesses.append(f"[{cat.name}]: {cat.reason}")
                
            # 3. Compile Detailed Recommendations
            for suggestion in cat.improvement_suggestions:
                detailed_recommendations.append(f"[{cat.name}] {suggestion}")

        # 4. Extract Top 3-4 Priority Improvements from lowest scored categories
        for cat in sorted_categories:
            if cat.current_score < 85.0 and cat.improvement_suggestions:
                for sugg in cat.improvement_suggestions:
                    if len(priority_improvements) < 4:
                        priority_improvements.append(sugg)
                        
        # Fallbacks if empty
        if not strengths:
            strengths.append("Structured profile information parsed successfully.")
        if not weaknesses:
            weaknesses.append("No critical ATS compliance blocker gaps found.")
        if not priority_improvements:
            priority_improvements.append("Maintain high-quality standards by continually updating skills and project metrics.")
            
        return strengths, weaknesses, priority_improvements, detailed_recommendations
