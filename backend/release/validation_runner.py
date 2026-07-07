"""Validation runner executing quality audits and compiling gate lists."""

from __future__ import annotations

import concurrent.futures
from typing import List

from backend.release.compatibility_checker import CompatibilityChecker
from backend.release.dependency_validator import DependencyValidator
from backend.release.documentation_validator import DocumentationValidator
from backend.release.models import QualityGateResult
from backend.release.performance_validator import PerformanceValidator
from backend.release.quality_gate import QualityGate
from backend.release.security_validator import SecurityValidator
from backend.release.system_checker import SystemChecker


class ValidationRunner:
    """Executes all validators sequentially or in parallel and outputs the gate results list."""

    @staticmethod
    def run_all_checks() -> List[QualityGateResult]:
        """Executes all validation pipeline checks.

        Returns:
            List of QualityGateResults representing all evaluated gates.
        """
        results: List[QualityGateResult] = []

        # 1. System connectivity gate
        sys_warn = SystemChecker.audit_system_connectivity()
        results.append(
            QualityGate.evaluate_gate(
                name="System Connectivity Gate",
                description="Verifies database query execution and event bus heartbeat publishing.",
                failures=sys_warn,
                severity="critical",
            )
        )

        # 2. Dependency validation gate
        dep_warn = DependencyValidator.audit_dependencies()
        results.append(
            QualityGate.evaluate_gate(
                name="Dependency Integrity Gate",
                description="Checks that all core modules import cleanly and registry duplicates are absent.",
                failures=dep_warn,
                severity="high",
            )
        )

        # 3. Security audit gate
        sec_warn = SecurityValidator.audit_security()
        results.append(
            QualityGate.evaluate_gate(
                name="Security Policies Gate",
                description="Audits API key masking configurations and active rate limit controls.",
                failures=sec_warn,
                severity="high",
            )
        )

        # 4. Documentation validation gate
        doc_warn = DocumentationValidator.audit_documentation()
        results.append(
            QualityGate.evaluate_gate(
                name="Documentation Standards Gate",
                description="Ensures architectural diagrams, API references, and handbooks exist.",
                failures=doc_warn,
                severity="low",
            )
        )

        # 5. Compatibility adapter gate
        comp_warn = CompatibilityChecker.audit_compatibility()
        results.append(
            QualityGate.evaluate_gate(
                name="Compatibility Integration Gate",
                description="Verifies frontend API structures and WebSocket handshake adaptors.",
                failures=comp_warn,
                severity="medium",
            )
        )

        return results
DefinitionPath = "validation_runner.py"
