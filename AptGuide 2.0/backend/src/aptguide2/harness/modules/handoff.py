"""Handoff procedure for AptGuide 2.0 harness.

Handles user-initiated and tool-failure-triggered handoff to human agents.
"""

from __future__ import annotations

from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision


class HandoffProcedure:
    """Generates handoff summaries and sets handoff state on the frame."""

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        message = frame.message or ""

        # User-initiated handoff
        if decision.task == "handoff" and decision.procedure == "handoff.user_initiated":
            return self._user_initiated_handoff(frame)

        # Tool-failure-triggered handoff
        if decision.procedure == "handoff.tool_failure":
            return self._tool_failure_handoff(frame)

        # Fallback: treat as user-initiated
        return self._user_initiated_handoff(frame)

    def _user_initiated_handoff(self, frame: ConversationFrame) -> ProcedureResult:
        summary = self._build_handoff_summary(frame)
        frame.handoff = {
            "status": "handoff_requested",
            "trigger": "user_initiated",
            "summary": summary,
        }
        return ProcedureResult(
            task="handoff",
            phase="handoff_requested",
            reply="正在为您转接人工客服，请稍候...",
            metadata={"handoff_trigger": "user_initiated"},
            sources=[summary],
        )

    def _tool_failure_handoff(self, frame: ConversationFrame) -> ProcedureResult:
        summary = self._build_handoff_summary(frame)
        summary["trigger_reason"] = "consecutive_tool_failures"
        frame.handoff = {
            "status": "handoff_requested",
            "trigger": "tool_failure",
            "summary": summary,
        }
        return ProcedureResult(
            task="handoff",
            phase="handoff_requested",
            reply="系统遇到了一些问题，正在为您转接人工客服，请稍候...",
            metadata={"handoff_trigger": "tool_failure"},
            sources=[summary],
        )

    def _build_handoff_summary(self, frame: ConversationFrame) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "user_id": frame.user_id,
            "session_id": frame.session_id,
            "current_message": frame.message,
            "active_task": frame.active_task,
            "phase": frame.phase,
        }
        if frame.recent_messages:
            summary["recent_messages"] = frame.recent_messages[-6:]
        if frame.tool_observations:
            summary["tool_observations"] = frame.tool_observations[-5:]
        if frame.last_recommendations:
            summary["last_recommendations"] = frame.last_recommendations[:3]
        return summary
