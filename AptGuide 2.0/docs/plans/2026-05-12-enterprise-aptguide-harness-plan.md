# Enterprise AptGuide Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build AptGuide 2.0 as an enterprise-grade rental Agent harness first, then implement RAG as one high-quality module inside that system.

**Architecture:** Add a system-level `aptguide2.harness` runtime beside the current MVP `aptguide2.rag`. The harness owns request contracts, context, routing, workflow selection, tool execution, trace, replay, strategy registry, and response composition. RAG is mounted as `aptguide2.harness.modules.rag`, not as an isolated application architecture.

**Tech Stack:** FastAPI, Pydantic, OpenAI-compatible LLM and embedding APIs, Milvus, existing `LeaseAdapter` and `VectorAdapter`, pytest, YAML configuration.

---

## 1. Correct Scope

This plan supersedes the earlier RAG-only framing. The correct system boundary is:

```text
AptGuide 2.0 Enterprise Harness
  -> API and response contracts
  -> session/context/memory
  -> domain and safety routing
  -> procedure/workflow runtime
  -> tool registry and adapters
  -> RAG module
  -> action and confirmation module
  -> handoff module
  -> trace/replay/observability
  -> config and strategy registry
```

RAG is important, but it is only one module:

```text
harness.modules.rag
  -> query understanding
  -> query rewrite
  -> room retrieval
  -> KB retrieval
  -> validation
  -> rerank
  -> confidence
  -> grounded response
```

## 2. Why This Is Needed

The current code has a working FastAPI + RAG MVP, but not a full AptGuide 2.0 harness.

Current gaps:

- `/chat` directly calls the RAG MVP pipeline instead of a system-level conversation runtime.
- `session_id` exists in schema but is not used to load conversation context.
- Domain boundary, phase routing, procedure selection, tool registry, and response composition exist mainly in docs, not as one runtime harness.
- RAG routing and rewrite rely heavily on string matching.
- Room facts are not yet strictly validated through `lease` before final presentation.
- Trace schemas exist, but the runtime does not yet produce a complete stage-by-stage replayable trace.

The first engineering objective is therefore not "improve one RAG function". It is to build a harness that can host RAG, appointment, user data, memory, handoff, and future modules consistently.

## 3. Target Runtime Shape

```text
ChatRequest
  -> AptGuideRequest
  -> ContextLoader
  -> EventFilter
  -> SafetyBoundary
  -> ConversationManager
  -> HybridRouter
  -> ProcedureSelector
  -> ProcedureRuntime
      -> rag.room_search
      -> rag.kb_qa
      -> appointment.workflow
      -> user_data.query
      -> memory.workflow
      -> handoff.workflow
      -> capability.workflow
  -> ToolRegistry
  -> RecoveryPolicy
  -> ResponseComposer
  -> TraceRecorder
  -> AptGuideResponse
```

Every stage must have:

- typed input and output;
- strategy name and version;
- latency and error capture;
- deterministic fallback behavior;
- enough trace data to replay one request offline.

## 4. Target File Structure

Create:

```text
backend/src/aptguide2/harness/
├── __init__.py
├── contracts.py
├── config.py
├── errors.py
├── orchestrator.py
├── registry.py
├── context.py
├── event_filter.py
├── safety.py
├── routing.py
├── procedures.py
├── tools.py
├── recovery.py
├── composer.py
├── trace.py
├── replay.py
└── modules/
    ├── __init__.py
    ├── rag/
    │   ├── __init__.py
    │   ├── contracts.py
    │   ├── understanding.py
    │   ├── rewrite.py
    │   ├── planning.py
    │   ├── retrieval.py
    │   ├── validation.py
    │   ├── rerank.py
    │   ├── confidence.py
    │   └── composer.py
    ├── appointment/
    │   ├── __init__.py
    │   └── workflow.py
    ├── memory/
    │   ├── __init__.py
    │   └── workflow.py
    ├── user_data/
    │   ├── __init__.py
    │   └── workflow.py
    ├── handoff/
    │   ├── __init__.py
    │   └── workflow.py
    └── capability/
        ├── __init__.py
        └── workflow.py
```

Initial tests:

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
└── modules/
    └── rag/
        ├── test_understanding.py
        ├── test_rewrite.py
        ├── test_retrieval.py
        ├── test_validation.py
        ├── test_rerank.py
        └── test_confidence.py
```

## 5. Core System Contracts

The harness should introduce stable system contracts in `harness/contracts.py`.

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

## 6. Implementation Phases

### Phase 0: Harness Contracts and Runtime Shell

Goal: create the system-level harness package and make it runnable without changing default MVP behavior.

Tasks:

- Add `aptguide2.harness.contracts`.
- Add `StrategyRegistry`.
- Add `TraceRecorder`.
- Add `ContextLoader` baseline that creates a `ConversationFrame` from request.
- Add `ResponseComposer` baseline.
- Add `AptGuideHarness.run(request)`.
- Keep existing `/chat -> aptguide2.rag.pipeline.run_pipeline()` default.
- Add config switch `APTGUIDE_PIPELINE_VERSION=v1|harness_v1`.

Acceptance:

- Unit tests cover all contracts.
- Default API behavior remains unchanged.
- Harness can return a capability/fallback response through a fake route.

### Phase 1: Boundary, Routing, and Procedure Runtime

Goal: make AptGuide 2.0 route through a system harness before calling any business module.

Tasks:

- Implement `EventFilter` for text/action/system event distinction.
- Implement `SafetyBoundary` for privacy, guarantee, domain, and stale action flags.
- Implement `HybridRouter` for capability, room search, KB QA, appointment, user data, memory, handoff, fallback.
- Implement `ProcedureSelector`.
- Implement `ProcedureRuntime` with typed procedure interface.
- Add placeholder procedures for capability and fallback.

Acceptance:

- Domain-out requests do not call RAG or lease tools.
- Capability questions return fixed capability profile.
- Route decisions are recorded in trace.

### Phase 2: Tool Registry and Adapter Governance

Goal: make all business calls go through a system registry instead of direct ad hoc calls.

Tasks:

- Add system `ToolDefinition`.
- Add `ToolCallRequest` and `ToolCallResult`.
- Wrap existing `VectorAdapter` and `LeaseAdapter` behind registered tool executors.
- Add timeout, error envelope, and PII-safe trace summaries.
- Register MVP tools: `room.search`, `room.detail`, `kb.search`, `appointment.create`, `appointment.list_mine`, `lease.list_mine`, `trace.record`.

Acceptance:

- No new harness procedure directly calls arbitrary backend URLs.
- Tool failures produce recoverable typed errors.
- Trace records tool name, backend, latency, ok/error code, result count.

### Phase 3: RAG Module Integration

Goal: mount the current RAG MVP as a module inside the AptGuide harness.

Tasks:

- Add `harness.modules.rag.contracts`.
- Adapt current `understand_query()` into a baseline RAG understanding strategy.
- Adapt current `retrieve_rooms()` and `retrieve_kb()` into RAG module retrievers.
- Adapt current `rank_rooms()` and `check_confidence()` into baseline module strategies.
- Ensure RAG module returns `ProcedureResult`, not API response directly.
- Keep response composition at the system harness layer.

Acceptance:

- Room search and KB QA both run through the harness procedure runtime.
- Existing RAG tests still pass.
- Harness response shape matches `AptGuideResponse`.

### Phase 4: RAG Quality Upgrade

Goal: optimize RAG to enterprise quality inside the system harness.

Tasks:

- Replace string task detection with structured router strategy.
- Add task-specific query rewrite strategy.
- Add room hybrid retrieval: lease exact search + Milvus vector recall + merge.
- Add KB hybrid retrieval: keyword/BM25 baseline + Milvus vector recall + merge.
- Add room validation gate through lease facts.
- Add KB grounding validation.
- Add reranker interface and rule baseline.
- Add optional semantic reranker provider.
- Add confidence gate v2 with source coverage and risk constraints.
- Add grounded response composer for KB and room recommendation reasons.

Acceptance:

- Milvus is only a candidate/source retriever, not final room fact owner.
- High-risk KB answers are source-bound.
- RAG stages are traceable and replayable.

### Phase 5: Action and Appointment Workflow

Goal: implement write operations as deterministic procedures.

Tasks:

- Add `appointment.workflow`.
- Resolve selected room from `last_recommendations`.
- Parse and validate appointment time.
- Create pending action with `confirmation_id`.
- Require structured action confirmation.
- Reject stale or duplicate confirmation.
- Execute `appointment.create` through Tool Registry.
- Compose success/failure response.

Acceptance:

- Pure text "确认" cannot execute a write action.
- Expired confirmation cannot execute.
- Tool failure never becomes success text.

### Phase 6: Memory and Context

Goal: make `session_id` meaningful and prepare long-term preferences safely.

Tasks:

- Add session context store interface.
- Persist short-term `ConversationFrame` fields.
- Preserve last recommendations for follow-up actions.
- Add memory candidate workflow.
- Require confirmation before writing long-term profile.
- Add delete/read memory procedures.

Acceptance:

- Follow-up messages can inherit prior constraints.
- Long-term memory is auditable and deletable.
- Pending action survives context compression.

### Phase 7: Handoff, Replay, and Operational Hardening

Goal: make failures diagnosable and safely escalated.

Tasks:

- Add handoff trigger rules.
- Add handoff summary composer.
- Add replay JSONL writer with PII guard.
- Add debug trace endpoint for development only.
- Add degradation policies for LLM, Milvus, lease, reranker, and memory failures.

Acceptance:

- Repeated tool failures can trigger handoff.
- One request can be replayed offline from stored trace/replay case.
- Provider outage returns controlled fallback, not traceback.

## 7. Recommended Execution Order

```text
1. Harness contracts
2. Registry, trace, replay shell
3. Context loader and response composer
4. Safety boundary and hybrid router
5. Procedure runtime
6. Tool registry
7. Mount current RAG MVP as module
8. Upgrade RAG module
9. Appointment workflow
10. Memory context
11. Handoff and operational hardening
```

## 8. Verification Commands

After harness foundation tasks:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness -q
```

Before switching `/chat` to harness:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit tests/e2e -q
```

Manual smoke test:

```bash
cd "AptGuide 2.0/backend"
APTGUIDE_PIPELINE_VERSION=harness_v1 uv run uvicorn aptguide2.api.app:app --reload
```

Then:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"番禺1500以内安静点的房子","session_id":"dev-session"}'
```

Expected:

- no traceback;
- response has `reply`, `phase`, `domain_category`, and `metadata`;
- room search either returns validated room cards or a clear fallback reason;
- trace is included only when debug config allows it.

## 9. What This Plan Defers

Deferred until the harness is stable:

- large-scale eval platform redesign;
- online A/B testing;
- Learning to Rank;
- full front-end app;
- MCP exposure;
- operations dashboard.

These are important, but the system harness must come first.
