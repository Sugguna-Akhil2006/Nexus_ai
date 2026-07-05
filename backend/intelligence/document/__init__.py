"""Document Intelligence package auto-registration."""

from backend.intelligence.core.registry import IntelligenceRegistry
from backend.intelligence.document.document_agent import DocumentModule

try:
    IntelligenceRegistry().register(DocumentModule())
except Exception:
    pass
