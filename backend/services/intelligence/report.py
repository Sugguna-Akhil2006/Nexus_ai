"""Report Service Module."""

import json
from typing import Any, Dict
from backend.runtime.event import Event, EventBus, EventType

class ReportService:
    """Stateless service providing reports styling formatting capabilities."""

    def generate_report_formats(self, data: Dict[str, Any], title: str = "Analysis Report") -> Dict[str, Any]:
        """Compiles analysis payloads into Markdown, JSON, and PDF ready templates structures."""
        markdown_str = (
            f"# {title}\n"
            f"Compiled Payload Metrics:\n"
            f"```json\n{json.dumps(data, indent=2)}\n```\n"
        )
        
        pdf_ready_model = {
            "title": title,
            "data_summary": f"Contains {len(data)} analysis attributes keys"
        }
        
        # Publish report.generated event
        event_bus = EventBus()
        event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ReportService",
            payload={
                "event_name": "report.generated",
                "title": title
            }
        ))
        event_bus.dispatch_all()

        return {
            "json": data,
            "markdown": markdown_str,
            "pdf_data_model": pdf_ready_model
        }
