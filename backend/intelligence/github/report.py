"""Generates the unified, comprehensive engineering and health reports for GitHub repositories."""

import uuid
from datetime import datetime
from typing import List, Dict, Any

from backend.intelligence.github.models import (
    RepositoryAnalysisReport,
    EngineeringAnalysisReport,
    RepositoryHealthReport,
    GitHubIntelligenceReport,
    DeveloperSkillEvidence
)


class GitHubReportGenerator:
    """Consolidates findings from parsing, architecture analysis, and commit timelines into a final product report."""

    def generate_report(
        self,
        repo_report: RepositoryAnalysisReport,
        quality_report: EngineeringAnalysisReport,
        health_report: RepositoryHealthReport,
        workspace_id: str = "default-ws"
    ) -> GitHubIntelligenceReport:
        """Constructs a consolidated product report.

        Args:
            repo_report: Static files and technology scan results.
            quality_report: Code quality, security, and complexity audit results.
            health_report: Git activity logs, contributors, and health score results.
            workspace_id: Associated workspace ID.

        Returns:
            GitHubIntelligenceReport: Unified 12-section product report.
        """
        report_id = f"rep-{str(uuid.uuid4())[:8]}"

        # Technology stack mapping
        languages = []
        frameworks = []
        for tech in repo_report.detected_technologies:
            if tech.category in ["Language", "Programming Languages"]:
                languages.append(tech.name)
            else:
                frameworks.append(tech.name)

        tech_stack = {
            "languages": languages,
            "frameworks": frameworks,
            "raw_technologies": [t.model_dump() for t in repo_report.detected_technologies]
        }

        # Repository overview
        overview = {
            "file_count": repo_report.file_count,
            "total_lines": repo_report.total_lines,
            "branch": repo_report.branch,
            "total_commits": health_report.total_commits,
            "active_contributors": health_report.active_contributors,
            "bus_factor": health_report.bus_factor,
            "workspace_id": workspace_id
        }

        # Engineering Quality mapping
        quality = {
            "maintainability_score": quality_report.maintainability_score,
            "complexity_score": quality_report.complexity_score,
            "detected_patterns": quality_report.detected_patterns,
            "detected_anti_patterns": quality_report.detected_anti_patterns,
            "circular_dependencies": quality_report.circular_dependencies,
            "improvements": [imp.model_dump() for imp in quality_report.improvements]
        }

        # Repository Health mapping
        health = {
            "overall_health_score": health_report.health_scores.overall_health_score,
            "health_scores": health_report.health_scores.model_dump(),
            "releases": [rel.model_dump() for rel in health_report.releases],
            "burst_activities": [burst.model_dump() for burst in health_report.burst_activities],
            "inactive_periods": [p.model_dump() for p in health_report.inactive_periods]
        }

        # Documentation Quality mapping
        doc_quality = {}
        if repo_report.documentation:
            doc_quality = repo_report.documentation.model_dump()

        # Executive summary generation
        primary_lang = languages[0] if languages else "Software"
        overall_health = health_report.health_scores.overall_health_score
        maintainability = quality_report.maintainability_score
        exec_summary = (
            f"The repository {repo_report.repository_url} has been analyzed successfully. "
            f"It is a {primary_lang}-based project containing {repo_report.file_count} files "
            f"and {repo_report.total_lines} lines of code. The overall project health score "
            f"is evaluated as {overall_health}/100 with a code maintainability index of {maintainability}/100. "
            f"We identified {health_report.active_contributors} active contributors and a Bus Factor of {health_report.bus_factor}."
        )

        # Extract strengths & risks
        strengths = []
        risks = []

        # From health insights
        for ins in health_report.insights:
            if ins.priority in ["Medium", "High"] and ins.insight_type in ["Activity", "Maintenance"]:
                strengths.append(ins.description)
            elif ins.priority == "High":
                risks.append(ins.description)

        # Add generic fallback if empty
        if not strengths:
            if maintainability >= 75.0:
                strengths.append("High codebase maintainability and clean modular structure.")
            if overall_health >= 70.0:
                strengths.append("Active repository with consistent commit frequency.")

        for imp in quality_report.improvements:
            if imp.priority == "High":
                risks.append(f"Security Alert: {imp.description}")

        if health_report.bus_factor == 1:
            risks.append("Silo Risk: Bus Factor is 1. Knowledge distribution is concentrated in a single contributor.")

        if repo_report.documentation and not repo_report.documentation.has_readme:
            risks.append("Documentation Risk: Repository is missing a README.md file.")

        if not risks:
            risks.append("No immediate high-severity security or dependency risks identified.")

        # Roadmap
        roadmap = []
        for rec in health_report.recommendations:
            roadmap.append(f"Recommend to {rec.action.lower()}: {rec.rationale}")
        for imp in quality_report.improvements:
            roadmap.append(f"Improvement ({imp.issue_type}): {imp.suggested_fix} in {imp.file_path}")

        if not roadmap:
            roadmap.append("Continue regular maintenance and monitor dependency updates.")

        # Developer Skill Evidence
        skill_evidence = []
        for tech in repo_report.detected_technologies:
            if tech.category in ["Language", "Programming Languages", "Framework"]:
                exp_lvl = "Intermediate"
                if repo_report.total_lines > 5000:
                    exp_lvl = "Expert"
                elif repo_report.total_lines < 1000:
                    exp_lvl = "Beginner"

                evidence_desc = f"Identified usage of {tech.name} in codebase files."
                skill_evidence.append(DeveloperSkillEvidence(
                    skill_name=tech.name,
                    experience_level=exp_lvl,
                    evidence_description=evidence_desc,
                    associated_files=[tech.name]
                ))

        # Knowledge Profile Updates
        kp_updates = {
            "new_skills": languages + frameworks,
            "repositories_added": [repo_report.repository_url]
        }

        # Execution timings mapping
        timings = {
            "Parser": 0.0,
            "Code Quality": 0.0,
            "Activity Analysis": 0.0,
            "Total": 0.0
        }

        return GitHubIntelligenceReport(
            report_id=report_id,
            repository=repo_report.repository_url,
            timestamp=datetime.utcnow(),
            knowledge_profile_version="1.0",
            executive_summary=exec_summary,
            repository_overview=overview,
            technology_stack=tech_stack,
            architecture_style=repo_report.architecture.name if repo_report.architecture else "Traditional Monolith",
            engineering_quality=quality,
            repository_health=health,
            documentation_quality=doc_quality,
            strengths=strengths,
            engineering_risks=risks,
            improvement_roadmap=roadmap,
            developer_skill_evidence=skill_evidence,
            knowledge_profile_updates=kp_updates,
            pipeline_stage="Completed",
            execution_metrics=timings
        )
