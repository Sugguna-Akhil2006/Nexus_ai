"""Database storage layer for Nexus AI relational entities.

Uses SQLite as the local engine, providing tables for users, workspaces,
members, documents, conversations, and messages.
"""

from datetime import datetime
import json
import sqlite3
import threading
from typing import Any, Dict, List, Optional
import uuid


class DBStorage:
    """Thread-safe relational database manager using SQLite."""

    _instance: Optional["DBStorage"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "DBStorage":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            if db_path == ":memory:":
                self.db_path = "file::memory:?cache=shared"
                self._is_uri = True
            else:
                self.db_path = db_path
                self._is_uri = False
            self._lock = threading.RLock()
            if self._is_uri:
                self._keep_alive = sqlite3.connect(self.db_path, uri=True)
            self._init_db()
            self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        try:
            from backend.platform.hardening.metrics_collector import MetricsCollector
            MetricsCollector().increment("db_queries_total")
        except Exception:
            pass
        if getattr(self, "_is_uri", False):
            conn = sqlite3.connect(self.db_path, uri=True, timeout=60.0)
        else:
            conn = sqlite3.connect(self.db_path, timeout=60.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT,
                created_at TEXT
            )
            """)

            # Workspaces table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                workspace_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT
            )
            """)

            # Members table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                workspace_id TEXT,
                user_id TEXT,
                role TEXT,
                status TEXT,
                PRIMARY KEY (workspace_id, user_id)
            )
            """)

            # Documents table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                checksum TEXT,
                created_at TEXT
            )
            """)

            # Conversations table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT
            )
            """)

            # Messages table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT
            )
            """)

            # Resumes Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                document_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                name TEXT,
                email TEXT,
                phone TEXT,
                location TEXT,
                linkedin TEXT,
                github TEXT,
                portfolio TEXT,
                education TEXT,
                certifications TEXT,
                skills TEXT,
                languages TEXT,
                experience TEXT,
                projects TEXT,
                publications TEXT,
                awards TEXT,
                created_at TEXT
            )
            """)

            # Resume Analysis History Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_analysis_history (
                analysis_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                report_data TEXT NOT NULL,
                created_at TEXT
            )
            """)

            # ATS Reports Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ats_reports (
                ats_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                report_data TEXT NOT NULL,
                created_at TEXT
            )
            """)

            # Resume Comparison History Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_comparison_history (
                comparison_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                document_ids TEXT NOT NULL,
                comparison_data TEXT NOT NULL,
                created_at TEXT
            )
            """)

            # Workflow Definitions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_definitions (
                definition_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT
            )
            """)

            # Drop old constraints if any
            cursor.execute("DROP TABLE IF EXISTS workflow_steps")
            cursor.execute("DROP TABLE IF EXISTS workflow_conditions")

            # Workflow Steps Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_steps (
                step_id TEXT,
                definition_id TEXT,
                name TEXT NOT NULL,
                step_type TEXT NOT NULL,
                config TEXT NOT NULL,
                dependencies TEXT NOT NULL,
                PRIMARY KEY (step_id, definition_id)
            )
            """)

            # Workflow Conditions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_conditions (
                condition_id TEXT,
                definition_id TEXT,
                expression TEXT NOT NULL,
                true_step_id TEXT NOT NULL,
                false_step_id TEXT NOT NULL,
                PRIMARY KEY (condition_id, definition_id)
            )
            """)

            # Workflow Instances Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_instances (
                instance_id TEXT PRIMARY KEY,
                definition_id TEXT NOT NULL,
                status TEXT NOT NULL,
                step_statuses TEXT NOT NULL,
                step_results TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                variables TEXT NOT NULL
            )
            """)

            # Workflow Approvals Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_approvals (
                approval_id TEXT PRIMARY KEY,
                instance_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                status TEXT NOT NULL,
                approver TEXT,
                comments TEXT,
                created_at TEXT,
                decided_at TEXT
            )
            """)

            # Workflow History Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_history (
                history_id TEXT PRIMARY KEY,
                instance_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL
            )
            """)

            # Workflow Schedules Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_schedules (
                schedule_id TEXT PRIMARY KEY,
                definition_id TEXT NOT NULL,
                cron_expr TEXT NOT NULL,
                next_run TEXT NOT NULL
            )
            """)

            # Seed default admin user if it does not exist
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, email, role, created_at) VALUES (?, ?, ?, ?, ?)",
                ("admin", "hashed_admin123", "admin@nexus.ai", "admin", datetime.utcnow().isoformat())
            )

            conn.commit()
            conn.close()

    # User operations
    def create_user(self, username: str, password_hash: str, email: str, role: str = "user") -> None:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, email, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, email, role, datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

    # Workspace operations
    def create_workspace(self, workspace_id: str, name: str, owner_id: str) -> Dict[str, Any]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO workspaces (workspace_id, name, owner_id, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (workspace_id, name, owner_id, "active", now)
            )
            cursor.execute(
                "INSERT INTO members (workspace_id, user_id, role, status) VALUES (?, ?, ?, ?)",
                (workspace_id, owner_id, "OWNER", "active")
            )
            conn.commit()
            conn.close()
            return {
                "workspace_id": workspace_id,
                "name": name,
                "owner_id": owner_id,
                "status": "active",
                "created_at": now
            }

    def list_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT w.* FROM workspaces w JOIN members m ON w.workspace_id = m.workspace_id WHERE m.user_id = ?",
                (user_id,)
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

    # Document operations
    def create_document(self, document_id: str, workspace_id: str, name: str, checksum: str) -> Dict[str, Any]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO documents (document_id, workspace_id, name, status, checksum, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (document_id, workspace_id, name, "pending", checksum, now)
            )
            conn.commit()
            conn.close()
            return {
                "document_id": document_id,
                "workspace_id": workspace_id,
                "name": name,
                "status": "pending",
                "checksum": checksum,
                "created_at": now
            }

    def update_document_status(self, document_id: str, status: str) -> None:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE documents SET status = ? WHERE document_id = ?", (status, document_id))
            conn.commit()
            conn.close()

    def list_documents(self, workspace_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE workspace_id = ?", (workspace_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

    # Conversation operations
    def create_conversation(self, conversation_id: str, workspace_id: str, title: str) -> Dict[str, Any]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO conversations (conversation_id, workspace_id, title, created_at) VALUES (?, ?, ?, ?)",
                (conversation_id, workspace_id, title, now)
            )
            conn.commit()
            conn.close()
            return {
                "conversation_id": conversation_id,
                "workspace_id": workspace_id,
                "title": title,
                "created_at": now
            }

    def list_conversations(self, workspace_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE workspace_id = ?", (workspace_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

    def create_message(self, message_id: str, conversation_id: str, role: str, content: str) -> None:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (message_id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (message_id, conversation_id, role, content, datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

    # Resume operations
    def create_resume_metadata(
        self,
        document_id: str,
        workspace_id: str,
        name: str = "",
        email: str = "",
        phone: str = "",
        location: str = "",
        linkedin: str = "",
        github: str = "",
        portfolio: str = "",
        education: str = "[]",
        certifications: str = "[]",
        skills: str = "[]",
        languages: str = "[]",
        experience: str = "[]",
        projects: str = "[]",
        publications: str = "[]",
        awards: str = "[]"
    ) -> None:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO resumes (
                    document_id, workspace_id, name, email, phone, location,
                    linkedin, github, portfolio, education, certifications,
                    skills, languages, experience, projects, publications, awards, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id, workspace_id, name, email, phone, location,
                    linkedin, github, portfolio, education, certifications,
                    skills, languages, experience, projects, publications, awards,
                    datetime.utcnow().isoformat()
                )
            )
            conn.commit()
            conn.close()

    def get_resume_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM resumes WHERE document_id = ?", (document_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

    def create_analysis_report(self, analysis_id: str, document_id: str, workspace_id: str, report_data: str) -> None:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO resume_analysis_history (analysis_id, document_id, workspace_id, report_data, created_at) VALUES (?, ?, ?, ?, ?)",
                (analysis_id, document_id, workspace_id, report_data, datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()

    def get_analysis_report(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM resume_analysis_history WHERE analysis_id = ?", (analysis_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

    def create_ats_report(self, ats_id: str, document_id: str, score: int, report_data: str) -> None:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO ats_reports (ats_id, document_id, score, report_data, created_at) VALUES (?, ?, ?, ?, ?)",
                (ats_id, document_id, score, report_data, datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()

    def get_ats_report(self, ats_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ats_reports WHERE ats_id = ?", (ats_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

    def get_ats_report_by_doc(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ats_reports WHERE document_id = ? ORDER BY created_at DESC LIMIT 1", (document_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

    def create_comparison_history(self, comparison_id: str, workspace_id: str, document_ids: str, comparison_data: str) -> None:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO resume_comparison_history (comparison_id, workspace_id, document_ids, comparison_data, created_at) VALUES (?, ?, ?, ?, ?)",
                (comparison_id, workspace_id, document_ids, comparison_data, datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()

    def get_comparison_history(self, comparison_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM resume_comparison_history WHERE comparison_id = ?", (comparison_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

    # Workflow operations
    def create_workflow_definition(self, definition_id: str, name: str, description: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO workflow_definitions (definition_id, name, description, created_at) VALUES (?, ?, ?, ?)",
                    (definition_id, name, description, datetime.utcnow().isoformat())
                )
                conn.commit()
            finally:
                conn.close()

    def get_workflow_definition(self, definition_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workflow_definitions WHERE definition_id = ?", (definition_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def create_workflow_step(self, step_id: str, definition_id: str, name: str, step_type: str, config: str, dependencies: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO workflow_steps (step_id, definition_id, name, step_type, config, dependencies) VALUES (?, ?, ?, ?, ?, ?)",
                    (step_id, definition_id, name, step_type, config, dependencies)
                )
                conn.commit()
            finally:
                conn.close()

    def list_workflow_steps(self, definition_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workflow_steps WHERE definition_id = ?", (definition_id,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def create_workflow_condition(self, condition_id: str, definition_id: str, expression: str, true_step_id: str, false_step_id: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO workflow_conditions (condition_id, definition_id, expression, true_step_id, false_step_id) VALUES (?, ?, ?, ?, ?)",
                    (condition_id, definition_id, expression, true_step_id, false_step_id)
                )
                conn.commit()
            finally:
                conn.close()

    def list_workflow_conditions(self, definition_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workflow_conditions WHERE definition_id = ?", (definition_id,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def create_workflow_instance(self, instance_id: str, definition_id: str, status: str, step_statuses: str, step_results: str, variables: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO workflow_instances (instance_id, definition_id, status, step_statuses, step_results, started_at, variables) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (instance_id, definition_id, status, step_statuses, step_results, datetime.utcnow().isoformat(), variables)
                )
                conn.commit()
            finally:
                conn.close()

    def get_workflow_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workflow_instances WHERE instance_id = ?", (instance_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def update_workflow_instance(self, instance_id: str, status: str, step_statuses: str, step_results: str, variables: str, completed: bool = False) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if completed:
                    cursor.execute(
                        "UPDATE workflow_instances SET status = ?, step_statuses = ?, step_results = ?, variables = ?, completed_at = ? WHERE instance_id = ?",
                        (status, step_statuses, step_results, variables, datetime.utcnow().isoformat(), instance_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE workflow_instances SET status = ?, step_statuses = ?, step_results = ?, variables = ? WHERE instance_id = ?",
                        (status, step_statuses, step_results, variables, instance_id)
                    )
                conn.commit()
            finally:
                conn.close()

    def create_workflow_approval(self, approval_id: str, instance_id: str, step_id: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO workflow_approvals (approval_id, instance_id, step_id, status, created_at) VALUES (?, ?, ?, ?, ?)",
                    (approval_id, instance_id, step_id, "PENDING", datetime.utcnow().isoformat())
                )
                conn.commit()
            finally:
                conn.close()

    def update_workflow_approval(self, approval_id: str, status: str, approver: str, comments: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE workflow_approvals SET status = ?, approver = ?, comments = ?, decided_at = ? WHERE approval_id = ?",
                    (status, approver, comments, datetime.utcnow().isoformat(), approval_id)
                )
                conn.commit()
            finally:
                conn.close()

    def get_workflow_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workflow_approvals WHERE approval_id = ?", (approval_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def get_pending_workflow_approval(self, instance_id: str, step_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workflow_approvals WHERE instance_id = ? AND step_id = ? AND status = 'PENDING'", (instance_id, step_id))
                row = cursor.fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def create_workflow_history(self, history_id: str, instance_id: str, action: str, details: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO workflow_history (history_id, instance_id, action, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (history_id, instance_id, action, details, datetime.utcnow().isoformat())
                )
                conn.commit()
            finally:
                conn.close()

    def list_workflow_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workflow_history ORDER BY timestamp DESC")
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def create_workflow_schedule(self, schedule_id: str, definition_id: str, cron_expr: str, next_run: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO workflow_schedules (schedule_id, definition_id, cron_expr, next_run) VALUES (?, ?, ?, ?)",
                    (schedule_id, definition_id, cron_expr, next_run)
                )
                conn.commit()
            finally:
                conn.close()

    def list_workflow_schedules(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workflow_schedules")
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()
