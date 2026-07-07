"""Resource Adapter mapping workspace documents and assets to MCP URI schemas."""

from __future__ import annotations

from typing import List

from backend.mcp.models import MCPResource


class MCPResourceAdapter:
    """Maps workspace contents, profiles, and reports to MCP resources URI structures."""

    def get_sdk_resources(self, workspace_id: str) -> List[MCPResource]:
        """Lists active documents and profiles as exposed MCP resources."""
        # Query local database using SQLite connection
        from backend.api.sqlite_mock import DBStorage
        db = DBStorage()
        
        resources = []
        conn = db._get_connection()
        try:
            rows = conn.execute("SELECT * FROM documents WHERE workspace_id = ?", (workspace_id,)).fetchall()
            for r in rows:
                resources.append(MCPResource(
                    uri=f"mcp://{workspace_id}/document/{r['document_id']}",
                    name=r["name"],
                    mimeType="text/plain",
                    description=f"Plaintext content asset for: {r['name']}"
                ))
        except Exception:
            pass
        finally:
            conn.close()

        # Add profile
        resources.append(MCPResource(
            uri=f"mcp://{workspace_id}/profile/knowledge",
            name="Workspace Knowledge Profile",
            mimeType="application/json",
            description="Consolidated skillset, history and portfolio metrics profile."
        ))
        
        return resources
