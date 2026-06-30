"""Execution runner wrapper for each Resume Intelligence pipeline stage."""

import time
from typing import Dict, Any

from backend.intelligence.resume.models import (
    Resume,
    UnifiedResumeReport,
    ATSReport,
    JDMatchReport,
    ResumeAnalysisReport
)
from backend.intelligence.resume.context import WorkflowContext
from backend.intelligence.resume.state import WorkflowState
from backend.intelligence.resume.workflow import StageNames, StageExecutionError

# Component Imports
from backend.intelligence.resume.parser import ResumeParser, extract_raw_text
from backend.intelligence.resume.ats_engine import ATSEngine
from backend.intelligence.resume.skill_extractor import SkillExtractor
from backend.intelligence.resume.jd_matcher import JDMatcher
from backend.intelligence.resume.resume_analyzer import ResumeAnalysisEngine


class PipelineExecutionRunner:
    """Invokes specific engine steps, measures duration, and captures results in context."""

    def run_parser_stage(self, context: WorkflowContext, state: WorkflowState) -> None:
        """Parses raw document text into canonical Resume model."""
        start = time.perf_counter()
        state.start_stage(StageNames.PARSER)
        try:
            parser = ResumeParser()
            parsed_data = parser.parse(context.contents, context.filename)
            context.parsed_resume_data = parsed_data
            
            ats = ATSEngine()
            context.canonical_resume = ats._map_data_to_canonical(parsed_data)
            
            state.complete_stage(StageNames.PARSER, time.perf_counter() - start)
        except Exception as e:
            state.fail_stage(StageNames.PARSER, str(e))
            raise StageExecutionError(StageNames.PARSER, str(e)) from e

    def run_skills_stage(self, context: WorkflowContext, state: WorkflowState) -> None:
        """Extracts and categorizes skills profile from candidate details."""
        start = time.perf_counter()
        state.start_stage(StageNames.SKILL_EXTRACTION)
        try:
            if not context.canonical_resume:
                # Mock fallback if parser stage failed but workflow continued
                context.canonical_resume = Resume()
                
            extractor = SkillExtractor()
            context.skill_profile = extractor.extract_skills_profile(context.canonical_resume)
            
            state.complete_stage(StageNames.SKILL_EXTRACTION, time.perf_counter() - start)
        except Exception as e:
            state.fail_stage(StageNames.SKILL_EXTRACTION, str(e))
            raise StageExecutionError(StageNames.SKILL_EXTRACTION, str(e)) from e

    def run_ats_stage(self, context: WorkflowContext, state: WorkflowState) -> None:
        """Evaluates candidate profile completeness and scores ATS compatibility."""
        start = time.perf_counter()
        state.start_stage(StageNames.ATS_ENGINE)
        try:
            raw_text = extract_raw_text(context.contents, context.filename)
            ats = ATSEngine()
            
            # Re-map legacy data fallback
            legacy_data = context.parsed_resume_data
            if not legacy_data:
                # Mock fallback
                from backend.intelligence.resume.models import ResumeData, ContactInfo
                legacy_data = ResumeData(contact_info=ContactInfo(name="Unknown"))
                
            # Legacy analyze_ats returns ATSResult, we wrap/cast as ATSReport in schema
            res = ats.analyze_ats(legacy_data, raw_text)
            
            # Map legacy ATSResult properties to ATSReport
            category_scores = []
            for cat in res.category_scores:
                from backend.intelligence.resume.models import ATSCategoryScore
                category_scores.append(ATSCategoryScore(
                    name=cat.name,
                    weight=cat.weight,
                    max_score=cat.max_score,
                    current_score=cat.current_score,
                    reason=cat.reason,
                    improvement_suggestions=cat.improvement_suggestions
                ))
            context.ats_report = ATSReport(
                overall_score=res.score,
                category_scores=category_scores,
                strengths=res.strengths,
                weaknesses=res.weaknesses,
                priority_improvements=res.priority_improvements,
                detailed_recommendations=res.detailed_recommendations
            )
            
            state.complete_stage(StageNames.ATS_ENGINE, time.perf_counter() - start)
        except Exception as e:
            state.fail_stage(StageNames.ATS_ENGINE, str(e))
            raise StageExecutionError(StageNames.ATS_ENGINE, str(e)) from e

    def run_jd_stage(self, context: WorkflowContext, state: WorkflowState) -> None:
        """Matches candidate resume competencies against target job postings."""
        if not context.raw_job_description:
            return

        start = time.perf_counter()
        state.start_stage(StageNames.JD_MATCHING)
        try:
            if not context.canonical_resume:
                context.canonical_resume = Resume()

            matcher = JDMatcher()
            # Parse JD
            context.job_description = matcher.parser.parse_jd(
                context.raw_job_description,
                context.workspace_id,
                context.document_id
            )
            # Run comparison
            context.jd_match_report = matcher.match_resume_to_jd(
                context.canonical_resume,
                context.job_description,
                context.workspace_id,
                context.document_id
            )
            
            state.complete_stage(StageNames.JD_MATCHING, time.perf_counter() - start)
        except Exception as e:
            state.fail_stage(StageNames.JD_MATCHING, str(e))
            raise StageExecutionError(StageNames.JD_MATCHING, str(e)) from e

    def run_analysis_stage(self, context: WorkflowContext, state: WorkflowState) -> None:
        """Executes general SWOT, stage tracker, and career readiness logic."""
        start = time.perf_counter()
        state.start_stage(StageNames.ANALYSIS)
        try:
            if not context.canonical_resume:
                context.canonical_resume = Resume()

            analyzer = ResumeAnalysisEngine()
            context.analysis_report = analyzer.analyze_resume_canonical(
                resume=context.canonical_resume,
                skill_profile=context.skill_profile,
                ats_report=context.ats_report,
                jd_match=context.jd_match_report,
                workspace_id=context.workspace_id,
                document_id=context.document_id
            )
            
            state.complete_stage(StageNames.ANALYSIS, time.perf_counter() - start)
        except Exception as e:
            state.fail_stage(StageNames.ANALYSIS, str(e))
            raise StageExecutionError(StageNames.ANALYSIS, str(e)) from e

    def run_consolidation_stage(self, context: WorkflowContext, state: WorkflowState) -> None:
        """Consolidates findings and telemetry mapping into UnifiedResumeReport."""
        start = time.perf_counter()
        state.start_stage(StageNames.CONSOLIDATOR)
        try:
            resume = context.canonical_resume or Resume()
            analysis = context.analysis_report
            
            # Calculate simple summary details
            summary = {
                "name": resume.personal_info.full_name or "Candidate",
                "email": resume.personal_info.email or "",
                "phone": resume.personal_info.phone or "",
                "education_count": len(resume.education),
                "experience_count": len(resume.experience),
                "projects_count": len(resume.projects),
                "career_stage": analysis.career_stage if analysis else "Junior Backend Engineer"
            }

            skills_list = [s.name for s in resume.skills if s.name]

            # Collect all recommendations
            recommendations = []
            if analysis:
                recommendations.extend(analysis.recommendations)

            # Metadata compilation
            meta = {
                "workspace_id": context.workspace_id,
                "document_id": context.document_id,
                "filename": context.filename,
                "completed_stages": state.completed_stages,
                "failed_stage": state.failed_stage,
                "pipeline_status": state.pipeline_status,
                "errors": state.errors
            }

            metrics = {
                "retry_counts": state.retry_counts,
                "execution_times": state.execution_times
            }

            context.final_report = UnifiedResumeReport(
                resume_summary=summary,
                skills=skills_list,
                ats_report=context.ats_report,
                jd_match_report=context.jd_match_report,
                resume_analysis=context.analysis_report,
                recommendations=recommendations,
                pipeline_metadata=meta,
                execution_metrics=metrics
            )
            
            state.complete_stage(StageNames.CONSOLIDATOR, time.perf_counter() - start)
        except Exception as e:
            state.fail_stage(StageNames.CONSOLIDATOR, str(e))
            raise StageExecutionError(StageNames.CONSOLIDATOR, str(e)) from e
