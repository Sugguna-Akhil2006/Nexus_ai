"""Runtime variable store shared across all steps within a single workflow execution."""

import threading
from typing import Any, Dict, Optional


class WorkflowContext:
    """Thread-safe execution context carrying variables and cancellation state."""

    def __init__(self, workspace_id: str, variables: Optional[Dict[str, Any]] = None) -> None:
        self._lock = threading.Lock()
        self.workspace_id: str = workspace_id
        self._variables: Dict[str, Any] = dict(variables or {})
        self._step_outputs: Dict[str, Any] = {}
        self._cancelled: bool = False

    # ------------------------------------------------------------------
    # Variable access
    # ------------------------------------------------------------------

    def set(self, key: str, value: Any) -> None:
        """Writes a variable into the context store."""
        with self._lock:
            self._variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Reads a variable from the context store."""
        with self._lock:
            return self._variables.get(key, default)

    def all_variables(self) -> Dict[str, Any]:
        """Returns a snapshot of all current variables."""
        with self._lock:
            return dict(self._variables)

    # ------------------------------------------------------------------
    # Step output store
    # ------------------------------------------------------------------

    def store_output(self, step_id: str, output: Dict[str, Any]) -> None:
        """Persists the output dict produced by a completed step."""
        with self._lock:
            self._step_outputs[step_id] = output
            # Also merge into variables for downstream condition evaluation
            self._variables.update(output)

    def get_output(self, step_id: str) -> Dict[str, Any]:
        """Retrieves the output dict produced by a specific step."""
        with self._lock:
            return dict(self._step_outputs.get(step_id, {}))

    # ------------------------------------------------------------------
    # Cancellation
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Signals the running execution to stop after the current step."""
        with self._lock:
            self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Returns True when a cancellation has been requested."""
        with self._lock:
            return self._cancelled

    # ------------------------------------------------------------------
    # Condition evaluation
    # ------------------------------------------------------------------

    def evaluate_condition(self, expression: str) -> bool:
        """Safely evaluates a Python boolean expression against context variables.

        Args:
            expression: A Python expression string, e.g. ``"score > 0.5"``.

        Returns:
            Boolean result of the expression, or ``True`` if expression is empty.
        """
        if not expression:
            return True
        try:
            result = eval(expression, {"__builtins__": {}}, self.all_variables())  # noqa: S307
            return bool(result)
        except NameError:
            # Undefined variable in condition → treat as unmet condition → skip step
            return False
        except Exception:
            # Unexpected evaluation error → default to running the step
            return True
