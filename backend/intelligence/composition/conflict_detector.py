"""Conflict detector — surfaces disagreements between module structured outputs."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.intelligence.composition.models import ConflictRecord, ConflictSeverity
from backend.intelligence.contracts.response_models import IntelligenceResponse


class ConflictDetector:
    """Detects field-level conflicts between pairs of intelligence module responses.

    Compares the ``structured_output`` dicts of each module pair and
    records disagreements with supporting evidence and severity.
    Confidence difference is used to classify severity:

    - |delta| < 0.05  → LOW
    - |delta| < 0.15  → MEDIUM
    - |delta| < 0.30  → HIGH
    - |delta| >= 0.30 → CRITICAL
    """

    # Numeric delta thresholds used to classify severity
    _THRESHOLDS = [
        (0.30, ConflictSeverity.CRITICAL),
        (0.15, ConflictSeverity.HIGH),
        (0.05, ConflictSeverity.MEDIUM),
        (0.00, ConflictSeverity.LOW),
    ]

    @classmethod
    def detect(
        cls,
        responses: List[IntelligenceResponse],
    ) -> List[ConflictRecord]:
        """Scans all response pairs for disagreements in shared output keys.

        Args:
            responses: List of module ``IntelligenceResponse`` objects.

        Returns:
            List of ``ConflictRecord`` objects, one per disagreement.
        """
        conflicts: List[ConflictRecord] = []

        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                a, b = responses[i], responses[j]
                pair_conflicts = cls._compare_pair(a, b)
                conflicts.extend(pair_conflicts)

        return conflicts

    @classmethod
    def _compare_pair(
        cls,
        a: IntelligenceResponse,
        b: IntelligenceResponse,
    ) -> List[ConflictRecord]:
        """Compares two module responses and returns all conflicts."""
        conflicts: List[ConflictRecord] = []
        shared_keys = set(a.structured_output.keys()) & set(b.structured_output.keys())

        for key in shared_keys:
            val_a = a.structured_output[key]
            val_b = b.structured_output[key]

            if val_a == val_b:
                continue  # no conflict

            severity = cls._classify_severity(val_a, val_b, a.confidence, b.confidence)
            explanation = cls._explain(key, val_a, val_b, a.module, b.module)

            conflicts.append(ConflictRecord(
                field=key,
                module_a=a.module,
                module_b=b.module,
                value_a=val_a,
                value_b=val_b,
                severity=severity,
                explanation=explanation,
            ))

        return conflicts

    @classmethod
    def _classify_severity(
        cls,
        val_a: Any,
        val_b: Any,
        conf_a: float,
        conf_b: float,
    ) -> ConflictSeverity:
        """Classifies conflict severity based on confidence delta."""
        delta = abs(conf_a - conf_b)
        for threshold, severity in cls._THRESHOLDS:
            if delta >= threshold:
                return severity
        return ConflictSeverity.LOW

    @staticmethod
    def _explain(
        field: str,
        val_a: Any,
        val_b: Any,
        mod_a: str,
        mod_b: str,
    ) -> str:
        """Generates a human-readable conflict explanation."""
        return (
            f"Field '{field}': {mod_a} reports {val_a!r} while "
            f"{mod_b} reports {val_b!r}. "
            "Review supporting evidence to determine which value is more reliable."
        )

    @staticmethod
    def resolve_by_confidence(
        conflict: ConflictRecord,
        responses: List[IntelligenceResponse],
    ) -> ConflictRecord:
        """Resolves a conflict by selecting the higher-confidence module's value.

        Args:
            conflict: The ``ConflictRecord`` to resolve.
            responses: All module responses (used to look up confidence).

        Returns:
            Updated ``ConflictRecord`` with ``resolved=True`` and resolution note.
        """
        conf_map: Dict[str, float] = {r.module: r.confidence for r in responses}
        conf_a = conf_map.get(conflict.module_a, 0.0)
        conf_b = conf_map.get(conflict.module_b, 0.0)
        winner = conflict.module_a if conf_a >= conf_b else conflict.module_b
        conflict.resolved = True
        conflict.resolution_note = (
            f"Resolved in favour of '{winner}' "
            f"(confidence {conf_map.get(winner, 0.0):.2f} vs "
            f"{conf_map.get(conflict.module_b if winner == conflict.module_a else conflict.module_a, 0.0):.2f})."
        )
        return conflict
