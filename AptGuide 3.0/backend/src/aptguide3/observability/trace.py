from __future__ import annotations

from aptguide3.observability.events import ChatTrace
from aptguide3.observability.sink import TraceSink


class Tracer:
    def __init__(self, sink: TraceSink) -> None:
        self.sink = sink

    def start_trace(self, session_id: str) -> ChatTrace:
        return ChatTrace(session_id)

    def finish_trace(self, trace: ChatTrace) -> None:
        for event in trace.events:
            self.sink.write(event)
