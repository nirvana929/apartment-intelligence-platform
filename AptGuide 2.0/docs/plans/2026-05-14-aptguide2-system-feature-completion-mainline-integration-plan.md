# AptGuide 2.0 System Feature Completion Mainline Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete AptGuide 2.0 as a coherent system by making harness the only product runtime, disconnecting the legacy RAG MVP from public interfaces, and finishing appointment, lease, memory, handoff, response, and system smoke behavior.

**Architecture:** `/chat` should enter `AptGuideHarness` by default. Harness procedures own product behavior, ToolRuntime owns governed backend access, and RAG v2 is mounted as an internal harness procedure for room and KB workflows. The legacy `aptguide2.rag.pipeline.run_pipeline()` remains in the repository but is not imported by API or harness wiring.

**Tech Stack:** Python 3.13, FastAPI, Pydantic, pytest, ruff, OpenAI-compatible embeddings/LLM, Milvus, Lease Java backend, AptGuide harness/tool-runtime packages.

---

## Phase Decision

Old RAG is legacy retained code. It must not be connected to:

- `backend/src/aptguide2/api/app.py`
- `backend/src/aptguide2/api/deps.py`
- `AptGuideHarness`
- any `/chat` e2e acceptance path

RAG v2 remains important, but retrieval-quality tuning is not the active objective for this phase. This phase only needs RAG v2 to be correctly mounted behind the system harness.

## File Map

### Create

- `backend/src/aptguide2/harness/modules/rag/v2.py` - harness procedure adapter for `run_pipeline_v2()`.
- `backend/tests/unit/harness/modules/test_rag_v2.py` - unit tests for the new harness RAG v2 procedure.
- `backend/tests/e2e/test_system_mainline.py` - e2e tests that exercise `/chat` through the harness mainline.
- `backend/tests/unit/api/test_mainline_wiring.py` - tests proving API/deps no longer wire legacy RAG.

### Modify

- `backend/src/aptguide2/core/config.py` - default runtime becomes harness mainline.
- `backend/src/aptguide2/api/app.py` - remove direct legacy `v1` and standalone `rag_v2` `/chat` branches.
- `backend/src/aptguide2/api/schemas.py` - add a first-class `cards` field to `ChatResponse` for non-room cards.
- `backend/src/aptguide2/api/deps.py` - register RAG v2 harness procedure instead of `RagBaselineProcedure`.
- `backend/src/aptguide2/rag/schemas.py` - own the shared `PipelineResult` contract used by both legacy and v2 modules.
- `backend/src/aptguide2/rag/pipeline.py` - import `PipelineResult` from schemas instead of owning it.
- `backend/src/aptguide2/rag/pipeline_v2.py` - import `PipelineResult` from schemas, not from legacy pipeline.
- `backend/src/aptguide2/harness/modules/appointment.py` - complete cancel/list behavior and metadata.
- `backend/src/aptguide2/harness/tools/contracts.py` - add or verify appointment cancel and lease list schemas.
- `backend/src/aptguide2/harness/tools/builtins.py` - register completed tool definitions.
- `backend/src/aptguide2/harness/tools/lease_tools.py` - add cancel appointment executor and strengthen list executors.
- `backend/src/aptguide2/tools/lease_adapter.py` - add `cancel_appointment()` and `list_leases()` adapter methods.
- `backend/src/aptguide2/harness/routing.py` - route lease list and appointment cancel/list reliably.
- `backend/src/aptguide2/harness/composer.py` - consistently preserves cards/actions/pending_action/sources and standard metadata.
- `backend/tests/unit/harness/test_composer.py` - verify response composer metadata and pass-through behavior.
- `backend/tests/e2e/test_api.py` - migrate old `/chat` branch expectations to mainline expectations.
- `backend/tests/e2e/test_pipeline.py` - reduce to legacy isolated tests or remove from system acceptance.
- `docs/27-current-implementation-guide.md` - update runtime description after implementation.
- `docs/README.md` - update current status after implementation.
- `progress/current-plan.md` - set this plan active.
- `progress/next-steps.md` - replace immediate RAG quality item with system feature completion.
- `reports/evaluation-report.md` - update `next_step`.

### Legacy Files Left In Place

- `backend/src/aptguide2/rag/pipeline.py`
- `backend/src/aptguide2/harness/modules/rag/baseline.py`
- `backend/tests/unit/rag/test_kb_retrieval.py`
- `backend/tests/unit/rag/test_room_retrieval.py`

These may remain for historical/unit comparison, but no user-facing route should depend on them.

---

## Task 1: Prove The Current Wiring Still Touches Legacy RAG

**Files:**
- Create: `backend/tests/unit/api/test_mainline_wiring.py`
- Modify: none

- [ ] **Step 1: Add a wiring test that fails on current code**

Create `backend/tests/unit/api/test_mainline_wiring.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_api_app_does_not_import_legacy_pipeline() -> None:
    source = (ROOT / "src/aptguide2/api/app.py").read_text(encoding="utf-8")

    assert "from aptguide2.rag.pipeline import" not in source
    assert "run_pipeline(" not in source


def test_api_deps_does_not_register_rag_baseline_procedure() -> None:
    source = (ROOT / "src/aptguide2/api/deps.py").read_text(encoding="utf-8")

    assert "RagBaselineProcedure" not in source
    assert "harness.modules.rag.baseline" not in source


def test_default_pipeline_version_is_harness_mainline() -> None:
    from aptguide2.core.config import Settings

    assert Settings().pipeline_version == "harness_v1"
```

- [ ] **Step 2: Run the test and verify current failure**

Run:

```bash
cd backend
uv run pytest tests/unit/api/test_mainline_wiring.py -q
```

Expected: fails because `api.app` imports legacy `run_pipeline`, `api.deps` registers `RagBaselineProcedure`, and default `pipeline_version` is `v1`.

- [ ] **Step 3: Keep this test as the phase guard**

Do not weaken string checks in this task. Later tasks must make this test pass by changing wiring.

---

## Task 2: Extract Shared RAG Result Contract Out Of Legacy Pipeline

**Files:**
- Modify: `backend/src/aptguide2/rag/schemas.py` (create only if missing in another branch; this repository already has it)
- Modify: `backend/src/aptguide2/rag/pipeline.py`
- Modify: `backend/src/aptguide2/rag/pipeline_v2.py`
- Modify: `backend/tests/unit/api/test_mainline_wiring.py`

- [ ] **Step 1: Extend the wiring guard to catch transitive legacy result imports**

Add this test to `backend/tests/unit/api/test_mainline_wiring.py`:

```python
def test_rag_v2_does_not_import_legacy_pipeline_contracts() -> None:
    source = (ROOT / "src/aptguide2/rag/pipeline_v2.py").read_text(encoding="utf-8")

    assert "from aptguide2.rag.pipeline import PipelineResult" not in source
```

- [ ] **Step 2: Run the guard and verify current failure**

Run:

```bash
cd backend
uv run pytest tests/unit/api/test_mainline_wiring.py::test_rag_v2_does_not_import_legacy_pipeline_contracts -q
```

Expected: fails because `pipeline_v2.py` currently imports `PipelineResult` from `aptguide2.rag.pipeline`.

- [ ] **Step 3: Move `PipelineResult` to schemas**

In `backend/src/aptguide2/rag/schemas.py`, add the existing `PipelineResult` model with the same fields it currently has in `pipeline.py`. The model should stay compatible with current call sites:

```python
class PipelineResult(BaseModel):
    task: str
    message: str = ""
    rooms: list[RankedRoom] = Field(default_factory=list)
    kb_sources: list[KBSource] = Field(default_factory=list)
    is_confident: bool = False
    fallback_reason: str = ""
    query_understanding: QueryUnderstandingResult | None = None
```

Do not add or remove fields during the move. The purpose of this task is dependency separation only.

- [ ] **Step 4: Update legacy and v2 imports**

Modify `backend/src/aptguide2/rag/pipeline.py`:

```python
from aptguide2.rag.schemas import PipelineResult, QueryUnderstandingResult
```

Remove the local `PipelineResult` class from `pipeline.py`. Remove `BaseModel`, `Field`, `Literal`, `RankedRoom`, and `KBSource` imports from `pipeline.py` if they are no longer used.

Modify `backend/src/aptguide2/rag/pipeline_v2.py`:

```python
from aptguide2.rag.schemas import PipelineResult
```

- [ ] **Step 5: Run focused RAG tests**

Run:

```bash
cd backend
uv run pytest tests/unit/rag/test_schemas.py tests/unit/rag/test_pipeline_v2_trace.py tests/e2e/test_pipeline.py -q
```

Expected: all focused tests pass. Legacy pipeline may still exist, but it no longer owns the shared result contract.

---

## Task 3: Mount RAG v2 As A Harness Procedure

**Files:**
- Create: `backend/src/aptguide2/harness/modules/rag/v2.py`
- Create: `backend/tests/unit/harness/modules/test_rag_v2.py`
- Modify: `backend/src/aptguide2/api/deps.py`

- [ ] **Step 1: Write unit tests for the RAG v2 harness adapter**

Create `backend/tests/unit/harness/modules/test_rag_v2.py`:

```python
from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.modules.rag.v2 import RagV2Procedure
from aptguide2.rag.schemas import KBSource, RankedRoom
from aptguide2.rag.schemas import PipelineResult


def _frame(message: str = "番禺1500以内找房") -> ConversationFrame:
    return ConversationFrame(
        request_id="req-1",
        session_id="s-1",
        user_id="u-1",
        message=message,
    )


def _decision(task: str) -> RouteDecision:
    return RouteDecision(
        task=task,
        procedure=f"rag.{task}",
        confidence=0.9,
        domain_category="in_domain_task",
        reason="test",
    )


def test_rag_v2_room_result_maps_cards() -> None:
    def fake_pipeline(**kwargs):
        return PipelineResult(
            task="room_search",
            rooms=[
                RankedRoom(
                    room_id=200013,
                    apartment_id=1,
                    apartment_name="南亭公寓",
                    room_number="A101",
                    district_name="番禺区",
                    rent=1450,
                    tags=["安静"],
                    facilities=["空调"],
                    recommendation_reason="预算和区域匹配",
                    final_score=0.91,
                )
            ],
        )

    proc = RagV2Procedure(vector_adapter=object(), embed_fn=lambda text: [], run_pipeline_v2_fn=fake_pipeline)
    result = proc.run(_frame(), _decision("room_search"), tool_runtime=object())

    assert result.task == "room_search"
    assert result.phase == "showing_room_results"
    assert result.cards[0]["room_id"] == 200013
    assert result.metadata["source"] == "rag_v2"


def test_rag_v2_kb_result_maps_sources() -> None:
    def fake_pipeline(**kwargs):
        return PipelineResult(
            task="kb_qa",
            message="押金按合同规则处理。",
            is_confident=True,
            kb_sources=[
                KBSource(
                    chunk_id="c1",
                    doc_id="KB-LEASE-001",
                    title="押金规则",
                    module="lease",
                    content="押金退还以合同和账单为准。",
                    score=0.8,
                    risk_level="high",
                )
            ],
        )

    proc = RagV2Procedure(vector_adapter=object(), embed_fn=lambda text: [], run_pipeline_v2_fn=fake_pipeline)
    result = proc.run(_frame("押金怎么退"), _decision("kb_qa"), tool_runtime=object())

    assert result.task == "kb_qa"
    assert result.phase == "answering_knowledge"
    assert result.sources[0]["title"] == "押金规则"
    assert result.metadata["is_confident"] is True


def test_rag_v2_passes_tool_runtime_as_lease_validator() -> None:
    captured = {}

    def fake_pipeline(**kwargs):
        captured.update(kwargs)
        return PipelineResult(task="fallback", message="fallback")

    tool_runtime = object()
    proc = RagV2Procedure(vector_adapter=object(), embed_fn=lambda text: [], run_pipeline_v2_fn=fake_pipeline)
    proc.run(_frame(), _decision("room_search"), tool_runtime=tool_runtime)

    assert captured["lease_validator"] is not None
```

- [ ] **Step 2: Run the tests and verify import failure**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/modules/test_rag_v2.py -q
```

Expected: fails because `aptguide2.harness.modules.rag.v2` does not exist.

- [ ] **Step 3: Implement `RagV2Procedure`**

Create `backend/src/aptguide2/harness/modules/rag/v2.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.rag.pipeline_v2 import run_pipeline_v2
from aptguide2.rag.tool_validation import ToolRuntimeRoomValidator


class RagV2Procedure:
    """Harness procedure that mounts RAG v2 as the system retrieval module."""

    def __init__(
        self,
        vector_adapter: Any,
        embed_fn: Callable[[str], list[float]],
        run_pipeline_v2_fn: Callable[..., Any] = run_pipeline_v2,
    ) -> None:
        self.vector_adapter = vector_adapter
        self.embed_fn = embed_fn
        self.run_pipeline_v2_fn = run_pipeline_v2_fn

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        lease_validator = ToolRuntimeRoomValidator(tool_runtime) if tool_runtime is not None else None
        result = self.run_pipeline_v2_fn(
            message=frame.message,
            vector_adapter=self.vector_adapter,
            embed_fn=self.embed_fn,
            lease_validator=lease_validator,
        )
        if result.task == "room_search":
            return self._room_result(result)
        if result.task == "kb_qa":
            return self._kb_result(result)
        return ProcedureResult(
            task="fallback",
            phase="boundary_declined",
            reply=result.message,
            fallback_reason=getattr(result, "fallback_reason", "rag_v2_fallback"),
            metadata={"source": "rag_v2"},
        )

    def _room_result(self, result: Any) -> ProcedureResult:
        cards = [
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
            for room in result.rooms
        ]
        return ProcedureResult(
            task="room_search",
            phase="showing_room_results" if cards else "search_failed",
            reply="为您找到以下房源推荐。" if cards else (result.message or "抱歉，没有找到符合条件的房源。"),
            cards=cards,
            metadata={"source": "rag_v2", "room_count": len(cards)},
            fallback_reason="" if cards else getattr(result, "fallback_reason", "room_search_empty"),
        )

    def _kb_result(self, result: Any) -> ProcedureResult:
        sources = [
            {
                "title": source.title,
                "content": source.content,
                "module": source.module,
                "score": round(source.score, 3),
            }
            for source in result.kb_sources[:3]
        ]
        return ProcedureResult(
            task="kb_qa",
            phase="answering_knowledge" if result.is_confident else "knowledge_low_confidence",
            reply=result.message or "我找到了相关知识来源，但需要进一步生成答案。",
            sources=sources,
            metadata={"source": "rag_v2", "is_confident": result.is_confident, "source_count": len(sources)},
            fallback_reason="" if result.is_confident else "kb_low_confidence",
        )
```

- [ ] **Step 4: Register RAG v2 in deps**

Modify `backend/src/aptguide2/api/deps.py`:

```python
from aptguide2.harness.modules.rag.v2 import RagV2Procedure
```

Replace the RAG registration block with:

```python
    rag = RagV2Procedure(
        vector_adapter=get_vector_adapter(),
        embed_fn=get_embed_fn(),
    )
    runtime.register("rag.room_search", rag)
    runtime.register("rag.kb_qa", rag)
```

Remove the `RagBaselineProcedure` import.

- [ ] **Step 5: Run focused tests**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/modules/test_rag_v2.py tests/unit/api/test_mainline_wiring.py::test_api_deps_does_not_register_rag_baseline_procedure -q
```

Expected: RAG v2 procedure tests pass. The API app wiring test may still fail until Task 4.

---

## Task 4: Make Harness The Only `/chat` Product Runtime

**Files:**
- Modify: `backend/src/aptguide2/core/config.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Modify: `backend/tests/e2e/test_api.py`

- [ ] **Step 1: Change the default runtime**

Modify `backend/src/aptguide2/core/config.py`:

```python
    # Harness
    pipeline_version: str = "harness_v1"
    harness_include_trace: bool = False
```

- [ ] **Step 2: Simplify `/chat` to the harness runtime**

Modify `backend/src/aptguide2/api/app.py` so `chat()` always uses harness:

```python
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Main chat endpoint - runs the AptGuide system harness."""
    harness = get_aptguide_harness()
    result = harness.run(
        AptGuideRequest(
            request_id=f"r-{uuid4().hex}",
            session_id=req.session_id,
            user_id=req.user_id,
            message=req.message,
            action=req.action,
            client_context=req.client_context,
        )
    )
    return _build_response_from_harness(result)
```

Remove these imports from `api/app.py`:

```python
from aptguide2.rag.pipeline import PipelineResult, run_pipeline
from aptguide2.rag.pipeline_v2 import run_pipeline_v2
from aptguide2.rag.tool_validation import ToolRuntimeRoomValidator
```

Before deleting `_build_response()`, `_generate_room_message()`, or `_generate_kb_answer()`, verify references:

```bash
cd backend
rg "_build_response\\(|_generate_room_message|_generate_kb_answer" src tests
```

Delete these helpers only if the search shows they are referenced only inside `src/aptguide2/api/app.py` by the legacy `/chat` branches being removed. Do not delete anything used by another module or test.

- [ ] **Step 3: Update API tests to assert mainline behavior**

In `backend/tests/e2e/test_api.py`, replace tests that expect default `v1` or standalone `rag_v2` branches with tests that assert:

```python
def test_chat_uses_harness_mainline_by_default(monkeypatch):
    from aptguide2.api import app as app_module
    from aptguide2.core.config import Settings

    settings = Settings()
    assert settings.pipeline_version == "harness_v1"
```

Use existing test doubles in the file for API client tests. The response should include harness fields:

```python
assert "phase" in data
assert "actions" in data
assert "metadata" in data
```

- [ ] **Step 4: Run focused API tests**

Run:

```bash
cd backend
uv run pytest tests/unit/api/test_mainline_wiring.py tests/e2e/test_api.py -q
```

Expected: wiring tests pass, and API e2e tests pass after migrated assertions.

---

## Task 5: Complete Appointment Cancel And Lease List Tooling

**Files:**
- Modify: `backend/src/aptguide2/tools/lease_adapter.py`
- Modify: `backend/src/aptguide2/harness/tools/contracts.py`
- Modify: `backend/src/aptguide2/harness/tools/builtins.py`
- Modify: `backend/src/aptguide2/harness/tools/lease_tools.py`
- Modify: `backend/tests/unit/harness/tools/test_lease_tools.py`
- Modify: `backend/tests/unit/harness/tools/test_builtins.py`

- [ ] **Step 1: Add failing executor tests**

Add tests to `backend/tests/unit/harness/tools/test_lease_tools.py`:

```python
class FakeLeaseAdapterForCompletion:
    def cancel_appointment(self, payload):
        return {"appointment_id": payload["appointment_id"], "status": "cancelled"}

    def list_leases(self, payload):
        return {"leases": [{"lease_id": "l-1", "status": "active"}]}


def test_appointment_cancel_executor_calls_adapter() -> None:
    from aptguide2.harness.tools.lease_tools import AppointmentCancelExecutor

    executor = AppointmentCancelExecutor(FakeLeaseAdapterForCompletion())
    result = executor.execute(
        ToolCallRequest(
            tool="appointment.cancel",
            request_id="r-1",
            user_id="u-1",
            payload={"appointment_id": "a-1", "user_id": "u-1"},
        )
    )

    assert result.ok is True
    assert result.data["status"] == "cancelled"


def test_lease_list_mine_executor_calls_adapter() -> None:
    executor = LeaseListMineExecutor(FakeLeaseAdapterForCompletion())
    result = executor.execute(
        ToolCallRequest(
            tool="lease.list_mine",
            request_id="r-1",
            user_id="u-1",
            payload={"user_id": "u-1", "limit": 10},
        )
    )

    assert result.ok is True
    assert result.data["leases"][0]["lease_id"] == "l-1"
```

- [ ] **Step 2: Run the tests and verify `AppointmentCancelExecutor` failure**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/tools/test_lease_tools.py -q
```

Expected: fails because `AppointmentCancelExecutor` is not implemented.

- [ ] **Step 3: Add lease adapter methods**

Modify `backend/src/aptguide2/tools/lease_adapter.py`:

```python
    async def cancel_appointment(self, payload: dict) -> dict:
        """Cancel a viewing appointment through lease."""
        client = await self._get_client()
        camel_payload = convert_keys_to_camel(payload)
        resp = await client.post("/internal/ai/tools/appointment/cancel", json=camel_payload)
        data = self._handle_response(resp, "appointment.cancel")
        result = data.get("data", {})
        return convert_keys_to_snake(result) if isinstance(result, dict) else {}

    async def list_leases(self, payload: dict) -> dict:
        """List user's leases through lease."""
        client = await self._get_client()
        camel_payload = convert_keys_to_camel(payload)
        resp = await client.post("/internal/ai/tools/lease/list", json=camel_payload)
        data = self._handle_response(resp, "lease.list")
        result = data.get("data", {})
        return convert_keys_to_snake(result) if isinstance(result, dict) else {}
```

- [ ] **Step 4: Add cancel executor**

Modify `backend/src/aptguide2/harness/tools/lease_tools.py`:

```python
class AppointmentCancelExecutor:
    """Calls adapter.cancel_appointment(payload) if available."""

    def __init__(self, adapter: Any) -> None:
        self._adapter = adapter

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        method = getattr(self._adapter, "cancel_appointment", None)
        if method is None:
            return _not_implemented(request.tool)
        try:
            result = _run_awaitable(method(request.payload))
            if result is _NOT_IMPLEMENTED_SENTINEL:
                return _not_implemented(request.tool)
            data = result if isinstance(result, dict) else {"appointment_id": str(result)}
            return ToolCallResult.ok_result(tool=request.tool, data=data, backend=BACKEND)
        except Exception as exc:
            return _error_from_exception(request.tool, exc)
```

- [ ] **Step 5: Register cancel tool and executor**

Modify `backend/src/aptguide2/harness/tools/builtins.py` to include `appointment.cancel` with required fields:

```python
ToolDefinition(
    name="appointment.cancel",
    backend="lease",
    description="Cancel one of the current user's viewing appointments.",
    input_schema={"type": "object", "required": ["appointment_id", "user_id"]},
    requires_auth=True,
    requires_confirmation=True,
)
```

Modify `backend/src/aptguide2/api/deps.py` imports and runtime registration:

```python
from aptguide2.harness.tools.lease_tools import AppointmentCancelExecutor
```

```python
runtime.register_executor("appointment.cancel", AppointmentCancelExecutor(lease_adapter))
```

- [ ] **Step 6: Run focused tool tests**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/tools/test_lease_tools.py tests/unit/harness/tools/test_builtins.py -q
```

Expected: all focused tool tests pass.

---

## Task 6: Complete Appointment Workflow Behavior

**Files:**
- Modify: `backend/src/aptguide2/harness/modules/appointment.py`
- Modify: `backend/src/aptguide2/harness/routing.py`
- Modify: `backend/tests/unit/harness/modules/test_appointment.py`
- Modify: `backend/tests/unit/harness/test_routing.py`

- [ ] **Step 1: Add tests for cancel request ID resolution and two-turn confirmation**

Add to `backend/tests/unit/harness/modules/test_appointment.py`:

```python
def test_cancel_appointment_requires_user_id() -> None:
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id=None, message="取消预约a-1")
    result = proc.run(frame, _decision(), tool_runtime=object())

    assert result.phase == "appointment_auth_required"
    assert result.fallback_reason == "missing_user_id"


def test_cancel_appointment_first_turn_returns_pending_action_without_tool_call() -> None:
    runtime = CapturingToolRuntime(ok=True, data={"appointment_id": "a-1", "status": "cancelled"})
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id="u-1", message="取消预约a-1")
    result = proc.run(frame, _decision(), tool_runtime=runtime)

    assert result.phase == "appointment_cancel_needs_confirmation"
    assert result.pending_action["type"] == "appointment.cancel"
    assert result.pending_action["payload"]["appointment_id"] == "a-1"
    assert runtime.calls == []


def test_cancel_appointment_confirm_calls_tool_runtime_from_pending_action() -> None:
    runtime = CapturingToolRuntime(
        ok=True,
        data={"appointment_id": "a-1", "status": "cancelled"},
    )
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(
        request_id="r-1",
        session_id="s-1",
        user_id="u-1",
        message="确认",
        pending_action={
            "type": "appointment.cancel",
            "confirmation_id": "c-cancel",
            "status": "pending",
            "payload": {"appointment_id": "a-1", "user_id": "u-1"},
        },
    )
    result = proc.run(frame, _decision(), tool_runtime=runtime)

    assert result.phase == "appointment_cancelled"
    assert runtime.last_request.tool == "appointment.cancel"
    assert runtime.last_request.payload["appointment_id"] == "a-1"
    assert runtime.last_request.confirmation_id == "c-cancel"


def test_cancel_appointment_uses_action_payload_before_message_regex() -> None:
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(
        request_id="r-1",
        session_id="s-1",
        user_id="u-1",
        message="取消预约",
        action={"type": "cancel_appointment", "payload": {"appointment_id": "a-from-action"}},
    )
    result = proc.run(frame, _decision(), tool_runtime=CapturingToolRuntime(ok=True, data={}))

    assert result.pending_action["payload"]["appointment_id"] == "a-from-action"


def test_lease_list_request_routes_to_lease_list() -> None:
    router = HybridRouter()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id="u-1", message="查看我的租约")
    decision = router.route(frame)

    assert decision.task == "lease"
    assert decision.procedure == "lease.workflow"
```

Use existing local helper patterns in the test file for `_decision()` and `CapturingToolRuntime`; if names differ, extend the file's helpers rather than creating duplicate machinery.

- [ ] **Step 2: Run focused tests and verify failure**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/modules/test_appointment.py tests/unit/harness/test_routing.py -q
```

Expected: cancel tests fail because cancel is currently unsupported and not two-turn; lease route fails until a lease procedure is added or routed.

- [ ] **Step 3: Implement appointment cancel ID resolution**

Add helpers to `AppointmentWorkflowProcedure`. `appointment_id` source priority must be:

1. `frame.action["payload"]["appointment_id"]`
2. `frame.pending_action["payload"]["appointment_id"]`
3. regex extraction from `frame.message`

```python
    def _extract_appointment_id(self, frame: ConversationFrame, message: str) -> str | None:
        action_payload = (frame.action or {}).get("payload", {})
        if isinstance(action_payload, dict) and action_payload.get("appointment_id"):
            return str(action_payload["appointment_id"])

        pending_payload = (frame.pending_action or {}).get("payload", {})
        if isinstance(pending_payload, dict) and pending_payload.get("appointment_id"):
            return str(pending_payload["appointment_id"])

        patterns = [
            r"预约(?:编号)?\s*([A-Za-z0-9_-]{2,32})",
            r"取消预约\s*([A-Za-z0-9_-]{2,32})",
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        return None
```

Add a pending-action detector:

```python
    def _is_pending_cancel_action(self, frame: ConversationFrame) -> bool:
        return bool(frame.pending_action and frame.pending_action.get("type") == "appointment.cancel")
```

- [ ] **Step 4: Route cancel through a two-turn confirmation flow**

In `run()`, handle pending cancel before a new cancel request:

```python
        if self._is_pending_cancel_action(frame):
            return self._handle_cancel_confirmation(frame, tool_runtime)
```

Replace the current unsupported cancel branch with first-turn pending action creation:

```python
        if self._is_cancel_request(message):
            return self._create_cancel_confirmation(frame, message)
```

Add `_create_cancel_confirmation()`:

```python
    def _create_cancel_confirmation(self, frame: ConversationFrame, message: str) -> ProcedureResult:
        if not frame.user_id:
            return ProcedureResult(
                task="appointment",
                phase="appointment_auth_required",
                reply="请先登录后再取消预约。",
                fallback_reason="missing_user_id",
            )
        appointment_id = self._extract_appointment_id(frame, message)
        if not appointment_id:
            return ProcedureResult(
                task="appointment",
                phase="appointment_needs_info",
                reply="请提供要取消的预约编号。",
                metadata={"missing": "appointment_id"},
            )
        confirmation_id = str(uuid.uuid4())[:8]
        now = time.time()
        pending_action = {
            "type": "appointment.cancel",
            "confirmation_id": confirmation_id,
            "status": "pending",
            "payload": {"appointment_id": appointment_id, "user_id": frame.user_id},
            "created_at": now,
            "expires_at": now + 300,
        }
        return ProcedureResult(
            task="appointment",
            phase="appointment_cancel_needs_confirmation",
            reply=f"请确认取消预约 {appointment_id}。回复'确认'继续，或'取消'放弃。",
            pending_action=pending_action,
            actions=[
                {"type": "confirm", "confirmation_id": confirmation_id, "label": "确认取消"},
                {"type": "cancel", "confirmation_id": confirmation_id, "label": "保留预约"},
            ],
            metadata={"appointment_id": appointment_id},
        )
```

Add `_handle_cancel_confirmation()`:

```python
    def _handle_cancel_confirmation(self, frame: ConversationFrame, tool_runtime: Any | None) -> ProcedureResult:
        message = frame.message or ""
        action_type = (frame.action or {}).get("type")
        is_confirm = action_type == "confirm" or any(term in message for term in ("确认", "好的", "是的", "确定", "行", "可以", "yes", "ok"))
        is_cancel = action_type == "cancel" or any(term in message for term in ("取消", "不要了", "算了", "no"))

        if is_cancel:
            frame.pending_action = None
            return ProcedureResult(task="appointment", phase="appointment_cancel_aborted", reply="好的，已保留该预约。")

        if not is_confirm:
            return ProcedureResult(
                task="appointment",
                phase="appointment_cancel_needs_confirmation",
                reply="请确认是否取消预约？回复'确认'继续，或'取消'放弃。",
                pending_action=frame.pending_action,
            )

        if tool_runtime is None:
            return ProcedureResult(
                task="appointment",
                phase="appointment_tool_unavailable",
                reply="预约服务暂时不可用，请稍后再试。",
                fallback_reason="tool_runtime_missing",
            )
        pending = frame.pending_action or {}
        payload = dict(pending.get("payload", {}))
        appointment_id = payload.get("appointment_id")
        request = ToolCallRequest(
            tool="appointment.cancel",
            request_id=frame.request_id,
            user_id=frame.user_id or "",
            confirmation_id=pending.get("confirmation_id", ""),
            payload={**payload, "user_id": frame.user_id or payload.get("user_id", "")},
        )
        result = tool_runtime.execute(request)
        frame.pending_action = None
        if result.ok:
            return ProcedureResult(
                task="appointment",
                phase="appointment_cancelled",
                reply=f"已取消预约：{appointment_id}。",
                metadata={"appointment_id": appointment_id},
            )
        return ProcedureResult(
            task="appointment",
            phase="appointment_cancel_failed",
            reply="取消预约失败，请稍后再试或联系人工客服。",
            fallback_reason="appointment_cancel_failed",
        )
```

- [ ] **Step 5: Update routing for pending cancel follow-up**

Modify `HybridRouter.route()` so pending appointment follow-up includes both create and cancel:

```python
        if frame.pending_action and frame.pending_action.get("type") in {"appointment.create", "appointment.cancel"}:
            if self._is_pending_action_followup(message):
                return RouteDecision(
                    task="appointment",
                    procedure="appointment.workflow",
                    confidence=0.98,
                    domain_category="in_domain_task",
                    reason="pending appointment action",
                )
```

- [ ] **Step 6: Run appointment tests**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/modules/test_appointment.py -q
```

Expected: appointment tests pass after helper names are aligned with existing tests.

---

## Task 7: Add Lease Workflow Procedure

**Files:**
- Create: `backend/src/aptguide2/harness/modules/lease.py`
- Create: `backend/tests/unit/harness/modules/test_lease.py`
- Modify: `backend/src/aptguide2/api/deps.py`
- Modify: `backend/src/aptguide2/harness/routing.py`

- [ ] **Step 1: Add lease procedure tests**

Create `backend/tests/unit/harness/modules/test_lease.py`:

```python
from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.modules.lease import LeaseWorkflowProcedure
from aptguide2.harness.tools.contracts import ToolCallResult


class CapturingRuntime:
    def __init__(self, result):
        self.result = result
        self.last_request = None

    def execute(self, request):
        self.last_request = request
        return self.result


def _decision() -> RouteDecision:
    return RouteDecision(
        task="lease",
        procedure="lease.workflow",
        confidence=0.9,
        domain_category="in_domain_task",
        reason="test",
    )


def test_lease_list_requires_user_id() -> None:
    proc = LeaseWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id=None, message="我的租约")

    result = proc.run(frame, _decision(), tool_runtime=object())

    assert result.phase == "lease_auth_required"
    assert result.fallback_reason == "missing_user_id"


def test_lease_list_calls_tool_runtime() -> None:
    runtime = CapturingRuntime(
        ToolCallResult.ok_result(
            tool="lease.list_mine",
            data={"leases": [{"lease_id": "l-1", "status": "active"}]},
            backend="lease",
        )
    )
    proc = LeaseWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id="u-1", message="我的租约")

    result = proc.run(frame, _decision(), tool_runtime=runtime)

    assert result.phase == "lease_list"
    assert result.cards[0]["lease_id"] == "l-1"
    assert runtime.last_request.tool == "lease.list_mine"
```

- [ ] **Step 2: Run tests and verify import failure**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/modules/test_lease.py -q
```

Expected: fails because `LeaseWorkflowProcedure` does not exist.

- [ ] **Step 3: Implement lease procedure**

Create `backend/src/aptguide2/harness/modules/lease.py`:

```python
from __future__ import annotations

from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.tools.contracts import ToolCallRequest


class LeaseWorkflowProcedure:
    """Handles current user's lease queries through governed tools."""

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        if not frame.user_id:
            return ProcedureResult(
                task="lease",
                phase="lease_auth_required",
                reply="请先登录后再查看您的租约。",
                fallback_reason="missing_user_id",
            )
        if tool_runtime is None:
            return ProcedureResult(
                task="lease",
                phase="lease_tool_unavailable",
                reply="租约服务暂时不可用，请稍后再试。",
                fallback_reason="tool_runtime_missing",
            )
        request = ToolCallRequest(
            tool="lease.list_mine",
            request_id=frame.request_id,
            user_id=frame.user_id,
            payload={"user_id": frame.user_id, "limit": 10},
        )
        result = tool_runtime.execute(request)
        if not result.ok:
            return ProcedureResult(
                task="lease",
                phase="lease_list_failed",
                reply="查询租约失败，请稍后再试。",
                fallback_reason="lease_list_failed",
            )
        leases = result.data.get("leases", [])
        cards = [
            {
                "type": "lease_record",
                "lease_id": lease.get("lease_id", ""),
                "room_id": lease.get("room_id", ""),
                "status": lease.get("status", ""),
                "start_date": lease.get("start_date", ""),
                "end_date": lease.get("end_date", ""),
            }
            for lease in leases[:5]
        ]
        return ProcedureResult(
            task="lease",
            phase="lease_list" if cards else "lease_list_empty",
            reply=f"您有{len(leases)}条租约记录。" if cards else "您当前没有租约记录。",
            cards=cards,
            metadata={"lease_count": len(leases)},
        )
```

- [ ] **Step 4: Register procedure and routing**

Modify `backend/src/aptguide2/api/deps.py`:

```python
from aptguide2.harness.modules.lease import LeaseWorkflowProcedure
```

```python
runtime.register("lease.workflow", LeaseWorkflowProcedure())
```

Modify `backend/src/aptguide2/harness/routing.py`:

```python
    lease_terms = ("我的租约", "查看租约", "租约列表", "合同列表", "我的合同")
```

Add before KB routing:

```python
        if any(term in message for term in self.lease_terms):
            return RouteDecision(
                task="lease",
                procedure="lease.workflow",
                confidence=0.85,
                domain_category="in_domain_task",
                reason="lease list request",
            )
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/modules/test_lease.py tests/unit/harness/test_routing.py -q
```

Expected: focused tests pass.

---

## Task 8: Normalize System Response Shape

**Files:**
- Modify: `backend/src/aptguide2/api/schemas.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Modify: `backend/src/aptguide2/harness/composer.py`
- Modify: `backend/tests/unit/harness/test_composer.py`
- Modify: `backend/tests/e2e/test_system_mainline.py`

- [ ] **Step 1: Add e2e response-shape tests**

Create `backend/tests/e2e/test_system_mainline.py` with a reusable assertion:

```python
def assert_system_response_shape(data: dict) -> None:
    assert isinstance(data["task"], str)
    assert isinstance(data["message"], str)
    assert "phase" in data
    assert isinstance(data["cards"], list)
    assert isinstance(data["actions"], list)
    assert "pending_action" in data
    assert isinstance(data["metadata"], dict)
    assert isinstance(data["rooms"], list)
    assert isinstance(data["kb_sources"], list)
```

Add test cases for:

```python
def test_capability_response_shape(client):
    response = client.post("/chat", json={"message": "你能做什么", "session_id": "s-mainline"})
    assert response.status_code == 200
    assert_system_response_shape(response.json())
```

```python
def test_handoff_response_shape(client):
    response = client.post("/chat", json={"message": "转人工", "session_id": "s-handoff"})
    assert response.status_code == 200
    assert_system_response_shape(response.json())
    assert response.json()["task"] == "handoff"
```

Use the existing e2e client fixture. If the project names it differently, import the same fixture style used by `tests/e2e/test_api.py`.

- [ ] **Step 2: Run response tests**

Run:

```bash
cd backend
uv run pytest tests/e2e/test_system_mainline.py -q
```

Expected: failures identify missing response fields or fixture adjustments.

- [ ] **Step 3: Add first-class cards to ChatResponse**

Modify `backend/src/aptguide2/api/schemas.py`:

```python
class ChatResponse(BaseModel):
    """Outgoing chat response."""

    task: str
    message: str = ""
    phase: str = ""
    cards: list[dict] = Field(default_factory=list)
    rooms: list[RoomResponse] = Field(default_factory=list)
    kb_sources: list[KBSourceResponse] = Field(default_factory=list)
    is_confident: bool = False
    actions: list[dict] = Field(default_factory=list)
    pending_action: dict | None = None
    metadata: dict = Field(default_factory=dict)
```

`rooms` remains a compatibility projection for room cards. `cards` is the canonical field for all card types, including `appointment_record`, `appointment_confirmation`, and `lease_record`.

- [ ] **Step 4: Ensure `_build_response_from_harness()` maps all card types safely**

Modify `backend/src/aptguide2/api/app.py` so non-room cards are returned through `ChatResponse.cards`, not through `metadata`:

```python
    return ChatResponse(
        task=result.metadata.get("task", "fallback"),
        message=result.reply,
        phase=result.phase,
        cards=result.cards,
        rooms=rooms,
        kb_sources=sources,
        is_confident=bool(result.metadata.get("is_confident", False)),
        actions=result.actions,
        pending_action=result.pending_action,
        metadata=result.metadata,
    )
```

- [ ] **Step 5: Define ResponseComposer responsibilities and metadata contract**

`ResponseComposer` is responsible for composing `AptGuideResponse` from `ProcedureResult`; it should not know API response schemas. It must:

- pass through `cards`
- pass through `actions`
- pass through `pending_action`
- pass through `sources`
- merge procedure metadata
- inject standard routing/shape metadata

Modify `backend/src/aptguide2/harness/composer.py` metadata construction:

```python
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
```

- [ ] **Step 6: Add composer unit tests**

Update `backend/tests/unit/harness/test_composer.py` with assertions equivalent to:

```python
def test_composer_preserves_cards_actions_pending_and_standard_metadata():
    composer = ResponseComposer()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", message="我的预约")
    decision = RouteDecision(
        task="appointment",
        procedure="appointment.workflow",
        confidence=0.9,
        domain_category="in_domain_task",
        reason="test",
    )
    result = ProcedureResult(
        task="appointment",
        phase="appointment_list",
        reply="您有1条预约记录。",
        cards=[{"type": "appointment_record", "appointment_id": "a-1"}],
        actions=[{"type": "cancel_appointment"}],
        pending_action={"type": "appointment.cancel"},
        sources=[],
        metadata={"appointment_count": 1},
    )
    trace = AptGuideTrace(trace_id="t-1", request_id="r-1", session_id="s-1", stages=[])

    response = composer.compose(frame, decision, result, trace)

    assert response.cards == result.cards
    assert response.actions == result.actions
    assert response.pending_action == result.pending_action
    assert response.metadata["appointment_count"] == 1
    assert response.metadata["procedure"] == "appointment.workflow"
    assert response.metadata["task"] == "appointment"
    assert response.metadata["card_count"] == 1
    assert response.metadata["action_count"] == 1
    assert response.metadata["has_pending_action"] is True
```

- [ ] **Step 7: Run e2e system tests**

Run:

```bash
cd backend
uv run pytest tests/e2e/test_system_mainline.py tests/e2e/test_api.py -q
```

Expected: system response shape passes for all covered flows.

---

## Task 9: Migrate System Acceptance Away From Legacy Pipeline Tests

**Files:**
- Modify: `backend/tests/e2e/test_pipeline.py`
- Modify: `backend/tests/e2e/test_api.py`
- Modify: `backend/tests/e2e/test_system_mainline.py`

- [ ] **Step 1: Mark old pipeline tests as legacy isolation**

At the top of `backend/tests/e2e/test_pipeline.py`, add:

```python
"""Legacy RAG MVP isolated tests.

These tests verify old pipeline behavior for historical comparison only.
They are not system acceptance tests for AptGuide 2.0 mainline behavior.
"""
```

If these tests are no longer valuable after mainline tests are complete, move critical expectations into `test_system_mainline.py` and delete duplicate legacy e2e cases.

- [ ] **Step 2: Add mainline acceptance coverage**

In `backend/tests/e2e/test_system_mainline.py`, cover:

```python
def test_appointment_create_returns_pending_action(client):
    response = client.post(
        "/chat",
        json={"message": "预约200013号房明天下午3点", "session_id": "s-appt", "user_id": "u-1"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["task"] == "appointment"
    assert data["pending_action"]["type"] == "appointment.create"
    assert data["actions"][0]["type"] == "confirm"
```

```python
def test_missing_user_id_blocks_appointment(client):
    response = client.post(
        "/chat",
        json={"message": "预约200013号房明天下午3点", "session_id": "s-auth"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["task"] == "appointment"
    assert data["metadata"].get("fallback_reason") == "missing_user_id"
    assert "登录" in data["message"]
```

- [ ] **Step 3: Run e2e tests**

Run:

```bash
cd backend
uv run pytest tests/e2e -q
```

Expected: e2e tests validate the harness mainline. Legacy pipeline tests no longer define system acceptance.

---

## Task 10: System Smoke And Readiness Alignment

**Files:**
- Modify: `backend/src/aptguide2/system/readiness.py`
- Modify: `backend/scripts/check_live_dependencies.py`
- Modify: `docs/tests/system-smoke-checklist.md`
- Modify: `backend/tests/unit/system/test_readiness.py`

- [ ] **Step 1: Extend smoke checklist**

Update `docs/tests/system-smoke-checklist.md` to include these manual smoke cases:

```text
1. Capability: "你能做什么"
2. Room search: "番禺1500以内找房"
3. KB QA: "押金怎么退"
4. Appointment create: "预约200013号房明天下午3点"
5. Appointment confirm: action.type=confirm with returned confirmation_id
6. Appointment list: "我的预约"
7. Appointment cancel: "取消预约 <appointment_id>"
8. Lease list: "我的租约"
9. User handoff: "转人工"
10. Safety fallback: "帮我查其他租户手机号"
```

- [ ] **Step 2: Add readiness field for mainline runtime**

In `backend/src/aptguide2/system/readiness.py`, add a check that reports the configured runtime:

```python
DependencyCheck(
    name="pipeline",
    required=True,
    ok=settings.pipeline_version == "harness_v1",
    detail=f"pipeline_version={settings.pipeline_version}",
)
```

Place it with the existing dependency checks used by `backend/scripts/check_live_dependencies.py` so the markdown report shows whether the system is using the mainline runtime. If the script constructs `DependencyCheck` instances directly, add the `pipeline` check there rather than only changing the model module.

- [ ] **Step 3: Run readiness tests**

Run:

```bash
cd backend
uv run pytest tests/unit/system/test_readiness.py -q
```

Expected: update expected markdown/check counts if needed, with `pipeline` included as ok/ready in rendered markdown.

---

## Task 11: Documentation And Progress Updates

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/27-current-implementation-guide.md`
- Modify: `docs/plans/README.md`
- Modify: `progress/current-plan.md`
- Modify: `progress/next-steps.md`
- Modify: `reports/evaluation-report.md`

- [ ] **Step 1: Update current implementation wording**

Update docs to say:

```text
旧 RAG MVP pipeline 已保留为 legacy reference，但不再接入 /chat、harness procedure 或系统验收测试。AptGuide 2.0 主线运行时为 harness mainline，RAG v2 作为 harness 内部检索模块使用。
```

- [ ] **Step 2: Update progress objective**

Set `progress/current-plan.md` active objective to:

```text
System feature completion and mainline integration: make harness the only product runtime, disconnect legacy RAG from public interfaces, and complete appointment, lease, memory, handoff, response, and smoke behavior.
```

- [ ] **Step 3: Update next step**

Set `reports/evaluation-report.md` JSON `next_step` to:

```json
"next_step": "Complete system feature mainline integration; legacy RAG remains disconnected from public interfaces"
```

- [ ] **Step 4: Run link and regression checks**

Run:

```bash
cd backend
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/unit/evals tests/unit/system tests/e2e -q
uv run ruff check src tests
```

Expected: all tests pass and ruff reports no errors.

---

## Final Acceptance

Run:

```bash
cd backend
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/unit/evals tests/unit/system tests/e2e -q
uv run ruff check src tests
```

Expected:

- All tests pass.
- `api.app` does not import `aptguide2.rag.pipeline`.
- `api.deps` does not import or register `RagBaselineProcedure`.
- `pipeline_v2.py` does not import `PipelineResult` from legacy `pipeline.py`.
- `/chat` enters `AptGuideHarness`.
- Harness uses `RagV2Procedure`.
- `ChatResponse` exposes first-class `cards` plus compatibility `rooms`.
- Appointment create/list/cancel, lease list, handoff, fallback, and response metadata are covered by tests.

## Self-Review

- Spec coverage: Covers old RAG disconnection, harness mainline, RAG v2 mounting, appointment completion, lease completion, response shape, smoke/readiness, tests, and docs.
- Placeholder scan: No placeholder tasks remain; deferred retrieval-quality work is explicitly outside this phase.
- Type consistency: Procedure names, tool names, and runtime flow use existing AptGuide naming conventions.
