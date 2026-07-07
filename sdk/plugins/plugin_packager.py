"""Plugin packager creating ZIP distribution archives for plugin projects."""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone
from typing import Dict

from sdk.plugins.models import PluginManifestModel


class PluginPackager:
    """Packages plugin source files into a distributable ZIP archive.

    The archive contains:
    - All plugin source files under their relative paths.
    - A ``MANIFEST.json`` file at the archive root with the manifest metadata.
    - A ``CHECKSUMS.sha256`` file with per-file SHA-256 hashes.

    Example::

        packager = PluginPackager()
        archive_path = packager.package(
            manifest=manifest,
            source_files={"my_plugin/__init__.py": "..."},
            output_dir="/dist",
        )
    """

    @staticmethod
    def package(
        manifest: PluginManifestModel,
        source_files: Dict[str, str],
        output_dir: str,
    ) -> str:
        """Creates a ZIP package from in-memory source files.

        Args:
            manifest: Plugin manifest to embed.
            source_files: Mapping of relative paths to file content strings.
            output_dir: Directory where the ZIP file will be written.

        Returns:
            Absolute path to the created ZIP archive.
        """
        os.makedirs(output_dir, exist_ok=True)
        archive_name = f"{manifest.plugin_id}-{manifest.version}.zip"
        archive_path = os.path.join(output_dir, archive_name)

        checksums: Dict[str, str] = {}

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write source files
            for rel_path, content in source_files.items():
                data = content.encode("utf-8")
                checksums[rel_path] = hashlib.sha256(data).hexdigest()
                zf.writestr(rel_path, content)

            # Write embedded manifest
            manifest_data = manifest.model_dump_json(indent=2)
            zf.writestr("MANIFEST.json", manifest_data)

            # Write checksum file
            checksum_lines = "\n".join(
                f"{digest}  {path}" for path, digest in sorted(checksums.items())
            )
            zf.writestr("CHECKSUMS.sha256", checksum_lines)

        return archive_path

    @staticmethod
    def inspect(archive_path: str) -> Dict[str, object]:
        """Reads and returns metadata from a packaged plugin archive.

        Args:
            archive_path: Path to the ZIP archive.

        Returns:
            Dict with ``manifest`` (parsed) and ``files`` (list of member paths).

        Raises:
            FileNotFoundError: If the archive does not exist.
            KeyError: If MANIFEST.json is missing from the archive.
        """
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            if "MANIFEST.json" not in names:
                raise KeyError("MANIFEST.json not found in archive.")
            manifest_raw = zf.read("MANIFEST.json").decode("utf-8")
            manifest_data = json.loads(manifest_raw)

        return {"manifest": manifest_data, "files": names}
