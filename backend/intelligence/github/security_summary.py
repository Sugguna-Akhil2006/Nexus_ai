"""Scans configuration files and Docker files for exposed credentials or security flags."""

from typing import List
from backend.intelligence.github.models import QualityImprovement
from backend.intelligence.github.repository import GitRepositoryReader


class SecurityConfigurationScanner:
    """Scans settings, environment templates, and Dockerfiles for insecure flags."""

    def scan_security(self, reader: GitRepositoryReader) -> List[QualityImprovement]:
        """Runs rule checks for hardcoded credentials or insecure root commands.

        Args:
            reader: Workspace reader.

        Returns:
            List[QualityImprovement]: Identified security improvement alerts.
        """
        files = reader.scan_files()
        improvements = []

        for f in files:
            basename = os.path.basename(f).lower()
            content = reader.read_file(f)
            
            # 1. Dockerfile root user check
            if "dockerfile" in basename:
                if "user root" in content.lower():
                    improvements.append(QualityImprovement(
                        rule_id="SEC-001",
                        priority="High",
                        file_path=f,
                        issue_type="Security",
                        description="Dockerfile sets user to root. Running applications as root increases vulnerability risk.",
                        suggested_fix="Define a non-root user (e.g. 'USER node' or 'USER appuser') in the Dockerfile."
                    ))

            # 2. Raw secrets check (simple API key / Token regex)
            if f.endswith((".py", ".js", ".ts", ".json", ".env")):
                import re
                key_pattern = r"(api_key|client_secret|token|password)\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"
                matches = re.findall(key_pattern, content.lower())
                if matches:
                    improvements.append(QualityImprovement(
                        rule_id="SEC-002",
                        priority="High",
                        file_path=f,
                        issue_type="Security",
                        description="Possible exposed hardcoded credential or secret key discovered.",
                        suggested_fix="Move the hardcoded credential to an external environment variable configuration (.env)."
                    ))

        return improvements

import os
