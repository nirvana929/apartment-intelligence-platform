# Enterprise AptGuide Harness Agent Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the first enterprise-grade AptGuide 2.0 harness foundation so `/chat` can run through a system-level harness while the existing RAG MVP remains available.

**Architecture:** Create `aptguide2.harness` as the system runtime. It owns request contracts, context loading, safety routing, procedure selection, tool governance, response composition, trace, and replay. The current `aptguide2.rag` package remains the RAG baseline and is mounted into the harness as one module.

**Tech Stack:** FastAPI, Pydantic, pytest, existing `aptguide2.rag`, existing `VectorAdapter`, existing `LeaseAdapter`, OpenAI-compatible clients already configured in `api/deps.py`.

---

## Execution Rules

1. Do not delete or rewrite `aptguide2.rag` during this plan.
2. Default `/chat` behavior must remain the current MVP unless `APTGUIDE_PIPELINE_VERSION=harness_v1`.
3. Write tests before implementation for each task.
4. Keep harness stages typed with Pydantic models.
5. Do not call external Milvus, lease, or LLM services in unit tests. Use fake strategies and fake adapters.
6. Run the listed tests after each task.

## Current Code Anchors

Read these files before starting:

- `backend/src/aptguide2/api/app.py`
- `backend/src/aptguide2/api/schemas.py`
- `backend/src/aptguide2/api/deps.py`
- `backend/src/aptguide2/core/config.py`
- `backend/src/aptguide2/rag/pipeline.py`
- `backend/src/aptguide2/rag/schemas.py`
- `backend/src/aptguide2/tools/vector_adapter.py`
- `backend/src/aptguide2/tools/lease_adapter.py`

## Target Package

Create this package:

```text
backend/src/aptguide2/harness/
├── __init__.py
├── contracts.py
├── errors.py
├── registry.py
├── context.py
├── safety.py
├── routing.py
├── procedures.py
├── composer.py
├── trace.py
├── replay.py
├── orchestrator.py
└── modules/
    ├── __init__.py
    └── rag/
        ├── __init__.py
        └── baseline.py
```

Create tests:

```text
backend/tests/unit/harness/
├── test_contracts.py
├── test_registry.py
├── test_context.py
├── test_safety.py
├── test_routing.py
├── test_procedures.py
├── test_composer.py
├── test_trace.py
├── test_replay.py
├── test_orchestrator.py
└── modules/
    └── rag/
        └── test_baseline.py
```

---

## Task 1: Add Harness Contracts

**Files:**

- Create: `backend/src/aptguide2/harness/__init__.py`
- Create: `backend/src/aptguide2/harness/contracts.py`
- Create: `backend/src/aptguide2/harness/errors.py`
- Test: `backend/tests/unit/harness/test_contracts.py`

- [ ] **Step 1: Write failing contract tests**

Create `backend/tests/unit/harness/test_contracts.py`:

```python
import pytest
from pydantic import ValidationError

from aptguide2.harness.contracts import (
    AptGuideRequest,
    AptGuideResponse,
    ConversationFrame,
    ProcedureResult,
    RouteDecision,
    StageTrace,
)


def test_request_requires_request_id():
    req = AptGuideRequest(request_id="r-1", session_id="s-1", message="找房")
    assert req.request_id == "r-1"
    assert req.message == "找房"
    assert req.harness_version == "harness_v1"


def test_frame_defaults_are_isolated():
    f1 = ConversationFrame(request_id="r-1")
    f2 = ConversationFrame(request_id="r-2")
    f1.last_recommendations.append({"room_id": 1})
    assert f2.last_recommendations == []


def test_route_decision_confidence_bounds():
    with pytest.raises(ValidationError):
        RouteDecision(task="room_search", procedure="rag.room_search", confidence=1.5)


def test_procedure_result_defaults():
    result = ProcedureResult(task="capability", phase="idle", reply="我是租房助手")
    assert result.cards == []
    assert result.sources == []


def test_response_carries_trace_id():
    resp = AptGuideResponse(
        request_id="r-1",
        trace_id="t-1",
        reply="ok",
        phase="idle",
        domain_category="in_domain",
    )
    assert resp.trace_id == "t-1"


def test_stage_trace_defaults():
    stage = StageTrace(stage="routing", strategy="rule_v1")
    assert stage.errors == []
```

- [ ] **Step 2: Run tests and confirm failure**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_contracts.py -q
```

Expected: fail with `ModuleNotFoundError: No module named 'aptguide2.harness'`.

- [ ] **Step 3: Implement `errors.py`**

Create `backend/src/aptguide2/harness/errors.py`:

```python
from __future__ import annotations


class AptGuideHarnessError(Exception):
    """Base exception for the AptGuide system harness."""


class StrategyNotFoundError(AptGuideHarnessError):
    """Raised when a named strategy is not registered."""


class ProcedureNotFoundError(AptGuideHarnessError):
    """Raised when no procedure can handle the selected route."""


class ReplayPIIError(AptGuideHarnessError):
    """Raised when a replay payload contains disallowed PII keys."""
```

- [ ] **Step 4: Implement `contracts.py`**

Create `backend/src/aptguide2/harness/contracts.py`:

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Task = Literal[
    "room_search",
    "kb_qa",
    "appointment",
    "user_data",
    "memory",
    "handoff",
    "capability",
    "fallback",
]
RiskLevel = Literal["low", "medium", "high"]


class AptGuideRequest(BaseModel):
    session_id: str | None = None
    request_id: str
    user_id: str | None = None
    message: str = ""
    action: dict[str, Any] | None = None
    client_context: dict[str, Any] = Field(default_factory=dict)
    harness_version: str = "harness_v1"


class ConversationFrame(BaseModel):
    session_id: str | None = None
    request_id: str
    user_id: str | None = None
    message: str = ""
    action: dict[str, Any] | None = None
    phase: str = "idle"
    domain_category: str = "unknown"
    active_task: Task | None = None
    task_slots: dict[str, Any] = Field(default_factory=dict)
    recent_messages: list[dict[str, Any]] = Field(default_factory=list)
    rolling_summary: str = ""
    long_term_profile: dict[str, Any] = Field(default_factory=dict)
    pending_action: dict[str, Any] | None = None
    last_recommendations: list[dict[str, Any]] = Field(default_factory=list)
    tool_observations: list[dict[str, Any]] = Field(default_factory=list)
    recovery_decision: dict[str, Any] | None = None
    handoff: dict[str, Any] | None = None


class RouteDecision(BaseModel):
    task: Task
    procedure: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel = "low"
    domain_category: str = "unknown"
    reason: str = ""
    safety_flags: list[str] = Field(default_factory=list)


class ProcedureResult(BaseModel):
    task: Task
    phase: str
    reply: str = ""
    cards: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    fallback_reason: str = ""


class StageTrace(BaseModel):
    stage: str
    strategy: str
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
    errors: list[str] = Field(default_factory=list)


class AptGuideTrace(BaseModel):
    trace_id: str
    request_id: str
    session_id: str | None = None
    stages: list[StageTrace] = Field(default_factory=list)


class AptGuideResponse(BaseModel):
    session_id: str | None = None
    request_id: str
    trace_id: str
    reply: str
    phase: str
    domain_category: str
    cards: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    trace: AptGuideTrace | None = None
```

Create `backend/src/aptguide2/harness/__init__.py`:

```python
"""Enterprise AptGuide 2.0 system harness."""
```

- [ ] **Step 5: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_contracts.py -q
```

Expected: pass.

---

## Task 2: Add Strategy Registry

**Files:**

- Create: `backend/src/aptguide2/harness/registry.py`
- Test: `backend/tests/unit/harness/test_registry.py`

- [ ] **Step 1: Write failing registry tests**

Create `backend/tests/unit/harness/test_registry.py`:

```python
import pytest

from aptguide2.harness.errors import StrategyNotFoundError
from aptguide2.harness.registry import StrategyRegistry


def test_register_and_get_strategy():
    registry = StrategyRegistry()
    strategy = object()
    registry.register("router", "rule_v1", strategy)
    assert registry.get("router", "rule_v1") is strategy


def test_missing_strategy_raises_clear_error():
    registry = StrategyRegistry()
    with pytest.raises(StrategyNotFoundError) as exc:
        registry.get("router", "missing")
    assert "router.missing" in str(exc.value)


def test_names_returns_registered_names_for_category():
    registry = StrategyRegistry()
    registry.register("router", "rule_v1", object())
    registry.register("router", "llm_v1", object())
    registry.register("reranker", "rule_v1", object())
    assert registry.names("router") == ["llm_v1", "rule_v1"]
```

- [ ] **Step 2: Implement registry**

Create `backend/src/aptguide2/harness/registry.py`:

```python
from __future__ import annotations

from typing import Any

from aptguide2.harness.errors import StrategyNotFoundError


class StrategyRegistry:
    """In-memory registry for harness strategies and procedures."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Any] = {}

    def register(self, category: str, name: str, strategy: Any) -> None:
        self._items[(category, name)] = strategy

    def get(self, category: str, name: str) -> Any:
        key = (category, name)
        if key not in self._items:
            raise StrategyNotFoundError(f"Strategy not found: {category}.{name}")
        return self._items[key]

    def names(self, category: str) -> list[str]:
        return sorted(name for (cat, name) in self._items if cat == category)
```

- [ ] **Step 3: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_registry.py -q
```

Expected: pass.

---

## Task 3: Add Trace Recorder

**Files:**

- Create: `backend/src/aptguide2/harness/trace.py`
- Test: `backend/tests/unit/harness/test_trace.py`

- [ ] **Step 1: Write failing trace tests**

Create `backend/tests/unit/harness/test_trace.py`:

```python
from aptguide2.harness.trace import TraceRecorder


def test_trace_recorder_records_stage():
    recorder = TraceRecorder(trace_id="t-1", request_id="r-1", session_id="s-1")
    token = recorder.start_stage("routing", "rule_v1", {"message_len": 4})
    recorder.finish_stage(token, {"task": "room_search"})
    trace = recorder.to_trace()

    assert trace.trace_id == "t-1"
    assert trace.request_id == "r-1"
    assert trace.stages[0].stage == "routing"
    assert trace.stages[0].output_summary == {"task": "room_search"}
    assert trace.stages[0].latency_ms >= 0


def test_trace_recorder_records_errors():
    recorder = TraceRecorder(trace_id="t-1", request_id="r-1")
    token = recorder.start_stage("tool", "room.search", {})
    recorder.finish_stage(token, {}, errors=["TOOL_TIMEOUT"])
    trace = recorder.to_trace()
    assert trace.stages[0].errors == ["TOOL_TIMEOUT"]
```

- [ ] **Step 2: Implement trace recorder**

Create `backend/src/aptguide2/harness/trace.py`:

```python
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
```

- [ ] **Step 3: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_trace.py -q
```

Expected: pass.

---

## Task 4: Add Context Loader

**Files:**

- Create: `backend/src/aptguide2/harness/context.py`
- Test: `backend/tests/unit/harness/test_context.py`

- [ ] **Step 1: Write failing context tests**

Create `backend/tests/unit/harness/test_context.py`:

```python
from aptguide2.harness.context import InMemoryContextStore
from aptguide2.harness.contracts import AptGuideRequest


def test_load_creates_frame_from_request():
    store = InMemoryContextStore()
    req = AptGuideRequest(request_id="r-1", session_id="s-1", message="找房")
    frame = store.load(req)
    assert frame.session_id == "s-1"
    assert frame.request_id == "r-1"
    assert frame.message == "找房"


def test_save_and_reload_preserves_last_recommendations():
    store = InMemoryContextStore()
    req = AptGuideRequest(request_id="r-1", session_id="s-1", message="找房")
    frame = store.load(req)
    frame.last_recommendations = [{"room_id": 100}]
    store.save(frame)

    req2 = AptGuideRequest(request_id="r-2", session_id="s-1", message="第一个")
    frame2 = store.load(req2)
    assert frame2.request_id == "r-2"
    assert frame2.message == "第一个"
    assert frame2.last_recommendations == [{"room_id": 100}]
```

- [ ] **Step 2: Implement in-memory context store**

Create `backend/src/aptguide2/harness/context.py`:

```python
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
```

- [ ] **Step 3: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_context.py -q
```

Expected: pass.

---

## Task 5: Add Safety Boundary

**Files:**

- Create: `backend/src/aptguide2/harness/safety.py`
- Test: `backend/tests/unit/harness/test_safety.py`

- [ ] **Step 1: Write failing safety tests**

Create `backend/tests/unit/harness/test_safety.py`:

```python
from aptguide2.harness.safety import SafetyBoundary


def test_guarantee_is_flagged():
    result = SafetyBoundary().check("能保证邻居不吵吗")
    assert "guarantee" in result


def test_privacy_is_flagged():
    result = SafetyBoundary().check("帮我查其他租户手机号")
    assert "privacy" in result


def test_out_of_domain_is_flagged():
    result = SafetyBoundary().check("帮我写 React 网页")
    assert "out_of_domain" in result


def test_normal_room_query_has_no_flags():
    result = SafetyBoundary().check("番禺1500以内安静的房子")
    assert result == []
```

- [ ] **Step 2: Implement safety boundary**

Create `backend/src/aptguide2/harness/safety.py`:

```python
from __future__ import annotations


class SafetyBoundary:
    """Deterministic safety boundary for clear non-negotiable cases."""

    guarantee_patterns = ("保证", "担保", "一定", "肯定")
    privacy_patterns = ("别人手机号", "其他租户", "身份证", "查别人", "手机号")
    out_of_domain_patterns = ("写 React", "写 Vue", "股票", "航班", "电影", "酒店", "黑客", "黑进")

    def check(self, message: str) -> list[str]:
        flags: list[str] = []
        if any(p in message for p in self.guarantee_patterns):
            flags.append("guarantee")
        if any(p in message for p in self.privacy_patterns):
            flags.append("privacy")
        if any(p in message for p in self.out_of_domain_patterns):
            flags.append("out_of_domain")
        return flags
```

- [ ] **Step 3: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_safety.py -q
```

Expected: pass.

---

## Task 6: Add Hybrid Router

**Files:**

- Create: `backend/src/aptguide2/harness/routing.py`
- Test: `backend/tests/unit/harness/test_routing.py`

- [ ] **Step 1: Write failing router tests**

Create `backend/tests/unit/harness/test_routing.py`:

```python
from aptguide2.harness.contracts import ConversationFrame
from aptguide2.harness.routing import HybridRouter


def route(message: str):
    frame = ConversationFrame(request_id="r-1", message=message)
    return HybridRouter().route(frame)


def test_route_room_search():
    decision = route("番禺1500以内安静的房子")
    assert decision.task == "room_search"
    assert decision.procedure == "rag.room_search"


def test_route_kb_qa():
    decision = route("押金多久到账")
    assert decision.task == "kb_qa"
    assert decision.procedure == "rag.kb_qa"
    assert decision.risk_level == "high"


def test_route_capability():
    decision = route("你能做什么")
    assert decision.task == "capability"
    assert decision.procedure == "capability.profile"


def test_route_safety_fallback():
    decision = route("你能保证邻居不会吵吗")
    assert decision.task == "fallback"
    assert "guarantee" in decision.safety_flags
```

- [ ] **Step 2: Implement router**

Create `backend/src/aptguide2/harness/routing.py`:

```python
from __future__ import annotations

from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.safety import SafetyBoundary


class HybridRouter:
    """Baseline router for AptGuide procedures."""

    name = "hybrid_router_v1"

    capability_terms = ("你能做什么", "你是谁", "你是什么助手")
    room_terms = ("找房", "房子", "房源", "租房", "公寓", "以内", "附近", "安静", "近地铁", "推荐")
    kb_terms = ("押金", "退租", "合同", "租约", "预约规则", "怎么预约", "报修", "投诉", "隐私", "注销")
    appointment_terms = ("预约第", "预约看房", "帮我预约")
    high_risk_terms = ("押金", "违约金", "退租", "合同", "赔偿", "扣钱", "扣多少")

    def __init__(self, safety: SafetyBoundary | None = None) -> None:
        self.safety = safety or SafetyBoundary()

    def route(self, frame: ConversationFrame) -> RouteDecision:
        message = frame.message or ""
        flags = self.safety.check(message)
        if flags:
            return RouteDecision(
                task="fallback",
                procedure="fallback.safety",
                confidence=0.95,
                domain_category="blocked",
                reason="safety boundary matched",
                safety_flags=flags,
            )

        if any(term in message for term in self.capability_terms):
            return RouteDecision(
                task="capability",
                procedure="capability.profile",
                confidence=0.95,
                domain_category="in_domain_capability",
                reason="capability question",
            )

        if any(term in message for term in self.appointment_terms):
            return RouteDecision(
                task="appointment",
                procedure="appointment.workflow",
                confidence=0.8,
                domain_category="in_domain_task",
                reason="appointment request",
            )

        risk_level = "high" if any(term in message for term in self.high_risk_terms) else "low"
        if any(term in message for term in self.kb_terms):
            return RouteDecision(
                task="kb_qa",
                procedure="rag.kb_qa",
                confidence=0.85,
                risk_level=risk_level,
                domain_category="in_domain_knowledge",
                reason="rental knowledge question",
            )

        if any(term in message for term in self.room_terms):
            return RouteDecision(
                task="room_search",
                procedure="rag.room_search",
                confidence=0.75,
                domain_category="in_domain_task",
                reason="room search request",
            )

        return RouteDecision(
            task="fallback",
            procedure="fallback.unknown",
            confidence=0.5,
            domain_category="unknown",
            reason="no supported procedure matched",
        )
```

- [ ] **Step 3: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_routing.py -q
```

Expected: pass.

---

## Task 7: Add Procedure Runtime

**Files:**

- Create: `backend/src/aptguide2/harness/procedures.py`
- Test: `backend/tests/unit/harness/test_procedures.py`

- [ ] **Step 1: Write failing procedure tests**

Create `backend/tests/unit/harness/test_procedures.py`:

```python
import pytest

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.errors import ProcedureNotFoundError
from aptguide2.harness.procedures import ProcedureRuntime


class FakeProcedure:
    def run(self, frame, decision):
        return ProcedureResult(task=decision.task, phase="done", reply="ok")


def test_runtime_runs_registered_procedure():
    runtime = ProcedureRuntime()
    runtime.register("fake.run", FakeProcedure())
    frame = ConversationFrame(request_id="r-1", message="hello")
    decision = RouteDecision(task="capability", procedure="fake.run", confidence=1.0)
    result = runtime.run(frame, decision)
    assert result.reply == "ok"


def test_runtime_raises_for_missing_procedure():
    runtime = ProcedureRuntime()
    frame = ConversationFrame(request_id="r-1", message="hello")
    decision = RouteDecision(task="capability", procedure="missing", confidence=1.0)
    with pytest.raises(ProcedureNotFoundError):
        runtime.run(frame, decision)
```

- [ ] **Step 2: Implement procedure runtime**

Create `backend/src/aptguide2/harness/procedures.py`:

```python
from __future__ import annotations

from typing import Protocol

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.errors import ProcedureNotFoundError


class Procedure(Protocol):
    def run(self, frame: ConversationFrame, decision: RouteDecision) -> ProcedureResult:
        ...


class ProcedureRuntime:
    """Executes registered procedures by route decision."""

    def __init__(self) -> None:
        self._procedures: dict[str, Procedure] = {}

    def register(self, name: str, procedure: Procedure) -> None:
        self._procedures[name] = procedure

    def run(self, frame: ConversationFrame, decision: RouteDecision) -> ProcedureResult:
        procedure = self._procedures.get(decision.procedure)
        if procedure is None:
            raise ProcedureNotFoundError(f"Procedure not found: {decision.procedure}")
        return procedure.run(frame, decision)
```

- [ ] **Step 3: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_procedures.py -q
```

Expected: pass.

---

## Task 8: Add System Response Composer

**Files:**

- Create: `backend/src/aptguide2/harness/composer.py`
- Test: `backend/tests/unit/harness/test_composer.py`

- [ ] **Step 1: Write failing composer tests**

Create `backend/tests/unit/harness/test_composer.py`:

```python
from aptguide2.harness.composer import ResponseComposer
from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.trace import TraceRecorder


def test_composer_builds_response():
    frame = ConversationFrame(request_id="r-1", session_id="s-1", message="你能做什么")
    decision = RouteDecision(
        task="capability",
        procedure="capability.profile",
        confidence=0.9,
        domain_category="in_domain_capability",
    )
    result = ProcedureResult(task="capability", phase="idle", reply="我是租房助手")
    trace = TraceRecorder(trace_id="t-1", request_id="r-1", session_id="s-1").to_trace()

    response = ResponseComposer(include_trace=True).compose(frame, decision, result, trace)
    assert response.reply == "我是租房助手"
    assert response.trace_id == "t-1"
    assert response.domain_category == "in_domain_capability"
    assert response.trace is not None


def test_composer_can_hide_trace():
    frame = ConversationFrame(request_id="r-1", session_id="s-1")
    decision = RouteDecision(task="fallback", procedure="fallback.unknown", confidence=0.5)
    result = ProcedureResult(task="fallback", phase="boundary_declined", reply="暂时无法处理")
    trace = TraceRecorder(trace_id="t-1", request_id="r-1", session_id="s-1").to_trace()

    response = ResponseComposer(include_trace=False).compose(frame, decision, result, trace)
    assert response.trace is None
```

- [ ] **Step 2: Implement composer**

Create `backend/src/aptguide2/harness/composer.py`:

```python
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
            },
            trace=trace if self.include_trace else None,
        )
```

- [ ] **Step 3: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_composer.py -q
```

Expected: pass.

---

## Task 9: Add Capability and Fallback Procedures

**Files:**

- Create: `backend/src/aptguide2/harness/modules/__init__.py`
- Create: `backend/src/aptguide2/harness/modules/capability.py`
- Create: `backend/src/aptguide2/harness/modules/fallback.py`
- Test: `backend/tests/unit/harness/test_builtin_procedures.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/harness/test_builtin_procedures.py`:

```python
from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.modules.capability import CapabilityProcedure
from aptguide2.harness.modules.fallback import FallbackProcedure


def test_capability_procedure_returns_fixed_profile():
    frame = ConversationFrame(request_id="r-1", message="你能做什么")
    decision = RouteDecision(task="capability", procedure="capability.profile", confidence=1.0)
    result = CapabilityProcedure().run(frame, decision)
    assert result.task == "capability"
    assert "找房" in result.reply
    assert result.phase == "idle"


def test_fallback_procedure_uses_safety_reason():
    frame = ConversationFrame(request_id="r-1", message="保证不吵")
    decision = RouteDecision(
        task="fallback",
        procedure="fallback.safety",
        confidence=0.95,
        safety_flags=["guarantee"],
    )
    result = FallbackProcedure().run(frame, decision)
    assert result.task == "fallback"
    assert result.fallback_reason == "safety_boundary"
    assert "无法保证" in result.reply
```

- [ ] **Step 2: Implement procedures**

Create `backend/src/aptguide2/harness/modules/__init__.py`:

```python
"""Harness procedure modules."""
```

Create `backend/src/aptguide2/harness/modules/capability.py`:

```python
from __future__ import annotations

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision


class CapabilityProcedure:
    """Fixed capability response. Does not call an LLM."""

    def run(self, frame: ConversationFrame, decision: RouteDecision) -> ProcedureResult:
        return ProcedureResult(
            task="capability",
            phase="idle",
            reply=(
                "我是 AptGuide 2.0 租房助手，可以帮你找房、解释租房规则、"
                "整理看房预约信息，并在需要时引导人工接管。"
            ),
            metadata={"procedure": decision.procedure},
        )
```

Create `backend/src/aptguide2/harness/modules/fallback.py`:

```python
from __future__ import annotations

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision


class FallbackProcedure:
    """Safe fallback procedure for unsupported or blocked requests."""

    def run(self, frame: ConversationFrame, decision: RouteDecision) -> ProcedureResult:
        if "guarantee" in decision.safety_flags:
            return ProcedureResult(
                task="fallback",
                phase="boundary_declined",
                reply="我无法保证邻居、噪音或未来变化，但可以帮你优先筛选安静、低噪音、适合学习的房源。",
                fallback_reason="safety_boundary",
            )
        if "privacy" in decision.safety_flags:
            return ProcedureResult(
                task="fallback",
                phase="boundary_declined",
                reply="我不能查询或透露其他租户的个人信息。可以帮你处理自己的找房、预约或租约问题。",
                fallback_reason="privacy_boundary",
            )
        return ProcedureResult(
            task="fallback",
            phase="boundary_declined",
            reply="抱歉，这个问题超出了我的服务范围。我可以帮你找房或回答租房相关问题。",
            fallback_reason="unsupported_request",
        )
```

- [ ] **Step 3: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_builtin_procedures.py -q
```

Expected: pass.

---

## Task 10: Add RAG Baseline Module Adapter

**Files:**

- Create: `backend/src/aptguide2/harness/modules/rag/__init__.py`
- Create: `backend/src/aptguide2/harness/modules/rag/baseline.py`
- Test: `backend/tests/unit/harness/modules/rag/test_baseline.py`

- [ ] **Step 1: Write failing RAG baseline tests**

Create directory `backend/tests/unit/harness/modules/rag/`.

Create `backend/tests/unit/harness/modules/rag/test_baseline.py`:

```python
from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.modules.rag.baseline import RagBaselineProcedure


class FakePipelineResult:
    def __init__(self, task, message="", rooms=None, kb_sources=None, is_confident=False):
        self.task = task
        self.message = message
        self.rooms = rooms or []
        self.kb_sources = kb_sources or []
        self.is_confident = is_confident


class FakeRoom:
    room_id = 1
    apartment_name = "测试公寓"
    room_number = "101"
    rent = 1500
    district_name = "番禺区"
    tags = ["安静"]
    facilities = ["空调"]
    recommendation_reason = "符合安静偏好"


class FakeSource:
    title = "押金规则"
    content = "押金按合同约定退还。"
    module = "lease"
    score = 0.8


def test_rag_baseline_maps_room_result_to_procedure_result():
    procedure = RagBaselineProcedure(
        run_pipeline_fn=lambda **kwargs: FakePipelineResult(task="room_search", rooms=[FakeRoom()]),
        vector_adapter=object(),
        embed_fn=lambda text: [0.0],
    )
    frame = ConversationFrame(request_id="r-1", message="番禺安静房子")
    decision = RouteDecision(task="room_search", procedure="rag.room_search", confidence=0.8)
    result = procedure.run(frame, decision)
    assert result.task == "room_search"
    assert result.cards[0]["room_id"] == 1
    assert result.phase == "showing_room_results"


def test_rag_baseline_maps_kb_result_to_sources():
    procedure = RagBaselineProcedure(
        run_pipeline_fn=lambda **kwargs: FakePipelineResult(
            task="kb_qa",
            message="押金按合同约定退还。",
            kb_sources=[FakeSource()],
            is_confident=True,
        ),
        vector_adapter=object(),
        embed_fn=lambda text: [0.0],
    )
    frame = ConversationFrame(request_id="r-1", message="押金怎么退")
    decision = RouteDecision(task="kb_qa", procedure="rag.kb_qa", confidence=0.8)
    result = procedure.run(frame, decision)
    assert result.task == "kb_qa"
    assert result.sources[0]["title"] == "押金规则"
    assert result.metadata["is_confident"] is True
```

- [ ] **Step 2: Implement RAG baseline adapter**

Create `backend/src/aptguide2/harness/modules/rag/__init__.py`:

```python
"""RAG module mounted inside the AptGuide harness."""
```

Create `backend/src/aptguide2/harness/modules/rag/baseline.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.rag.pipeline import run_pipeline


class RagBaselineProcedure:
    """Adapter that mounts the current MVP RAG pipeline into the harness."""

    def __init__(
        self,
        vector_adapter: Any,
        embed_fn: Callable[[str], list[float]],
        run_pipeline_fn: Callable[..., Any] = run_pipeline,
    ) -> None:
        self.vector_adapter = vector_adapter
        self.embed_fn = embed_fn
        self.run_pipeline_fn = run_pipeline_fn

    def run(self, frame: ConversationFrame, decision: RouteDecision) -> ProcedureResult:
        previous_state = dict(frame.task_slots)
        result = self.run_pipeline_fn(
            message=frame.message,
            vector_adapter=self.vector_adapter,
            embed_fn=self.embed_fn,
            previous_state=previous_state,
        )
        if result.task == "room_search":
            return self._room_result(result)
        if result.task == "kb_qa":
            return self._kb_result(result)
        return ProcedureResult(
            task="fallback",
            phase="boundary_declined",
            reply=result.message,
            fallback_reason=getattr(result, "fallback_reason", "rag_fallback"),
        )

    def _room_result(self, result: Any) -> ProcedureResult:
        cards = []
        for room in result.rooms:
            cards.append(
                {
                    "type": "room",
                    "room_id": room.room_id,
                    "apartment_name": room.apartment_name,
                    "room_number": room.room_number,
                    "rent": room.rent,
                    "district": getattr(room, "district_name", ""),
                    "tags": room.tags,
                    "facilities": room.facilities,
                    "recommendation_reason": room.recommendation_reason,
                }
            )
        if cards:
            reply = "为您找到以下房源推荐。"
            phase = "showing_room_results"
        else:
            reply = result.message or "抱歉，没有找到符合条件的房源。"
            phase = "search_failed"
        return ProcedureResult(
            task="room_search",
            phase=phase,
            reply=reply,
            cards=cards,
            metadata={"source": "rag_mvp_baseline", "room_count": len(cards)},
        )

    def _kb_result(self, result: Any) -> ProcedureResult:
        sources = []
        for source in result.kb_sources[:3]:
            sources.append(
                {
                    "title": source.title,
                    "content": source.content,
                    "module": source.module,
                    "score": round(source.score, 3),
                }
            )
        return ProcedureResult(
            task="kb_qa",
            phase="answering_knowledge",
            reply=result.message or "我找到了相关知识来源，但需要进一步生成答案。",
            sources=sources,
            metadata={
                "source": "rag_mvp_baseline",
                "is_confident": result.is_confident,
                "source_count": len(sources),
            },
            fallback_reason="" if result.is_confident else "kb_low_confidence",
        )
```

- [ ] **Step 3: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/modules/rag/test_baseline.py -q
```

Expected: pass.

---

## Task 11: Add Orchestrator

**Files:**

- Create: `backend/src/aptguide2/harness/orchestrator.py`
- Test: `backend/tests/unit/harness/test_orchestrator.py`

- [ ] **Step 1: Write failing orchestrator tests**

Create `backend/tests/unit/harness/test_orchestrator.py`:

```python
from aptguide2.harness.context import InMemoryContextStore
from aptguide2.harness.contracts import AptGuideRequest, ProcedureResult
from aptguide2.harness.modules.capability import CapabilityProcedure
from aptguide2.harness.modules.fallback import FallbackProcedure
from aptguide2.harness.orchestrator import AptGuideHarness
from aptguide2.harness.procedures import ProcedureRuntime
from aptguide2.harness.routing import HybridRouter


def build_harness():
    runtime = ProcedureRuntime()
    runtime.register("capability.profile", CapabilityProcedure())
    runtime.register("fallback.safety", FallbackProcedure())
    runtime.register("fallback.unknown", FallbackProcedure())
    return AptGuideHarness(
        context_store=InMemoryContextStore(),
        router=HybridRouter(),
        procedure_runtime=runtime,
        include_trace=True,
    )


def test_harness_runs_capability_request():
    harness = build_harness()
    response = harness.run(AptGuideRequest(request_id="r-1", session_id="s-1", message="你能做什么"))
    assert response.reply
    assert response.metadata["procedure"] == "capability.profile"
    assert response.trace is not None


def test_harness_runs_safety_fallback():
    harness = build_harness()
    response = harness.run(AptGuideRequest(request_id="r-1", session_id="s-1", message="保证不吵吗"))
    assert response.metadata["procedure"] == "fallback.safety"
    assert response.phase == "boundary_declined"
```

- [ ] **Step 2: Implement orchestrator**

Create `backend/src/aptguide2/harness/orchestrator.py`:

```python
from __future__ import annotations

from aptguide2.harness.composer import ResponseComposer
from aptguide2.harness.context import InMemoryContextStore
from aptguide2.harness.contracts import AptGuideRequest, AptGuideResponse
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
    ) -> None:
        self.context_store = context_store
        self.router = router
        self.procedure_runtime = procedure_runtime
        self.composer = ResponseComposer(include_trace=include_trace)

    def run(self, request: AptGuideRequest) -> AptGuideResponse:
        recorder = TraceRecorder(request_id=request.request_id, session_id=request.session_id)

        token = recorder.start_stage(
            "context.load",
            "in_memory_v1",
            {"session_id": request.session_id, "message_len": len(request.message)},
        )
        frame = self.context_store.load(request)
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
        result = self.procedure_runtime.run(frame, decision)
        recorder.finish_stage(
            token,
            {
                "phase": result.phase,
                "card_count": len(result.cards),
                "source_count": len(result.sources),
                "fallback_reason": result.fallback_reason,
            },
        )

        frame.phase = result.phase
        frame.active_task = result.task
        if result.cards:
            frame.last_recommendations = result.cards
        self.context_store.save(frame)

        trace = recorder.to_trace()
        return self.composer.compose(frame, decision, result, trace)
```

- [ ] **Step 3: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_orchestrator.py -q
```

Expected: pass.

---

## Task 12: Add API Version Switch

**Files:**

- Modify: `backend/src/aptguide2/core/config.py`
- Modify: `backend/src/aptguide2/api/deps.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Test: `backend/tests/e2e/test_api.py`

- [ ] **Step 1: Add settings test or direct e2e coverage**

Add this test class to `backend/tests/e2e/test_api.py`:

```python
class TestChatPipelineVersion:
    def test_chat_default_pipeline_still_works(self):
        with patch("aptguide2.api.app.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.app.get_embed_fn", return_value=_fake_embed):
            from aptguide2.api.app import app
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "你能做什么"})
            assert resp.status_code == 200
            data = resp.json()
            assert "task" in data
            assert "message" in data
```

- [ ] **Step 2: Add config fields**

Modify `backend/src/aptguide2/core/config.py`:

```python
    # Harness
    pipeline_version: str = "v1"
    harness_include_trace: bool = False
```

With `env_prefix="APTGUIDE_"`, these map to:

```text
APTGUIDE_PIPELINE_VERSION
APTGUIDE_HARNESS_INCLUDE_TRACE
```

- [ ] **Step 3: Add `get_aptguide_harness()` dependency**

Modify `backend/src/aptguide2/api/deps.py`:

```python
from aptguide2.harness.context import InMemoryContextStore
from aptguide2.harness.modules.capability import CapabilityProcedure
from aptguide2.harness.modules.fallback import FallbackProcedure
from aptguide2.harness.modules.rag.baseline import RagBaselineProcedure
from aptguide2.harness.orchestrator import AptGuideHarness
from aptguide2.harness.procedures import ProcedureRuntime
from aptguide2.harness.routing import HybridRouter


@lru_cache
def get_context_store() -> InMemoryContextStore:
    return InMemoryContextStore()


def get_aptguide_harness() -> AptGuideHarness:
    runtime = ProcedureRuntime()
    runtime.register("capability.profile", CapabilityProcedure())
    runtime.register("fallback.safety", FallbackProcedure())
    runtime.register("fallback.unknown", FallbackProcedure())
    rag = RagBaselineProcedure(
        vector_adapter=get_vector_adapter(),
        embed_fn=get_embed_fn(),
    )
    runtime.register("rag.room_search", rag)
    runtime.register("rag.kb_qa", rag)
    settings = get_settings()
    return AptGuideHarness(
        context_store=get_context_store(),
        router=HybridRouter(),
        procedure_runtime=runtime,
        include_trace=settings.harness_include_trace,
    )
```

- [ ] **Step 4: Add harness response mapping**

Modify `backend/src/aptguide2/api/app.py`.

Imports:

```python
from uuid import uuid4

from aptguide2.api.deps import get_aptguide_harness
from aptguide2.harness.contracts import AptGuideRequest, AptGuideResponse
```

In `chat()` before old pipeline:

```python
    settings = get_settings()
    if settings.pipeline_version == "harness_v1":
        harness = get_aptguide_harness()
        result = harness.run(
            AptGuideRequest(
                request_id=f"r-{uuid4().hex}",
                session_id=req.session_id,
                message=req.message,
            )
        )
        return _build_response_from_harness(result)
```

Add:

```python
def _build_response_from_harness(result: AptGuideResponse) -> ChatResponse:
    rooms = []
    for card in result.cards:
        if card.get("type") != "room":
            continue
        rooms.append(
            RoomResponse(
                room_id=card.get("room_id", 0),
                apartment_name=card.get("apartment_name", ""),
                room_number=card.get("room_number", ""),
                rent=card.get("rent", 0),
                district_name=card.get("district", ""),
                tags=card.get("tags", []),
                facilities=card.get("facilities", []),
                recommendation_reason=card.get("recommendation_reason", ""),
            )
        )
    sources = [
        KBSourceResponse(
            title=s.get("title", ""),
            content=s.get("content", ""),
            module=s.get("module", ""),
            score=s.get("score", 0.0),
        )
        for s in result.sources
    ]
    return ChatResponse(
        task=result.metadata.get("task", "fallback"),
        message=result.reply,
        rooms=rooms,
        kb_sources=sources,
        is_confident=bool(result.metadata.get("is_confident", False)),
    )
```

- [ ] **Step 5: Run API tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/e2e/test_api.py -q
```

Expected: pass with default `APTGUIDE_PIPELINE_VERSION=v1`.

---

## Task 13: Add Harness Branch E2E Test

**Files:**

- Modify: `backend/tests/e2e/test_api.py`

- [ ] **Step 1: Add harness branch test**

Add this test to the `TestChatPipelineVersion` class created in Task 12:

```python
    def test_chat_harness_pipeline_version(self):
        from aptguide2.api.app import app

        settings = _fake_settings()
        settings.pipeline_version = "harness_v1"
        settings.harness_include_trace = False

        with patch("aptguide2.api.app.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "你能做什么", "session_id": "s-test"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "capability"
            assert "租房助手" in data["message"]
```

- [ ] **Step 2: Run e2e tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/e2e/test_api.py -q
```

Expected: pass.

---

## Task 14: Add Replay Writer

**Files:**

- Create: `backend/src/aptguide2/harness/replay.py`
- Test: `backend/tests/unit/harness/test_replay.py`

- [ ] **Step 1: Write replay tests**

Create `backend/tests/unit/harness/test_replay.py`:

```python
import json

import pytest

from aptguide2.harness.contracts import AptGuideRequest, AptGuideResponse
from aptguide2.harness.errors import ReplayPIIError
from aptguide2.harness.replay import ReplayWriter


def test_replay_writer_writes_jsonl(tmp_path):
    path = tmp_path / "replay.jsonl"
    writer = ReplayWriter(path)
    req = AptGuideRequest(request_id="r-1", session_id="s-1", message="找房")
    resp = AptGuideResponse(
        request_id="r-1",
        trace_id="t-1",
        reply="ok",
        phase="idle",
        domain_category="in_domain",
    )
    writer.write(req, resp)
    rows = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1
    payload = json.loads(rows[0])
    assert payload["request"]["request_id"] == "r-1"


def test_replay_writer_rejects_pii_key(tmp_path):
    writer = ReplayWriter(tmp_path / "replay.jsonl")
    req = AptGuideRequest(
        request_id="r-1",
        message="找房",
        client_context={"phone": "123"},
    )
    resp = AptGuideResponse(
        request_id="r-1",
        trace_id="t-1",
        reply="ok",
        phase="idle",
        domain_category="in_domain",
    )
    with pytest.raises(ReplayPIIError):
        writer.write(req, resp)
```

- [ ] **Step 2: Implement replay writer**

Create `backend/src/aptguide2/harness/replay.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aptguide2.harness.contracts import AptGuideRequest, AptGuideResponse
from aptguide2.harness.errors import ReplayPIIError


PII_KEYS = {"phone", "id_card", "bank_card", "real_name", "email", "mobile"}


def _assert_no_pii(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in PII_KEYS:
                raise ReplayPIIError(f"PII key is not allowed in replay: {key}")
            _assert_no_pii(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_pii(item)


class ReplayWriter:
    """Writes sanitized replay cases as JSONL."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write(self, request: AptGuideRequest, response: AptGuideResponse) -> None:
        payload = {
            "request": request.model_dump(mode="json"),
            "response": response.model_dump(mode="json"),
        }
        _assert_no_pii(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
```

- [ ] **Step 3: Run replay tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_replay.py -q
```

Expected: pass.

---

## Task 15: Documentation Update After Implementation

**Files:**

- Modify: `docs/system/enterprise-harness-architecture.md`
- Modify: `docs/plans/README.md`
- Modify: `docs/system/README.md`

- [ ] **Step 1: Update architecture doc with implemented package**

Add a short "Current implementation status" section:

```markdown
## Current Implementation Status

- `aptguide2.harness.contracts`: implemented
- `aptguide2.harness.orchestrator`: implemented
- `aptguide2.harness.modules.rag.baseline`: implemented
- `/chat` can switch between `v1` and `harness_v1` with `APTGUIDE_PIPELINE_VERSION`
```

- [ ] **Step 2: Run docs link smoke check**

```bash
cd "AptGuide 2.0"
rg -n "enterprise-aptguide-harness-agent-execution-plan|enterprise-harness-architecture" docs README.md
```

Expected: links appear in docs indexes or README.

---

## Final Verification

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness -q
```

Expected: all harness unit tests pass.

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag tests/e2e -q
```

Expected: existing MVP tests still pass.

Manual smoke test, default MVP:

```bash
cd "AptGuide 2.0/backend"
uv run uvicorn aptguide2.api.app:app --reload
```

Then:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"番禺区1500以内安静一点的房子","session_id":"s-manual"}'
```

Expected: current MVP response shape remains valid.

Manual smoke test, harness:

```bash
cd "AptGuide 2.0/backend"
APTGUIDE_PIPELINE_VERSION=harness_v1 uv run uvicorn aptguide2.api.app:app --reload
```

Then:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你能做什么","session_id":"s-harness"}'
```

Expected:

- response status is 200;
- `task` is `capability`;
- `message` mentions AptGuide or 租房助手.

## Definition of Done

This execution plan is complete when:

- `aptguide2.harness` package exists.
- Harness unit tests pass.
- Existing RAG unit tests pass.
- Existing API e2e tests pass.
- `/chat` defaults to MVP `v1`.
- `/chat` can run `harness_v1` with `APTGUIDE_PIPELINE_VERSION=harness_v1`.
- Current RAG MVP is mounted as a harness module, not duplicated or deleted.
- Trace is available internally through `AptGuideTrace`.
- Replay writer can produce PII-guarded JSONL cases.
