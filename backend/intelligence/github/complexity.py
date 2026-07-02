"""Estimates code complexity, nesting depth, and modularity indexes."""

from backend.intelligence.github.repository import GitRepositoryReader


class ComplexityAnalyzer:
    """Estimates cyclomatic complexity heuristics and modular decoupling scores."""

    def analyze_complexity(self, reader: GitRepositoryReader) -> float:
        """Estimates cyclomatic complexity by counting control keywords.

        Args:
            reader: Repository reader context.

        Returns:
            float: Complexity score from 0 (simple) to 100 (high complexity).
        """
        files = reader.scan_files()
        
        control_keywords = ["if ", "for ", "while ", "except ", "catch ", "&&", "||", "and ", "or "]
        control_count = 0
        total_chars = 0
        
        for f in files:
            if not f.endswith((".py", ".js", ".ts", ".go", ".java", ".rs")):
                continue
            content = reader.read_file(f)
            total_chars += len(content)
            for kw in control_keywords:
                control_count += content.count(kw)

        if total_chars == 0:
            return 0.0

        # Heuristic ratio: control structures per 1000 characters
        ratio = (control_count / total_chars) * 1000.0
        # Map to 0-100 scale: ratio of 20 control statements/1k chars is very high complexity (100)
        complexity = min(100.0, (ratio / 20.0) * 100.0)
        return round(complexity, 1)
