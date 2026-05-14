"""Memory manager for AptGuide 2.0 harness.

Handles per-turn message tracking, pending action lifecycle, and context updates.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from aptguide2.harness.contracts import ConversationFrame


class MemoryManager:
    """Manages conversation memory including recent messages and pending actions."""

    MAX_RECENT_MESSAGES = 12

    def update_recent_messages(self, frame: ConversationFrame, assistant_reply: str = "") -> None:
        """Append current user message and optional assistant reply to recent_messages."""
        if not frame.recent_messages:
            frame.recent_messages = []

        # Add user message
        frame.recent_messages.append({
            "role": "user",
            "content": frame.message,
            "request_id": frame.request_id,
            "timestamp": time.time(),
        })

        # Add assistant reply if provided
        if assistant_reply:
            frame.recent_messages.append({
                "role": "assistant",
                "content": assistant_reply,
                "request_id": frame.request_id,
                "timestamp": time.time(),
            })

        # Trim to max size
        if len(frame.recent_messages) > self.MAX_RECENT_MESSAGES:
            frame.recent_messages = frame.recent_messages[-self.MAX_RECENT_MESSAGES:]

    def create_pending_action(
        self,
        frame: ConversationFrame,
        action_type: str,
        payload: dict[str, Any],
        confirmation_id: str | None = None,
        expires_in_seconds: int = 300,
    ) -> dict[str, Any]:
        """Create a pending action requiring user confirmation."""
        if confirmation_id is None:
            confirmation_id = str(uuid.uuid4())[:8]

        pending = {
            "type": action_type,
            "confirmation_id": confirmation_id,
            "status": "pending",
            "payload": payload,
            "created_at": time.time(),
            "expires_at": time.time() + expires_in_seconds,
        }
        frame.pending_action = pending
        return pending

    def confirm_pending_action(self, frame: ConversationFrame, confirmation_id: str) -> dict[str, Any] | None:
        """Confirm a pending action. Returns payload if valid, None if expired/stale."""
        if frame.pending_action is None:
            return None

        pending = frame.pending_action

        # Check if expired
        if self.is_pending_action_expired(frame):
            frame.pending_action = None
            return None

        # Check confirmation_id matches
        if pending.get("confirmation_id") != confirmation_id:
            return None

        # Mark as confirmed
        pending["status"] = "confirmed"
        payload = pending.get("payload", {})
        frame.pending_action = None
        return payload

    def cancel_pending_action(self, frame: ConversationFrame) -> None:
        """Cancel the current pending action."""
        if frame.pending_action:
            frame.pending_action["status"] = "cancelled"
        frame.pending_action = None

    def is_pending_action_expired(self, frame: ConversationFrame) -> bool:
        """Check if pending action has expired."""
        if frame.pending_action is None:
            return False

        expires_at = frame.pending_action.get("expires_at", 0)
        return time.time() > expires_at

    def check_pending_action_expiry(self, frame: ConversationFrame) -> bool:
        """Check and clean up expired pending action. Returns True if action was expired."""
        if self.is_pending_action_expired(frame):
            frame.pending_action = None
            return True
        return False

    def update_tool_observations(self, frame: ConversationFrame, observation: dict[str, Any]) -> None:
        """Add a tool observation to the frame."""
        if not frame.tool_observations:
            frame.tool_observations = []
        frame.tool_observations.append(observation)

        # Keep only last 10 observations
        if len(frame.tool_observations) > 10:
            frame.tool_observations = frame.tool_observations[-10:]

    def get_consecutive_tool_failures(self, frame: ConversationFrame) -> int:
        """Count consecutive tool failures from the end of observations."""
        if not frame.tool_observations:
            return 0

        count = 0
        for obs in reversed(frame.tool_observations):
            if not obs.get("success", True):
                count += 1
            else:
                break
        return count
