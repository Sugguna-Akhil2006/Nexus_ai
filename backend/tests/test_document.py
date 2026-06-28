import concurrent.futures
from datetime import datetime, timedelta
import threading
import time
from typing import Any, Dict, List, Optional
import unittest
import uuid

from backend.agents.document import (
    DocumentError,
    DocumentValidationError,
    DocumentNotFoundError,
    DocumentStatus,
    DocumentMetadata,
    Document,
    DocumentVersion,
    DocumentImportRequest,
    DocumentImportResponse,
    DocumentProvider,
    InMemoryDocumentProvider,
    DocumentRegistry,
    DocumentRoutingStrategy,
    DefaultDocumentRoutingStrategy,
    DocumentAgent,
    detect_mime_type,
    compute_checksum,
    validate_mime_type,
    validate_file_size,
    validate_content,
)
from backend.runtime.base import AgentState, AgentStatus
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.task import Task


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestDocumentSystem(unittest.TestCase):
    """Suite of tests covering the enterprise document lifecycle management system."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        self.registry = DocumentRegistry()
        with self.registry._lock:
            self.registry._providers.clear()

        self.provider = InMemoryDocumentProvider()
        self.registry.register_provider("memory", self.provider)

        self.agent = DocumentAgent()
        self.agent.initialize()

    def test_validation_utilities(self) -> None:
        """Verifies validations on file size, checksum, and MIME types."""
        # MIME mapping
        self.assertEqual(detect_mime_type("document.pdf"), "application/pdf")
        self.assertEqual(detect_mime_type("README.md"), "text/markdown")
        self.assertEqual(detect_mime_type("raw_data.unknown"), "application/octet-stream")

        validate_mime_type("application/pdf")
        with self.assertRaises(DocumentValidationError):
            validate_mime_type("application/invalid-mime")

        # Checksum computation
        content = b"Nexus AI Framework Document Ingestion Content"
        checksum = compute_checksum(content)
        self.assertEqual(len(checksum), 64)  # SHA-256 is 64 hex characters

        # File size
        validate_file_size(1024)
        with self.assertRaises(DocumentValidationError):
            validate_file_size(-1)
        with self.assertRaises(DocumentValidationError):
            validate_file_size(200 * 1024 * 1024)  # default max is 100MB

        # Content validation
        validate_content(b"valid content")
        with self.assertRaises(DocumentValidationError):
            validate_content(b"")  # empty content is corrupted
        with self.assertRaises(DocumentValidationError):
            validate_content(None)  # type: ignore

    def test_registry_singleton(self) -> None:
        """Verifies singleton pattern constraints of DocumentRegistry."""
        registry2 = DocumentRegistry()
        self.assertIs(self.registry, registry2)

    def test_provider_registration(self) -> None:
        """Verifies provider register and unregister constraints on DocumentRegistry."""
        with self.assertRaises(DocumentValidationError):
            self.registry.register_provider("", self.provider)
        with self.assertRaises(DocumentValidationError):
            self.registry.register_provider("memory2", None)  # type: ignore
        with self.assertRaises(DocumentValidationError):
            self.registry.register_provider("memory", self.provider)  # duplicate check

        self.registry.unregister_provider("memory")
        self.assertNotIn("memory", self.registry.list_providers())

    def test_routing_strategies(self) -> None:
        """Verifies routing capabilities generated based on document formats."""
        strategy = DefaultDocumentRoutingStrategy()
        doc_pdf = Document(
            document_id="d1", workspace_id="ws", project_id="p", owner_id="u",
            filename="file.pdf", mime_type="application/pdf", file_size=10,
            checksum="abc", version=1, status="UPLOADED",
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
            metadata=DocumentMetadata()
        )
        plan_pdf = strategy.determine_route(doc_pdf, b"")
        self.assertIn("OCR", plan_pdf)
        self.assertIn("EMBEDDING", plan_pdf)

        doc_txt = Document(
            document_id="d2", workspace_id="ws", project_id="p", owner_id="u",
            filename="file.txt", mime_type="text/plain", file_size=10,
            checksum="abc", version=1, status="UPLOADED",
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
            metadata=DocumentMetadata()
        )
        plan_txt = strategy.determine_route(doc_txt, b"")
        self.assertNotIn("OCR", plan_txt)
        self.assertIn("EMBEDDING", plan_txt)

    def test_agent_import_document(self) -> None:
        """Verifies successful document ingestion, metadata caching, and event triggers."""
        task = Task(
            description="Import document",
            metadata={
                "action": "import_document",
                "workspace_id": "workspace_1",
                "uploaded_by": "user_123",
                "source": b"Ingested PDF content bytes representing document information.",
                "filename": "ingested_file.pdf",
                "content_type": "application/pdf",
                "metadata": {
                    "title": "Ingested PDF title",
                    "author": "User Author",
                    "tags": ["financial", "report"]
                }
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        res: DocumentImportResponse = self.agent.execute(task)
        self.agent.after_execute(res)

        self.assertEqual(res.document.filename, "ingested_file.pdf")
        self.assertEqual(res.document.mime_type, "application/pdf")
        self.assertEqual(res.document.version, 1)
        self.assertEqual(res.document.status, DocumentStatus.UPLOADED.value)
        self.assertEqual(res.document.metadata.author, "User Author")
        self.assertIn("OCR", res.routing_plan)

        # Confirm duplicate upload is rejected
        task_dup = Task(
            description="Import duplicate document",
            metadata={
                "action": "import_document",
                "workspace_id": "workspace_1",
                "uploaded_by": "user_123",
                "source": b"Ingested PDF content bytes representing document information.",
                "filename": "another_file.pdf",
                "content_type": "application/pdf"
            }
        )
        with self.assertRaises(DocumentValidationError):
            self.agent.execute(task_dup)

        # Confirm EventBus triggers
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("document.import.started", events)
        self.assertIn("document.validated", events)
        self.assertIn("document.routing.completed", events)
        self.assertIn("document.import.completed", events)

    def test_agent_lifecycle_operations(self) -> None:
        """Verifies retrieval, archiving, and deletion tasks."""
        # 1. Import document first
        task_import = Task(
            description="Import file",
            metadata={
                "action": "import_document",
                "workspace_id": "workspace_1",
                "uploaded_by": "user_123",
                "source": b"Document text context data.",
                "filename": "text_doc.txt"
            }
        )
        self.agent.validate_task(task_import)
        self.agent.before_execute(task_import)
        import_res = self.agent.execute(task_import)
        self.agent.after_execute(import_res)

        doc_id = import_res.document.document_id

        # 2. Retrieve document content
        task_ret = Task(
            description="Retrieve raw bytes",
            metadata={
                "action": "retrieve_document",
                "document_id": doc_id
            }
        )
        self.agent.validate_task(task_ret)
        self.agent.before_execute(task_ret)
        content = self.agent.execute(task_ret)
        self.agent.after_execute(content)
        self.assertEqual(content, b"Document text context data.")

        # 3. List documents query
        task_list = Task(
            description="List documents list",
            metadata={
                "action": "list_documents",
                "workspace_id": "workspace_1"
            }
        )
        self.agent.validate_task(task_list)
        self.agent.before_execute(task_list)
        doc_list = self.agent.execute(task_list)
        self.agent.after_execute(doc_list)
        self.assertEqual(len(doc_list), 1)

        # 4. Archive document
        task_arch = Task(
            description="Archive document",
            metadata={
                "action": "archive_document",
                "document_id": doc_id
            }
        )
        self.agent.validate_task(task_arch)
        self.agent.before_execute(task_arch)
        arch_success = self.agent.execute(task_arch)
        self.agent.after_execute(arch_success)
        self.assertTrue(arch_success)

        # Verify archived status updated in in-memory state
        updated_doc = self.provider.documents[doc_id]
        self.assertEqual(updated_doc.status, DocumentStatus.ARCHIVED.value)

        # 5. Delete document
        task_del = Task(
            description="Delete document",
            metadata={
                "action": "delete_document",
                "document_id": doc_id
            }
        )
        self.agent.validate_task(task_del)
        self.agent.before_execute(task_del)
        del_success = self.agent.execute(task_del)
        self.agent.after_execute(del_success)
        self.assertTrue(del_success)

        # Retrieve deleted doc should raise exception
        with self.assertRaises(DocumentNotFoundError):
            self.agent.execute(task_ret)

    def test_agent_versioning_operations(self) -> None:
        """Verifies creating new document versions bumps version number and updates parent checksums."""
        # 1. Import document first
        task_import = Task(
            description="Import document",
            metadata={
                "action": "import_document",
                "workspace_id": "workspace_1",
                "uploaded_by": "user_123",
                "source": b"Original document context representation.",
                "filename": "original_doc.txt"
            }
        )
        self.agent.validate_task(task_import)
        self.agent.before_execute(task_import)
        import_res = self.agent.execute(task_import)
        self.agent.after_execute(import_res)

        doc_id = import_res.document.document_id
        original_checksum = import_res.document.checksum

        # 2. Add a new version of the file
        task_ver = Task(
            description="Create new version",
            metadata={
                "action": "create_version",
                "document_id": doc_id,
                "workspace_id": "workspace_1",
                "source": b"Updated document version representation with more details.",
                "created_by": "user_editor",
                "metadata": {
                    "title": "Updated Version 2 Title"
                }
            }
        )
        self.agent.validate_task(task_ver)
        self.agent.before_execute(task_ver)
        version_info = self.agent.execute(task_ver)
        self.agent.after_execute(version_info)

        self.assertEqual(version_info.version_number, 2)
        self.assertNotEqual(version_info.checksum, original_checksum)

        # Verify updated parents details
        parent_doc = self.provider.documents[doc_id]
        self.assertEqual(parent_doc.version, 2)
        self.assertEqual(parent_doc.checksum, version_info.checksum)
        self.assertEqual(parent_doc.metadata.title, "Updated Version 2 Title")

        # Adding identical version checksum is rejected
        with self.assertRaises(DocumentValidationError):
            self.agent.execute(task_ver)

    def test_registry_thread_safety(self) -> None:
        """Verifies concurrent registrations and imports operate safely."""
        def run_thread(tid: int) -> None:
            class DummyDocProvider(DocumentProvider):
                def import_document(self, document, content): return document
                def retrieve_document(self, document_id): return None
                def update_document(self, document): return document
                def delete_document(self, document_id): return True
                def archive_document(self, document_id): return True
                def list_documents(self, workspace_id): return []
                def add_version(self, version): return version
                def get_versions(self, document_id): return []
                def health_check(self): return True

            pid = f"dummy-{tid}"
            self.registry.register_provider(pid, DummyDocProvider())
            self.assertIn(pid, self.registry.list_providers())
            self.registry.unregister_provider(pid)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()
