"""Execution analyzer compiling observability traces and metrics into aggregated execution stats."""

from typing import List, Dict
from backend.observability.models import ExecutionTrace, ModelMetrics, SpanStatus
from backend.execution_intelligence.models import ExecutionMetricsModel


class ExecutionAnalyzer:
    """Aggregates execution traces and model invocation metrics for workflows."""

    @staticmethod
    def analyze_workflow_executions(
        workflow_id: str,
        traces: List[ExecutionTrace],
        model_metrics: List[ModelMetrics]
    ) -> ExecutionMetricsModel:
        """Processes logs of a specific workflow, computing totals and averages."""
        matching_traces = [t for t in traces if t.workflow_id == workflow_id]
        execution_count = len(matching_traces)

        total_duration = sum(t.total_duration_ms for t in matching_traces)
        avg_duration = total_duration / execution_count if execution_count > 0 else 0.0

        module_times: Dict[str, float] = {}
        failures = 0
        fallback_usage = 0
        memory_usages = []

        # Analyze traces and their internal spans
        for trace in matching_traces:
            if trace.status == SpanStatus.FAILED:
                failures += 1
            
            for span in trace.spans:
                # Aggregate module runtimes
                mod_name = span.module or span.name
                module_times[mod_name] = module_times.get(mod_name, 0.0) + span.duration_ms
                
                # Check for fallbacks in metadata
                if span.metadata.get("fallback_used") or span.metadata.get("is_fallback"):
                    fallback_usage += 1
                
                # Extract memory usage if tracked
                mem_mb = span.metadata.get("memory_usage_mb") or span.metadata.get("memory_mb")
                if mem_mb is not None:
                    memory_usages.append(float(mem_mb))

        # Filter model metrics corresponding to target execution IDs
        trace_exec_ids = {t.execution_id for t in matching_traces}
        matching_model_metrics = [m for m in model_metrics if m.execution_id in trace_exec_ids]

        total_tokens_in = sum(m.tokens_in for m in matching_model_metrics)
        total_tokens_out = sum(m.tokens_out for m in matching_model_metrics)
        estimated_cost = sum(m.estimated_cost_usd for m in matching_model_metrics)
        retries = sum(m.retries for m in matching_model_metrics)

        provider_latencies: Dict[str, List[float]] = {}
        for m in matching_model_metrics:
            if m.provider not in provider_latencies:
                provider_latencies[m.provider] = []
            provider_latencies[m.provider].append(m.latency_ms)

        avg_memory = sum(memory_usages) / len(memory_usages) if memory_usages else 256.0

        return ExecutionMetricsModel(
            workflow_id=workflow_id,
            execution_count=execution_count,
            total_duration_ms=total_duration,
            average_duration_ms=avg_duration,
            module_execution_times=module_times,
            retry_counts=retries,
            failures_count=failures,
            fallback_usage_count=fallback_usage,
            total_tokens_in=total_tokens_in,
            total_tokens_out=total_tokens_out,
            estimated_cost_usd=estimated_cost,
            average_memory_usage_mb=avg_memory,
            provider_latencies=provider_latencies
        )
