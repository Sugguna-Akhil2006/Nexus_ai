"""PromptBuilder - versioned prompt template construction and rendering."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from sdk.adk.models import PromptTemplate


class PromptBuilder:
    """Fluent builder for constructing and validating prompt templates.

    Example::

        prompt = (
            PromptBuilder()
            .name("resume_summary")
            .version("1.0.0")
            .template("Summarize the following resume for {job_title}: {resume_text}")
            .variables(["job_title", "resume_text"])
            .build()
        )

        rendered = prompt.render(
            job_title="Software Engineer",
            resume_text="John Doe, 5 years Python..."
        )
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._version: str = "1.0.0"
        self._template: str = ""
        self._variables: List[str] = []

    def name(self, template_name: str) -> "PromptBuilder":
        """Sets the prompt template identifier.

        Args:
            template_name: Unique name string.

        Returns:
            Self for method chaining.
        """
        self._name = template_name
        return self

    def version(self, semver: str) -> "PromptBuilder":
        """Sets the template semantic version.

        Args:
            semver: Semantic version string.

        Returns:
            Self for method chaining.
        """
        self._version = semver
        return self

    def template(self, template_str: str) -> "PromptBuilder":
        """Sets the raw template string.

        Placeholders use Python format syntax: ``{variable_name}``.

        Args:
            template_str: Template string with ``{var}`` placeholders.

        Returns:
            Self for method chaining.
        """
        self._template = template_str
        # Auto-extract variable names from template
        found = re.findall(r"\{(\w+)\}", template_str)
        self._variables = list(dict.fromkeys(found))  # deduplicate while preserving order
        return self

    def variables(self, var_names: List[str]) -> "PromptBuilder":
        """Explicitly sets the expected variable list.

        Overrides auto-detected variables from the template string.

        Args:
            var_names: List of variable name strings.

        Returns:
            Self for method chaining.
        """
        self._variables = list(var_names)
        return self

    def validate(self) -> List[str]:
        """Validates the template, returning a list of detected issues.

        Returns:
            List of validation error strings (empty means valid).
        """
        issues: List[str] = []
        if not self._name.strip():
            issues.append("Prompt template name is required.")
        if not self._template.strip():
            issues.append("Prompt template string is required.")
        # Check all declared variables appear in template
        for var in self._variables:
            if f"{{{var}}}" not in self._template:
                issues.append(f"Variable '{var}' declared but not found in template.")
        return issues

    def build(self) -> PromptTemplate:
        """Validates and constructs the PromptTemplate.

        Returns:
            PromptTemplate instance.

        Raises:
            ValueError: If validation fails.
        """
        issues = self.validate()
        if issues:
            raise ValueError(f"Prompt validation failed: {'; '.join(issues)}")

        return PromptTemplate(
            name=self._name,
            version=self._version,
            template=self._template,
            variables=list(self._variables),
        )
