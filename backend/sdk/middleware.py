"""Request/response middleware chain for Nexus AI SDK clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.sdk.exceptions import NexusSDKError


class SDKMiddleware(ABC):
    """Abstract middleware hook for SDK HTTP requests."""

    @abstractmethod
    def on_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Processes an outgoing request before it is sent.

        Args:
            method: HTTP method verb.
            url: Fully qualified request URL.
            headers: Request headers.
            body: Optional JSON body.

        Returns:
            Dictionary with optional ``url``, ``headers``, and ``body`` overrides.
        """
        ...

    @abstractmethod
    def on_response(
        self,
        status_code: int,
        body: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Processes a successful response before returning to the caller.

        Args:
            status_code: HTTP status code.
            body: Parsed JSON response body.
            headers: Response headers.

        Returns:
            Potentially modified response body dictionary.
        """
        ...

    def on_error(self, error: NexusSDKError) -> None:
        """Called when a request fails with an SDK exception.

        Args:
            error: The raised SDK exception.
        """


class LoggingMiddleware(SDKMiddleware):
    """Debug middleware that records request/response metadata."""

    def __init__(self) -> None:
        self.last_request: Optional[Dict[str, Any]] = None
        self.last_response: Optional[Dict[str, Any]] = None
        self.last_error: Optional[NexusSDKError] = None

    def on_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        self.last_request = {"method": method, "url": url, "body": body}
        return {}

    def on_response(
        self,
        status_code: int,
        body: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        self.last_response = {"status_code": status_code, "body": body}
        return body

    def on_error(self, error: NexusSDKError) -> None:
        self.last_error = error


class RetryMiddleware(SDKMiddleware):
    """Records retry metadata; actual retries are handled at the client layer."""

    def __init__(self) -> None:
        self.retry_count: int = 0

    def on_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {}

    def on_response(
        self,
        status_code: int,
        body: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        return body


class MiddlewareChain:
    """Executes a chain of SDK middleware in order."""

    def __init__(self, middlewares: Optional[List[SDKMiddleware]] = None) -> None:
        self._middlewares: List[SDKMiddleware] = list(middlewares or [])

    def add(self, middleware: SDKMiddleware) -> None:
        """Appends a middleware to the chain.

        Args:
            middleware: Middleware instance to append.
        """
        self._middlewares.append(middleware)

    def process_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Runs all middleware on_request hooks.

        Args:
            method: HTTP method verb.
            url: Request URL.
            headers: Request headers.
            body: Optional JSON body.

        Returns:
            Merged overrides from all middleware.
        """
        merged: Dict[str, Any] = {"url": url, "headers": dict(headers), "body": body}
        for mw in self._middlewares:
            overrides = mw.on_request(method, url, merged["headers"], merged["body"])
            if "url" in overrides:
                merged["url"] = overrides["url"]
            if "headers" in overrides:
                merged["headers"].update(overrides["headers"])
            if "body" in overrides:
                merged["body"] = overrides["body"]
        return merged

    def process_response(
        self,
        status_code: int,
        body: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Runs all middleware on_response hooks in reverse order.

        Args:
            status_code: HTTP status code.
            body: Parsed JSON response body.
            headers: Response headers.

        Returns:
            Final response body after middleware processing.
        """
        result = body
        for mw in reversed(self._middlewares):
            result = mw.on_response(status_code, result, headers)
        return result

    def process_error(self, error: NexusSDKError) -> None:
        """Notifies all middleware of a request error.

        Args:
            error: The raised SDK exception.
        """
        for mw in self._middlewares:
            mw.on_error(error)
