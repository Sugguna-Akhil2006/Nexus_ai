"""Unit tests for public SDK and REST API layer."""

from __future__ import annotations

import io
import json
import unittest
from unittest.mock import MagicMock, patch
import urllib.request
from urllib.error import HTTPError

from backend.sdk.client import NexusClient
from backend.sdk.async_client import AsyncNexusClient
from backend.sdk.exceptions import (
    AuthenticationError,
    ValidationError,
    RateLimitError,
    ExecutionError,
    ProviderError
)
from backend.sdk.pagination import Page, Cursor
from backend.sdk.streaming import TokenStream, SSEStream


class TestPublicAPIAndSDK(unittest.TestCase):
    """Test suite covering client functions, error wrapping, streaming, and paginators."""

    def setUp(self) -> None:
        self.api_key = "test_developer_key"
        self.client = NexusClient(api_key=self.api_key, base_url="http://localhost:8000")
        self.async_client = AsyncNexusClient(api_key=self.api_key, base_url="http://localhost:8000")

    @patch("backend.sdk.api_client.urlopen")
    def test_client_authentication_headers(self, mock_urlopen: MagicMock) -> None:
        """Verifies that requests include expected authentication and correlation headers."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"workspaces": []}'
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Trigger list workspaces
        self.client.workspaces.list()

        self.assertTrue(mock_urlopen.called)
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertIsInstance(req, urllib.request.Request)
        headers_lower = {k.lower(): v for k, v in req.headers.items()}
        self.assertEqual(headers_lower.get("x-api-key"), self.api_key)
        self.assertIn("x-correlation-id", headers_lower)

    @patch("backend.sdk.api_client.urlopen")
    def test_workspace_creation(self, mock_urlopen: MagicMock) -> None:
        """Verifies workspace creation mapping."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"status": "success", "workspace": {"workspace_id": "ws-123", "name": "Public Space", "status": "active"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        ws = self.client.workspaces.create("Public Space")
        self.assertEqual(ws.workspace_id, "ws-123")
        self.assertEqual(ws.name, "Public Space")

    @patch("urllib.request.urlopen")
    def test_file_upload(self, mock_urlopen: MagicMock) -> None:
        """Verifies that file uploads send raw content with multipart/form-data."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"status": "success", "document_id": "doc-555", "chars_extracted": 100}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.files.upload("ws-123", "test.txt", b"Hello Public SDK!")
        self.assertEqual(res.document_id, "doc-555")
        self.assertEqual(res.chars_extracted, 100)

    @patch("backend.sdk.api_client.urlopen")
    def test_resume_analysis(self, mock_urlopen: MagicMock) -> None:
        """Verifies triggering resume intelligence analysis."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"job_id": "job-resume-123", "status": "pending"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.resume.analyze("ws-123", resume_text="Software Dev resume details...")
        self.assertEqual(res.job_id, "job-resume-123")
        self.assertEqual(res.status, "pending")

    @patch("backend.sdk.api_client.urlopen")
    def test_github_analysis(self, mock_urlopen: MagicMock) -> None:
        """Verifies triggering github repository analysis."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"job_id": "job-github-456", "status": "pending"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.github.analyze("ws-123", repository_url="https://github.com/test/repo")
        self.assertEqual(res.job_id, "job-github-456")

    @patch("backend.sdk.api_client.urlopen")
    def test_document_analysis(self, mock_urlopen: MagicMock) -> None:
        """Verifies triggering document analysis."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"job_id": "job-doc-789", "status": "pending"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.document.analyze("ws-123", query="summary of the handbook")
        self.assertEqual(res.job_id, "job-doc-789")

    @patch("backend.sdk.api_client.urlopen")
    def test_professional_analysis(self, mock_urlopen: MagicMock) -> None:
        """Verifies triggering professional intelligence analysis."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"job_id": "job-prof-111", "status": "pending"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.professional.analyze("ws-123", resume_text="Resume", github_username="developer1")
        self.assertEqual(res.job_id, "job-prof-111")

    @patch("backend.sdk.api_client.urlopen")
    def test_workflow_execution(self, mock_urlopen: MagicMock) -> None:
        """Verifies triggering workflow runs."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"job_id": "job-wf-222", "status": "pending"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.workflows.run("wf-999", "ws-123")
        self.assertEqual(res.job_id, "job-wf-222")

    @patch("backend.sdk.api_client.urlopen")
    def test_job_status_check(self, mock_urlopen: MagicMock) -> None:
        """Verifies retrieving job status."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"job_id": "job-123", "status": "completed", "progress": 100.0, "module": "ResumeIntelligence", "result": {"key": "val"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        job = self.client.jobs.get_status("job-123")
        self.assertEqual(job.job_id, "job-123")
        self.assertEqual(job.status.value, "completed")
        self.assertEqual(job.progress, 100.0)

    @patch("backend.sdk.api_client.urlopen")
    def test_history_check(self, mock_urlopen: MagicMock) -> None:
        """Verifies listing execution history."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"history": [{"entry_id": "hist-1", "job_id": "job-1", "module": "Resume", "status": "completed", "workspace_id": "ws-1", "created_at": "2026-07-07", "execution_time": 1.2}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        history = self.client.jobs.list_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].entry_id, "hist-1")

    @patch("backend.sdk.api_client.urlopen")
    def test_authentication_error_wrapping(self, mock_urlopen: MagicMock) -> None:
        """Verifies 401 raises AuthenticationError."""
        # Setup mock for HTTPError
        fp = io.BytesIO(b'{"message": "Unauthorized client access"}')
        http_error = HTTPError("url", 401, "Unauthorized", {}, fp)
        mock_urlopen.side_effect = http_error

        with self.assertRaises(AuthenticationError):
            self.client.workspaces.list()

    @patch("backend.sdk.api_client.urlopen")
    def test_validation_error_wrapping(self, mock_urlopen: MagicMock) -> None:
        """Verifies 400 raises ValidationError."""
        fp = io.BytesIO(b'{"message": "Bad input parameter field"}')
        http_error = HTTPError("url", 400, "Bad Request", {}, fp)
        mock_urlopen.side_effect = http_error

        with self.assertRaises(ValidationError):
            self.client.workspaces.list()

    @patch("backend.sdk.api_client.urlopen")
    def test_rate_limit_error_wrapping(self, mock_urlopen: MagicMock) -> None:
        """Verifies 429 raises RateLimitError."""
        fp = io.BytesIO(b'{"message": "Too many requests", "details": {"retry_after_seconds": 60}}')
        http_error = HTTPError("url", 429, "Too Many Requests", {}, fp)
        mock_urlopen.side_effect = http_error

        with self.assertRaises(RateLimitError) as context:
            self.client.workspaces.list()
        self.assertEqual(context.exception.retry_after, 60)

    @patch("backend.sdk.api_client.urlopen")
    def test_provider_error_wrapping(self, mock_urlopen: MagicMock) -> None:
        """Verifies 502/503 raises ProviderError."""
        fp = io.BytesIO(b'{"message": "Upstream service timeout"}')
        http_error = HTTPError("url", 502, "Bad Gateway", {}, fp)
        mock_urlopen.side_effect = http_error

        with self.assertRaises(ProviderError):
            self.client.workspaces.list()

    def test_token_streaming(self) -> None:
        """Verifies parsing tokens from Server Sent Events."""
        sse_lines = [
            "data: " + json.dumps({"token": "Hello"}) + "\n",
            "data: " + json.dumps({"token": " "}) + "\n",
            "data: " + json.dumps({"token": "World"}) + "\n",
            "data: [DONE]\n"
        ]
        stream = TokenStream(iter(sse_lines))
        tokens = list(stream)
        self.assertEqual("".join(tokens), "Hello World")

    def test_sse_stream_events(self) -> None:
        """Verifies sse processing yields events."""
        sse_data = [
            b"data: " + json.dumps({"status": "running", "progress": 50}).encode("utf-8") + b"\n",
            b"data: [DONE]\n"
        ]
        stream = SSEStream(iter(sse_data))
        events = list(stream.events())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "running")

    def test_pagination_page(self) -> None:
        """Verifies page-based list pagination wrapper functionality."""
        page_2 = Page(items=["item3", "item4"])
        fetch_fn = lambda page_num: page_2

        page_1 = Page(items=["item1", "item2"], next_page=2, fetch_next_fn=fetch_fn)
        self.assertTrue(page_1.has_next())
        
        next_page = page_1.next()
        self.assertIsNotNone(next_page)
        self.assertEqual(next_page.items, ["item3", "item4"])

    def test_pagination_cursor(self) -> None:
        """Verifies cursor-based pagination wrapper functionality."""
        cursor_2 = Cursor(items=["itemC", "itemD"])
        fetch_fn = lambda cur_str: cursor_2

        cursor_1 = Cursor(items=["itemA", "itemB"], next_cursor="cursor_val", fetch_next_fn=fetch_fn)
        self.assertTrue(cursor_1.has_next())
        
        next_cursor = cursor_1.next()
        self.assertIsNotNone(next_cursor)
        self.assertEqual(next_cursor.items, ["itemC", "itemD"])

    @patch("asyncio.to_thread")
    def test_async_client(self, mock_to_thread: MagicMock) -> None:
        """Verifies async clients redirect call executions in threadpools correctly."""
        import asyncio
        from backend.sdk.models import WorkspaceInfo
        mock_to_thread.return_value = WorkspaceInfo(workspace_id="ws-async", name="Async Workspace")
        
        async def run_async_test():
            return await self.async_client.workspaces.create("Async Workspace")

        ws = asyncio.run(run_async_test())
        self.assertEqual(ws.workspace_id, "ws-async")
        mock_to_thread.assert_called_once()
        args, kwargs = mock_to_thread.call_args
        self.assertEqual(args[1], "Async Workspace")
