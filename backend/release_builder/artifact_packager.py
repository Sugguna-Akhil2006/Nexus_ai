"""Artifact packager compressing release targets into zip distributions."""

from __future__ import annotations

import io
import zipfile
from typing import List

from backend.release_builder.checksum_generator import ChecksumGenerator
from backend.release_builder.models import ReleaseArtifact


class ArtifactPackager:
    """Simulates compressing files and cataloging artifact metadata records."""

    @staticmethod
    def package_bundle(
        name: str,
        artifact_type: str,
        files: dict[str, str],
    ) -> ReleaseArtifact:
        """Packages a collection of virtual files into an in-memory zip archive.

        Args:
            name: Filename of the target package (e.g. source.zip).
            artifact_type: Type category.
            files: Dictionary mapping file paths to their string contents.

        Returns:
            ReleaseArtifact detailing name, type, size, and SHA256.
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filepath, content in files.items():
                zip_file.writestr(filepath, content)

        data = zip_buffer.getvalue()
        sha256 = ChecksumGenerator.calculate_sha256(data)

        return ReleaseArtifact(
            name=name,
            artifact_type=artifact_type,
            sha256=sha256,
            size_bytes=len(data),
        )
DefinitionPath = "artifact_packager.py"
