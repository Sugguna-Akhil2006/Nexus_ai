"""MemoryBuilder - configures memory backend for ADK agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class MemoryConfig:
    """Resolved memory backend configuration.

    Attributes:
        backend: Backend type (``"in_memory"``, ``"sqlite"``, ``"redis"``).
        max_entries: Maximum number of memory entries to retain.
        ttl_seconds: Time-to-live for entries in seconds (0 = no expiry).
        connection_url: Optional connection URL for remote backends.
        options: Additional backend-specific options.
    """

    backend: str = "in_memory"
    max_entries: int = 1000
    ttl_seconds: int = 0
    connection_url: str = ""
    options: Dict[str, Any] = field(default_factory=dict)


class MemoryBuilder:
    """Fluent builder for memory backend configuration.

    Example::

        memory = (
            MemoryBuilder()
            .backend("sqlite")
            .max_entries(500)
            .ttl(3600)
            .build()
        )
    """

    def __init__(self) -> None:
        self._backend: str = "in_memory"
        self._max_entries: int = 1000
        self._ttl_seconds: int = 0
        self._connection_url: str = ""
        self._options: Dict[str, Any] = {}

    def backend(self, backend_type: str) -> "MemoryBuilder":
        """Sets the memory backend type.

        Args:
            backend_type: One of ``"in_memory"``, ``"sqlite"``, ``"redis"``.

        Returns:
            Self for method chaining.
        """
        self._backend = backend_type
        return self

    def max_entries(self, count: int) -> "MemoryBuilder":
        """Sets the maximum number of memory entries.

        Args:
            count: Maximum entry count.

        Returns:
            Self for method chaining.
        """
        self._max_entries = count
        return self

    def ttl(self, seconds: int) -> "MemoryBuilder":
        """Sets time-to-live for memory entries.

        Args:
            seconds: TTL in seconds (0 = no expiry).

        Returns:
            Self for method chaining.
        """
        self._ttl_seconds = seconds
        return self

    def connection_url(self, url: str) -> "MemoryBuilder":
        """Sets the connection URL for remote memory backends.

        Args:
            url: Connection string (e.g. ``"redis://localhost:6379"``).

        Returns:
            Self for method chaining.
        """
        self._connection_url = url
        return self

    def option(self, key: str, value: Any) -> "MemoryBuilder":
        """Sets a backend-specific option.

        Args:
            key: Option key.
            value: Option value.

        Returns:
            Self for method chaining.
        """
        self._options[key] = value
        return self

    def build(self) -> MemoryConfig:
        """Constructs the final MemoryConfig.

        Returns:
            Validated MemoryConfig instance.
        """
        return MemoryConfig(
            backend=self._backend,
            max_entries=self._max_entries,
            ttl_seconds=self._ttl_seconds,
            connection_url=self._connection_url,
            options=dict(self._options),
        )
