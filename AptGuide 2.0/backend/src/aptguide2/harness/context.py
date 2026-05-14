from __future__ import annotations

from aptguide2.harness.contracts import AptGuideRequest, ConversationFrame


class InMemoryContextStore:
    """Development context store. Replace with Redis or DB later."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationFrame] = {}

    def load(self, request: AptGuideRequest) -> ConversationFrame:
        if request.session_id and request.session_id in self._sessions:
            previous = self._sessions[request.session_id].model_copy(deep=True)
            previous.request_id = request.request_id
            previous.user_id = request.user_id
            previous.message = request.message
            previous.action = request.action
            return previous

        return ConversationFrame(
            session_id=request.session_id,
            request_id=request.request_id,
            user_id=request.user_id,
            message=request.message,
            action=request.action,
        )

    def save(self, frame: ConversationFrame) -> None:
        if frame.session_id:
            self._sessions[frame.session_id] = frame.model_copy(deep=True)
