"""Main Multi-Agent Collaboration Framework entry point facade."""

import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.collaboration.models import CollaborationSession, CollaborationReport, AgentTask
from backend.intelligence.collaboration.shared_context import SharedContext
from backend.intelligence.collaboration.agent_registry import AgentRegistry
from backend.intelligence.collaboration.task_delegator import TaskDelegator
from backend.intelligence.collaboration.consensus_engine import ConsensusEngine
from backend.intelligence.collaboration.conflict_resolver import ConflictResolver
from backend.intelligence.collaboration.collaboration_report import CollaborationReportBuilder


class CollaborationManager:
    """Orchestrates collaborative workflows, task dispatches, and consensus compiling."""

    def __init__(self) -> None:
        self.registry = AgentRegistry()
        self.delegator = TaskDelegator(self.registry)
        self.consensus_engine = ConsensusEngine()
        self.conflict_resolver = ConflictResolver()
        self.report_builder = CollaborationReportBuilder()
        self.event_bus = EventBus()

    def start_session(self, workspace_id: str, objective: str) -> Tuple[CollaborationSession, SharedContext]:
        """Initializes a new collaboration session and context blackboard."""
        session_id = f"sess-collab-{str(uuid.uuid4())[:8]}"
        session = CollaborationSession(
            session_id=session_id,
            workspace_id=workspace_id,
            objective=objective
        )
        context = SharedContext(objective=objective)

        # Emit collaboration started event
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CollaborationManager",
            payload={
                "event": "collaboration.started",
                "session_id": session_id,
                "workspace_id": workspace_id,
                "objective": objective,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        return session, context

    def delegate(
        self,
        session: CollaborationSession,
        context: SharedContext,
        sender_agent: str,
        receiver_agent: str,
        description: str,
        payload: Dict[str, Any],
        retry_count: int = 2
    ) -> Optional[Dict[str, Any]]:
        """Delegates tasks from one agent to another, updating context and publishing EventBus logs."""
        task_id = f"task-collab-{str(uuid.uuid4())[:8]}"
        task = AgentTask(
            task_id=task_id,
            sender_agent=sender_agent,
            receiver_agent=receiver_agent,
            description=description,
            payload=payload
        )

        # Emit task delegated event
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CollaborationManager",
            payload={
                "event": "agent.task.delegated",
                "session_id": session.session_id,
                "task_id": task_id,
                "sender": sender_agent,
                "receiver": receiver_agent,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        try:
            result = self.delegator.delegate_task(task, context, retry_count)
            
            # Emit response received event
            self.event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="CollaborationManager",
                payload={
                    "event": "agent.response.received",
                    "session_id": session.session_id,
                    "task_id": task_id,
                    "receiver": receiver_agent,
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            return result
        except Exception as e:
            # Emit failed response event
            self.event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="CollaborationManager",
                payload={
                    "event": "agent.response.received",
                    "session_id": session.session_id,
                    "task_id": task_id,
                    "receiver": receiver_agent,
                    "status": "failed",
                    "reason": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            raise e

    def complete_session(self, session: CollaborationSession, context: SharedContext) -> CollaborationReport:
        """Runs the consensus engine over evidence and returns the final CollaborationReport."""
        session.status = "COMPLETED"

        # Build consensus via Reasoning Engine
        reasoning_report = self.consensus_engine.build_consensus(
            workspace_id=session.workspace_id,
            objective=session.objective,
            context=context
        )

        # Construct final report
        report = self.report_builder.build_report(
            session_id=session.session_id,
            objective=session.objective,
            executed_agents=context.get_executed_agents(),
            timeline=context.get_timeline(),
            shared_evidence=context.get_evidence(),
            reasoning_report=reasoning_report
        )

        # Emit collaboration completed event
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CollaborationManager",
            payload={
                "event": "collaboration.completed",
                "session_id": session.session_id,
                "report_id": report.report_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        return report
