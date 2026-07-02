"""GitHub Intelligence package auto-registration."""

from backend.intelligence.core.registry import IntelligenceRegistry
from backend.intelligence.github.module import GitHubModule

try:
    IntelligenceRegistry().register(GitHubModule())
except Exception:
    pass
