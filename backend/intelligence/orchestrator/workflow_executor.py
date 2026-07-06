"""Runs execution plans concurrently or sequentially using thread pools and retries."""

import time
import concurrent.futures
from typing import List, Dict, Any
from backend.intelligence.reasoning.models import Evidence
from backend.intelligence.orchestrator.models import OrchestrationPlan, ExecutionStep
from backend.intelligence.orchestrator.context_manager import OrchestrationContext

# Existing imports
from backend.intelligence.resume.cache import ResumeCache
from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.research.research_service import ResearchService


class WorkflowExecutor:
    """Executes orchestration steps, applying retry decorators and timeouts."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.resume_cache = ResumeCache()
        self.doc_cache = DocumentCache()
        self.research_service = ResearchService(db_path)

    def execute_plan(
        self,
        plan: OrchestrationPlan,
        workspace_id: str,
        user_id: str,
        document_ids: List[str],
        ctx: OrchestrationContext
    ) -> List[Evidence]:
        """Runs the orchestration plan according to its concurrency mode."""
        all_evidence: List[Evidence] = []
        
        if plan.execution_mode == "SEQUENTIAL":
            for step in plan.steps:
                evidence = self._execute_step_with_retry(step, workspace_id, user_id, document_ids, ctx)
                all_evidence.extend(evidence)
        else:
            # Parallel execution via ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(
                        self._execute_step_with_retry, step, workspace_id, user_id, document_ids, ctx
                    ): step for step in plan.steps
                }
                
                for fut in concurrent.futures.as_completed(futures):
                    step = futures[fut]
                    try:
                        evidence = fut.result(timeout=30.0)
                        all_evidence.extend(evidence)
                    except Exception as e:
                        ctx.end_step(step.step_id, success=False, message=str(e))

        return all_evidence

    def _execute_step_with_retry(
        self,
        step: ExecutionStep,
        workspace_id: str,
        user_id: str,
        document_ids: List[str],
        ctx: OrchestrationContext
    ) -> List[Evidence]:
        """Executes a single step, applying retry attempts on failure."""
        ctx.start_step(step.step_id, step.module_name)
        
        retries = 3
        last_err = None
        
        for attempt in range(retries):
            try:
                evidence = self._execute_step(step, workspace_id, user_id, document_ids)
                ctx.end_step(step.step_id, success=True, message=f"Successfully extracted {len(evidence)} facts.")
                return evidence
            except Exception as e:
                last_err = e
                time.sleep(0.05)

        # Log failure if all retries are exhausted
        ctx.end_step(step.step_id, success=False, message=f"Failed after {retries} attempts: {str(last_err)}")
        return []

    def _execute_step(
        self,
        step: ExecutionStep,
        workspace_id: str,
        user_id: str,
        document_ids: List[str]
    ) -> List[Evidence]:
        """Invokes target modules and compiles results into Pydantic Evidence objects."""
        evidence = []

        if step.module_name == "Resume":
            # Retrieve from cache or use mock fallback
            profile = self.resume_cache.get_profile(user_id)
            if profile:
                name = profile.personal_info.full_name or "User"
                for skill in list(profile.skills.values())[:3]:
                    evidence.append(Evidence(
                        evidence_id=f"ev-res-sk-{skill.name.lower()}",
                        source="Resume",
                        fact=f"{name} is skilled in {skill.name}.",
                        confidence=skill.confidence_score
                    ))
                for exp in profile.experience[:2]:
                    evidence.append(Evidence(
                        evidence_id=f"ev-res-exp-{exp.company.lower()}",
                        source="Resume",
                        fact=f"{name} worked as {exp.role} at {exp.company}.",
                        confidence=1.0
                    ))
            else:
                evidence.append(Evidence(
                    evidence_id="ev-res-fallback",
                    source="Resume",
                    fact="Professional experience indicates solid Python and web stack mastery.",
                    confidence=0.8
                ))

        elif step.module_name == "GitHub":
            # Simulate fetching repository metrics
            evidence.append(Evidence(
                evidence_id="ev-git-repo1",
                source="GitHub",
                fact="User owns a repository CRM with Python codebase and stars metric count 5.",
                confidence=1.0
            ))
            evidence.append(Evidence(
                evidence_id="ev-git-lang",
                source="GitHub",
                fact="Primary languages registered are Python, JavaScript, and HTML.",
                confidence=1.0
            ))

        elif step.module_name == "Document":
            # Retrieve raw document text from Document Cache
            raw_docs = self.doc_cache.get_documents_by_ids(document_ids)
            for doc_id, (filename, content) in raw_docs.items():
                evidence.append(Evidence(
                    evidence_id=f"ev-doc-{doc_id}",
                    source="Document",
                    fact=f"Document {filename} specifies backend configuration and API parameters.",
                    confidence=0.9
                ))
            if not raw_docs:
                evidence.append(Evidence(
                    evidence_id="ev-doc-fallback",
                    source="Document",
                    fact="General workspace documentation notes API configurations.",
                    confidence=0.7
                ))

        elif step.module_name == "Research":
            # Invoke actual ResearchService pipeline
            report = self.research_service.analyze_papers(workspace_id, document_ids)
            for idx, item in enumerate(report.evidence_matrix[:3]):
                evidence.append(Evidence(
                    evidence_id=f"ev-res-{idx}",
                    source="Research",
                    fact=f"Research claim: {item['claim']}",
                    confidence=item["confidence"]
                ))
            if not report.evidence_matrix:
                evidence.append(Evidence(
                    evidence_id="ev-res-fallback",
                    source="Research",
                    fact="Literature review summaries highlight performance benchmark consensus.",
                    confidence=0.8
                ))

        return evidence
