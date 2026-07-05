"""Flagship DocumentProduct orchestrating ingestion, extraction, and graph modeling pipelines."""

import time
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

from backend.runtime.event import Event, EventType, EventBus
from backend.runtime.logger import StructuredLogger
from backend.intelligence.document.models import DocumentKnowledgeReport
from backend.intelligence.document.document_processor import DocumentProcessor
from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.document.history import DocumentHistoryManager
from backend.intelligence.profile.services import ProfileService
from backend.intelligence.profile.models import KnowledgeProfile, ProfilePersonalInfo, ProfileSkill, ProfileProject
from backend.intelligence.profile.merger import ProfileMerger
from backend.intelligence.document.workflow import DocumentStageNames, StageExecutionError


class DocumentProduct:
    """Consolidated entry facade executing the Intelligent Document Processing reasoning workflow."""

    @staticmethod
    def analyze(
        workspace_id: str,
        document_ids: List[str],
        user_id: str = "admin",
        options: Optional[Dict[str, Any]] = None
    ) -> DocumentKnowledgeReport:
        """Runs the entire document processing reasoning pipeline synchronously.

        Args:
            workspace_id: Active workspace identifier.
            document_ids: Target cached document identifiers.
            user_id: Requesting user identifier.
            options: Execution overriding options.

        Returns:
            DocumentKnowledgeReport: Consolidated analytical report.
        """
        logger = StructuredLogger()
        event_bus = EventBus()
        cache = DocumentCache()
        history_manager = DocumentHistoryManager()
        profile_svc = ProfileService()
        profile_merger = ProfileMerger()
        processor = DocumentProcessor()

        options = options or {}

        # 1. Publish started event
        event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="DocumentProduct",
            payload={
                "event": "document.workflow.started",
                "workspace_id": workspace_id,
                "user_id": user_id,
                "document_ids": document_ids,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        event_bus.dispatch()
        logger.info(f"DocumentProduct: Starting workflow run for workspace {workspace_id}")

        start_time = time.perf_counter()

        # Step 1: Loader Stage
        try:
            documents = cache.get_documents_by_ids(document_ids)
            if not documents:
                raise StageExecutionError(
                    DocumentStageNames.LOADER,
                    f"None of the document_ids {document_ids} are registered in cache."
                )
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.LOADER, str(e))

        # Step 2: Processing & Graph Extraction
        try:
            report = processor.process_documents(workspace_id, documents, options)
            
            event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="DocumentProduct",
                payload={
                    "event": "document.processing.completed",
                    "workspace_id": workspace_id,
                    "report_id": report.report_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            event_bus.dispatch()
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.PROCESSING, str(e))

        # Step 3: Knowledge Profile Integration
        try:
            profile = cache.get_profile(user_id)
            if not profile:
                profile = KnowledgeProfile(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    personal_info=ProfilePersonalInfo(full_name=user_id)
                )

            incoming_skills = {}
            incoming_projects = []
            for item in report.knowledge_objects:
                # Skill category checks
                is_skill = "skill" in item.title.lower() or "technology" in item.title.lower()
                if is_skill:
                    incoming_skills[item.title] = ProfileSkill(
                        name=item.title,
                        category="Technologies",
                        confidence_score=item.confidence,
                        sources=document_ids,
                        evidence=[item.evidence]
                    )
                else:
                    incoming_projects.append(ProfileProject(
                        name=item.title,
                        description=item.description,
                        technologies=[],
                        sources=document_ids
                    ))

            incoming_profile = KnowledgeProfile(
                workspace_id=workspace_id,
                user_id=user_id,
                skills=incoming_skills,
                projects=incoming_projects
            )

            updated_profile = profile_merger.merge_profiles(profile, incoming_profile)
            cache.set_profile(user_id, updated_profile)

            event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="DocumentProduct",
                payload={
                    "event": "document.knowledge.updated",
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            event_bus.dispatch()
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.PROFILE, str(e))

        # Step 4: Report persistence
        try:
            # Add execution metrics timings
            duration = time.perf_counter() - start_time
            
            # Cache the report
            cache.set_report(report.report_id, report)
            
            # Database log history
            history_manager.save_report(report)

            event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="DocumentProduct",
                payload={
                    "event": "document.report.generated",
                    "workspace_id": workspace_id,
                    "report_id": report.report_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            event_bus.dispatch()
        except Exception as e:
            raise StageExecutionError(DocumentStageNames.PERSISTENCE, str(e))

        # Final workflow completed event
        event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="DocumentProduct",
            payload={
                "event": "document.workflow.completed",
                "workspace_id": workspace_id,
                "report_id": report.report_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        event_bus.dispatch()

        return report
