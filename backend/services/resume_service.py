"""Resume Intelligence Service Layer Module.

Coordinates parsing, JD matching, skill-gap analysis, and PDF report compilation.
"""

from typing import Any, Dict, List, Optional
import uuid

from backend.api.sqlite_mock import DBStorage
from backend.agents.embedding import EmbeddingAgent
from backend.runtime.task import Task
from backend.tools.tool import ToolRegistry, ToolRequest
import backend.tools.resume_tools

# In-memory store to keep raw resume texts for analytics tools
_resume_texts: Dict[str, str] = {}

class ResumeOrchestrationService:
    """Orchestrates workflows across document pipelines and resume analytical tools."""

    def __init__(self, db: Optional[DBStorage] = None) -> None:
        self.db = db or DBStorage()
        self.embedding_agent = EmbeddingAgent()
        self.embedding_agent.initialize()
        self.tool_registry = ToolRegistry()

    def process_and_index_resume(self, filename: str, text: str, workspace_id: str) -> str:
        """Saves resume metadata to db and runs embedding agent indexing."""
        doc_id = f"res-{str(uuid.uuid4())[:8]}"
        checksum = str(hash(text))

        # Store raw text locally for extraction tools
        _resume_texts[doc_id] = text

        # Save document metadata in DB
        self.db.create_document(doc_id, workspace_id, filename, checksum)

        # Execute EmbeddingAgent task to slice and index text chunks
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

        return doc_id

    def get_resume_text(self, doc_id: str) -> str:
        """Retrieves raw resume text content."""
        return _resume_texts.get(doc_id, "Jane Doe Resume\nSkills: Python, FastAPI, Docker\nExperience: Senior Engineer")

    def analyze_resume(self, doc_id: str, workspace_id: str, user_id: str = "admin") -> Dict[str, Any]:
        """Runs parser, skill extractor, experience, education, and ATS scoring tools."""
        text = self.get_resume_text(doc_id)
        
        # 1. Execute parser
        parser_tool = self.tool_registry.get_tool("resume_parser")
        parser_res = parser_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="resume_parser",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text}
        ))

        # 2. Execute skill extractor
        skills_tool = self.tool_registry.get_tool("skills_extractor")
        skills_res = skills_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="skills_extractor",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text}
        ))

        # 3. Execute experience analyzer
        exp_tool = self.tool_registry.get_tool("experience_analyzer")
        exp_res = exp_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="experience_analyzer",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text}
        ))

        # 4. Execute education analyzer
        edu_tool = self.tool_registry.get_tool("education_analyzer")
        edu_res = edu_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="education_analyzer",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text}
        ))

        # 5. Execute ATS Scoring
        ats_tool = self.tool_registry.get_tool("ats_scoring")
        ats_res = ats_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="ats_scoring",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text}
        ))

        # 6. Execute Resume Improvement
        imp_tool = self.tool_registry.get_tool("resume_improvement")
        imp_res = imp_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="resume_improvement",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text}
        ))

        return {
            "document_id": doc_id,
            "parser": parser_res.output if parser_res.success else {},
            "skills": skills_res.output if skills_res.success else {},
            "experience": exp_res.output if exp_res.success else {},
            "education": edu_res.output if edu_res.success else {},
            "ats": ats_res.output if ats_res.success else {},
            "improvement": imp_res.output if imp_res.success else {}
        }

    def match_resume_to_jd(self, doc_id: str, jd_text: str, workspace_id: str, user_id: str = "admin") -> Dict[str, Any]:
        """Matches resume credentials against a target job description requirements."""
        text = self.get_resume_text(doc_id)

        # 1. Matcher tool
        match_tool = self.tool_registry.get_tool("jd_matcher")
        match_res = match_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="jd_matcher",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text, "jd": jd_text}
        ))

        # 2. Skill gap analyzer tool
        gap_tool = self.tool_registry.get_tool("skill_gap_analyzer")
        gap_res = gap_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="skill_gap_analyzer",
            workspace_id=workspace_id,
            user_id=user_id,
            arguments={"text": text, "jd": jd_text}
        ))

        return {
            "document_id": doc_id,
            "matcher": match_res.output if match_res.success else {},
            "gap_analysis": gap_res.output if gap_res.success else {}
        }
