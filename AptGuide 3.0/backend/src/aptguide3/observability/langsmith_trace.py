"""No-op safe LangSmith recorder for application-level chat output tracing.

When LangSmith is disabled or the ``langsmith`` package is not installed,
``record_chat`` silently does nothing so it never breaks the chat flow.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LangSmithChatRecorder:
    """Records final ChatService output as a LangSmith root run.

    Parameters
    ----------
    enabled:
        Master switch.  When ``False`` every call to ``record_chat`` is a no-op.
    project_name:
        LangSmith project name (e.g. ``"aptguide3-local"``).
    service_name:
        Logical service tag written into run metadata.
    environment:
        Deployment environment tag (e.g. ``"local"``, ``"prod"``).
    """

    def __init__(
        self,
        enabled: bool,
        project_name: str,
        service_name: str,
        environment: str,
    ) -> None:
        self.enabled = enabled
        self.project_name = project_name
        self.service_name = service_name
        self.environment = environment

    def record_chat(
        self,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        """Record a single chat turn.  No-op when disabled or on error."""
        if not self.enabled:
            return
        try:
            self._record(inputs=inputs, outputs=outputs, metadata=metadata)
        except Exception:
            logger.debug("LangSmith record_chat failed (non-fatal)", exc_info=True)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _record(
        self,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        try:
            from langsmith import Client as LangSmithClient
        except ImportError:
            logger.debug("langsmith package not installed; skipping trace")
            return

        try:
            client = LangSmithClient()
            client.create_run(
                name="chat_turn",
                run_type="chain",
                inputs=inputs,
                outputs=outputs,
                metadata={
                    "service": self.service_name,
                    "environment": self.environment,
                    **metadata,
                },
                project_name=self.project_name,
            )
        except Exception:
            logger.debug("LangSmith create_run failed (non-fatal)", exc_info=True)
