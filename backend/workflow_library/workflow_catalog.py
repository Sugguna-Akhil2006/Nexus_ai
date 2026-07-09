"""Workflow catalog detailing built-in automation templates."""

from __future__ import annotations

from typing import List

from backend.workflow_library.models import TemplateScope, WorkflowTemplate


class WorkflowCatalog:
    """Pre-seeds standard system templates for quick workflow instantiations."""

    @staticmethod
    def get_builtin_templates() -> List[WorkflowTemplate]:
        """Returns standard pre-seeded automated templates.

        Returns:
            List of WorkflowTemplates.
        """
        return [
            WorkflowTemplate(
                template_id="tpl-resume-review",
                name="Resume Review",
                description="Extracts candidate career trajectory metadata and profiles ATS compatibility metrics.",
                steps=["ExtractText", "ParseSkills", "EvaluateATSCompatibility"],
                variables={"model": "gpt-4", "ats_role": "Software Engineer"},
                scope=TemplateScope.MARKETPLACE,
                version="1.0.0",
                created_at="2026-07-07T12:00:00Z",
            ),
            WorkflowTemplate(
                template_id="tpl-github-review",
                name="GitHub Repository Review",
                description="Evaluates repository code maintainability split indices and developer activity scores.",
                steps=["CloneRepo", "AnalyzeLanguages", "AuditCodeQuality"],
                variables={"model": "claude-3", "depth": "full"},
                scope=TemplateScope.MARKETPLACE,
                version="1.0.0",
                created_at="2026-07-07T12:00:00Z",
            ),
            WorkflowTemplate(
                template_id="tpl-tech-interview",
                name="Technical Interview Preparation",
                description="Generates custom coding and architecture challenge interview prompts.",
                steps=["GenerateChallenges", "AssessResponses", "GradeAnswers"],
                variables={"topic": "System Design"},
                scope=TemplateScope.MARKETPLACE,
                version="1.0.0",
                created_at="2026-07-07T12:00:00Z",
            ),
            WorkflowTemplate(
                template_id="tpl-doc-summary",
                name="Document Summarization",
                description="Aggregates long technical guides into structured summary documents.",
                steps=["ChunkFiles", "SummarizeSections", "AssembleOutline"],
                variables={"summary_format": "bullets"},
                scope=TemplateScope.MARKETPLACE,
                version="1.0.0",
                created_at="2026-07-07T12:00:00Z",
            ),
            WorkflowTemplate(
                template_id="tpl-career-roadmap",
                name="Career Roadmap Generation",
                description="Maps out customized skill-acquisition target milestones based on current roles.",
                steps=["ParseCurrentRole", "RecommendSkills", "FormulateTimeline"],
                variables={"target_level": "Principal Architect"},
                scope=TemplateScope.MARKETPLACE,
                version="1.0.0",
                created_at="2026-07-07T12:00:00Z",
            ),
            WorkflowTemplate(
                template_id="tpl-proj-doc",
                name="Project Documentation Generator",
                description="Auto-generates markdown handbooks from active project folders.",
                steps=["ScanProjectFiles", "CompileAPIList", "GenerateDeveloperGuide"],
                variables={"doc_type": "handbook"},
                scope=TemplateScope.MARKETPLACE,
                version="1.0.0",
                created_at="2026-07-07T12:00:00Z",
            ),
        ]
DefinitionPath = "workflow_catalog.py"
