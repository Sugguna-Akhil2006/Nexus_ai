"""Bottleneck detector identifying slow modules, high retries, expensive providers, and publishing events."""

import uuid
from typing import List, Dict
from backend.execution_intelligence.models import BottleneckModel, BottleneckType, ImpactLevel, ExecutionMetricsModel
from backend.observability.models import ExecutionTrace
from backend.runtime.event import Event, EventBus, EventType, EventPriority


class BottleneckDetector:
    """Scans metrics and traces to locate hot spots and operational inefficiency."""

    def __init__(self) -> None:
        self._event_bus = EventBus()

    def detect_bottlenecks(
        self,
        metrics: ExecutionMetricsModel,
        traces: List[ExecutionTrace]
    ) -> List[BottleneckModel]:
        """Runs rule checks to flag performance, cost, and stability bottlenecks."""
        bottlenecks: List[BottleneckModel] = []
        exec_count = metrics.execution_count or 1

        # 1. Slow modules: modules taking > 40% of the average workflow duration
        for mod, total_time in metrics.module_execution_times.items():
            avg_mod_time = total_time / exec_count
            ratio = avg_mod_time / metrics.average_duration_ms if metrics.average_duration_ms > 0 else 0
            if ratio > 0.4 and avg_mod_time > 1000:
                impact = ImpactLevel.HIGH if ratio > 0.7 else ImpactLevel.MEDIUM
                bn = BottleneckModel(
                    bottleneck_id=f"bn-slow-{uuid.uuid4().hex[:6]}",
                    type=BottleneckType.SLOW_MODULE,
                    target=mod,
                    description=f"Module '{mod}' consumes {ratio:.1%} of total run time, averaging {avg_mod_time:.1f}ms per run.",
                    metric_value=avg_mod_time,
                    impact_level=impact
                )
                bottlenecks.append(bn)
                self._publish_bottleneck(bn)

        # 2. High retry workflows
        avg_retries = metrics.retry_counts / exec_count
        if avg_retries > 0.5:
            impact = ImpactLevel.HIGH if avg_retries > 1.5 else ImpactLevel.MEDIUM
            bn = BottleneckModel(
                bottleneck_id=f"bn-retry-{uuid.uuid4().hex[:6]}",
                type=BottleneckType.HIGH_RETRY,
                target=metrics.workflow_id,
                description=f"High retry rate detected. Averages {avg_retries:.2f} retries per execution.",
                metric_value=avg_retries,
                impact_level=impact
            )
            bottlenecks.append(bn)
            self._publish_bottleneck(bn)

        # 3. Repeated Failures
        failure_rate = metrics.failures_count / exec_count
        if failure_rate > 0.15:
            impact = ImpactLevel.CRITICAL if failure_rate > 0.5 else ImpactLevel.HIGH
            bn = BottleneckModel(
                bottleneck_id=f"bn-fail-{uuid.uuid4().hex[:6]}",
                type=BottleneckType.REPEATED_FAILURES,
                target=metrics.workflow_id,
                description=f"Stability issue: {failure_rate:.1%} failure rate over {exec_count} executions.",
                metric_value=failure_rate,
                impact_level=impact
            )
            bottlenecks.append(bn)
            self._publish_bottleneck(bn)

        # 4. Expensive Providers: average cost per run > $0.05
        avg_cost = metrics.estimated_cost_usd / exec_count
        if avg_cost > 0.05:
            impact = ImpactLevel.HIGH if avg_cost > 0.20 else ImpactLevel.MEDIUM
            bn = BottleneckModel(
                bottleneck_id=f"bn-cost-{uuid.uuid4().hex[:6]}",
                type=BottleneckType.EXPENSIVE_PROVIDER,
                target=metrics.workflow_id,
                description=f"High LLM expenditure: averaging ${avg_cost:.4f} per execution.",
                metric_value=avg_cost,
                impact_level=impact
            )
            bottlenecks.append(bn)
            self._publish_bottleneck(bn)

        # 5. Large Prompts: average tokens in > 5000
        avg_tokens_in = metrics.total_tokens_in / exec_count
        if avg_tokens_in > 5000:
            bn = BottleneckModel(
                bottleneck_id=f"bn-prompt-{uuid.uuid4().hex[:6]}",
                type=BottleneckType.LARGE_PROMPTS,
                target=metrics.workflow_id,
                description=f"Large payload: average input of {avg_tokens_in:.0f} tokens per run.",
                metric_value=avg_tokens_in,
                impact_level=ImpactLevel.MEDIUM
            )
            bottlenecks.append(bn)
            self._publish_bottleneck(bn)

        # 6. Duplicate Operations: same span name called multiple times in a single trace
        dupe_count = 0
        for trace in [t for t in traces if t.workflow_id == metrics.workflow_id]:
            span_names = [s.name for s in trace.spans]
            duplicates = len(span_names) - len(set(span_names))
            if duplicates > 0:
                dupe_count += duplicates

        if dupe_count > 0:
            avg_dupes = dupe_count / exec_count
            bn = BottleneckModel(
                bottleneck_id=f"bn-dupe-{uuid.uuid4().hex[:6]}",
                type=BottleneckType.DUPLICATE_OPERATIONS,
                target=metrics.workflow_id,
                description=f"Redundant execution: averaging {avg_dupes:.2f} duplicate span calls per workflow execution.",
                metric_value=avg_dupes,
                impact_level=ImpactLevel.MEDIUM
            )
            bottlenecks.append(bn)
            self._publish_bottleneck(bn)

        return bottlenecks

    def _publish_bottleneck(self, bn: BottleneckModel) -> None:
        """Publishes the bottleneck.detected event."""
        self._event_bus.publish(Event(
            event_type=EventType.BOTTLENECK_DETECTED,
            priority=EventPriority.NORMAL,
            payload={
                "bottleneck_id": bn.bottleneck_id,
                "type": bn.type.value,
                "target": bn.target,
                "impact_level": bn.impact_level.value,
                "description": bn.description
            }
        ))
