"""Provider-independent AI service contracts."""

from abc import ABC, abstractmethod

from backend.models.ai import CVOptimizationRequest, CVOptimizationResult


class AIProviderError(Exception):
    """Raised when an AI provider cannot complete a request safely."""


class AIProvider(ABC):
    """Interface implemented by CV optimization AI providers."""

    @abstractmethod
    def optimize_cv(
        self,
        request: CVOptimizationRequest,
    ) -> CVOptimizationResult:
        """Transform extracted CV content into a canonical optimized CV."""
