"""MCP Server exposing local intelligence capabilities as standard MCP JSON-RPC methods."""

from __future__ import annotations

from typing import Dict, List, Optional
import uuid

from backend.mcp.models import JSONRPCRequest, JSONRPCResponse, MCPTool, MCPResource, MCPPrompt
from backend.mcp.session import MCPSession
from backend.mcp.transport import StdioTransport
from backend.mcp.tool_adapter import MCPToolAdapter
from backend.mcp.resource_adapter import MCPResourceAdapter
from backend.mcp.prompt_adapter import MCPPromptAdapter


class MCPServer:
    """Orchestrates JSON-RPC request routing to adapters representing local features."""

    def __init__(self) -> None:
        self.tool_adapter = MCPToolAdapter()
        self.resource_adapter = MCPResourceAdapter()
        self.prompt_adapter = MCPPromptAdapter()

    def bind_to_session(self, session: MCPSession) -> None:
        """Hooks handler loops on the active session."""
        session.register_handler("tools/list", self._handle_list_tools)
        session.register_handler("tools/call", self._handle_call_tool)
        session.register_handler("resources/list", self._handle_list_resources)
        session.register_handler("prompts/list", self._handle_list_prompts)

    def _handle_list_tools(self, req: JSONRPCRequest) -> JSONRPCResponse:
        tools_map = self.tool_adapter.get_sdk_tools()
        tools_list = [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.inputSchema
            } for t in tools_map.values()
        ]
        return JSONRPCResponse(id=req.id, result={"tools": tools_list})

    def _handle_call_tool(self, req: JSONRPCRequest) -> JSONRPCResponse:
        name = req.params.get("name")
        arguments = req.params.get("arguments", {})
        if not name:
            return JSONRPCResponse(
                id=req.id,
                error={"code": -32602, "message": "Missing required parameter: 'name'."}
            )

        try:
            out = self.tool_adapter.execute_local_tool(name, arguments)
            return JSONRPCResponse(id=req.id, result=out)
        except Exception as e:
            return JSONRPCResponse(
                id=req.id,
                error={"code": -32603, "message": f"Execution error: {str(e)}"}
            )

    def _handle_list_resources(self, req: JSONRPCRequest) -> JSONRPCResponse:
        workspace_id = req.params.get("workspace_id", "default")
        resources = self.resource_adapter.get_sdk_resources(workspace_id)
        res_list = [
            {
                "uri": r.uri,
                "name": r.name,
                "mimeType": r.mimeType,
                "description": r.description
            } for r in resources
        ]
        return JSONRPCResponse(id=req.id, result={"resources": res_list})

    def _handle_list_prompts(self, req: JSONRPCRequest) -> JSONRPCResponse:
        prompts = self.prompt_adapter.get_sdk_prompts()
        prompt_list = [
            {
                "name": p.name,
                "description": p.description,
                "arguments": p.arguments
            } for p in prompts
        ]
        return JSONRPCResponse(id=req.id, result={"prompts": prompt_list})
