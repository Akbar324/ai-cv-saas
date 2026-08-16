"""Domain models for the AI CV SaaS."""

from backend.models.cv import CanonicalCV
from backend.models.document import ExtractedDocument

__all__ = [
    "CanonicalCV",
    "ExtractedDocument",
]
