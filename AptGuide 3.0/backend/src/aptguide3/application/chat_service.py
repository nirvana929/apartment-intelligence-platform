from __future__ import annotations

from typing import TYPE_CHECKING

from aptguide3.application.procedure_runtime import ProcedureRuntime
from aptguide3.application.response_composer import ResponseComposer
from aptguide3.application.safety_boundary import SafetyBoundary
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.responses import ChatResponse
from aptguide3.persistence.session_repo import InMemorySessionRepo, SessionRepository

if TYPE_CHECKING:
    from aptguide3.observability.trace import Tracer


class ChatService:
    def __init__(
        self,
        safety: SafetyBoundary,
        understanding,
        runtime: ProcedureRuntime,
        session_repo: SessionRepository | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self.safety = safety
        self.understanding = understanding
        self.runtime = runtime
        self.composer = ResponseComposer()
        self.session_repo = session_repo or InMemorySessionRepo()
        self.tracer = tracer

    def run(self, frame: ConversationFrame) -> ChatResponse:
        trace = self.tracer.start_trace(frame.session_id) if self.tracer else None

        if trace:
            trace.emit("chat_started", message=frame.message, session_id=frame.session_id)

        session_data = self.session_repo.load(frame.session_id)
        if session_data and "pending_action" in session_data and frame.pending_action is None:
            frame = frame.model_copy(update={"pending_action": session_data["pending_action"]})

        safety_decision = self.safety.check(frame.message)
        if trace:
            trace.emit("safety_check", blocked=safety_decision.blocked)

        if safety_decision.blocked:
            if trace:
                trace.emit("chat_completed", phase="safety", card_count=0)
                self.tracer.finish_trace(trace)
            return self.composer.compose(
                ProcedureResult(
                    message=safety_decision.message,
                    phase="safety",
                    metadata={"reason": safety_decision.reason},
                )
            )

        understanding = self.understanding.understand(frame.message)
        if trace:
            trace.emit(
                "understanding_completed",
                route=understanding.route,
                task=understanding.task,
                confidence=understanding.confidence,
            )

        result = self.runtime.run(frame, understanding)
        if trace:
            procedure_name = self.runtime._procedure_name(understanding)
            trace.emit("procedure_dispatched", procedure_name=procedure_name)

        new_session = {
            **(session_data or {}),
            "last_task": understanding.task,
        }
        if result.metadata:
            new_session["last_metadata"] = result.metadata
        self.session_repo.save(frame.session_id, new_session)

        response = self.composer.compose(result)
        if trace:
            trace.emit("chat_completed", phase=result.phase, card_count=len(result.cards))
            self.tracer.finish_trace(trace)
        return response
