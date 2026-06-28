"""Resume Intelligence Service Layer Module.

Coordinates parsing, JD matching, skill-gap analysis, database writes, 
and EventBus notifications dispatching.
"""

import json
from typing import Any, Dict, List, Optional
import uuid

from backend.api.sqlite_mock import DBStorage
from backend.agents.embedding import EmbeddingAgent
from backend.runtime.task import Task
from backend.tools.tool import ToolRegistry, ToolRequest
from backend.runtime.event import Event, EventBus, EventType

# Import resume tools module to guarantee auto registration in ToolRegistry
import backend.tools.resume_tools

# In-memory backup store to map raw resume texts
_resume_texts: Dict[str, str] = {}

class ResumeOrchestrationService:
    """Orchestrates workflows across SQLite relational storage and resume intelligence tools."""

    def __init__(self, db: Optional[DBStorage] = None) -> None:
        self.db = db or DBStorage()
        self.embedding_agent = EmbeddingAgent()
        self.embedding_agent.initialize()
        self.tool_registry = ToolRegistry()
        self.event_bus = EventBus()

    def _publish_platform_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Publishes custom platform notification to EventBus."""
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ResumeIntelligencePlatform",
            payload={
                "event_name": event_name,
                **payload
            }
        )
        self.event_bus.publish(event)
        self.event_bus.dispatch_all()

    def process_and_index_resume(self, filename: str, text: str, workspace_id: str) -> str:
        """Saves document details and indexes in vector database."""
        doc_id = f"res-{str(uuid.uuid4())[:8]}"
        checksum = str(hash(text))

        # Store raw text locally
        _resume_texts[doc_id] = text

        # Save document row
        self.db.create_document(doc_id, workspace_id, filename, checksum)

        # Execute core indexing task
        task_embed = Task(
            description="Index resume content",
            metadata={
                "action": "embed",
                "workspace_id": workspace_id,
                "document_id": doc_id,
                "text": text,
                "filename": filename,
                "checksum": checksum,
                "collection": f"col_{workspace_id}"
            }
        )
        self.embedding_agent.execute(task_embed)
        self.db.update_document_status(doc_id, "indexed")

        # Publish upload event
        self._publish_platform_event("resume.uploaded", {
            "document_id": doc_id,
            "workspace_id": workspace_id,
            "filename": filename
        })

        return doc_id

    def get_resume_text(self, doc_id: str) -> str:
        """Retrieves raw text content of resume."""
        return _resume_texts.get(doc_id, "Jane Doe Resume\nSkills: Python, FastAPI\nExperience: Engineer")

    def analyze_resume(self, doc_id: str, workspace_id: str, user_id: str = "admin") -> Dict[str, Any]:
        """Runs parser, ATS checklist scoring, and updates tables."""
        text = self.get_resume_text(doc_id)

        # 1. Execute Resume Parser
        parser_tool = self.tool_registry.get_tool("resume_parser")
        parser_res = parser_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="resume_parser",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text}
        ))
        parsed_data = parser_res.output if parser_res.success else {}

        # 2. Write details to sqlite 'resumes' table
        self.db.create_resume_metadata(
            document_id=doc_id,
            workspace_id=workspace_id,
            name=parsed_data.get("name", "Jane Doe"),
            email=parsed_data.get("email", ""),
            phone=parsed_data.get("phone", ""),
            location=parsed_data.get("location", ""),
            linkedin=parsed_data.get("linkedin", ""),
            github=parsed_data.get("github", ""),
            portfolio=parsed_data.get("portfolio", ""),
            education=json.dumps(parsed_data.get("education", [])),
            certifications=json.dumps(parsed_data.get("certifications", [])),
            skills=json.dumps(parsed_data.get("skills", [])),
            languages=json.dumps(parsed_data.get("languages", [])),
            experience=json.dumps(parsed_data.get("experience", [])),
            projects=json.dumps(parsed_data.get("projects", [])),
            publications=json.dumps(parsed_data.get("publications", [])),
            awards=json.dumps(parsed_data.get("awards", []))
        )

        # 3. Execute ATS Scoring
        ats_tool = self.tool_registry.get_tool("ats_scoring")
        ats_res = ats_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="ats_scoring",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text}
        ))
        ats_data = ats_res.output if ats_res.success else {"ats_score": 0}

        # 4. Save ATS Report to DB
        ats_id = f"ats-{str(uuid.uuid4())[:8]}"
        self.db.create_ats_report(ats_id, doc_id, ats_data.get("ats_score", 0), json.dumps(ats_data))

        # 5. Compile and save full analysis report
        report_data = {
            "parser": parsed_data,
            "ats": ats_data
        }
        analysis_id = f"anl-{str(uuid.uuid4())[:8]}"
        self.db.create_analysis_report(analysis_id, doc_id, workspace_id, json.dumps(report_data))

        # Publish analysis event
        self._publish_platform_event("resume.analyzed", {
            "document_id": doc_id,
            "workspace_id": workspace_id,
            "analysis_id": analysis_id,
            "ats_score": ats_data.get("ats_score", 0)
        })

        return {
            "document_id": doc_id,
            "analysis_id": analysis_id,
            "report_data": report_data
        }

    def match_resume_to_jd(self, doc_id: str, jd_text: str, workspace_id: str, user_id: str = "admin") -> Dict[str, Any]:
        """Runs match comparison metrics against job description."""
        text = self.get_resume_text(doc_id)

        # 1. Execute job matcher
        matcher = self.tool_registry.get_tool("job_matcher")
        matcher_res = matcher.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="job_matcher",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text, "jd": jd_text}
        ))
        match_data = matcher_res.output if matcher_res.success else {}

        # 2. Execute Skill Gap
        gap_tool = self.tool_registry.get_tool("skill_gap")
        gap_res = gap_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="skill_gap",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text, "jd": jd_text}
        ))
        gap_data = gap_res.output if gap_res.success else {}

        compiled_match = {
            "matcher": match_data,
            "skill_gap": gap_data
        }

        # Publish match event
        self._publish_platform_event("resume.matched", {
            "document_id": doc_id,
            "workspace_id": workspace_id,
            "compatibility_score": match_data.get("compatibility_score", 0)
        })

        return compiled_match

    def compare_resumes(self, doc_ids: List[str], workspace_id: str, user_id: str = "admin") -> Dict[str, Any]:
        """Runs side-by-side comparison across version history files."""
        resumes_list = []
        for doc_id in doc_ids:
            text = self.get_resume_text(doc_id)
            resumes_list.append({"candidate_id": doc_id, "text": text})

        compare_tool = self.tool_registry.get_tool("resume_comparison")
        tool_res = compare_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="resume_comparison",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"resumes": resumes_list}
        ))
        compare_data = tool_res.output if tool_res.success else {}

        # Save to DB history
        comparison_id = f"cmp-{str(uuid.uuid4())[:8]}"
        self.db.create_comparison_history(comparison_id, workspace_id, ",".join(doc_ids), json.dumps(compare_data))

        # Publish comparison event
        self._publish_platform_event("resume.compared", {
            "comparison_id": comparison_id,
            "workspace_id": workspace_id,
            "document_ids": doc_ids
        })

        return {
            "comparison_id": comparison_id,
            "compare_data": compare_data
        }

    def generate_report(self, doc_id: str, workspace_id: str, user_id: str = "admin") -> Dict[str, Any]:
        """Generates formats using Report tool."""
        # Compile report details first
        report = self.analyze_resume(doc_id, workspace_id, user_id)
        
        report_tool = self.tool_registry.get_tool("resume_report")
        tool_res = report_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="resume_report",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"report_data": report.get("report_data", {})}
        ))
        report_data = tool_res.output if tool_res.success else {}

        # Publish generated event
        self._publish_platform_event("resume.report.generated", {
            "document_id": doc_id,
            "workspace_id": workspace_id
        })

        return report_data
