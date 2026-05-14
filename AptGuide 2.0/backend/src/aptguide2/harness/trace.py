from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import uuid4

from aptguide2.harness.contracts import AptGuideTrace, StageTrace


@dataclass(frozen=True)
class StageToken:
    index: int
    started_at: float


class TraceRecorder:
    """Records stage-level execution trace without chain-of-thought."""

    def __init__(
        self,
        trace_id: str | None = None,
        request_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        self.trace_id = trace_id or f"t-{uuid4().hex}"
        self.request_id = request_id or f"r-{uuid4().hex}"
        self.session_id = session_id
        self._stages: list[StageTrace] = []

    def start_stage(
        self,
        stage: str,
        strategy: str,
        input_summary: dict,
    ) -> StageToken:
        self._stages.append(
            StageTrace(
                stage=stage,
                strategy=strategy,
                input_summary=input_summary,
            )
        )
        return StageToken(index=len(self._stages) - 1, started_at=time.perf_counter())

    def finish_stage(
        self,
        token: StageToken,
        output_summary: dict,
        errors: list[str] | None = None,
    ) -> None:
        elapsed_ms = (time.perf_counter() - token.started_at) * 1000
        stage = self._stages[token.index]
        stage.output_summary = output_summary
        stage.latency_ms = round(elapsed_ms, 3)
        stage.errors = errors or []

    def to_trace(self) -> AptGuideTrace:
        return AptGuideTrace(
            trace_id=self.trace_id,
            request_id=self.request_id,
            session_id=self.session_id,
            stages=self._stages,
        )
