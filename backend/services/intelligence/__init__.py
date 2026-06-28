"""Intelligence Engine Core Services Module.

Exposes stateless AI analysis components and shared routing helpers.
"""

import datetime
import uuid
import threading
from typing import Any, Dict

from backend.agents.chat import ChatAgent, ChatRegistry, Conversation
from backend.runtime.task import Task
from backend.runtime.event import Event, EventBus, EventType

_conv_lock = threading.Lock()

def query_intelligence_agent(prompt: str, workspace_id: str, user_id: str = "admin") -> str:
    """Standardized utility to invoke Conversational ChatAgent with context."""
    event_bus = EventBus()
    
    # 1. Publish analysis.started event
    event_bus.publish(Event(
        event_type=EventType.CUSTOM_EVENT,
        source="IntelligenceEngine",
        payload={"event_name": "analysis.started", "workspace_id": workspace_id}
    ))
    event_bus.dispatch_all()

    chat_agent = ChatAgent()
    chat_agent.initialize()
    
    registry = ChatRegistry()
    conv_id = f"intel-conv-{str(uuid.uuid4())[:8]}"
    
    with _conv_lock:
        registry._conversations[conv_id] = Conversation(
            conversation_id=conv_id,
            workspace_id=workspace_id,
            title="Intelligence Engine Conv",
            participants=[user_id],
            messages=[],
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        
    task = Task(
        description="Intelligence Query Execution",
        metadata={
            "action": "send_message",
            "conversation_id": conv_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "message": prompt
        }
    )
    
    try:
        res = chat_agent.execute(task)
        
        # 2. Publish analysis.completed event
        event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="IntelligenceEngine",
            payload={"event_name": "analysis.completed", "workspace_id": workspace_id}
        ))
        event_bus.dispatch_all()
        
        return res.message
    except Exception as e:
        # 3. Publish analysis.failed event
        event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="IntelligenceEngine",
            payload={
                "event_name": "analysis.failed", 
                "workspace_id": workspace_id, 
                "error": str(e)
            }
        ))
        event_bus.dispatch_all()
        raise e

from backend.services.intelligence.summary import SummaryService
from backend.services.intelligence.entity import EntityExtractionService
from backend.services.intelligence.classification import ClassificationService
from backend.services.intelligence.comparison import ComparisonService
from backend.services.intelligence.recommendation import RecommendationService
from backend.services.intelligence.confidence import ConfidenceService
from backend.services.intelligence.report import ReportService
import backend.tools.intelligence_tools
