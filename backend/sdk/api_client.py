"""Low-level HTTP client for Nexus AI public API."""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Iterator, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.sdk.authentication import Authenticator
from backend.sdk.config import NexusConfig
from backend.sdk.exceptions import ExecutionError, NexusSDKError, map_status_to_exception
from backend.sdk.middleware import MiddlewareChain


class APIClient:
    """Thread-safe synchronous HTTP client for the Nexus AI public API."""

    def __init__(
        self,
        config: NexusConfig,
        authenticator: Optional[Authenticator] = None,
        middleware: Optional[MiddlewareChain] = None,
    ) -> None:
        self._config = config
        self._authenticator = authenticator or Authenticator(config)
        self._middleware = middleware or MiddlewareChain()

    @property
    def config(self) -> NexusConfig:
        """Returns the client configuration.

        Returns:
            NexusConfig instance.
        """
        return self._config

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
        """Executes an HTTP request against the public API.

        Args:
            method: HTTP method verb.
            path: API path relative to the versioned base (e.g. ``/resume/analyze``).
            body: Optional JSON request body.
            params: Optional query parameters.
            headers: Optional additional headers.
            timeout: Optional per-request timeout override.

        Returns:
            Tuple of (status_code, parsed_json_body, response_headers).

        Raises:
            NexusSDKError: On HTTP or network errors.
        """
        correlation_id = f"req-{uuid.uuid4().hex[:12]}"
        url = f"{self._config.api_base}{path}"
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url = f"{url}?{urlencode(filtered)}"

        req_headers = self._authenticator.build_headers(headers)
        req_headers["X-Correlation-ID"] = correlation_id

        data: Optional[bytes] = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        prepared = self._middleware.process_request(
            method=method,
            url=url,
            headers=req_headers,
            body=body,
        )

        request = Request(
            prepared["url"],
            data=data,
            headers=prepared["headers"],
            method=method.upper(),
        )

        try:
            with urlopen(request, timeout=timeout or self._config.timeout) as response:
                raw = response.read().decode("utf-8")
                status = response.status
                resp_headers = dict(response.headers)
                parsed: Dict[str, Any] = json.loads(raw) if raw else {}
        except HTTPError as exc:
            status = exc.code
            resp_headers = dict(exc.headers) if exc.headers else {}
            raw = exc.read().decode("utf-8") if exc.fp else "{}"
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"message": raw or str(exc)}
            error = map_status_to_exception(status, parsed, correlation_id)
            self._middleware.process_error(error)
            raise error from exc
        except URLError as exc:
            raise ExecutionError(
                f"Network error: {exc.reason}",
                correlation_id=correlation_id,
            ) from exc
        except json.JSONDecodeError as exc:
            raise ExecutionError(
                "Invalid JSON response from server.",
                correlation_id=correlation_id,
            ) from exc

        result_body = self._middleware.process_response(
            status_code=status,
            body=parsed,
            headers=resp_headers,
        )
        return status, result_body, resp_headers

    def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Executes a GET request.

        Args:
            path: API path relative to the versioned base.
            params: Optional query parameters.
            headers: Optional additional headers.

        Returns:
            Parsed JSON response body.
        """
        _, body, _ = self.request("GET", path, params=params, headers=headers)
        return body

    def post(
        self,
        path: str,
        *,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Executes a POST request.

        Args:
            path: API path relative to the versioned base.
            body: Optional JSON request body.
            params: Optional query parameters.
            headers: Optional additional headers.

        Returns:
            Parsed JSON response body.
        """
        _, body, _ = self.request("POST", path, body=body, params=params, headers=headers)
        return body

    def stream_sse(
        self,
        path: str,
        *,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Opens a Server-Sent Events stream and yields parsed event payloads.

        Args:
            path: API path relative to the versioned base.
            body: Optional JSON request body for POST-initiated streams.
            headers: Optional additional headers.

        Yields:
            Parsed SSE event data dictionaries.
        """
        correlation_id = f"req-{uuid.uuid4().hex[:12]}"
        url = f"{self._config.api_base}{path}"
        req_headers = self._authenticator.build_headers(headers)
        req_headers["Accept"] = "text/event-stream"
        req_headers["X-Correlation-ID"] = correlation_id

        data: Optional[bytes] = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        request = Request(url, data=data, headers=req_headers, method="POST")

        try:
            with urlopen(request, timeout=self._config.timeout) as response:
                buffer = ""
                for chunk in iter(lambda: response.read(1024), b""):
                    buffer += chunk.decode("utf-8")
                    while "\n\n" in buffer:
                        event_block, buffer = buffer.split("\n\n", 1)
                        event_data = _parse_sse_block(event_block)
                        if event_data is not None:
                            yield event_data
        except HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp else "{}"
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"message": raw}
            raise map_status_to_exception(exc.code, parsed, correlation_id) from exc
        except URLError as exc:
            raise ExecutionError(f"Network error: {exc.reason}") from exc


def _parse_sse_block(block: str) -> Optional[Dict[str, Any]]:
    """Parses a single SSE event block into a dictionary.

    Args:
        block: Raw SSE event text block.

    Returns:
        Parsed event data dictionary, or None for empty/comment blocks.
    """
    data_lines: list[str] = []
    for line in block.split("\n"):
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if not data_lines:
        return None
    raw = "\n".join(data_lines)
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"data": parsed}
    except json.JSONDecodeError:
        return {"data": raw}
