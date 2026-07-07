"""Release candidate builder orchestrating packaging, checksums, and manifest creation."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.release_builder.artifact_packager import ArtifactPackager
from backend.release_builder.changelog_generator import ChangelogGenerator
from backend.release_builder.dependency_auditor import DependencyAuditor
from backend.release_builder.manifest_generator import ManifestGenerator
from backend.release_builder.models import BuildHistoryRecord, ReleaseArtifact, ReleaseManifest, ReleaseType
from backend.release_builder.release_notes import ReleaseNotesCompiler
from backend.release_builder.version_manager import VersionManager


class ReleaseCandidateBuilder:
    """Facade orchestrating the complete release packaging and manifesting lifecycle."""

    _instance: Optional["ReleaseCandidateBuilder"] = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ReleaseCandidateBuilder":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        if getattr(self, "_initialized", False):
            return
        self.db = DBStorage(db_path)
        self._init_table()
        self._initialized = True

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS release_builds (
                build_id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                status TEXT NOT NULL,
                artifacts TEXT NOT NULL,
                manifest TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def build_release(
        self,
        current_version: str,
        release_type: ReleaseType,
    ) -> BuildHistoryRecord:
        """Executes audits, compiles manifests, packs zip files, and outputs build logs.

        Args:
            current_version: Current version (e.g. 1.0.0-rc1).
            release_type: SemVer transition (RC, Stable, Hotfix).

        Returns:
            BuildHistoryRecord detailing the output assets.
        """
        # 1. Increment Version
        next_ver = VersionManager.increment_version(current_version, release_type)

        # 2. Audit Dependencies
        deps = DependencyAuditor.audit()

        # 3. Generate Manifest
        manifest = ManifestGenerator.generate_manifest(
            version=next_ver,
            dependencies=deps,
            providers=["openai", "gemini", "anthropic", "ollama"],
        )

        # 4. Compile Changelog & Notes
        log = ChangelogGenerator.generate_changelog(next_ver)
        notes = ReleaseNotesCompiler.compile_notes(next_ver, log)

        # 5. Package Source and Config Bundles
        src_art = ArtifactPackager.package_bundle(
            name=f"nexus-ai-source-{next_ver}.zip",
            artifact_type="source",
            files={"main.py": "print('Nexus AI Gateway')", "README.md": "Nexus platform"},
        )
        conf_art = ArtifactPackager.package_bundle(
            name=f"nexus-ai-config-{next_ver}.zip",
            artifact_type="config",
            files={"config.json": json.dumps({"port": 8000}), "secret.env": "API_KEY=mask"},
        )

        # 6. Assemble Build Record
        record = BuildHistoryRecord(
            build_id=f"build-{uuid_name()}",
            version=next_ver,
            status="success",
            artifacts=[src_art, conf_art],
            manifest=manifest,
            created_at=datetime.utcnow().isoformat(),
        )

        # 7. Persist Record to database
        self.save_build(record)

        return record

    def save_build(self, record: BuildHistoryRecord) -> None:
        """Saves a BuildHistoryRecord to SQLite database."""
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO release_builds
                (build_id, version, status, artifacts, manifest, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.build_id,
                    record.version,
                    record.status,
                    json.dumps([a.model_dump() for a in record.artifacts]),
                    record.manifest.model_dump_json() if record.manifest else "",
                    record.created_at,
                ),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def get_latest_build(self) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent build entry from the database."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM release_builds ORDER BY created_at DESC LIMIT 1")
            r = cursor.fetchone()
            if not r:
                return None
            return self._format_row(r)
        except Exception:
            return None
        finally:
            conn.close()

    def list_history(self) -> List[Dict[str, Any]]:
        """Retrieves all release builds history logs from the database."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM release_builds ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._format_row(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def _format_row(self, r: Any) -> Dict[str, Any]:
        return {
            "build_id": r["build_id"],
            "version": r["version"],
            "status": r["status"],
            "artifacts": json.loads(r["artifacts"]),
            "manifest": json.loads(r["manifest"]) if r["manifest"] else None,
            "created_at": r["created_at"],
        }


def uuid_name() -> str:
    import uuid
    return uuid.uuid4().hex[:8]
