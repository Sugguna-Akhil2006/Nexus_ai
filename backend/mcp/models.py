"""Data schemas representing JSON-RPC requests, capability lists, and adapters specifications for MCP."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 request envelope."""

    jsonrpc: str = "2.0"
    method: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 response envelope."""

    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


@dataclass
class MCPTool:
    """Defines an MCP Tool specification advertised by servers."""

    name: str
    description: str
    inputSchema: Dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})


@dataclass
class MCPResource:
    """Defines an MCP Resource mapping representing content assets."""

    uri: str
    name: str
    mimeType: str
    description: str = ""


@dataclass
class MCPPrompt:
    """Defines an MCP Prompt representation containing arguments guidelines."""

    name: str
    description: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MCPServerInfo:
    """Contains information about a registered or connected MCP server."""

    server_id: str
    name: str
    version: str
    url: Optional[str] = None
    status: str = "disconnected"
    tools: List[MCPTool] = field(default_factory=list)
    resources: List[MCPResource] = field(default_factory=list)
    prompts: List[MCPPrompt] = field(default_factory=list)
