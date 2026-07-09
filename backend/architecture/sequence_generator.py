"""Sequence generator compiling sequence diagram workflows (Resume, GitHub, Document, Professional)."""

from __future__ import annotations

from typing import List

from backend.architecture.models import SequenceFlow, SequenceStep


class SequenceGenerator:
    """Auto-generates Mermaid sequence diagrams mapping request lifecycles."""

    @classmethod
    def generate_flow(cls, scenario: str) -> SequenceFlow:
        """Constructs sequence steps and formats a Mermaid sequence diagram string.

        Args:
            scenario: Target flow ("resume", "github", "document", "professional").

        Returns:
            SequenceFlow detailing the execution steps.
        """
        scenario_clean = scenario.lower().strip()
        steps: List[SequenceStep] = []

        if "resume" in scenario_clean:
            flow_name = "Resume Analysis Sequence"
            steps = [
                SequenceStep(sender="User", receiver="Gateway", message="POST /v1/resume/analyze (upload PDF)"),
                SequenceStep(sender="Gateway", receiver="Orchestrator", message="orchestrate_request(options)"),
                SequenceStep(sender="Orchestrator", receiver="Registry", message="get_module('resume')"),
                SequenceStep(sender="Registry", receiver="Orchestrator", message="ResumeModule instance"),
                SequenceStep(sender="Orchestrator", receiver="ResumeModule", message="execute_workflow(context)"),
                SequenceStep(sender="ResumeModule", receiver="Database", message="write_profile(user_id, data)"),
                SequenceStep(sender="ResumeModule", receiver="Orchestrator", message="ExecutionReport outcome"),
                SequenceStep(sender="Orchestrator", receiver="Gateway", message="OrchestratedResult payload"),
                SequenceStep(sender="Gateway", receiver="User", message="200 OK (Resume profile results)"),
            ]
        elif "github" in scenario_clean:
            flow_name = "GitHub Analysis Sequence"
            steps = [
                SequenceStep(sender="User", receiver="Gateway", message="POST /v1/github/analyze (repo URL)"),
                SequenceStep(sender="Gateway", receiver="Orchestrator", message="orchestrate_request(options)"),
                SequenceStep(sender="Orchestrator", receiver="GitHubModule", message="execute_workflow(context)"),
                SequenceStep(sender="GitHubModule", receiver="Database", message="save_github_health(metrics)"),
                SequenceStep(sender="Orchestrator", receiver="Gateway", message="OrchestratedResult payload"),
                SequenceStep(sender="Gateway", receiver="User", message="200 OK (Engineering Quality Report)"),
            ]
        elif "document" in scenario_clean:
            flow_name = "Document Analysis Sequence"
            steps = [
                SequenceStep(sender="User", receiver="Gateway", message="POST /v1/document/analyze (files)"),
                SequenceStep(sender="Gateway", receiver="Orchestrator", message="orchestrate_request(options)"),
                SequenceStep(sender="Orchestrator", receiver="DocumentModule", message="execute_workflow(context)"),
                SequenceStep(sender="DocumentModule", receiver="KnowledgeFabric", message="index_document(doc_id, text)"),
                SequenceStep(sender="Orchestrator", receiver="Gateway", message="OrchestratedResult payload"),
                SequenceStep(sender="Gateway", receiver="User", message="200 OK (Document analysis results)"),
            ]
        else:
            flow_name = "Professional Intelligence Sequence"
            steps = [
                SequenceStep(sender="User", receiver="Gateway", message="POST /v1/professional/analyze (workspace ID)"),
                SequenceStep(sender="Gateway", receiver="Orchestrator", message="orchestrate_request(options)"),
                SequenceStep(sender="Orchestrator", receiver="ProfessionalModule", message="execute_workflow(context)"),
                SequenceStep(sender="ProfessionalModule", receiver="KnowledgeFabric", message="retrieve_insights(user_id)"),
                SequenceStep(sender="Orchestrator", receiver="Gateway", message="OrchestratedResult payload"),
                SequenceStep(sender="Gateway", receiver="User", message="200 OK (Unified Professional Profile)"),
            ]

        # Generate Mermaid string
        mermaid_lines = ["sequenceDiagram", "  autonumber"]
        for s in steps:
            mermaid_lines.append(f"  {s.sender}->>{s.receiver}: {s.message}")

        return SequenceFlow(
            flow_name=flow_name,
            steps=steps,
            mermaid_diagram="\n".join(mermaid_lines),
        )
DefinitionPath = "sequence_generator.py"
