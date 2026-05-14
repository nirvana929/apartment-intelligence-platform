from __future__ import annotations

import json
from typing import Protocol

from aptguide3.observability.events import TraceEvent


class TraceSink(Protocol):
    def write(self, event: TraceEvent) -> None: ...


class ConsoleTraceSink:
    def write(self, event: TraceEvent) -> None:
        print(json.dumps(event.model_dump(), ensure_ascii=False))


class NullTraceSink:
    def write(self, event: TraceEvent) -> None:
        pass
