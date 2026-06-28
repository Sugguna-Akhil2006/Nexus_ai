"""Resume Intelligence Platform Tools Module.

Implements all 10 analytical tools governing parsing, skills extraction, 
ATS checking, and gap analysis under the Tool Framework.
"""

from abc import ABC, abstractmethod
import datetime
import json
import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional
import uuid

from backend.tools.tool import Tool, ToolMetadata, ToolCategory, ToolRequest, ToolResponse, ToolRegistry
from backend.runtime.task import Task
from backend.agents.chat import ChatAgent, ChatRegistry, Conversation

# Ensure thread lock for conversations seeding
_conv_lock = threading.Lock()

def _query_chat_agent(prompt: str, workspace_id: str, user_id: str) -> str:
    """Helper to route prompts to ChatAgent via mock conversation."""
    chat_agent = ChatAgent()
    chat_agent.initialize()
    
    registry = ChatRegistry()
    conv_id = f"tool-conv-{str(uuid.uuid4())[:8]}"
    
    with _conv_lock:
        registry._conversations[conv_id] = Conversation(
            conversation_id=conv_id,
            workspace_id=workspace_id,
            title="Resume Tool Conv",
            participants=[user_id],
            messages=[],
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
    
    task = Task(
        description="Resume Tool Query",
        metadata={
            "action": "send_message",
            "conversation_id": conv_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "message": prompt
        }
    )
    res = chat_agent.execute(task)
    return res.message


# =====================================================================
# 1. Resume Parser Tool
# =====================================================================

class ResumeParserTool(Tool):
    @property
    def name(self) -> str:
        return "Resume Parser Tool"

    @property
    def description(self) -> str:
        return "Parses raw resume text into structured json schema (name, email, phone, location)."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="resume_parser",
            name=self.name,
            version="1.0.0",
            author="Architect",
            description=self.description,
            category=ToolCategory.DOCUMENT,
            permissions=["read"],
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments:
            raise Exception("Missing 'text' parameter.")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        
        prompt = (
            "Analyze and extract structured information from the following resume text. "
            "Return JSON only: {name, email, phone, location, education, experience, skills}\n"
            f"Resume Text:\n{text}"
        )
        
        try:
            ans = _query_chat_agent(prompt, request.workspace_id, request.user_id)
            if "Mock" in ans:
                # Mock fallback
                data = {
                    "name": "Jane Doe",
                    "email": "jane.doe@example.com",
                    "phone": "123-456-7890",
                    "location": "San Francisco, CA",
                    "skills": ["Python", "FastAPI", "React", "Docker"],
                    "experience": "Senior Developer with 5 years experience.",
                    "education": "B.S. in Computer Science"
                }
            else:
                match = re.search(r"\{.*\}", ans, re.DOTALL)
                data = json.loads(match.group(0)) if match else {"raw": ans}
                
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=data,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output={"error": str(e)},
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 2. Skills Extraction Tool
# =====================================================================

class SkillsExtractionTool(Tool):
    @property
    def name(self) -> str:
        return "Skills Extraction Tool"

    @property
    def description(self) -> str:
        return "Isolates and classifies hard, soft, and domain skills from resume text."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="skills_extractor",
            name=self.name,
            version="1.0.0",
            author="Architect",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments:
            raise Exception("Missing 'text' parameter.")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        
        prompt = (
            "Extract all skills from this text and group them as hard_skills, soft_skills, and domain_expertise. "
            "Return JSON only: {hard_skills: [], soft_skills: [], domain_expertise: []}\n"
            f"Text:\n{text}"
        )
        
        try:
            ans = _query_chat_agent(prompt, request.workspace_id, request.user_id)
            if "Mock" in ans:
                data = {
                    "hard_skills": ["Python", "FastAPI", "SQL", "Docker"],
                    "soft_skills": ["Communication", "Leadership", "Problem Solving"],
                    "domain_expertise": ["Software Engineering", "Cloud Computing"]
                }
            else:
                match = re.search(r"\{.*\}", ans, re.DOTALL)
                data = json.loads(match.group(0)) if match else {"raw": ans}
                
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=data,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output={"error": str(e)},
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 3. Experience Analyzer Tool
# =====================================================================

class ExperienceAnalyzerTool(Tool):
    @property
    def name(self) -> str:
        return "Experience Analyzer Tool"

    @property
    def description(self) -> str:
        return "Analyzes roles, employment history, progression, and key metrics accomplishments."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="experience_analyzer",
            name=self.name,
            version="1.0.0",
            author="Architect",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments:
            raise Exception("Missing 'text' parameter.")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        
        prompt = (
            "Analyze the experience section from this resume text. Extract employment duration, job titles "
            "progression, and list key metric-driven accomplishments. "
            "Return JSON only: {total_years: float, roles: [], progression_healthy: bool, metrics_found: []}\n"
            f"Text:\n{text}"
        )
        
        try:
            ans = _query_chat_agent(prompt, request.workspace_id, request.user_id)
            if "Mock" in ans:
                data = {
                    "total_years": 5.5,
                    "roles": ["Junior Developer", "Senior Developer"],
                    "progression_healthy": True,
                    "metrics_found": ["Reduced latency by 40%", "Led a team of 3 developers"]
                }
            else:
                match = re.search(r"\{.*\}", ans, re.DOTALL)
                data = json.loads(match.group(0)) if match else {"raw": ans}
                
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=data,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output={"error": str(e)},
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 4. Education Analyzer Tool
# =====================================================================

class EducationAnalyzerTool(Tool):
    @property
    def name(self) -> str:
        return "Education Analyzer Tool"

    @property
    def description(self) -> str:
        return "Evaluates degrees, majors, institutional rankings, and graduation statuses."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="education_analyzer",
            name=self.name,
            version="1.0.0",
            author="Architect",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments:
            raise Exception("Missing 'text' parameter.")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        
        prompt = (
            "Analyze the education section of this resume. Extract degrees, majors, and institutional names. "
            "Return JSON only: {degrees: [], institutional_rankings_level: str, graduation_status: str}\n"
            f"Text:\n{text}"
        )
        
        try:
            ans = _query_chat_agent(prompt, request.workspace_id, request.user_id)
            if "Mock" in ans:
                data = {
                    "degrees": ["B.S. in Computer Science"],
                    "institutional_rankings_level": "Tier-1",
                    "graduation_status": "Graduated"
                }
            else:
                match = re.search(r"\{.*\}", ans, re.DOTALL)
                data = json.loads(match.group(0)) if match else {"raw": ans}
                
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=data,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output={"error": str(e)},
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 5. ATS Scoring Tool
# =====================================================================

class ATSScoringTool(Tool):
    @property
    def name(self) -> str:
        return "ATS Scoring Tool"

    @property
    def description(self) -> str:
        return "Scores structural, length, formatting, and keyword densities for ATS optimization."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="ats_scoring",
            name=self.name,
            version="1.0.0",
            author="Architect",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments:
            raise Exception("Missing 'text' parameter.")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        
        prompt = (
            "Analyze the formatting, layout, structure, and text of this resume. "
            "Provide an ATS score from 0 to 100 with recommendations. "
            "Return JSON only: {ats_score: int, formatting_issues: [], keyword_density_score: int, recommendations: []}\n"
            f"Text:\n{text}"
        )
        
        try:
            ans = _query_chat_agent(prompt, request.workspace_id, request.user_id)
            if "Mock" in ans:
                data = {
                    "ats_score": 85,
                    "formatting_issues": ["Avoid two-column structures"],
                    "keyword_density_score": 80,
                    "recommendations": ["Add more metrics-oriented results in experience section."]
                }
            else:
                match = re.search(r"\{.*\}", ans, re.DOTALL)
                data = json.loads(match.group(0)) if match else {"raw": ans}
                
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=data,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output={"error": str(e)},
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 6. Job Description Matcher Tool
# =====================================================================

class JobDescriptionMatcherTool(Tool):
    @property
    def name(self) -> str:
        return "Job Description Matcher Tool"

    @property
    def description(self) -> str:
        return "Matches resume credentials against a target Job Description."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="jd_matcher",
            name=self.name,
            version="1.0.0",
            author="Architect",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "jd": {"type": "string"}
                },
                "required": ["text", "jd"]
            },
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments or "jd" not in arguments:
            raise Exception("Missing parameters: text and jd are required.")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        jd = request.arguments.get("jd", "")
        
        prompt = (
            "Evaluate how well this resume matches the given Job Description. "
            "Provide match percentage, matching keywords, and missing requirements. "
            "Return JSON only: {match_percentage: int, matching_keywords: [], missing_requirements: []}\n"
            f"Resume Text:\n{text}\n\nJob Description:\n{jd}"
        )
        
        try:
            ans = _query_chat_agent(prompt, request.workspace_id, request.user_id)
            if "Mock" in ans:
                data = {
                    "match_percentage": 78,
                    "matching_keywords": ["Python", "FastAPI", "SQL"],
                    "missing_requirements": ["Kubernetes", "AWS Solutions Architect"]
                }
            else:
                match = re.search(r"\{.*\}", ans, re.DOTALL)
                data = json.loads(match.group(0)) if match else {"raw": ans}
                
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=data,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output={"error": str(e)},
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 7. Skill Gap Analyzer Tool
# =====================================================================

class SkillGapAnalyzerTool(Tool):
    @property
    def name(self) -> str:
        return "Skill Gap Analyzer Tool"

    @property
    def description(self) -> str:
        return "Identifies gaps between candidate skills and job description requirements."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="skill_gap_analyzer",
            name=self.name,
            version="1.0.0",
            author="Architect",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "jd": {"type": "string"}
                },
                "required": ["text", "jd"]
            },
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments or "jd" not in arguments:
            raise Exception("Missing parameters: text and jd are required.")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        jd = request.arguments.get("jd", "")
        
        prompt = (
            "Cross reference the candidate's skills in this resume with the Job Description's requirements. "
            "List matching skills, missing skills, and prioritized gap score. "
            "Return JSON only: {matching_skills: [], missing_skills: [], criticality_score: int}\n"
            f"Resume Text:\n{text}\n\nJob Description:\n{jd}"
        )
        
        try:
            ans = _query_chat_agent(prompt, request.workspace_id, request.user_id)
            if "Mock" in ans:
                data = {
                    "matching_skills": ["Python", "FastAPI"],
                    "missing_skills": ["Kubernetes", "AWS Solutions Architect"],
                    "criticality_score": 75
                }
            else:
                match = re.search(r"\{.*\}", ans, re.DOTALL)
                data = json.loads(match.group(0)) if match else {"raw": ans}
                
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=data,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output={"error": str(e)},
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 8. Resume Improvement Tool
# =====================================================================

class ResumeImprovementTool(Tool):
    @property
    def name(self) -> str:
        return "Resume Improvement Tool"

    @property
    def description(self) -> str:
        return "Suggests layout formatting, bullet point wordings, and action verb improvements."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="resume_improvement",
            name=self.name,
            version="1.0.0",
            author="Architect",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments:
            raise Exception("Missing 'text' parameter.")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        
        prompt = (
            "Provide actionable advice to improve this resume's text, verbs, impact, and layout structures. "
            "Return JSON only: {formatting_suggestions: [], active_verbs_to_include: [], rewrite_examples: []}\n"
            f"Text:\n{text}"
        )
        
        try:
            ans = _query_chat_agent(prompt, request.workspace_id, request.user_id)
            if "Mock" in ans:
                data = {
                    "formatting_suggestions": ["Ensure contact details are in a single line at the top."],
                    "active_verbs_to_include": ["Spearheaded", "Optimized", "Architected"],
                    "rewrite_examples": ["Instead of 'Wrote code for backend', use 'Architected and implemented FastAPI REST services.'"]
                }
            else:
                match = re.search(r"\{.*\}", ans, re.DOTALL)
                data = json.loads(match.group(0)) if match else {"raw": ans}
                
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=data,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output={"error": str(e)},
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 9. Resume Comparison Tool
# =====================================================================

class ResumeComparisonTool(Tool):
    @property
    def name(self) -> str:
        return "Resume Comparison Tool"

    @property
    def description(self) -> str:
        return "Performs side-by-side comparative analysis and candidate matching rankings."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="resume_comparison",
            name=self.name,
            version="1.0.0",
            author="Architect",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={
                "type": "object",
                "properties": {
                    "resumes": {
                        "type": "array",
                        "items": {"type": "object", "properties": {"candidate_id": {"type": "string"}, "text": {"type": "string"}}, "required": ["candidate_id", "text"]}
                    },
                    "jd": {"type": "string"}
                },
                "required": ["resumes"]
            },
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "resumes" not in arguments:
            raise Exception("Missing 'resumes' parameter.")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        resumes = request.arguments.get("resumes", [])
        jd = request.arguments.get("jd", "N/A")
        
        prompt = (
            f"Compare these resumes side-by-side. Rank candidates and highlight their strengths and weaknesses.\n"
            f"Job Description context: {jd}\n"
            f"Resumes:\n{json.dumps(resumes)}"
        )
        
        try:
            ans = _query_chat_agent(prompt, request.workspace_id, request.user_id)
            if "Mock" in ans:
                # Simulates multi-candidate rankings comparison
                data = {
                    "rankings": [
                        {"candidate_id": resumes[0].get("candidate_id", "C1") if resumes else "C1", "rank": 1, "match_percentage": 85, "strengths": ["FastAPI", "Python"]},
                    ],
                    "comparison_summary": "All candidates show strong background, C1 stands out in API designs."
                }
            else:
                match = re.search(r"\{.*\}", ans, re.DOTALL)
                data = json.loads(match.group(0)) if match else {"raw": ans}
                
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=data,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output={"error": str(e)},
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 10. PDF Report Generator Tool
# =====================================================================

class PDFReportGenerator(Tool):
    @property
    def name(self) -> str:
        return "PDF Report Generator"

    @property
    def description(self) -> str:
        return "Compiles resume intelligence reports metadata into a download representation."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="pdf_generator",
            name=self.name,
            version="1.0.0",
            author="Architect",
            description=self.description,
            category=ToolCategory.CUSTOM,
            permissions=["read"],
            input_schema={"type": "object", "properties": {"report_data": {"type": "object"}}, "required": ["report_data"]},
            output_schema={"type": "string"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "report_data" not in arguments:
            raise Exception("Missing 'report_data' parameter.")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        report_data = request.arguments.get("report_data", {})
        
        # In a real environment, this generates PDF binaries from templates.
        # Here we compile metadata into structured HTML/Markdown formatted printable report content
        report_markdown = (
            f"# Nexus AI Resume Intelligence Analysis Report\n"
            f"Generated At: {datetime.datetime.utcnow().isoformat()}\n\n"
            f"## Candidate Summary\n"
            f"- Name: {report_data.get('parser', {}).get('name', 'N/A')}\n"
            f"- Email: {report_data.get('parser', {}).get('email', 'N/A')}\n"
            f"- Phone: {report_data.get('parser', {}).get('phone', 'N/A')}\n"
            f"- Location: {report_data.get('parser', {}).get('location', 'N/A')}\n\n"
            f"## ATS Score Checklist\n"
            f"- Overall ATS Score: **{report_data.get('ats', {}).get('ats_score', 0)}/100**\n"
            f"- Keyword Density Level: {report_data.get('ats', {}).get('keyword_density_score', 0)}%\n\n"
            f"## Identified Skills\n"
            f"- Hard Skills: {', '.join(report_data.get('skills', {}).get('hard_skills', []))}\n"
            f"- Soft Skills: {', '.join(report_data.get('skills', {}).get('soft_skills', []))}\n\n"
            f"## Actionable Recommendations\n"
            f"{json.dumps(report_data.get('improvement', {}).get('formatting_suggestions', []))}\n"
        )
        
        return ToolResponse(
            response_id=str(uuid.uuid4()),
            success=True,
            output=report_markdown,
            execution_time=time.perf_counter() - start_time
        )


# =====================================================================
# Registration Hooks
# =====================================================================

def register_resume_tools() -> None:
    """Convenience method to register all tools on start/import."""
    registry = ToolRegistry()
    
    tools_list = [
        ResumeParserTool(),
        SkillsExtractionTool(),
        ExperienceAnalyzerTool(),
        EducationAnalyzerTool(),
        ATSScoringTool(),
        JobDescriptionMatcherTool(),
        SkillGapAnalyzerTool(),
        ResumeImprovementTool(),
        ResumeComparisonTool(),
        PDFReportGenerator()
    ]
    
    for tool in tools_list:
        try:
            registry.register_tool(tool)
        except Exception:
            # Skip if already registered
            pass

# Run registration on initial module load
register_resume_tools()
