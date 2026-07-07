"""Tool Adapter mapping local intelligence capabilities to MCP Tool specifications."""

from __future__ import annotations

from typing import Any, Dict

from backend.mcp.models import MCPTool


class MCPToolAdapter:
    """Exposes local platform modules as standard MCP tools."""

    def get_sdk_tools(self) -> Dict[str, MCPTool]:
        """Compiles local tool specifications."""
        return {
            "resume_analyze": MCPTool(
                name="resume_analyze",
                description="Performs skill extraction and ATS analysis on resume contents.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {"type": "string"},
                        "resume_text": {"type": "string"}
                    },
                    "required": ["workspace_id", "resume_text"]
                }
            ),
            "github_analyze": MCPTool(
                name="github_analyze",
                description="Audits repositories health scoring and language density metrics.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {"type": "string"},
                        "repository_url": {"type": "string"}
                    },
                    "required": ["workspace_id", "repository_url"]
                }
            ),
            "document_query": MCPTool(
                name="document_query",
                description="Performs semantic retrieval queries across workspace documents.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {"type": "string"},
                        "query": {"type": "string"}
                    },
                    "required": ["workspace_id", "query"]
                }
            ),
            "professional_analyze": MCPTool(
                name="professional_analyze",
                description="Compiles cross-intelligence career analysis reports.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {"type": "string"},
                        "user_id": {"type": "string"},
                        "resume_text": {"type": "string"},
                        "target_role": {"type": "string"}
                    },
                    "required": ["workspace_id", "user_id", "resume_text", "target_role"]
                }
            )
        }

    def execute_local_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Routes execution call to local intelligence modules via gateway."""
        from backend.api.intelligence.gateway import IntelligenceGateway
        gateway = IntelligenceGateway()

        if name == "resume_analyze":
            res = gateway.execute("RESUME_PARSING", params.get("workspace_id", "default"), params)
            return {"status": "success", "result": res.output_summary}
        elif name == "github_analyze":
            res = gateway.execute("GITHUB_INTELLIGENCE", params.get("workspace_id", "default"), params)
            return {"status": "success", "result": res.output_summary}
        elif name == "document_query":
            res = gateway.execute("DOCUMENT_QUERY", params.get("workspace_id", "default"), params)
            return {"status": "success", "result": res.output_summary}
        elif name == "professional_analyze":
            from backend.intelligence.professional.professional_agent import ProfessionalAgent
            from backend.intelligence.professional.models import ProfessionalAnalysisRequest
            agent = ProfessionalAgent()
            req = ProfessionalAnalysisRequest(
                workspace_id=params["workspace_id"],
                user_id=params["user_id"],
                resume_text=params["resume_text"],
                target_role=params["target_role"]
            )
            rep = agent.analyze(req)
            return {"status": "success", "result": {"ats_score": rep.ats_score}}
        else:
            raise ValueError(f"Unknown local MCP tool: '{name}'.")
