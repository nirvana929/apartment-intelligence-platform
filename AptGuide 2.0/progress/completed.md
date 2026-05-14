# Completed

## Phase 1: Harness Foundation (2026-05-13)

- `aptguide2.harness` package with 17 Python files
- Contracts: AptGuideRequest, ConversationFrame, RouteDecision, ProcedureResult, StageTrace, AptGuideTrace, AptGuideResponse
- Errors: StrategyNotFoundError, ProcedureNotFoundError, ReplayPIIError
- Registry: StrategyRegistry
- Context: InMemoryContextStore
- Safety: SafetyBoundary (keyword matching)
- Routing: HybridRouter (rule-based)
- Procedures: Procedure Protocol + ProcedureRuntime
- Composer: ResponseComposer
- Trace: TraceRecorder
- Replay: ReplayWriter (PII-guarded JSONL)
- Orchestrator: AptGuideHarness.run()
- Modules: RagBaselineProcedure, CapabilityProcedure, FallbackProcedure
- API: pipeline version switch (`APTGUIDE_PIPELINE_VERSION=harness_v1`)
- E2E: 9 API tests including harness branch
- Regression: 147 tests all passed

## Phase 2: Tool Registry And Adapter Governance (2026-05-14)

- `aptguide2.harness.tools` package with 8 Python files
- Contracts: ToolDefinition, ToolCallRequest, ToolCallResult, ToolError, RetryPolicy, 8 MVP tool schemas
- Errors: ToolAlreadyRegisteredError, ToolNotFoundError, ToolTimeoutError, ToolExecutionError
- Registry: ToolRegistry (register/get/names/by_backend/requires_confirmation)
- Builtins: build_default_tool_registry() with 8 MVP tools
- Runtime: ToolRuntime (permission checks, confirmation gates, executor dispatch, error normalization, trace integration)
- Trace: summarize_tool_request, summarize_tool_result, redact_pii
- Lease executors: LeaseHealthExecutor, RoomSearchExecutor, RoomDetailExecutor, AppointmentCreateExecutor, AppointmentListMineExecutor, LeaseListMineExecutor
- Vector executors: KBSearchExecutor
- Dependency: get_tool_runtime() in deps.py
- Regression: 206 tests all passed

## Phase 3: Enterprise RAG v2 Hybrid Retrieval And Governed Rerank (2026-05-14)

- `aptguide2.rag` package: 8 new Python files (planning, sparse, hybrid, rerank, validation, pipeline_v2, tool_validation, eval_metrics)
- Contracts: RetrievalPlan, HybridCandidate, RerankWeights, LeaseRoomValidator Protocol
- Planning: build_retrieval_plan() separating hard filters from semantic queries, module intent inference, step-back queries
- Sparse: sparse_score() with CJK + ASCII tokenization
- Hybrid: merge_hybrid_candidates() with deduplication, score normalization, channel attribution
- Rerank: rerank_kb_sources() with explicit feature weights (dense 0.35, sparse 0.15, module 0.20, risk 0.15, validation 0.10, lexical 0.05)
- Validation: validate_room_candidates() lease gate — no room shown without lease backend confirmation
- Pipeline v2: run_pipeline_v2() behind `rag_v2` feature flag with trace_recorder support
- Tool Validation: ToolRuntimeRoomValidator adapter over governed ToolRuntime
- Eval Metrics: hit_at_k, mean_reciprocal_rank, ndcg_at_k
- Eval Runner: evals/runners/run_rag_v2.py with gate thresholds
- Character-match audit: reports/rag-v2-character-match-audit.md (keep/weaken/replace taxonomy)
- Eval gates docs: docs/tests/rag-v2-evaluation-gates.md
- E2E: 4 new API tests for rag_v2 branch
- Regression: 246 tests all passed

## Phase 4: Appointment, Memory, Handoff, Procedure-Tool Integration (2026-05-14)

### Step 1: Procedure-Tool Runtime Integration
- Extended Procedure protocol with optional `tool_runtime` parameter (backward compatible)
- Updated ProcedureRuntime.run() to forward tool_runtime
- AptGuideHarness accepts and forwards tool_runtime to procedure_runtime
- All existing procedures (Capability, Fallback, RagBaseline) accept tool_runtime param
- deps.py wires get_tool_runtime() into AptGuideHarness
- Regression: all existing tests still pass

### Step 2: Appointment Workflow
- AppointmentWorkflowProcedure: room_id extraction (regex), time extraction, create/list/cancel flows
- LeaseAdapter: create_appointment() and list_appointments() methods
- Routing: added appointment list terms ("我的预约", "查看预约", "预约列表", "预约记录")
- Registered in deps.py as "appointment.workflow"
- 11 new tests covering extraction, create success/failure, list empty/with data, missing info

### Step 3: Memory Module MVP
- MemoryManager: update_recent_messages (max 12), pending_action lifecycle (create/confirm/cancel/expiry, 300s TTL), tool_observations tracking (max 10), consecutive failure counting
- Integrated into orchestrator: check_pending_action_expiry after context.load, update_recent_messages after procedure.run
- ProcedureResult.pending_action propagated to frame.pending_action
- 19 new tests for message tracking, pending action, tool observations

### Step 4: Handoff Module MVP
- HandoffProcedure: user_initiated and tool_failure handoff with summary generation
- Routing: handoff_terms ("转人工", "找真人", "人工客服", etc.)
- Registered as "handoff.user_initiated" and "handoff.tool_failure"
- Handoff summary includes recent_messages, tool_observations, last_recommendations
- 5 new tests for handoff flows and routing detection

### Regression
- 281 tests all passed (246 baseline + 11 appointment + 19 memory + 5 handoff)

## Phase 5: Harness Correction — Appointment Confirmation and Auto Handoff (2026-05-14)

### Task 1: Reality Audit
- Verified ProcedureRuntime and AptGuideHarness already forward tool_runtime
- Identified appointment.create direct-call bug and missing confirmation_id
- Baseline: 39 focused harness tests pass

### Task 2: ProcedureRuntime-ToolRuntime Integration Tests
- Added explicit forwarding test for ProcedureRuntime (ToolAwareProcedure)
- Added explicit forwarding test for AptGuideHarness (CapturingProcedure)
- 6 tests pass

### Task 3: Pending-Action-Aware Routing
- HybridRouter routes confirmation/cancel messages to appointment.workflow when pending_action exists
- Added `_is_pending_action_followup()` helper with confirm/cancel term detection
- Routing priority: safety > pending_action > capability > handoff > appointment > kb > room > fallback
- 7 routing tests pass

### Task 4: Appointment List Auth Check
- `_list_appointments()` now requires `frame.user_id`, returns `appointment_auth_required` if missing
- Added `test_list_appointments_requires_user_id`
- 12 appointment tests pass

### Task 5: Appointment Create Two-Turn Confirmation
- First turn returns `pending_action` with `confirmation_id`, does NOT call `appointment.create`
- Confirmed turn calls `appointment.create` with `confirmation_id` in `ToolCallRequest`
- Cancelled turn clears pending_action, no tool call
- Supports both text confirmation ("确认") and frontend action (`action.type == "confirm"`)
- Added `test_create_appointment_requires_user_id`
- 15 appointment tests pass

### Task 6: Orchestrator Pending Action Persistence
- Added `test_harness_persists_pending_appointment_across_turns` (two-turn orchestrator test)
- Fixed pending_action expiry: appointment procedure now includes `created_at` and `expires_at` fields
- Added "预约" to appointment_terms for better message matching
- 4 orchestrator tests pass

### Task 7: Tool-Failure Automatic Handoff
- Added `ProcedureRuntime.has()` method
- Orchestrator auto-routes to `handoff.tool_failure` after 2 consecutive tool failures
- Added `FailingAppointmentProcedure` and `test_harness_suggests_handoff_after_consecutive_tool_failures`
- 5 orchestrator tests pass

### Regression
- 292 tests all passed (279 unit + 13 e2e)

## Phase 6: System Feature Completion And Mainline Integration (2026-05-14)

- `/chat` now enters `AptGuideHarness` by default.
- Legacy RAG MVP is disconnected from public interfaces:
  - `api/app.py` no longer imports `aptguide2.rag.pipeline`
  - `api/deps.py` no longer registers `RagBaselineProcedure`
  - system e2e acceptance no longer depends on legacy `run_pipeline()`
- RAG v2 is mounted as an internal harness module through `RagV2Procedure`.
- `PipelineResult` moved to `rag/schemas.py`; `pipeline_v2.py` no longer imports result contracts from legacy `pipeline.py`.
- `LeaseWorkflowProcedure` added for user lease list.
- `appointment.cancel` added with two-turn confirmation and `confirmation_id`.
- `appointment.cancel` tool executor registered in governed ToolRuntime.
- `ChatResponse.cards` added as a first-class field for all card types.
- `ResponseComposer` includes standard metadata: `card_count`, `source_count`, `action_count`, `has_pending_action`.
- Readiness check includes configured pipeline version.
- Regression: 323 tests all passed (308 unit + 15 e2e)
- Ruff: clean

## Phase 7: Semantic Interaction Routing (2026-05-14)

- Added `aptguide2.interaction` package with `InteractionIntent`, `EntityMention`, entity resolution, heuristic fallback, and LLM classifier adapter.
- Replaced keyword-primary `HybridRouter` routing with semantic intent routing while preserving `SafetyBoundary` and pending-action priority.
- `RouteDecision` now carries intent metadata.
- `RagV2Procedure` extracts `InteractionIntent` and passes it into `run_pipeline_v2()`.
- `understand_query()` accepts `interaction_intent` and avoids independent keyword task re-detection when intent exists.
- Appointment workflow can read semantic room entities before regex fallback; two-turn confirmation remains required.
- Added interaction intent eval dataset and runner.
- Verification:
  - `uv run pytest tests/unit/interaction -q` — 9 passed
  - `uv run pytest tests/unit/harness/test_routing.py tests/unit/rag/test_query_understanding.py tests/unit/harness/modules/test_rag_v2.py -q` — 40 passed
  - `uv run pytest tests/unit/harness/modules/test_appointment.py -q` — 22 passed
  - `uv run pytest tests/unit/evals/test_run_interaction_intent_eval.py -q` — 3 passed
  - interaction intent eval — total=8, exact=8, exact_rate=1.0
  - `uv run pytest tests/ -q` — 402 passed, 3 warnings
