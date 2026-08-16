"""Domain models for the AI CV SaaS."""

from backend.models.ai import (
    AIUsage,
    CVOptimizationRequest,
    CVOptimizationResult,
)
from backend.models.cv import CanonicalCV
from backend.models.document import ExtractedDocument

__all__ = [
    "AIUsage",
    "CVOptimizationRequest",
    "CVOptimizationResult",
    "CanonicalCV",
    "ExtractedDocument",
]
