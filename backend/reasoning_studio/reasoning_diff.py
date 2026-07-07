"""Reasoning diff — field-level differencing of two Studio traces."""

from __future__ import annotations

from typing import List

from backend.reasoning_studio.models import DiffEntry, DiffStatus, StudioTrace, TraceDiff


class ReasoningDiff:
    """Computes field-level diffs between two Studio traces.

    Supports comparison by step descriptions, confidence values, and
    provider/prompt-version strings so developers can contrast two
    executions, two prompt versions, or two provider backends.
    """

    @staticmethod
    def diff(left: StudioTrace, right: StudioTrace) -> TraceDiff:
        """Computes a structured diff between *left* and *right* traces.

        Args:
            left:  The baseline trace.
            right: The trace being compared.

        Returns:
            A populated ``TraceDiff`` with step, confidence, and provider diffs.
        """
        step_diffs: List[DiffEntry] = []
        confidence_diffs: List[DiffEntry] = []
        provider_diffs: List[DiffEntry] = []

        left_steps = left.steps
        right_steps = right.steps
        max_len = max(len(left_steps), len(right_steps))

        for i in range(max_len):
            left_step = left_steps[i] if i < len(left_steps) else None
            right_step = right_steps[i] if i < len(right_steps) else None

            # ── Step description diff ─────────────────────────────────
            left_desc = left_step.description if left_step else None
            right_desc = right_step.description if right_step else None

            if left_desc is None:
                status = DiffStatus.ADDED
            elif right_desc is None:
                status = DiffStatus.REMOVED
            elif left_desc != right_desc:
                status = DiffStatus.CHANGED
            else:
                status = DiffStatus.UNCHANGED

            step_diffs.append(DiffEntry(
                index=i,
                status=status,
                left_value=left_desc,
                right_value=right_desc,
                field="description",
            ))

            # ── Confidence diff ───────────────────────────────────────
            left_conf = str(left_step.confidence) if left_step else None
            right_conf = str(right_step.confidence) if right_step else None

            if left_conf == right_conf:
                conf_status = DiffStatus.UNCHANGED
            elif left_conf is None:
                conf_status = DiffStatus.ADDED
            elif right_conf is None:
                conf_status = DiffStatus.REMOVED
            else:
                conf_status = DiffStatus.CHANGED

            confidence_diffs.append(DiffEntry(
                index=i,
                status=conf_status,
                left_value=left_conf,
                right_value=right_conf,
                field="confidence",
            ))

            # ── Provider / prompt-version diff ────────────────────────
            left_prov = left_step.provider_response_summary if left_step else None
            right_prov = right_step.provider_response_summary if right_step else None

            if left_prov == right_prov:
                prov_status = DiffStatus.UNCHANGED
            elif left_prov is None:
                prov_status = DiffStatus.ADDED
            elif right_prov is None:
                prov_status = DiffStatus.REMOVED
            else:
                prov_status = DiffStatus.CHANGED

            provider_diffs.append(DiffEntry(
                index=i,
                status=prov_status,
                left_value=left_prov,
                right_value=right_prov,
                field="provider_response_summary",
            ))

        total_changed = sum(
            1 for d in step_diffs + confidence_diffs + provider_diffs
            if d.status != DiffStatus.UNCHANGED
        )

        # Similarity: proportion of unchanged step descriptions
        unchanged_steps = sum(1 for d in step_diffs if d.status == DiffStatus.UNCHANGED)
        similarity = unchanged_steps / max_len if max_len > 0 else 1.0

        return TraceDiff(
            left_trace_id=left.studio_trace_id,
            right_trace_id=right.studio_trace_id,
            step_diffs=step_diffs,
            confidence_diffs=confidence_diffs,
            provider_diffs=provider_diffs,
            total_changed=total_changed,
            similarity_score=round(similarity, 4),
        )
