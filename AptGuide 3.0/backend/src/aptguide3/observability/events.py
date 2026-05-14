from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    event_type: str
    timestamp: float = Field(default_factory=time.time)
    session_id: str
    data: dict[str, Any] = Field(default_factory=dict)


class ChatTrace:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.events: list[TraceEvent] = []

    def emit(self, event_type: str, **data: Any) -> None:
        self.events.append(TraceEvent(event_type=event_type, session_id=self.session_id, data=data))

    def to_dict(self) -> dict[str, Any]:
        return {"session_id": self.session_id, "events": [e.model_dump() for e in self.events]}
