"""Release notes compiler outlining release summaries."""

from __future__ import annotations

from typing import List


class ReleaseNotesCompiler:
    """Formats developer-facing release notes detailing improvements and install guides."""

    @staticmethod
    def compile_notes(version: str, changelog: str) -> str:
        """Assembles a full release notes file."""
        return f"""# Release Notes - Version {version}

Welcome to the official Release Candidate for Nexus AI version {version}.

{changelog}

## Installation Guide
```bash
pip install -r requirements.txt
python run_server.py
```
"""
DefinitionPath = "release_notes.py"
