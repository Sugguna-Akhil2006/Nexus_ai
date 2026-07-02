"""GitHub Intelligence module specific exception classes."""

class GitHubAnalysisError(Exception):
    """Base exception for all GitHub Analysis engine failures."""
    pass


class InvalidRepositoryError(GitHubAnalysisError):
    """Raised when repository format, URL, or local path is invalid or unreadable."""
    pass


class ConnectionTimeoutError(GitHubAnalysisError):
    """Raised when request timeout prevents retrieving GitHub API data."""
    pass


class AnalysisPipelineError(GitHubAnalysisError):
    """Raised when execution workflow fails at a component stage."""
    pass
