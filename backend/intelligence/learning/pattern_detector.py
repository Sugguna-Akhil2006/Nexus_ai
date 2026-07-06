"""Scans query history to identify repeated keywords, templates, and topics."""

import re
from datetime import datetime
from collections import Counter
from typing import List
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.learning.experience_store import ExperienceStore


class PatternDetector:
    """Extracts frequent workflows and search terms to detect recurring usage patterns."""

    def __init__(self, store: ExperienceStore) -> None:
        self.store = store
        self.event_bus = EventBus()

    def detect_patterns(self, workspace_id: str, query_history: List[str]) -> List[str]:
        """Detects frequent terms appearing in query history."""
        patterns = []
        if len(query_history) < 3:
            return patterns

        # 1. Tokenize query words
        words = []
        for q in query_history:
            words.extend(re.findall(r"\b\w{4,15}\b", q.lower()))

        # 2. Count frequency
        counts = Counter(words)
        for term, count in counts.items():
            if count >= 3:
                pattern_desc = f"Frequently queried topic: {term}"
                patterns.append(pattern_desc)
                
                # Publish pattern detected
                self.event_bus.publish(Event(
                    event_type=EventType.CUSTOM_EVENT,
                    source="PatternDetector",
                    payload={
                        "event": "learning.pattern.detected",
                        "workspace_id": workspace_id,
                        "pattern_type": "frequent_topic",
                        "details": term,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ))

        return patterns
