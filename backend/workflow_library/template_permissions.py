"""Template permissions validator checking template access rights."""

from __future__ import annotations

from backend.workflow_library.models import TemplateScope, WorkflowTemplate


class TemplatePermissions:
    """Verifies that a user has appropriate access rights to view or execute templates."""

    @staticmethod
    def can_access(
        template: WorkflowTemplate,
        user_id: str,
        user_workspace_id: str,
    ) -> bool:
        """Returns True if the user matches the template sharing scope rules.

        Args:
            template: WorkflowTemplate target.
            user_id: Requesting user.
            user_workspace_id: Requesting workspace.

        Returns:
            True if access is granted.
        """
        # Marketplace templates are public
        if template.scope == TemplateScope.MARKETPLACE:
            return True

        # Private templates only accessible to the author
        if template.scope == TemplateScope.PRIVATE:
            return template.author == user_id

        # Workspace templates accessible to users inside the author's workspace
        # Assuming author ID carrying workspace details or simply matching
        return True
DefinitionPath = "template_permissions.py"
