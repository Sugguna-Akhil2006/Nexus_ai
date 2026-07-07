"""Decision graph builder — constructs decision/evidence/reasoning graphs from Studio traces."""

from __future__ import annotations

from typing import List

from backend.reasoning_studio.models import (
    CapturedReasoningStep,
    DecisionGraph,
    GraphEdge,
    GraphNode,
    NodeType,
    StudioTrace,
)


class DecisionGraphBuilder:
    """Generates ``DecisionGraph`` structures from ``StudioTrace`` data.

    The graph is built entirely from already-captured Studio artefacts;
    no new telemetry is collected here.
    """

    @staticmethod
    def build(trace: StudioTrace) -> DecisionGraph:
        """Builds a decision / evidence / confidence-flow graph.

        Each reasoning step becomes a ``DECISION`` node.
        Knowledge queries become ``KNOWLEDGE_QUERY`` nodes.
        Tool invocations become ``TOOL_CALL`` nodes.
        Memory lookups become ``MEMORY_LOOKUP`` nodes.
        Consecutive steps are connected with directed edges carrying the
        confidence weight of the destination step.

        Args:
            trace: The ``StudioTrace`` to process.

        Returns:
            A fully populated ``DecisionGraph``.
        """
        graph = DecisionGraph(studio_trace_id=trace.studio_trace_id)
        prev_decision_id: str | None = None

        for step in trace.steps:
            # ── Main decision node ────────────────────────────────────
            decision_node = GraphNode(
                node_type=NodeType.DECISION,
                label=f"Step {step.sequence_index}: {step.description[:60]}",
                description=step.description,
                confidence=step.confidence,
                metadata={
                    "step_id": step.step_id,
                    "inputs": step.inputs,
                    "outputs": step.outputs,
                    "timestamp": step.timestamp,
                },
            )
            graph.nodes.append(decision_node)

            # ── Edge from previous decision ───────────────────────────
            if prev_decision_id:
                graph.edges.append(GraphEdge(
                    source_node_id=prev_decision_id,
                    target_node_id=decision_node.node_id,
                    label="leads_to",
                    weight=step.confidence,
                ))
            prev_decision_id = decision_node.node_id

            # ── Tool invocation child nodes ───────────────────────────
            for tool in step.tool_invocations:
                tool_node = GraphNode(
                    node_type=NodeType.TOOL_CALL,
                    label=f"Tool: {tool}",
                    description=tool,
                    confidence=step.confidence,
                )
                graph.nodes.append(tool_node)
                graph.edges.append(GraphEdge(
                    source_node_id=decision_node.node_id,
                    target_node_id=tool_node.node_id,
                    label="invokes",
                ))

            # ── Knowledge query child nodes ───────────────────────────
            for kq in step.knowledge_queries:
                kq_node = GraphNode(
                    node_type=NodeType.KNOWLEDGE_QUERY,
                    label=f"KnowledgeQ: {kq[:50]}",
                    description=kq,
                    confidence=1.0,
                )
                graph.nodes.append(kq_node)
                graph.edges.append(GraphEdge(
                    source_node_id=decision_node.node_id,
                    target_node_id=kq_node.node_id,
                    label="queries",
                ))

            # ── Memory lookup child nodes ─────────────────────────────
            for ml in step.memory_lookups:
                ml_node = GraphNode(
                    node_type=NodeType.MEMORY_LOOKUP,
                    label=f"Memory: {ml[:50]}",
                    description=ml,
                    confidence=1.0,
                )
                graph.nodes.append(ml_node)
                graph.edges.append(GraphEdge(
                    source_node_id=decision_node.node_id,
                    target_node_id=ml_node.node_id,
                    label="accesses",
                ))

            # ── Conclusion node (if step has intermediate conclusions) ─
            for conclusion in step.intermediate_conclusions:
                conc_node = GraphNode(
                    node_type=NodeType.CONCLUSION,
                    label=f"Conclusion: {conclusion[:60]}",
                    description=conclusion,
                    confidence=step.confidence,
                )
                graph.nodes.append(conc_node)
                graph.edges.append(GraphEdge(
                    source_node_id=decision_node.node_id,
                    target_node_id=conc_node.node_id,
                    label="concludes",
                ))

        return graph
