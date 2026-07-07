"""Artifact collector — aggregates, deduplicates, and ranks artifacts from all modules."""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from backend.intelligence.contracts.response_models import Artifact, IntelligenceResponse


class ArtifactCollector:
    """Collects and deduplicates artifacts from multiple ``IntelligenceResponse`` objects.

    Deduplication key: ``(artifact_type, name)`` — if two modules produce an
    artifact with the same type and name, the one from the higher-confidence
    module is retained.
    """

    @staticmethod
    def collect(
        responses: List[IntelligenceResponse],
    ) -> List[Artifact]:
        """Merges artifacts from all responses, deduplicating by (type, name).

        Args:
            responses: Module responses whose artifacts should be collected.

        Returns:
            Deduplicated artifact list, ordered by module confidence descending.
        """
        # Sort responses by confidence so high-confidence artefacts win dedup
        sorted_responses = sorted(
            responses, key=lambda r: r.confidence, reverse=True
        )

        seen: Set[tuple] = set()
        collected: List[Artifact] = []

        for resp in sorted_responses:
            for art in resp.artifacts:
                key = (art.artifact_type, art.name)
                if key in seen:
                    continue
                seen.add(key)
                collected.append(art)

        return collected

    @staticmethod
    def filter_by_type(
        artifacts: List[Artifact],
        artifact_type: str,
    ) -> List[Artifact]:
        """Filters artifacts to a specific type.

        Args:
            artifacts:     Full artifact list.
            artifact_type: e.g. "report", "chart_data", "json_export", "markdown".

        Returns:
            Filtered list preserving order.
        """
        return [a for a in artifacts if a.artifact_type == artifact_type]

    @staticmethod
    def build_manifest(artifacts: List[Artifact]) -> List[Dict[str, str]]:
        """Builds a lightweight manifest (id, name, type, mime_type) for the composed response header.

        Args:
            artifacts: Collected artifacts.

        Returns:
            List of dicts suitable for embedding in JSON responses.
        """
        return [
            {
                "artifact_id": a.artifact_id,
                "name": a.name,
                "artifact_type": a.artifact_type,
                "mime_type": a.mime_type,
            }
            for a in artifacts
        ]
