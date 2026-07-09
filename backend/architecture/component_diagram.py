"""Component diagram compiler formatting Mermaid graph definitions."""

from __future__ import annotations


class ComponentDiagram:
    """Compiles complete system architecture component layout representations in Mermaid."""

    @staticmethod
    def compile_diagram() -> str:
        """Returns a Mermaid graph layout representing all primary subsystem packages."""
        diagram = """graph LR
    subgraph Client ["Client Layer"]
        UI["React/TypeScript Frontend"]
        SDK["Python SDK Client"]
    end

    subgraph API ["Gateway Layer"]
        FASTAPI["FastAPI Routing Services"]
    end

    subgraph Core ["Orchestration & Runtime"]
        ORCH["Dynamic Execution Orchestrator"]
        BUS["Thread-safe Event Bus"]
        REGISTRY["Intelligence Module Registry"]
    end

    subgraph Modules ["Intelligence Systems"]
        RESUME["Resume Intelligence"]
        GITHUB["GitHub Intelligence"]
        DOCS["Document Intelligence"]
        PROF["Professional Report Analyzer"]
    end

    subgraph Data ["Storage & Fabric"]
        DB["Relational Database SQLite"]
        FABRIC["Knowledge Fabric Vector DB"]
    end

    UI --> FASTAPI
    SDK --> FASTAPI
    FASTAPI --> ORCH
    ORCH --> BUS
    ORCH --> REGISTRY
    REGISTRY --> RESUME
    REGISTRY --> GITHUB
    REGISTRY --> DOCS
    REGISTRY --> PROF
    RESUME --> DB
    GITHUB --> DB
    DOCS --> FABRIC
    PROF --> FABRIC
"""
        return diagram
DefinitionPath = "component_diagram.py"
