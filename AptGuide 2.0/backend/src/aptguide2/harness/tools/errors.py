from __future__ import annotations


class ToolGovernanceError(Exception):
    """Base error for tool governance."""


class ToolAlreadyRegisteredError(ToolGovernanceError):
    """Raised when registering a tool name that already exists."""


class ToolNotFoundError(ToolGovernanceError):
    """Raised when a requested tool is not in the registry."""


class ToolTimeoutError(ToolGovernanceError):
    """Raised when a tool execution exceeds its timeout."""


class ToolExecutionError(ToolGovernanceError):
    """Raised when a tool executor fails unexpectedly."""
