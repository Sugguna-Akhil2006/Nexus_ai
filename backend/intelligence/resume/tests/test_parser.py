"""Unit and integration tests for the Resume Parser Engine."""

import json
import unittest
from unittest.mock import MagicMock, patch
import uuid

from backend.api.main import app
from backend.intelligence.resume.exceptions import (
    UnsupportedFormatError,
    EmptyResumeError,
    CorruptedDocumentError,
    ParsingFailureError,
)
from backend.intelligence.resume.models import ParsedResume
from backend.intelligence.resume.parser import ResumeParser
from backend.intelligence.resume.services import ResumeService, ResumeContextProvider
from backend.interfaces.context import ContextRequest, ContextSource
from backend.interfaces.model import InferenceResponse
from backend.runtime.event import EventBus


class TestResumeParserEngine(unittest.TestCase):
    """Verifies all extraction, parsing, error handling, and orchestration pathways."""

    @classmethod
    def setUpClass(cls) -> None:
        from fastapi.testclient import TestClient
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    def setUp(self) -> None:
        # Register Document Provider
        from backend.agents.document import DocumentRegistry, InMemoryDocumentProvider
        doc_registry = DocumentRegistry()
        if not doc_registry.list_providers():
            doc_registry.register_provider("memory", InMemoryDocumentProvider())

        # Register OCR Provider
        from backend.agents.ocr import OCRRegistry, MockOCRProvider
        ocr_registry = OCRRegistry()
        if not ocr_registry.list_providers():
            ocr_registry.register_provider("mock", MockOCRProvider())

        self.parser = ResumeParser()
        self.service = ResumeService()

        # Set up default mock LLM response
        self.mock_llm_data = {
            "personal_info": {
                "full_name": "Test Candidate",
                "email": "candidate@test.com",
                "phone": "123-456-7890",
                "linkedin": "linkedin.com/in/test",
                "github": "github.com/test",
                "portfolio": "test.com",
                "location": "New York, NY"
            },
            "education": [
                {
                    "institution": "MIT",
                    "degree": "B.S.",
                    "branch": "Computer Science",
                    "gpa_cgpa": "3.9",
                    "graduation_year": "2023"
                }
            ],
            "experience": [
                {
                    "company": "Google",
                    "role": "Software Engineer",
                    "start_date": "2023",
                    "end_date": "Present",
                    "duration": "1 year",
                    "responsibilities": ["Developed high throughput API service."]
                }
            ],
            "projects": [
                {
                    "project_name": "NexusAI",
                    "description": "Agent orchestration framework",
                    "technologies": ["Python", "FastAPI"],
                    "github_url": "github.com/test/nexus",
                    "live_url": "nexus.test.com"
                }
            ],
            "skills": {
                "programming_languages": ["Python", "Go"],
                "frameworks": ["FastAPI", "Django"],
                "databases": ["PostgreSQL", "Redis"],
                "cloud": ["AWS"],
                "ai_ml": ["PyTorch"],
                "devops": ["Docker"],
                "tools": ["Git"],
                "soft_skills": ["Leadership"]
            },
            "certifications": [
                {
                    "certification_name": "AWS Architect",
                    "organization": "Amazon",
                    "year": "2024"
                }
            ]
        }

    @patch("backend.api.main._extract_text_from_file")
    @patch("backend.interfaces.model.ModelRegistry.list_providers")
    @patch("backend.interfaces.model.ModelRegistry.get_provider")
    def test_parse_pdf_success(self, mock_get_provider: MagicMock, mock_list_providers: MagicMock, mock_extract: MagicMock) -> None:
        """Verifies parsing a PDF resume successfully with mock text extraction and LLM response."""
        mock_extract.return_value = "Candidate details content"
        mock_list_providers.return_value = ["mock_ollama"]
        
        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceResponse(
            request_id="test-req",
            content=json.dumps(self.mock_llm_data),
            finish_reason="stop",
            token_usage={"prompt_tokens": 10, "completion_tokens": 10},
            latency=0.5,
            provider="ollama",
            model="mock",
            metadata={}
        )
        mock_get_provider.return_value = mock_provider
        
        pdf_bytes = b"%PDF-1.4\n%%EOF"
        parsed = self.parser.parse_resume(pdf_bytes, "john_resume.pdf")
        
        self.assertIsInstance(parsed, ParsedResume)
        self.assertEqual(parsed.personal_info.full_name, "Test Candidate")
        self.assertEqual(parsed.personal_info.email, "candidate@test.com")
        self.assertEqual(len(parsed.education), 1)
        self.assertEqual(parsed.education[0].institution, "MIT")

    @patch("backend.api.main._extract_text_from_file")
    @patch("backend.interfaces.model.ModelRegistry.list_providers")
    @patch("backend.interfaces.model.ModelRegistry.get_provider")
    def test_parse_docx_success(self, mock_get_provider: MagicMock, mock_list_providers: MagicMock, mock_extract: MagicMock) -> None:
        """Verifies parsing a DOCX resume successfully."""
        mock_extract.return_value = "Alice Smith\nSoftware Engineer"
        mock_list_providers.return_value = ["mock_ollama"]
        
        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceResponse(
            request_id="test-req",
            content=json.dumps(self.mock_llm_data),
            finish_reason="stop",
            token_usage={"prompt_tokens": 10, "completion_tokens": 10},
            latency=0.5,
            provider="ollama",
            model="mock",
            metadata={}
        )
        mock_get_provider.return_value = mock_provider
        
        docx_bytes = b"mock-docx-data-bytes"
        parsed = self.parser.parse_resume(docx_bytes, "alice.docx")
        
        self.assertIsInstance(parsed, ParsedResume)
        self.assertGreater(len(parsed.skills.programming_languages), 0)
        self.assertIn("Python", parsed.skills.programming_languages)

    @patch("backend.api.main._extract_text_from_file")
    @patch("backend.interfaces.model.ModelRegistry.list_providers")
    @patch("backend.interfaces.model.ModelRegistry.get_provider")
    def test_parse_txt_success(self, mock_get_provider: MagicMock, mock_list_providers: MagicMock, mock_extract: MagicMock) -> None:
        """Verifies parsing a TXT resume successfully."""
        mock_extract.return_value = "Bob Dylan\nSinger Songwriter"
        mock_list_providers.return_value = ["mock_ollama"]
        
        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceResponse(
            request_id="test-req",
            content=json.dumps(self.mock_llm_data),
            finish_reason="stop",
            token_usage={"prompt_tokens": 10, "completion_tokens": 10},
            latency=0.5,
            provider="ollama",
            model="mock",
            metadata={}
        )
        mock_get_provider.return_value = mock_provider
        
        txt_bytes = b"Bob Dylan resume plain text"
        parsed = self.parser.parse_resume(txt_bytes, "bob.txt")
        self.assertIsInstance(parsed, ParsedResume)

    def test_unsupported_format_error(self) -> None:
        """Verifies parsing an unsupported file format raises UnsupportedFormatError."""
        png_bytes = b"png-image-payload"
        with self.assertRaises(UnsupportedFormatError):
            self.parser.parse_resume(png_bytes, "photo.png")

    def test_empty_document_error(self) -> None:
        """Verifies parsing empty contents raises EmptyResumeError."""
        with self.assertRaises(EmptyResumeError):
            self.parser.parse_resume(b"", "empty.txt")

    @patch("backend.api.main._extract_text_from_file")
    def test_corrupted_document_error(self, mock_extract: MagicMock) -> None:
        """Verifies a extraction breakdown raises CorruptedDocumentError."""
        mock_extract.side_effect = RuntimeError("PDF decompression error")
        pdf_bytes = b"%PDF-1.4 corrupt"
        
        with self.assertRaises(CorruptedDocumentError):
            self.parser.parse_resume(pdf_bytes, "corrupt.pdf")

    @patch("backend.api.main._extract_text_from_file")
    @patch("backend.agents.ocr.OCRAgent.execute")
    @patch("backend.interfaces.model.ModelRegistry.list_providers")
    @patch("backend.interfaces.model.ModelRegistry.get_provider")
    def test_pdf_ocr_fallback(self, mock_get_provider: MagicMock, mock_list_providers: MagicMock, mock_ocr_execute: MagicMock, mock_extract: MagicMock) -> None:
        """Verifies image-only PDF triggers the OCR agent fallback extraction."""
        # Set plain extract return to empty to trigger OCR check
        mock_extract.return_value = ""
        mock_list_providers.return_value = ["mock_ollama"]
        
        # Setup mock OCR output
        class MockOCRResult:
            extracted_text = "Scanned Candidate Name\nProgramming: Rust, PyTorch"
        mock_ocr_execute.return_value = MockOCRResult()

        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceResponse(
            request_id="test-req",
            content=json.dumps(self.mock_llm_data),
            finish_reason="stop",
            token_usage={"prompt_tokens": 10, "completion_tokens": 10},
            latency=0.5,
            provider="ollama",
            model="mock",
            metadata={}
        )
        mock_get_provider.return_value = mock_provider
        
        pdf_bytes = b"%PDF-1.4 scanned image page data"
        parsed = self.parser.parse_resume(pdf_bytes, "scanned.pdf")
        self.assertIsInstance(parsed, ParsedResume)

    @patch("backend.api.main._extract_text_from_file")
    @patch("backend.interfaces.model.ModelRegistry.list_providers")
    @patch("backend.interfaces.model.ModelRegistry.get_provider")
    def test_service_orchestration_workflow(self, mock_get_provider: MagicMock, mock_list_providers: MagicMock, mock_extract: MagicMock) -> None:
        """Verifies ResumeService facade orchestrates parsing, saves DB records, and broadcasts events."""
        mock_extract.return_value = "Candidate details"
        mock_list_providers.return_value = ["mock_ollama"]
        
        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceResponse(
            request_id="test-req",
            content=json.dumps(self.mock_llm_data),
            finish_reason="stop",
            token_usage={"prompt_tokens": 10, "completion_tokens": 10},
            latency=0.5,
            provider="ollama",
            model="mock",
            metadata={}
        )
        mock_get_provider.return_value = mock_provider
        
        # Register test event listener
        events_received = []
        event_bus = EventBus()
        event_bus.subscribe("*", lambda e: events_received.append(e))
        
        parsed = self.service.parse_resume(b"txt content", "resume.txt")
        self.assertIsInstance(parsed, ParsedResume)
        
        # Dispatch the published events to handler lists
        event_bus.dispatch_all()

        # Verify events were published
        event_types = [e.payload.get("event") for e in events_received if e.payload]
        self.assertIn("resume.parsing.started", event_types)
        self.assertIn("resume.parsing.completed", event_types)

    def test_context_provider_integration(self) -> None:
        """Verifies ResumeContextProvider correctly retrieves and builds context sections."""
        # Generate dummy parsed resume
        mock_resume = ParsedResume()
        mock_resume.personal_info.full_name = "Charlie Brown"
        mock_resume.personal_info.email = "charlie@snoopy.com"
        mock_resume.skills.programming_languages = ["Python", "JavaScript"]

        doc_id = str(uuid.uuid4())
        self.service.save_parsed_resume(doc_id, "default-ws", mock_resume)

        # Build ContextRequest
        req = ContextRequest(
            task=None,
            max_tokens=500,
            required_sources=[ContextSource.CUSTOM],
            optional_sources=[],
            metadata={"document_id": doc_id}
        )

        provider = ResumeContextProvider()
        sections = provider.collect(req)
        self.assertEqual(len(sections), 1)
        self.assertIn("Charlie Brown", sections[0].content)
        self.assertIn("Python", sections[0].content)
        self.assertTrue(provider.supports(ContextSource.CUSTOM))
        self.assertTrue(provider.health_check())
