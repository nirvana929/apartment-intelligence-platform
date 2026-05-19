from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aptguide3.observability.events import TraceEvent

if TYPE_CHECKING:
    from aptguide3.persistence.contracts import TraceRepository


class RepositoryTraceSink:
    def __init__(self, repo: TraceRepository) -> None:
        self.repo = repo

    def write(self, event: TraceEvent) -> None:
        coro = self.repo.append_trace_event(
            trace_id=event.session_id,
            request_id="",
            session_id=event.session_id,
            event_name=event.event_type,
            payload=event.data,
        )
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(coro)
        else:
            asyncio.run(coro)
