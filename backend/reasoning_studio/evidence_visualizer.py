"""Evidence visualizer — extracts and structures evidence references from Studio traces."""

from __future__ import annotations

from typing import List

from backend.observability.models import ExecutionTrace
from backend.reasoning_studio.models import EvidenceNode, EvidenceTree, StudioTrace


class EvidenceVisualizer:
    """Builds ``EvidenceTree`` structures from Studio traces and raw ExecutionTraces.

    Surfaces the knowledge sources, documents, memory lookups, and tool
    responses that influenced each reasoning step.  Reads only already-
    captured telemetry; no new collection is performed here.
    """

    @staticmethod
    def build_tree(studio_trace: StudioTrace, execution_trace: ExecutionTrace) -> EvidenceTree:
        """Constructs an evidence tree combining Studio and Observability data.

        Args:
            studio_trace:    Enriched Studio trace.
            execution_trace: The corresponding raw execution trace from the
                             Observability layer (provides ``knowledge_sources``
                             and ``memory_accesses``).

        Returns:
            A populated ``EvidenceTree``.
        """
        tree = EvidenceTree(studio_trace_id=studio_trace.studio_trace_id)
        seen_ids: set[str] = set()

        # ── Evidence from Observability knowledge sources ─────────────
        for ks in execution_trace.knowledge_sources:
            if ks.source_id in seen_ids:
                continue
            seen_ids.add(ks.source_id)

            # Find reasoning steps that queried this source (heuristic: same timestamp bucket)
            related_steps = [
                step.step_id
                for step in studio_trace.steps
                if ks.identifier in step.knowledge_queries
            ]

            node = EvidenceNode(
                source_type=ks.source_type,
                source_identifier=ks.identifier,
                content_summary=f"[{ks.source_type}] {ks.identifier} (relevance={ks.relevance_score:.2f})",
                confidence=ks.relevance_score,
                knowledge_fabric_ref=ks.source_id,
                related_step_ids=related_steps,
            )
            tree.root_evidence.append(node)

        # ── Evidence from Studio step evidence refs ───────────────────
        for step in studio_trace.steps:
            for ref in step.evidence_refs:
                if ref in seen_ids:
                    continue
                seen_ids.add(ref)
                node = EvidenceNode(
                    source_type="step_evidence",
                    source_identifier=ref,
                    content_summary=f"Evidence ref from step '{step.step_id}': {ref}",
                    confidence=step.confidence,
                    related_step_ids=[step.step_id],
                )
                tree.root_evidence.append(node)

        # ── Evidence from memory accesses ─────────────────────────────
        for ma in execution_trace.memory_accesses:
            key = f"memory:{ma.key}"
            if key in seen_ids:
                continue
            seen_ids.add(key)

            related_steps = [
                step.step_id
                for step in studio_trace.steps
                if f"{ma.operation}:{ma.key}" in step.memory_lookups
            ]

            node = EvidenceNode(
                source_type="memory",
                source_identifier=ma.key,
                content_summary=f"Memory {ma.operation}: namespace={ma.namespace}, key={ma.key}",
                confidence=1.0,
                related_step_ids=related_steps,
            )
            tree.root_evidence.append(node)

        return tree

    @staticmethod
    def evidence_for_step(
        tree: EvidenceTree,
        step_id: str,
    ) -> List[EvidenceNode]:
        """Filters evidence nodes that are related to a specific reasoning step.

        Args:
            tree:    The full evidence tree.
            step_id: Target step identifier.

        Returns:
            List of ``EvidenceNode`` objects related to that step.
        """
        return [node for node in tree.root_evidence if step_id in node.related_step_ids]
