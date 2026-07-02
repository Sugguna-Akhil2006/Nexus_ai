"""Parses configuration manifests into flat libraries dependency mapping structures."""

import json
import re
from typing import Dict
from backend.intelligence.github.models import DependencyNode
from backend.intelligence.github.repository import GitRepositoryReader


class DependencyAnalyzer:
    """Analyzes requirements.txt, package.json, and other config manifests into DependencyNode maps."""

    def analyze_dependencies(self, reader: GitRepositoryReader) -> Dict[str, DependencyNode]:
        """Scans workspace config files to return dependencies.

        Args:
            reader: Workspace reader context.

        Returns:
            Dict[str, DependencyNode]: Library mapped dependencies.
        """
        deps: Dict[str, DependencyNode] = {}
        files = reader.scan_files()

        for f in files:
            basename = os.path.basename(f).lower()
            
            if basename == "requirements.txt":
                content = reader.read_file(f)
                for line in content.splitlines():
                    line_clean = line.strip()
                    if not line_clean or line_clean.startswith("#"):
                        continue
                    # Parse name and version (e.g. fastapi==0.100.0 or django>=4.0)
                    match = re.split(r"==|>=|<=|>|<|~=", line_clean)
                    name = match[0].strip()
                    version = match[1].strip() if len(match) > 1 else None
                    deps[name.lower()] = DependencyNode(
                        name=name,
                        version=version,
                        license="Open Source"
                    )

            elif basename == "package.json":
                content = reader.read_file(f)
                try:
                    data = json.loads(content)
                    dependencies = data.get("dependencies", {})
                    devDependencies = data.get("devDependencies", {})
                    
                    all_deps = {**dependencies, **devDependencies}
                    for name, version in all_deps.items():
                        deps[name.lower()] = DependencyNode(
                            name=name,
                            version=str(version).replace("^", "").replace("~", ""),
                            license="NPM Open Source"
                        )
                except Exception:
                    pass

            elif basename == "go.mod":
                content = reader.read_file(f)
                for line in content.splitlines():
                    line_clean = line.strip()
                    if line_clean.startswith("require"):
                        # Single line or block start
                        if "(" in line_clean:
                            continue
                        parts = line_clean.split()
                        if len(parts) >= 3:
                            name = parts[1]
                            version = parts[2]
                            deps[name.lower()] = DependencyNode(
                                name=name,
                                version=version,
                                license="Go Open Source"
                            )
                    elif not line_clean.startswith("module") and not line_clean.startswith("go") and not line_clean.startswith(")") and len(line_clean.split()) >= 2:
                        parts = line_clean.split()
                        name = parts[0]
                        version = parts[1]
                        deps[name.lower()] = DependencyNode(
                            name=name,
                            version=version,
                            license="Go Open Source"
                        )

        return deps

import os # Need this for os.path
