from __future__ import annotations

from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision


class CapabilityProcedure:
    """Fixed capability response. Does not call an LLM."""

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        return ProcedureResult(
            task="capability",
            phase="idle",
            reply=(
                "我是 AptGuide 2.0 租房助手，可以帮你找房、解释租房规则、"
                "整理看房预约信息，并在需要时引导人工接管。"
            ),
            metadata={"procedure": decision.procedure},
        )
