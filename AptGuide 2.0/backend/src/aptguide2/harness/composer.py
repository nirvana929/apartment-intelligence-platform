from __future__ import annotations

from aptguide2.harness.contracts import (
    AptGuideResponse,
    AptGuideTrace,
    ConversationFrame,
    ProcedureResult,
    RouteDecision,
)


class ResponseComposer:
    """Builds the final AptGuide response from procedure output."""

    def __init__(self, include_trace: bool = False) -> None:
        self.include_trace = include_trace

    def compose(
        self,
        frame: ConversationFrame,
        decision: RouteDecision,
        result: ProcedureResult,
        trace: AptGuideTrace,
    ) -> AptGuideResponse:
        return AptGuideResponse(
            session_id=frame.session_id,
            request_id=frame.request_id,
            trace_id=trace.trace_id,
            reply=result.reply,
            phase=result.phase,
            domain_category=decision.domain_category,
            cards=result.cards,
            actions=result.actions,
            pending_action=result.pending_action,
            sources=result.sources,
            metadata={
                **result.metadata,
                "procedure": decision.procedure,
                "task": decision.task,
                "route_confidence": decision.confidence,
                "fallback_reason": result.fallback_reason,
                "card_count": len(result.cards),
                "source_count": len(result.sources),
                "action_count": len(result.actions),
                "has_pending_action": result.pending_action is not None,
            },
            trace=trace if self.include_trace else None,
        )
