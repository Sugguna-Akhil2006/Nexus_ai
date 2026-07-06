"""Central orchestrator for the Unified AI Reasoning Engine pipeline."""

import uuid
from datetime import datetime
from typing import Dict, List, Any
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.reasoning.models import ReasoningRequest, ReasoningReport, Evidence, Conflict
from backend.intelligence.reasoning.reasoning_context import ReasoningContext
from backend.intelligence.reasoning.planner import PipelinePlanner
from backend.intelligence.reasoning.evidence_collector import EvidenceCollector
from backend.intelligence.reasoning.fact_resolver import FactResolver
from backend.intelligence.reasoning.confidence_engine import ConfidenceEngine
from backend.intelligence.reasoning.knowledge_fusion import KnowledgeFuser
from backend.intelligence.reasoning.response_planner import ResponsePlanner


class UnifiedReasoningEngine:
    """Powers central cross-source correlation, conflict checks, and confidence scoring."""

    def __init__(self) -> None:
        self.planner = PipelinePlanner()
        self.collector = EvidenceCollector()
        self.resolver = FactResolver()
        self.confidence_engine = ConfidenceEngine()
        self.fuser = KnowledgeFuser()
        self.response_planner = ResponsePlanner()
        self.event_bus = EventBus()

    def execute_reasoning(self, req: ReasoningRequest) -> ReasoningReport:
        """Executes the full pipeline stages: collect -> rank -> fuse -> resolve -> score -> output."""
        ctx = ReasoningContext(req.workspace_id, req.query, req.options)
        
        # Publish reasoning.started event
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="UnifiedReasoningEngine",
            payload={
                "event": "reasoning.started",
                "workspace_id": req.workspace_id,
                "query": req.query,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        # 1. Formulate execution stages
        stages = self.planner.formulate_plan(ctx)
        
        ranked_evidence: List[Evidence] = []
        fused_evidence: List[Evidence] = []
        conflicts: List[Conflict] = []
        overall_confidence = 1.0

        # 2. Sequential execution of stages
        for stage in stages:
            if stage == "EVIDENCE_COLLECTION":
                ranked_evidence = self.collector.collect_and_rank_evidence(req.query, req.sources, ctx)
                # Emit evidence collected event
                self.event_bus.publish(Event(
                    event_type=EventType.CUSTOM_EVENT,
                    source="UnifiedReasoningEngine",
                    payload={
                        "event": "reasoning.evidence.collected",
                        "workspace_id": req.workspace_id,
                        "evidence_count": len(ranked_evidence),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ))

            elif stage == "EVIDENCE_RANKING":
                # Ranking is already calculated in collector
                pass

            elif stage == "KNOWLEDGE_FUSION":
                fused_evidence = self.fuser.fuse_knowledge(ranked_evidence, ctx)

            elif stage == "CONFLICT_DETECTION":
                conflicts = self.resolver.detect_conflicts(req.query, fused_evidence, ctx)
                # Emit conflict detected event if conflicts exist
                if conflicts:
                    self.event_bus.publish(Event(
                        event_type=EventType.CUSTOM_EVENT,
                        source="UnifiedReasoningEngine",
                        payload={
                            "event": "reasoning.conflict.detected",
                            "workspace_id": req.workspace_id,
                            "conflicts_count": len(conflicts),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    ))

            elif stage == "CONFIDENCE_SCORING":
                overall_confidence = self.confidence_engine.compute_overall_confidence(fused_evidence, conflicts, ctx)

        # 3. Compile final conclusions
        conclusions = self.response_planner.compile_conclusions(req.query, fused_evidence, conflicts, ctx)

        # 4. Extract unique source names
        supporting_sources = list(set(ev.source for ev in fused_evidence))

        report = ReasoningReport(
            report_id=f"rep-reason-{str(uuid.uuid4())[:8]}",
            query=req.query,
            collected_evidence=fused_evidence,
            supporting_sources=supporting_sources,
            confidence=overall_confidence,
            detected_conflicts=conflicts,
            final_conclusions=conclusions,
            reasoning_trace=ctx.get_trace()
        )

        # Publish reasoning.completed event
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="UnifiedReasoningEngine",
            payload={
                "event": "reasoning.completed",
                "workspace_id": req.workspace_id,
                "report_id": report.report_id,
                "confidence": overall_confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        return report
