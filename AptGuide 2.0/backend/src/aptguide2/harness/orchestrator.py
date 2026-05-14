from __future__ import annotations

from typing import Any

from aptguide2.harness.composer import ResponseComposer
from aptguide2.harness.context import InMemoryContextStore
from aptguide2.harness.contracts import AptGuideRequest, AptGuideResponse
from aptguide2.harness.memory import MemoryManager
from aptguide2.harness.procedures import ProcedureRuntime
from aptguide2.harness.routing import HybridRouter
from aptguide2.harness.trace import TraceRecorder


class AptGuideHarness:
    """System-level AptGuide 2.0 harness orchestrator."""

    def __init__(
        self,
        context_store: InMemoryContextStore,
        router: HybridRouter,
        procedure_runtime: ProcedureRuntime,
        include_trace: bool = False,
        tool_runtime: Any | None = None,
    ) -> None:
        self.context_store = context_store
        self.router = router
        self.procedure_runtime = procedure_runtime
        self.composer = ResponseComposer(include_trace=include_trace)
        self.tool_runtime = tool_runtime
        self.memory = MemoryManager()

    def run(self, request: AptGuideRequest) -> AptGuideResponse:
        recorder = TraceRecorder(request_id=request.request_id, session_id=request.session_id)

        token = recorder.start_stage(
            "context.load",
            "in_memory_v1",
            {"session_id": request.session_id, "message_len": len(request.message)},
        )
        frame = self.context_store.load(request)
        self.memory.check_pending_action_expiry(frame)
        recorder.finish_stage(token, {"phase": frame.phase, "has_pending_action": frame.pending_action is not None})

        token = recorder.start_stage("routing", self.router.name, {"message": request.message[:80]})
        decision = self.router.route(frame)
        recorder.finish_stage(
            token,
            {
                "task": decision.task,
                "procedure": decision.procedure,
                "domain_category": decision.domain_category,
            },
        )

        token = recorder.start_stage("procedure.run", decision.procedure, {"task": decision.task})
        result = self.procedure_runtime.run(frame, decision, tool_runtime=self.tool_runtime)
        recorder.finish_stage(
            token,
            {
                "phase": result.phase,
                "card_count": len(result.cards),
                "source_count": len(result.sources),
                "fallback_reason": result.fallback_reason,
            },
        )

        if (
            result.task != "handoff"
            and self.memory.get_consecutive_tool_failures(frame) >= 2
            and self.procedure_runtime.has("handoff.tool_failure")
        ):
            handoff_decision = decision.model_copy(
                update={
                    "task": "handoff",
                    "procedure": "handoff.tool_failure",
                    "confidence": 0.9,
                    "domain_category": "handoff",
                    "reason": "consecutive tool failures",
                }
            )
            token = recorder.start_stage("procedure.run", "handoff.tool_failure", {"task": "handoff"})
            result = self.procedure_runtime.run(frame, handoff_decision, tool_runtime=self.tool_runtime)
            recorder.finish_stage(
                token,
                {
                    "phase": result.phase,
                    "card_count": len(result.cards),
                    "source_count": len(result.sources),
                    "fallback_reason": result.fallback_reason,
                },
            )
            decision = handoff_decision

        frame.phase = result.phase
        frame.active_task = result.task
        if result.cards:
            frame.last_recommendations = result.cards
        if result.pending_action:
            frame.pending_action = result.pending_action
        self.memory.update_recent_messages(frame, assistant_reply=result.reply)
        self.context_store.save(frame)

        trace = recorder.to_trace()
        return self.composer.compose(frame, decision, result, trace)
