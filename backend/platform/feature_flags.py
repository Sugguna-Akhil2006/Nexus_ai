"""Feature Flags manager tracking experimental features and workspace overrides."""

from __future__ import annotations

from typing import Dict

from backend.platform.models import FeatureFlag


class FeatureFlagsManager:
    """Controls availability of experimental feature toggles."""

    def __init__(self) -> None:
        self._flags: Dict[str, FeatureFlag] = {
            "mcp-integration": FeatureFlag("mcp-integration", "MCP Integration support", True),
            "multimodal-parsing": FeatureFlag("multimodal-parsing", "Experimental image analysis", False)
        }

    def is_feature_enabled(self, flag_id: str, workspace_id: Optional[str] = None) -> bool:
        """Determines if feature flag is active."""
        flag = self._flags.get(flag_id)
        if not flag:
            return False

        if workspace_id and workspace_id in flag.workspace_level_overrides:
            return flag.workspace_level_overrides[workspace_id]

        return flag.is_enabled

    def set_flag_enabled(self, flag_id: str, is_enabled: bool) -> None:
        if flag_id in self._flags:
            self._flags[flag_id].is_enabled = is_enabled

    def set_workspace_override(self, flag_id: str, workspace_id: str, is_enabled: bool) -> None:
        if flag_id in self._flags:
            self._flags[flag_id].workspace_level_overrides[workspace_id] = is_enabled
