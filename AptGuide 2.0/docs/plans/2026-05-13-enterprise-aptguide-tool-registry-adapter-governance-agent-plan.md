# Enterprise AptGuide Tool Registry And Adapter Governance Agent Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `project-harness resume` first. Use `subagent-driven-development` or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After the harness foundation is complete, add a governed Tool Registry layer so AptGuide procedures call business capabilities through typed tools, standard error envelopes, permission checks, timeout handling, and trace-safe summaries.

**Architecture:** Build `aptguide2.harness.tools` as the system tool governance layer under the existing `aptguide2.harness` package. It defines tool contracts, registry, execution runtime, built-in tool definitions, and adapters around existing `LeaseAdapter` and `VectorAdapter`. Existing `aptguide2.rag` and default `/chat` behavior must remain intact.

**Tech Stack:** FastAPI, Pydantic, pytest, respx/httpx, existing `LeaseAdapter`, existing `VectorAdapter`, existing `TraceRecorder`, local `project-harness`.

---

## Current Handoff Status

Harness foundation is complete as of 2026-05-13.

Evidence reported by the completing agent:

- 17 Python files added for the full `aptguide2.harness` package.
- 147 tests passed: 33 harness unit tests and 114 existing tests.
- 16/16 features have `passes: true`.
- 5/5 sprints are `completed`.
- JSON project state files are valid.
- Documentation implementation status has been updated.
- `/chat` default behavior remains MVP `v1`.
- `/chat` can switch to `harness_v1` with `APTGUIDE_PIPELINE_VERSION=harness_v1`.

This plan is now the recommended next execution plan. A fresh agent can start from this file after running the Reality Audit Gate below.

## Runtime Decision

This plan uses a **synchronous Tool Runtime** for the first implementation.

Reason:

- the completed harness foundation is synchronous (`AptGuideHarness.run()`, `ProcedureRuntime.run()`, `HybridRouter.route()`);
- switching the whole harness to async would broaden the blast radius;
- the first Tool Registry goal is governance, not concurrency.

Required shape:

```text
ToolRuntime.execute(request) -> ToolCallResult
ToolExecutor.execute(request) -> ToolCallResult
```

Timeout policy for this phase:

- do not introduce an async runtime;
- do not use `asyncio.wait_for` in `ToolRuntime`;
- rely on adapter-level timeouts where available, especially `LeaseAdapter`'s `httpx.Timeout`;
- map `TimeoutError`, `httpx.TimeoutException`, and explicit `ToolTimeoutError` to `TOOL_TIMEOUT`;
- record elapsed time in `metadata["latency_ms"]`;
- if a future executor needs hard preemption, add it in a later async/runtime upgrade plan.

The existing `LeaseAdapter` currently exposes async methods. Lease tool executors may bridge those async adapter methods inside sync executors with a small helper that runs awaitables only when no event loop is already running. Do not convert `AptGuideHarness` to async in this plan.

Suggested prompt for the next agent:

```text
Use this plan and execute it task-by-task:

/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/docs/plans/2026-05-13-enterprise-aptguide-tool-registry-adapter-governance-agent-plan.md

Start with the Reality Audit Gate. The tool runtime in this plan is synchronous to match the completed harness foundation. Do not skip verification. Keep default /chat behavior unchanged. Do not call real Milvus, lease, or LLM services in unit tests. Update project feature/sprint/progress/report state only with passing evidence.
```

## 0. When To Use This Plan

Use this plan only after the previous plan is complete:

```text
docs/plans/2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md
```

Expected previous-state requirements:

- `backend/src/aptguide2/harness` exists.
- `AptGuideHarness` exists.
- `AptGuideRequest`, `ConversationFrame`, `RouteDecision`, `ProcedureResult`, `AptGuideResponse`, and `AptGuideTrace` exist.
- `TraceRecorder` exists.
- `RagBaselineProcedure` exists.
- `/chat` still defaults to MVP behavior.
- `APTGUIDE_PIPELINE_VERSION=harness_v1` can run the harness branch.
- `project/feature-list.json` marks harness foundation features complete with evidence.

If any of the above is false, do not start implementation. First update `reports/evaluation-report.md`, `progress/known-issues.md`, and either finish the foundation plan or write an explicit variance note.

## 1. Reality Audit Gate

The executing agent must start here. The purpose is to adapt this plan to real code, not to blindly follow stale assumptions.

- [ ] **Step 1: Resume project context**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform"
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Expected:

- default project is `AptGuide 2.0`;
- `progress/current-plan.md` and `reports/evaluation-report.md` are readable.

- [ ] **Step 2: Inspect harness foundation status**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0"
git status --short
find backend/src/aptguide2/harness -maxdepth 4 -type f | sort
find backend/tests/unit/harness -maxdepth 5 -type f | sort
python3 -m json.tool project/feature-list.json >/tmp/aptguide-feature-list.valid
python3 -m json.tool project/sprint-plan.json >/tmp/aptguide-sprint-plan.valid
```

Expected:

- harness package files exist;
- harness tests exist;
- JSON state files are valid.

- [ ] **Step 3: Run foundation regression before adding tools**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness -q
uv run pytest tests/unit/rag tests/e2e -q
```

Expected: pass.

If tests fail, stop and fix/report the foundation failure before executing this plan.

- [ ] **Step 4: Write reality addendum if needed**

If the actual foundation differs from this plan, create:

```text
reports/tool-registry-reality-addendum.md
```

Required sections:

```markdown
# Tool Registry Reality Addendum

## Foundation State

## Interface Differences

## Plan Adjustments

## Blockers
```

Examples requiring an addendum:

- `TraceRecorder` method names differ from this plan.
- `aptguide2.harness.tools` already exists.
- The previous agent implemented `tools.py` instead of a `tools/` package.
- `AptGuideHarness` is no longer synchronous.
- `/chat` response mapping differs from the previous plan.

If the foundation regression passes and the harness remains synchronous, no addendum is required. Continue directly to Task 1.

## 2. Non-Negotiable Constraints

- [ ] Do not add a mock backend that can be registered by production runtime.
- [ ] Unit tests may use fake executors, fake adapters, `respx`, or recorded contract samples.
- [ ] Do not call real Milvus, lease, Redis, or LLM services in unit tests.
- [ ] Do not allow write tools to execute without confirmation metadata.
- [ ] Do not trust `user_id` supplied directly by the frontend for user-scoped tools.
- [ ] Do not record raw PII in trace summaries.
- [ ] Do not change default `/chat` behavior unless explicitly covered by tests.
- [ ] Keep `aptguide2.rag` intact.

## 3. Target Package

Preferred target:

```text
backend/src/aptguide2/harness/tools/
├── __init__.py
├── contracts.py
├── errors.py
├── registry.py
├── runtime.py
├── builtins.py
├── lease_tools.py
├── vector_tools.py
└── trace.py
```

If the previous harness foundation already created `backend/src/aptguide2/harness/tools.py`, the executing agent must decide during the Reality Audit Gate whether to:

- keep `tools.py` and implement focused helpers nearby; or
- migrate to `harness/tools/` package with tests proving imports still work.

Prefer `harness/tools/` package unless it would break existing implemented code.

## 4. Target Tests

Create:

```text
backend/tests/unit/harness/tools/
├── test_contracts.py
├── test_registry.py
├── test_runtime.py
├── test_builtins.py
├── test_lease_tools.py
├── test_vector_tools.py
└── test_trace.py
```

May modify:

```text
backend/tests/unit/tools/test_lease_adapter.py
backend/tests/unit/tools/test_vector_adapter.py
```

Only modify adapter tests when adding adapter methods or fixing existing adapter behavior needed by tool wrappers.

## 5. Tool Contract Scope

Implement governance for these MVP tools:

```text
lease.health
room.search
room.detail
kb.search
trace.record
appointment.create
appointment.list_mine
lease.list_mine
```

First implementation rule:

- `lease.health`, `room.search`, `room.detail`, `kb.search`, and `trace.record` must have working executors with fake-adapter unit tests.
- `appointment.create`, `appointment.list_mine`, and `lease.list_mine` must have schemas, definitions, permission/confirmation metadata, and explicit safe failure if no real adapter method exists yet.

Do not fake appointment success.

## 6. Task 1: Add Tool Contracts

**Files:**

- Create: `backend/src/aptguide2/harness/tools/__init__.py`
- Create: `backend/src/aptguide2/harness/tools/contracts.py`
- Create: `backend/src/aptguide2/harness/tools/errors.py`
- Test: `backend/tests/unit/harness/tools/test_contracts.py`

- [ ] **Step 1: Write failing tests**

Test behaviors:

```python
import pytest
from pydantic import ValidationError

from aptguide2.harness.tools.contracts import (
    RetryPolicy,
    RoomSearchInput,
    ToolCallRequest,
    ToolCallResult,
    ToolDefinition,
    ToolError,
)


def test_tool_definition_defaults():
    definition = ToolDefinition(
        name="room.search",
        backend="lease",
        permission="public",
        input_schema="RoomSearchInput",
        output_schema="RoomSearchOutput",
    )
    assert definition.requires_user is False
    assert definition.requires_confirmation is False
    assert definition.timeout_seconds == 5.0
    assert definition.retry.max_attempts == 1


def test_write_tool_requires_confirmation_metadata():
    definition = ToolDefinition(
        name="appointment.create",
        backend="lease",
        permission="user",
        input_schema="AppointmentCreateInput",
        output_schema="AppointmentCreateOutput",
        requires_user=True,
        requires_confirmation=True,
    )
    assert definition.requires_confirmation is True


def test_tool_call_request_carries_trace_context():
    req = ToolCallRequest(
        tool="room.search",
        request_id="r-1",
        trace_id="t-1",
        payload={"max_rent": 1800},
    )
    assert req.trace_id == "t-1"
    assert req.payload["max_rent"] == 1800


def test_tool_result_success_defaults():
    result = ToolCallResult.ok_result(
        tool="room.search",
        data={"rooms": []},
        backend="lease",
        latency_ms=1.2,
    )
    assert result.ok is True
    assert result.error is None
    assert result.metadata["result_count"] == 0


def test_health_result_uses_status_not_result_count():
    result = ToolCallResult.ok_result(
        tool="lease.health",
        data={"healthy": True},
        backend="lease",
        latency_ms=1.2,
        metadata={"status": "healthy"},
    )
    assert result.metadata["status"] == "healthy"
    assert "result_count" not in result.metadata


def test_tool_result_error_envelope():
    result = ToolCallResult.error_result(
        tool="room.search",
        code="TOOL_TIMEOUT",
        message="tool timed out",
        recoverable=True,
        backend="lease",
    )
    assert result.ok is False
    assert result.error.code == "TOOL_TIMEOUT"
    assert result.error.recoverable is True


def test_room_search_input_limit_bounds():
    with pytest.raises(ValidationError):
        RoomSearchInput(limit=0)
```

- [ ] **Step 2: Run and confirm failure**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/tools/test_contracts.py -q
```

Expected: fail because `aptguide2.harness.tools` does not exist.

- [ ] **Step 3: Implement contracts**

Required model names:

```text
RetryPolicy
ToolDefinition
ToolCallRequest
ToolError
ToolCallResult
LeaseHealthInput
LeaseHealthOutput
RoomSearchInput
RoomSearchOutput
RoomDetailInput
RoomDetailOutput
KBSearchInput
KBSearchOutput
TraceRecordInput
TraceRecordOutput
AppointmentCreateInput
AppointmentCreateOutput
AppointmentListMineInput
AppointmentListMineOutput
LeaseListMineInput
LeaseListMineOutput
```

Contract guidance:

- Use `Literal` for backend, permission, and standard error code fields.
- Use `Field(default_factory=...)` for mutable defaults.
- `ToolCallResult.ok_result()` and `ToolCallResult.error_result()` should be classmethods.
- `ToolCallResult.metadata` must include `backend` and `latency_ms`.
- `result_count` is optional. Include it for list/search tools such as `room.search` and `kb.search`; do not force it for health/status tools.
- For `lease.health`, use metadata such as `{"status": "healthy"}` or `{"status": "unhealthy"}`.
- Tool input schemas must be Pydantic models, not raw dict aliases.

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/harness/tools/test_contracts.py -q
```

Expected: pass.

## 7. Task Dependency And Parallelization

Dependency chain:

```text
Task 1 contracts
  -> Task 2 registry
  -> Task 3 runtime
  -> Task 5 lease executors
  -> Task 7 dependency wiring
  -> Task 8 trace wiring

Task 1 contracts
  -> Task 4 trace summaries

Task 3 runtime
  -> Task 6 vector executors
  -> Task 7 dependency wiring
```

Safe parallelism:

- After Task 1 passes, Task 2 and Task 4 can run in parallel.
- After Task 3 passes, Task 5 and Task 6 can run in parallel.
- Task 7 must wait for Task 5 and Task 6.
- Task 8 should wait for Task 3 and Task 4.

If using multiple agents, split write scopes:

- Registry worker owns `registry.py`, `builtins.py`, and registry tests.
- Trace worker owns `trace.py` and trace tests.
- Lease worker owns `lease_tools.py` and lease tool tests.
- Vector worker owns `vector_tools.py` and vector tool tests.

## 8. Task 2: Add Tool Registry And Built-In Definitions

**Files:**

- Create: `backend/src/aptguide2/harness/tools/registry.py`
- Create: `backend/src/aptguide2/harness/tools/builtins.py`
- Test: `backend/tests/unit/harness/tools/test_registry.py`
- Test: `backend/tests/unit/harness/tools/test_builtins.py`

- [ ] **Step 1: Write registry tests**

Required behaviors:

- register and get a tool definition;
- duplicate registration raises `ToolAlreadyRegisteredError`;
- missing tool raises `ToolNotFoundError`;
- list tools by backend;
- list tools requiring confirmation;
- built-in registry includes all MVP tool names.

Expected built-in names:

```python
{
    "lease.health",
    "room.search",
    "room.detail",
    "kb.search",
    "trace.record",
    "appointment.create",
    "appointment.list_mine",
    "lease.list_mine",
}
```

- [ ] **Step 2: Implement registry**

Required classes/functions:

```text
ToolRegistry
build_default_tool_registry()
ToolAlreadyRegisteredError
ToolNotFoundError
```

Registry behavior:

- `register(definition: ToolDefinition) -> None`
- `get(name: str) -> ToolDefinition`
- `names() -> list[str]`
- `by_backend(backend: str) -> list[ToolDefinition]`
- `requires_confirmation() -> list[ToolDefinition]`

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/unit/harness/tools/test_registry.py tests/unit/harness/tools/test_builtins.py -q
```

Expected: pass.

## 9. Task 3: Add Tool Runtime Governance

**Files:**

- Create: `backend/src/aptguide2/harness/tools/runtime.py`
- Test: `backend/tests/unit/harness/tools/test_runtime.py`

- [ ] **Step 1: Write runtime tests**

Required cases:

- public tool executes without user;
- user tool without `user_id` returns `MISSING_USER_ID`;
- confirmation-required tool without `confirmation_id` returns `CONFIRMATION_REQUIRED`;
- missing executor returns `TOOL_NOT_IMPLEMENTED`;
- executor exception maps to `UNKNOWN_TOOL_ERROR`;
- executor-raised `ToolTimeoutError`, built-in `TimeoutError`, or `httpx.TimeoutException` maps to `TOOL_TIMEOUT`;
- result includes backend, latency, and trace metadata.

Use fake executors only. Do not call lease/vector.

- [ ] **Step 2: Implement runtime**

Required interface:

```python
class ToolExecutor(Protocol):
    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        ...
```

Required runtime:

```text
ToolRuntime
  - register_executor(tool_name, executor)
  - execute(request: ToolCallRequest) -> ToolCallResult
```

Governance order:

```text
lookup definition
  -> validate requires_user
  -> validate requires_confirmation
  -> validate payload with input schema
  -> execute via registered sync executor
  -> normalize result envelope
  -> return ToolCallResult
```

Timeout handling:

- Do not use `asyncio.wait_for`.
- Default timeout comes from `ToolDefinition.timeout_seconds`.
- In this phase, timeout enforcement belongs to executors/adapters.
- `ToolRuntime` maps timeout exceptions to `TOOL_TIMEOUT` and records elapsed time.
- No retry in this sprint unless already trivial; retry policy can remain metadata.

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/unit/harness/tools/test_runtime.py -q
```

Expected: pass.

## 10. Task 4: Add Tool Trace Summaries

**Files:**

- Create: `backend/src/aptguide2/harness/tools/trace.py`
- Test: `backend/tests/unit/harness/tools/test_trace.py`

- [ ] **Step 1: Write trace tests**

Required behaviors:

- successful tool result summarizes `tool`, `backend`, `ok`, and `latency_ms`;
- list/search tool summaries include `result_count` when present;
- health/status tool summaries include `status` when present;
- failed result summarizes `error_code` and `recoverable`;
- PII keys are redacted or omitted from input summary;
- summary never includes raw `phone`, `id_card`, `bank_card`, `real_name`, `email`, `mobile`.

- [ ] **Step 2: Implement trace helpers**

Required functions:

```text
summarize_tool_request(request, definition) -> dict
summarize_tool_result(result) -> dict
redact_pii(value) -> value
```

PII rule:

```text
If a dict key lowercased is in {"phone", "id_card", "bank_card", "real_name", "email", "mobile"}, replace value with "[REDACTED]".
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/unit/harness/tools/test_trace.py -q
```

Expected: pass.

## 11. Task 5: Add Lease Tool Executors

**Files:**

- Create: `backend/src/aptguide2/harness/tools/lease_tools.py`
- Test: `backend/tests/unit/harness/tools/test_lease_tools.py`
- Possibly modify: `backend/src/aptguide2/tools/lease_adapter.py`
- Possibly modify: `backend/tests/unit/tools/test_lease_adapter.py`

- [ ] **Step 1: Write lease executor tests with fake adapter**

Test with a fake adapter object, not real HTTP:

- `lease.health` calls `adapter.health()`;
- `room.search` calls `adapter.search_rooms(payload)`;
- `room.detail` calls `adapter.get_room_detail(room_id)`;
- adapter `LeaseAdapterError("LEASE_UNAVAILABLE", ...)` maps to matching `ToolError`;
- unsupported `appointment.create` returns `TOOL_NOT_IMPLEMENTED` unless adapter method exists.
- if a fake adapter method returns an awaitable, the executor handles it without making `ToolRuntime` async.

- [ ] **Step 2: Implement lease executors**

Required classes:

```text
LeaseHealthExecutor
RoomSearchExecutor
RoomDetailExecutor
AppointmentCreateExecutor
AppointmentListMineExecutor
LeaseListMineExecutor
```

Rules:

- Use existing `LeaseAdapter` methods when available.
- Keep executor interface synchronous.
- If a lease adapter method returns an awaitable, bridge it inside the executor with a local helper such as `run_awaitable_blocking(value)`.
- `run_awaitable_blocking` may use `asyncio.run()` only when no event loop is running. If an event loop is already running, return a `ToolCallResult` with `UNKNOWN_TOOL_ERROR` and a clear message instead of blocking unpredictably.
- Do not fake success for missing methods.
- If adding new adapter methods, write `respx` tests in `tests/unit/tools/test_lease_adapter.py`.
- Map `LeaseAdapterError.code` to `ToolError.code`.
- Map `httpx.TimeoutException` to `TOOL_TIMEOUT` if directly encountered.
- Result envelope must be `ToolCallResult`.

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/unit/harness/tools/test_lease_tools.py -q
uv run pytest tests/unit/tools/test_lease_adapter.py -q
```

Expected: pass.

## 12. Task 6: Add Vector Tool Executors

**Files:**

- Create: `backend/src/aptguide2/harness/tools/vector_tools.py`
- Test: `backend/tests/unit/harness/tools/test_vector_tools.py`

- [ ] **Step 1: Write vector executor tests with fake adapter and fake embed function**

Required cases:

- `kb.search` uses `embed_fn(query)` then `vector_adapter.search_kb(vector, filters, top_k)`;
- result includes sources/chunks and result count;
- embed function failure maps to `UNKNOWN_TOOL_ERROR`;
- vector adapter failure maps to `UNKNOWN_TOOL_ERROR`;
- no real Milvus is called.

Optional case:

- `room.vector_search` may be deferred. Do not add it unless a direct user story needs it.

- [ ] **Step 2: Implement `KBSearchExecutor`**

Required constructor:

```python
KBSearchExecutor(vector_adapter, embed_fn)
```

Required behavior:

```text
request.payload["query"] -> embedding -> vector_adapter.search_kb(...)
```

Return data:

```json
{
  "sources": [...],
  "total": 3
}
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/unit/harness/tools/test_vector_tools.py -q
uv run pytest tests/unit/tools/test_vector_adapter.py -q
```

Expected: pass.

## 13. Task 7: Add Default Tool Runtime Dependency

**Files:**

- Modify: `backend/src/aptguide2/api/deps.py`
- Test: `backend/tests/unit/harness/tools/test_builtins.py` or new `backend/tests/unit/harness/tools/test_deps.py`

- [ ] **Step 1: Write dependency tests**

Test that a default runtime can be constructed with fake adapters or patched dependencies and includes executors for:

```text
lease.health
room.search
room.detail
kb.search
trace.record
```

For `appointment.create`, `appointment.list_mine`, `lease.list_mine`, the runtime must either have safe executors or return `TOOL_NOT_IMPLEMENTED`.

- [ ] **Step 2: Implement dependency**

Add:

```python
def get_tool_runtime() -> ToolRuntime:
    ...
```

Rules:

- Do not initialize Milvus during dependency construction.
- Do not call lease health during dependency construction.
- Register definitions and executors only.
- External calls happen only when `ToolRuntime.execute()` is called.

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/unit/harness/tools -q
```

Expected: pass.

## 14. Task 8: Wire Trace Into Tool Runtime

**Files:**

- Modify: `backend/src/aptguide2/harness/tools/runtime.py`
- Possibly modify: `backend/src/aptguide2/harness/trace.py`
- Test: `backend/tests/unit/harness/tools/test_runtime.py`
- Test: `backend/tests/unit/harness/tools/test_trace.py`

- [ ] **Step 1: Add tests**

Required behavior:

- If `ToolCallRequest.trace_id` exists, result metadata includes it.
- Runtime records request/result summaries when a recorder is provided.
- Trace summary contains no PII.

- [ ] **Step 2: Implement optional recorder hook**

Accept one of these designs based on actual foundation code:

```python
ToolRuntime(registry=registry, recorder=trace_recorder)
```

or:

```python
await runtime.execute(request, recorder=trace_recorder)
```

Choose the design that fits the existing `TraceRecorder` best. Document the choice in `reports/tool-registry-reality-addendum.md` if it differs from this plan.

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/unit/harness/tools/test_runtime.py tests/unit/harness/tools/test_trace.py -q
```

Expected: pass.

## 15. Task 9: Documentation And State Update

**Files:**

- Modify: `docs/04-tool-and-integration-contract.md`
- Modify: `docs/15-tool-registry-and-error-codes.md`
- Modify: `docs/system/enterprise-harness-architecture.md`
- Modify: `docs/plans/README.md`
- Modify: `project/feature-list.json`
- Modify: `project/sprint-plan.json`
- Modify: `progress/current-plan.md`
- Modify: `reports/evaluation-report.md`

- [ ] **Step 1: Update implementation status docs**

Add a short status note:

```markdown
## Current Implementation Status

- `aptguide2.harness.tools.contracts`: implemented
- `aptguide2.harness.tools.registry`: implemented
- `aptguide2.harness.tools.runtime`: implemented
- `aptguide2.harness.tools.lease_tools`: implemented for health/search/detail
- `aptguide2.harness.tools.vector_tools`: implemented for KB search
```

- [ ] **Step 2: Update feature and sprint state**

Add or update feature entries:

```text
feature_tool_contracts
feature_tool_registry
feature_tool_runtime
feature_tool_trace_summary
feature_tool_lease_executors
feature_tool_vector_executors
feature_tool_runtime_dependency
feature_tool_docs_sync
```

Do not mark a feature `passes=true` without evidence.

- [ ] **Step 3: Run docs smoke check**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0"
rg -n "Tool Registry|tool runtime|feature_tool_contracts|tool-registry" docs project progress reports
```

Expected: relevant docs and project state appear.

## 16. Final Verification

Run:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/tools -q
uv run pytest tests/unit/tools -q
uv run pytest tests/unit/harness -q
uv run pytest tests/unit/rag tests/e2e -q
```

Expected: pass.

Optional manual health smoke after implementation:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run python - <<'PY'
from aptguide2.api.deps import get_tool_runtime
runtime = get_tool_runtime()
print(sorted(runtime.registry.names()))
PY
```

Expected includes:

```text
appointment.create
appointment.list_mine
kb.search
lease.health
lease.list_mine
room.detail
room.search
trace.record
```

## 17. Checkpoint Protocol

Before stopping:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform"
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Then update:

```text
progress/current-plan.md
progress/completed.md
progress/known-issues.md
progress/next-steps.md
reports/evaluation-report.md
project/feature-list.json
project/sprint-plan.json
```

Final response must include:

```text
Checkpoint Summary
- Project:
- Current goal:
- Completed this session:
- Files changed:
- Verification:
- Known issues:
- Next steps:
```

## 18. Definition Of Done

This plan is complete when:

- [ ] `aptguide2.harness.tools` exists or an equivalent reconciled tool governance module exists.
- [ ] Tool contracts are typed with Pydantic.
- [ ] Built-in tool definitions cover MVP tools.
- [ ] Tool registry rejects missing/duplicate tools clearly.
- [ ] Tool runtime enforces user and confirmation gates.
- [ ] Tool runtime maps timeout and unknown failures to standard envelopes.
- [ ] Lease health/search/detail tools execute through governed wrappers.
- [ ] KB search executes through governed vector wrapper.
- [ ] Appointment and user scoped tools cannot fake success when not implemented.
- [ ] Tool trace summaries include backend, latency, ok/error, and result count.
- [ ] Tool trace summaries redact PII.
- [ ] Unit tests for harness tools pass.
- [ ] Existing harness, RAG, and API tests still pass.
- [ ] Project feature/sprint/progress/report state is updated with evidence.

## 19. Next Plan After This

After this plan passes, the next high-value plan should be:

```text
RAG Module Integration v2 And Quality Upgrade
```

That plan should use the Tool Registry from this plan to move room search and KB search toward:

- lease exact search + vector recall merge;
- room fact validation through lease;
- KB source grounding;
- high-risk confidence gates;
- recovery trace for empty results.
