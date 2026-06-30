"""Gap Analysis engine extracting missing attributes and sorting by score weight impact."""

from typing import List
from backend.intelligence.resume.models import JDCategoryMatch


class GapAnalyzer:
    """Extracts missing evidence from category matches and formats them by weight impact."""

    def analyze_gaps(self, category_matches: List[JDCategoryMatch]) -> List[str]:
        """Prioritizes candidate gaps by category weight impact.

        Args:
            category_matches: Calculated match metrics.

        Returns:
            List[str]: Prioritized gap statements.
        """
        gaps = []

        # Sort categories by weight in descending order
        sorted_matches = sorted(category_matches, key=lambda m: m.weight, reverse=True)

        for match in sorted_matches:
            if not match.missing_evidence:
                continue

            # Classify impact level based on weight limits
            if match.weight >= 0.15:
                impact = "High Impact"
            elif match.weight >= 0.10:
                impact = "Medium Impact"
            else:
                impact = "Low Impact"

            for miss in match.missing_evidence:
                # Strip prefix for cleaner reporting if present
                clean_miss = miss.replace("Missing target:", "").replace("Missing certification:", "").strip()
                gaps.append(f"[{impact} - {match.category_name}] Missing requirement: {clean_miss}")

        if not gaps:
            gaps.append("[Maintain standard] No critical competency gaps identified against the Job Description.")

        return gaps
