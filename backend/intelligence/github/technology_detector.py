"""Detects programming languages, databases, web frameworks, queues, and tools."""

import os
from typing import List
from backend.intelligence.github.models import TechnologyInfo
from backend.intelligence.github.repository import GitRepositoryReader


class TechnologyDetector:
    """Detects technological stacks used in code bases based on file extensions and contents."""

    def detect_technologies(self, reader: GitRepositoryReader) -> List[TechnologyInfo]:
        """Scans workspace files to build technology info list.

        Args:
            reader: Workspace reader.

        Returns:
            List[TechnologyInfo]: List of identified stacks.
        """
        files = reader.scan_files()
        techs = []

        # 1. Languages by extensions
        ext_map = {
            ".py": ("Python", "Language"),
            ".js": ("JavaScript", "Language"),
            ".ts": ("TypeScript", "Language"),
            ".tsx": ("React/TypeScript", "Framework"),
            ".jsx": ("React/JavaScript", "Framework"),
            ".go": ("Go", "Language"),
            ".rs": ("Rust", "Language"),
            ".java": ("Java", "Language"),
            ".cpp": ("C++", "Language"),
            ".cs": ("C#", "Language"),
            ".rb": ("Ruby", "Language"),
            ".php": ("PHP", "Language"),
            ".sh": ("Shell Script", "Tool")
        }

        found_exts = set()
        for f in files:
            _, ext = os.path.splitext(f.lower())
            if ext in ext_map:
                found_exts.add(ext)

        for ext in found_exts:
            name, category = ext_map[ext]
            techs.append(TechnologyInfo(
                name=name,
                category=category,
                confidence=0.9
            ))

        # 2. Frameworks and tools based on key project configuration file existence
        config_files = {
            "requirements.txt": ("Python Backend Stack", "Package Configuration"),
            "pipfile": ("Pipenv Python Stack", "Package Configuration"),
            "pyproject.toml": ("Poetry Python Stack", "Package Configuration"),
            "package.json": ("NodeJS Stack", "Runtime Environment"),
            "cargo.toml": ("Cargo Rust Stack", "Package Configuration"),
            "dockerfile": ("Docker Containerization", "DevOps"),
            "docker-compose.yml": ("Docker Compose Multi-container", "DevOps"),
            "go.mod": ("Go Module Management", "Package Configuration"),
            "pom.xml": ("Maven Java Stack", "Package Configuration"),
            "build.gradle": ("Gradle Java Stack", "Package Configuration")
        }

        for f in files:
            basename = os.path.basename(f).lower()
            if basename in config_files:
                name, category = config_files[basename]
                techs.append(TechnologyInfo(
                    name=name,
                    category=category,
                    confidence=1.0
                ))

            # Read content for deeper discovery (Frameworks/Libraries)
            content = ""
            if basename == "requirements.txt":
                content = reader.read_file(f).lower()
                if "django" in content:
                    techs.append(TechnologyInfo(name="Django", category="Framework", confidence=1.0))
                if "fastapi" in content:
                    techs.append(TechnologyInfo(name="FastAPI", category="Framework", confidence=1.0))
                if "flask" in content:
                    techs.append(TechnologyInfo(name="Flask", category="Framework", confidence=1.0))
                if "numpy" in content or "pandas" in content:
                    techs.append(TechnologyInfo(name="Data Science Stack", category="Libraries", confidence=0.9))
                if "torch" in content or "tensorflow" in content:
                    techs.append(TechnologyInfo(name="AI/ML Stack", category="Libraries", confidence=0.95))

            elif basename == "package.json":
                content = reader.read_file(f).lower()
                if "react" in content:
                    techs.append(TechnologyInfo(name="React", category="Framework", confidence=1.0))
                if "vue" in content:
                    techs.append(TechnologyInfo(name="Vue", category="Framework", confidence=1.0))
                if "next" in content:
                    techs.append(TechnologyInfo(name="Next.js", category="Framework", confidence=1.0))
                if "express" in content:
                    techs.append(TechnologyInfo(name="Express.js", category="Framework", confidence=1.0))

            elif basename == "go.mod":
                content = reader.read_file(f).lower()
                if "gin-gonic" in content:
                    techs.append(TechnologyInfo(name="Gin", category="Framework", confidence=1.0))

        # Filter duplicates (e.g. if React was found from tsx and package.json)
        unique_techs = {}
        for t in techs:
            unique_techs[t.name] = t
            
        return list(unique_techs.values())
