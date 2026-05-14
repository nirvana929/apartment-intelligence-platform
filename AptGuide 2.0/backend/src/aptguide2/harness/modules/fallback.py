from __future__ import annotations

from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision


class FallbackProcedure:
    """Safe fallback procedure for unsupported or blocked requests."""

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        if "guarantee" in decision.safety_flags:
            return ProcedureResult(
                task="fallback",
                phase="boundary_declined",
                reply="我无法保证邻居、噪音或未来变化，但可以帮你优先筛选安静、低噪音、适合学习的房源。",
                fallback_reason="safety_boundary",
            )
        if "privacy" in decision.safety_flags:
            return ProcedureResult(
                task="fallback",
                phase="boundary_declined",
                reply="我不能查询或透露其他租户的个人信息。可以帮你处理自己的找房、预约或租约问题。",
                fallback_reason="privacy_boundary",
            )
        return ProcedureResult(
            task="fallback",
            phase="boundary_declined",
            reply="抱歉，这个问题超出了我的服务范围。我可以帮你找房或回答租房相关问题。",
            fallback_reason="unsupported_request",
        )
