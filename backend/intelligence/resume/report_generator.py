"""JSON report compiler assembling all structured analysis metrics."""

import uuid
from datetime import datetime
from backend.intelligence.resume.exceptions import ReportGenerationError
from typing import Union
from backend.intelligence.resume.models import (
    ResumeReport,
    ResumeData,
    CategorizedSkills,
    ATSResult,
    ResumeAnalysis,
    ResumeAnalysisReport
)


class ReportGenerator:
    """Service to assemble separate analysis sections into a consolidated report."""

    def generate(
        self,
        workspace_id: str,
        document_id: str,
        resume_data: ResumeData,
        categorized_skills: CategorizedSkills,
        ats_analysis: ATSResult,
        general_analysis: Union[ResumeAnalysis, ResumeAnalysisReport]
    ) -> ResumeReport:
        """Assembles analyses inputs into a single structured ResumeReport.

        Args:
            workspace_id: Workspace tenant identifier.
            document_id: Ingested document tracking ID.
            resume_data: Fully parsed resume fields.
            categorized_skills: Grouped skills category lists.
            ats_analysis: ATS completeness and score indices.
            general_analysis: SWOT and interview tips.

        Returns:
            ResumeReport: Fully compiled report.

        Raises:
            ReportGenerationError: On assembly errors.
        """
        try:
            now_iso = datetime.utcnow().isoformat()
            report_id = f"rep-{str(uuid.uuid4())[:8]}"
            
            return ResumeReport(
                report_id=report_id,
                workspace_id=workspace_id,
                document_id=document_id,
                resume_data=resume_data,
                categorized_skills=categorized_skills,
                ats_analysis=ats_analysis,
                general_analysis=general_analysis,
                created_at=now_iso
            )
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate ResumeReport: {e}") from e
