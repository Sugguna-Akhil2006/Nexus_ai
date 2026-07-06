"""Isolates plugin execution and traps unhandled exceptions."""

from typing import Callable, List, Any


class PluginSandbox:
    """Safeguards host runtime processes by checking permissions and isolating exceptions."""

    def execute_safely(
        self,
        func: Callable[..., Any],
        declared_permissions: List[str],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Executes a plugin method, checking permission bounds and intercepting exceptions."""
        # 1. Simulate permission boundary checks
        # E.g., if a function name implies access to unsafe actions, check declared permissions
        func_name = getattr(func, "__name__", "unknown")
        
        if "network" in func_name.lower() and "network" not in declared_permissions:
            raise PermissionError(
                f"Plugin execution blocked: Method '{func_name}' requires 'network' permission, "
                f"which is not declared in manifest."
            )

        if "filesystem" in func_name.lower() and "filesystem" not in declared_permissions:
            raise PermissionError(
                f"Plugin execution blocked: Method '{func_name}' requires 'filesystem' permission, "
                f"which is not declared in manifest."
            )

        # 2. Execute within try-except block to prevent platform crashes
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Sandboxed plugin exception in method '{func_name}': {str(e)}") from e
