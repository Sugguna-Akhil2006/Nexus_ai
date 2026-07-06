"""Tracks token consumption per workspace and per model."""

import threading
from collections import defaultdict
from typing import Any, Dict


class TokenTracker:
    """Records and aggregates token usage across workspaces and models."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # workspace_id → {tokens_in, tokens_out}
        self._workspace: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"tokens_in": 0, "tokens_out": 0}
        )
        # model → {tokens_in, tokens_out}
        self._model: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"tokens_in": 0, "tokens_out": 0}
        )

    def record_usage(
        self,
        workspace_id: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
    ) -> None:
        """Records token consumption for a single model invocation.

        Args:
            workspace_id: The originating workspace.
            model: The model identifier (e.g. ``"llama3.2"``).
            tokens_in: Number of prompt tokens consumed.
            tokens_out: Number of completion tokens produced.
        """
        with self._lock:
            ws = self._workspace[workspace_id]
            ws["tokens_in"] += tokens_in
            ws["tokens_out"] += tokens_out

            m = self._model[model]
            m["tokens_in"] += tokens_in
            m["tokens_out"] += tokens_out

    def get_workspace_usage(self, workspace_id: str) -> Dict[str, int]:
        """Returns cumulative token counts for a workspace.

        Args:
            workspace_id: The workspace to query.

        Returns:
            Dict with ``tokens_in`` and ``tokens_out`` keys.
        """
        with self._lock:
            data = self._workspace.get(workspace_id, {"tokens_in": 0, "tokens_out": 0})
            return dict(data)

    def get_model_breakdown(self) -> Dict[str, Dict[str, int]]:
        """Returns token usage broken down by model.

        Returns:
            Dict mapping model name → ``{tokens_in, tokens_out}``.
        """
        with self._lock:
            return {m: dict(v) for m, v in self._model.items()}

    def get_total_tokens(self) -> Dict[str, int]:
        """Returns summed token counts across all workspaces and models."""
        with self._lock:
            total_in = sum(v["tokens_in"] for v in self._workspace.values())
            total_out = sum(v["tokens_out"] for v in self._workspace.values())
            return {"tokens_in": total_in, "tokens_out": total_out}
