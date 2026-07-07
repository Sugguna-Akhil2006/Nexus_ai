"""Capability Manager negotiating handshakes, prompts, and tools list."""

from __future__ import annotations

from typing import Dict, List

from backend.mcp.models import MCPTool, MCPResource, MCPPrompt


class MCPCapabilityManager:
    """Manages MCP handshake capability negotiations."""

    def __init__(self) -> None:
        self._tools: Dict[str, MCPTool] = {}
        self._resources: Dict[str, MCPResource] = {}
        self._prompts: Dict[str, MCPPrompt] = {}

    def register_tool(self, tool: MCPTool) -> None:
        self._tools[tool.name] = tool

    def register_resource(self, resource: MCPResource) -> None:
        self._resources[resource.uri] = resource

    def register_prompt(self, prompt: MCPPrompt) -> None:
        self._prompts[prompt.name] = prompt

    def list_tools(self) -> List[MCPTool]:
        return list(self._tools.values())

    def list_resources(self) -> List[MCPResource]:
        return list(self._resources.values())

    def list_prompts(self) -> List[MCPPrompt]:
        return list(self._prompts.values())

    def get_tool(self, name: str) -> Optional[MCPTool]:
        return self._tools.get(name)

    def get_resource(self, uri: str) -> Optional[MCPResource]:
        return self._resources.get(uri)

    def get_prompt(self, name: str) -> Optional[MCPPrompt]:
        return self._prompts.get(name)
