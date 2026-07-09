"""Documentation generator compiling module guides and API docs."""

from __future__ import annotations


class DocumentationGenerator:
    """Assembles developer READMEs and API guides for new scaffolding packages."""

    @staticmethod
    def generate_readme(name: str, scaffold_type: str, description: str) -> str:
        """Returns standard README documentation for the component."""
        return f"""# {name} ({scaffold_type.title()})

{description or 'No description provided.'}

## Overview
This is a standard {scaffold_type} component auto-scaffolded by the Internal Developer Platform (IDP).

## Usage
Import the package and register its service interfaces:
```python
from backend.generated.{name.lower()}.models import ComponentConfig
```

## Testing
Run unit tests for the component:
```bash
python -m unittest backend.generated.{name.lower()}.tests.test_{name.lower()}
```
"""
DefinitionPath = "documentation_generator.py"
