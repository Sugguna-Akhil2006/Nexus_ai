"""Project scaffolder generating boilerplate project structures."""

from __future__ import annotations

import os
from typing import List

from backend.idp.models import ScaffoldRequest, ScaffoldResult, ScaffoldType


class ProjectScaffolder:
    """Generates standard boilerplate folder layout and code structures."""

    @staticmethod
    def scaffold(request: ScaffoldRequest, base_workspace: str) -> ScaffoldResult:
        """Scaffolds boilerplate directories and files safely.

        Args:
            request: Scaffolding configuration.
            base_workspace: Base workspace folder directory path.

        Returns:
            ScaffoldResult.
        """
        if not request.name:
            return ScaffoldResult(success=False, message="Component name cannot be empty.")

        # Clean component name
        name_clean = request.name.lower().replace(" ", "_").strip()
        target_dir = os.path.abspath(os.path.join(base_workspace, request.target_directory or "generated", name_clean))

        try:
            os.makedirs(target_dir, exist_ok=True)
            generated_files = []

            # 1. Initialize file
            init_file = os.path.join(target_dir, "__init__.py")
            with open(init_file, "w") as f:
                f.write(f'"""{request.name} {request.scaffold_type.value} component."""\n')
            generated_files.append(os.path.basename(init_file))

            # 2. Add models file
            models_file = os.path.join(target_dir, "models.py")
            with open(models_file, "w") as f:
                f.write('"""Pydantic model definitions."""\nfrom pydantic import BaseModel\n\n\nclass ComponentConfig(BaseModel):\n    enabled: bool = True\n')
            generated_files.append(os.path.basename(models_file))

            # 3. Add tests folder
            tests_dir = os.path.join(target_dir, "tests")
            os.makedirs(tests_dir, exist_ok=True)
            test_file = os.path.join(tests_dir, f"test_{name_clean}.py")
            with open(test_file, "w") as f:
                f.write('"""Unit tests."""\nimport unittest\n\n\nclass TestComponent(unittest.TestCase):\n    def test_running(self):\n        self.assertTrue(True)\n')
            generated_files.append(f"tests/{os.path.basename(test_file)}")

            return ScaffoldResult(
                success=True,
                generated_files=generated_files,
                message=f"Successfully scaffolded {request.scaffold_type.value} '{request.name}' at: {target_dir}",
            )

        except Exception as e:
            return ScaffoldResult(success=False, message=f"Scaffolding failed: {e}")
DefinitionPath = "project_scaffolder.py"
