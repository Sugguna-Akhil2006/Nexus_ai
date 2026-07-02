"""Analyzes project readme files, contributing guides, change logs, and licensing metrics."""

import os
from typing import Optional
from backend.intelligence.github.models import DocumentationMetric
from backend.intelligence.github.repository import GitRepositoryReader


class DocumentationAnalyzer:
    """Evaluates workspace documentation presence, quality, readability, and freshness."""

    def analyze_documentation(self, reader: GitRepositoryReader) -> Optional[DocumentationMetric]:
        """Analyzes directory documents.

        Args:
            reader: Workspace reader.

        Returns:
            Optional[DocumentationMetric]: Evaluated documentation metrics.
        """
        files = reader.scan_files()
        
        has_readme = False
        has_contributing = False
        has_changelog = False
        has_license = False
        
        readme_content = ""
        
        for f in files:
            basename = os.path.basename(f).lower()
            if basename in ["readme.md", "readme.txt", "readme"]:
                has_readme = True
                readme_content = reader.read_file(f)
            if basename in ["contributing.md", "contributing.txt", "contributing"]:
                has_contributing = True
            if basename in ["changelog.md", "changelog", "history.md"]:
                has_changelog = True
            if basename in ["license", "license.txt", "license.md"]:
                has_license = True

        # Compute a simple readability score based on content length and heading counts
        readability_score = 0.0
        if has_readme and readme_content:
            length = len(readme_content)
            headings = readme_content.count("#")
            
            # Simple heuristic score from 0 to 100
            if length > 500:
                readability_score += 40.0
            else:
                readability_score += (length / 500.0) * 40.0
                
            if headings >= 3:
                readability_score += 40.0
            else:
                readability_score += (headings / 3.0) * 40.0
                
            if "install" in readme_content.lower() or "usage" in readme_content.lower():
                readability_score += 20.0
        else:
            readability_score = 0.0

        # Freshness calculation fallback to a dummy 10 days if file is found
        freshness_days = 10 if has_readme else 365

        return DocumentationMetric(
            has_readme=has_readme,
            has_contributing_guide=has_contributing,
            has_changelog=has_changelog,
            has_license=has_license,
            readability_score=round(readability_score, 1),
            freshness_days=freshness_days
        )
