"""Enables agent-to-agent message passing and event triggers within a session."""

import threading
from datetime import datetime
from typing import Dict, List, Any


class CollaborationBus:
    """Synchronized communication bus stashing messages in queues for agents."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._messages_map: Dict[str, List[Dict[str, Any]]] = {}

    def send_message(self, session_id: str, sender: str, receiver: str, content: str) -> None:
        """Appends a text message queue item to a session."""
        with self._lock:
            if session_id not in self._messages_map:
                self._messages_map[session_id] = []
            
            self._messages_map[session_id].append({
                "sender": sender,
                "receiver": receiver,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            })

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetches all messages passed in a session context."""
        with self._lock:
            return list(self._messages_map.get(session_id, []))
