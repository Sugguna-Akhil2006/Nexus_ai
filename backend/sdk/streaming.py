"""Streaming Response helpers for Nexus AI SDK."""

from __future__ import annotations

import json
from typing import Any, Dict, Generator, Iterator, Optional


class TokenStream:
    """Iterator over token fragments returned by a streaming endpoint."""

    def __init__(self, response_generator: Iterator[str]) -> None:
        self._generator = response_generator

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        line = next(self._generator)
        if line.startswith("data: "):
            content = line[6:].strip()
            if content == "[DONE]":
                raise StopIteration
            try:
                data = json.loads(content)
                if "token" in data:
                    return data["token"]
            except Exception:
                pass
        return ""


class SSEStream:
    """Helper to process Server-Sent Events stream."""

    def __init__(self, raw_lines: Iterator[bytes]) -> None:
        self.raw_lines = raw_lines

    def events(self) -> Generator[Dict[str, Any], None, None]:
        """Yields parsed event payloads from the stream."""
        for line in self.raw_lines:
            decoded = line.decode("utf-8").strip()
            if decoded.startswith("data: "):
                data_str = decoded[6:]
                if data_str == "[DONE]":
                    break
                try:
                    yield json.loads(data_str)
                except Exception:
                    yield {"text": data_str}
