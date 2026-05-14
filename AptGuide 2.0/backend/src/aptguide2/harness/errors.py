from __future__ import annotations


class AptGuideHarnessError(Exception):
    """Base exception for the AptGuide system harness."""


class StrategyNotFoundError(AptGuideHarnessError):
    """Raised when a named strategy is not registered."""


class ProcedureNotFoundError(AptGuideHarnessError):
    """Raised when no procedure can handle the selected route."""


class ReplayPIIError(AptGuideHarnessError):
    """Raised when a replay payload contains disallowed PII keys."""
