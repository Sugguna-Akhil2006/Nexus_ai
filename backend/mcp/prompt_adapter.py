"""Prompt Adapter mapping registered prompts to MCP Prompt specifications."""

from __future__ import annotations

from typing import List

from backend.mcp.models import MCPPrompt


class MCPPromptAdapter:
    """Exposes system prompt libraries to MCP client systems."""

    def get_sdk_prompts(self) -> List[MCPPrompt]:
        """Lists common reusable templates."""
        return [
            MCPPrompt(
                name="chat-instruction",
                description="Default system instruction to enforce assistant constraints.",
                arguments=[
                    {"name": "tone", "description": "Assistant tone (professional/playful)", "required": False}
                ]
            ),
            MCPPrompt(
                name="ats-extraction",
                description="Prompt to parse resumes and compile ATS scores list.",
                arguments=[
                    {"name": "role", "description": "Target job role name", "required": True}
                ]
            )
        ]
