"""Artifact serializer for frontend artifact exports and download delivery.

Handles serialization and file wrapping of structured output artifacts
(JSON, CSV, markdown, text) and creates secure download descriptors.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional

from backend.intelligence.contracts.response_models import Artifact
from backend.integration.frontend_contracts import ArtifactDownload


class ArtifactSerializer:
    """Serializes AI-generated artifacts for frontend representation and download."""

    @staticmethod
    def to_download(
        artifact: Artifact,
        base_url: str = "/api/artifacts",
        expires_in_seconds: int = 3600,
    ) -> ArtifactDownload:
        """Converts an Artifact contract into an ArtifactDownload descriptor."""
        return ArtifactDownload(
            artifact_id=artifact.artifact_id,
            name=artifact.name,
            artifact_type=artifact.artifact_type,
            mime_type=artifact.mime_type or "application/octet-stream",
            download_url=f"{base_url}/{artifact.artifact_id}",
            size_bytes=artifact.size_bytes or len(ArtifactSerializer.serialize_content(artifact)),
        )

    @staticmethod
    def serialize_content(artifact: Artifact) -> bytes:
        """Serializes the artifact's raw content into bytes based on mime/type.

        Args:
            artifact: The Artifact contract containing content.

        Returns:
            Bytes representation of the artifact content.
        """
        content = artifact.content
        mime = artifact.mime_type

        if isinstance(content, bytes):
            return content

        if mime == "application/json" or isinstance(content, (dict, list)):
            return json.dumps(content, indent=2, default=str).encode("utf-8")

        if isinstance(content, str):
            # Check if it is base64 encoded
            if content.startswith("data:") and ";base64," in content:
                _, b64data = content.split(";base64,", 1)
                try:
                    return base64.b64decode(b64data)
                except Exception:
                    pass
            return content.encode("utf-8")

        return str(content).encode("utf-8")
