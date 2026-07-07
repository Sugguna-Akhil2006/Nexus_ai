"""Capability Matcher resolving model capability tags support."""

from __future__ import annotations

from typing import List

from backend.platform.models import ModelProfile


class CapabilityMatcher:
    """Filters model capabilities matching inference request requirements."""

    def filter_eligible_models(self, models: List[ModelProfile], required_caps: List[str]) -> List[ModelProfile]:
        """Returns models supporting all requested capabilities."""
        if not required_caps:
            return models

        eligible = []
        for m in models:
            # Check model capabilities intersection
            # Convert capability tags to lower case lists
            m_caps = {c.lower() for c in m.capabilities}
            if all(r.lower() in m_caps for r in required_caps):
                eligible.append(m)

        return eligible
