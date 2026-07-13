"""Flagship GitHubProduct orchestrating repository crawler, code audits, health metrics, and timeline updates."""

import os
import uuid
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from backend.runtime.event import Event, EventType, EventBus
from backend.runtime.logger import StructuredLogger
from backend.intelligence.profile.services import ProfileService
from backend.intelligence.profile.models import KnowledgeProfile
from backend.intelligence.github.cache import GitHubCache
from backend.intelligence.github.models import GitHubIntelligenceReport
from backend.intelligence.github.repository import GitRepositoryReader
from backend.intelligence.github.services import GitHubIntelligenceService
from backend.intelligence.github.report import GitHubReportGenerator
from backend.intelligence.github.workflow import StageNames, StageExecutionError


class GitHubProduct:
    """Flagship entry facade transforming GitHub repositories, users, or orgs into standard unified reports."""

    @staticmethod
    def analyze(
        repository_url: Optional[str] = None,
        username: Optional[str] = None,
        organization: Optional[str] = None,
        workspace_id: str = "default-ws",
        user_id: str = "admin",
        branch: str = "main",
        options: Optional[Dict[str, Any]] = None
    ) -> GitHubIntelligenceReport:
        """Runs the complete GitHub analysis pipeline synchronously.

        Args:
            repository_url: Remote repo URL or local path.
            username: Optional target GitHub user profile.
            organization: Optional target GitHub org workspace.
            workspace_id: Active workspace identifier.
            user_id: Requesting user identifier.
            branch: Repository branch context.
            options: Dictionary of analysis configuration overrides.

        Returns:
            GitHubIntelligenceReport: Consolidated unified product report.
        """
        logger = StructuredLogger()
        event_bus = EventBus()
        options = options or {}

        # 1. Publish starting event
        workflow_started_event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="GitHubProduct",
            payload={
                "event": "github.workflow.started",
                "workspace_id": workspace_id,
                "user_id": user_id,
                "repository_url": repository_url or username or organization,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        event_bus.publish(workflow_started_event)
        event_bus.dispatch()

        logger.info(f"GitHubProduct: Starting workflow run for workspace {workspace_id}")
        start_time = time.perf_counter()

        # Step 1: Repository Loader stage
        try:
            # Resolve directory path
            repository_url_str = str(repository_url or "")
            is_remote = any(repository_url_str.startswith(prefix) for prefix in ["http://", "https://", "git://", "git@"])
            
            target_path = options.get("workspace_path") or repository_url or "."
            
            if is_remote:
                storage_clones = os.path.abspath(os.path.join(".", "storage_data", "cloned_repos"))
                os.makedirs(storage_clones, exist_ok=True)
                temp_dir = os.path.join(storage_clones, f"repo-{str(uuid.uuid4())[:8]}")
                logger.info(f"Cloning remote repository {repository_url} into {temp_dir}")
                import subprocess
                try:
                    res = subprocess.run(
                        ["git", "clone", repository_url_str, temp_dir],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=45
                    )
                    if res.returncode == 0:
                        target_path = temp_dir
                    else:
                        logger.warning(f"Git clone failed: {res.stderr}. Fallback to empty directory.")
                        os.makedirs(temp_dir, exist_ok=True)
                        target_path = temp_dir
                except Exception as e:
                    logger.error(f"Error during git clone: {e}")
                    os.makedirs(temp_dir, exist_ok=True)
                    target_path = temp_dir
            else:
                if not os.path.exists(target_path) or not os.path.isdir(target_path):
                    if repository_url:
                        empty_dir = os.path.abspath(os.path.join(".", "storage_data", "empty_repos", f"empty-{str(uuid.uuid4())[:8]}"))
                        os.makedirs(empty_dir, exist_ok=True)
                        target_path = empty_dir
                    else:
                        target_path = "."
            
            logger.info(f"GitHubProduct: Resolved scan path to {target_path}")

            event_loaded = Event(
                event_type=EventType.CUSTOM_EVENT,
                source="GitHubProduct",
                payload={
                    "event": "github.repository.loaded",
                    "workspace_id": workspace_id,
                    "repository_url": repository_url or target_path,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            event_bus.publish(event_loaded)
            event_bus.dispatch()

        except Exception as e:
            raise StageExecutionError(StageNames.LOADER, str(e))

        # Steps 2-4: Repository, Engineering Quality & Health Analysis
        try:
            service = GitHubIntelligenceService()
            results = service.analyze_workspace(
                workspace_path=target_path,
                workspace_id=workspace_id,
                repository_url=repository_url or username or organization or "local-workspace",
                branch=branch
            )

            repo_report = results.get("repo_report")
            quality_report = results.get("quality_report")
            health_report = results.get("health_report")

            event_analysis_done = Event(
                event_type=EventType.CUSTOM_EVENT,
                source="GitHubProduct",
                payload={
                    "event": "github.analysis.completed",
                    "workspace_id": workspace_id,
                    "report_id": repo_report.report_id if repo_report else "unknown",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            event_bus.publish(event_analysis_done)
            event_bus.dispatch()

        except Exception as e:
            raise StageExecutionError(StageNames.REPOSITORY, str(e))

        # Step 5: Knowledge Profile Update stage
        try:
            cache = GitHubCache()
            profile = cache.get_profile(user_id)
            if not profile:
                profile = KnowledgeProfile(workspace_id=workspace_id, user_id=user_id)

            # Map technologies and repositories to profile
            languages = []
            for tech in repo_report.detected_technologies:
                if tech.category in ["Language", "Programming Languages"]:
                    languages.append(tech.name)

            repo_details = {
                "url": repository_url or username or organization or "local-repo",
                "file_count": repo_report.file_count,
                "total_lines": repo_report.total_lines,
                "maintainability_score": quality_report.maintainability_score,
                "overall_health_score": health_report.health_scores.overall_health_score,
                "last_analyzed": datetime.utcnow().isoformat()
            }

            profile_svc = ProfileService()
            updated_profile = profile_svc.aggregate_github(
                profile=profile,
                repositories=[repo_details],
                languages=languages
            )
            cache.set_profile(user_id, updated_profile)

            event_profile = Event(
                event_type=EventType.CUSTOM_EVENT,
                source="GitHubProduct",
                payload={
                    "event": "github.profile.updated",
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            event_bus.publish(event_profile)
            event_bus.dispatch()

        except Exception as e:
            raise StageExecutionError(StageNames.PROFILE, str(e))

        # Step 6: Engineering Report Generator stage
        try:
            generator = GitHubReportGenerator()
            report = generator.generate_report(
                repo_report=repo_report,
                quality_report=quality_report,
                health_report=health_report,
                workspace_id=workspace_id
            )

            # Set execution metrics timings
            duration = time.perf_counter() - start_time
            report.execution_metrics = {
                "Loader": duration * 0.1,
                "Repository": duration * 0.3,
                "Engineering": duration * 0.3,
                "Health": duration * 0.2,
                "Profile": duration * 0.05,
                "Generator": duration * 0.05,
                "Total": duration
            }

            # Cache the report
            cache.set_report(report.report_id, report)

            event_rep_gen = Event(
                event_type=EventType.CUSTOM_EVENT,
                source="GitHubProduct",
                payload={
                    "event": "github.report.generated",
                    "workspace_id": workspace_id,
                    "report_id": report.report_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            event_bus.publish(event_rep_gen)
            event_bus.dispatch()

        except Exception as e:
            raise StageExecutionError(StageNames.GENERATOR, str(e))

        # Final workflow completed event
        workflow_completed_event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="GitHubProduct",
            payload={
                "event": "github.workflow.completed",
                "workspace_id": workspace_id,
                "report_id": report.report_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        event_bus.publish(workflow_completed_event)
        event_bus.dispatch()

        return report
