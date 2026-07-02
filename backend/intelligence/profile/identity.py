"""Identity Resolution engine checking if two profile entries belong to the same entity."""

from backend.intelligence.profile.models import ProfilePersonalInfo


class IdentityResolver:
    """Verifies contact match thresholds across name, email, github, and linkedin links."""

    def resolve_identity(self, base: ProfilePersonalInfo, incoming: ProfilePersonalInfo) -> bool:
        """Determines if the base profile and incoming profile belong to the same person.

        Args:
            base: Current profile contact info.
            incoming: Incoming profile contact info.

        Returns:
            bool: True if there is a match, False otherwise.
        """
        # Match by email
        if base.email and incoming.email:
            if base.email.strip().lower() == incoming.email.strip().lower():
                return True

        # Match by GitHub username/link
        if base.github and incoming.github:
            b_git = base.github.strip().lower().rstrip('/')
            i_git = incoming.github.strip().lower().rstrip('/')
            if b_git == i_git or b_git.split('/')[-1] == i_git.split('/')[-1]:
                return True

        # Match by LinkedIn URL
        if base.linkedin and incoming.linkedin:
            b_link = base.linkedin.strip().lower().rstrip('/')
            i_link = incoming.linkedin.strip().lower().rstrip('/')
            if b_link == i_link:
                return True

        # Match by exact name similarity
        if base.full_name and incoming.full_name:
            if base.full_name.strip().lower() == incoming.full_name.strip().lower():
                return True

        return False
