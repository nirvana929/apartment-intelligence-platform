# Checkpoint: system-feature-completion-mainline-integration

## Metadata

- Created at: 2026-05-14T15:54:02+08:00
- Task: system-feature-completion-mainline-integration
- Status: completed
- Test status: 323 passed (308 unit + 15 e2e)

## Goal

Make harness the only `/chat` runtime, disconnect legacy RAG MVP from all public interfaces, mount RAG v2 as internal harness module, and complete appointment/lease/response/readiness features.

## Context

Plan: `2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md`
Branch: `codex/update-project-readme`
Pre-existing tests: 246 (from prior phases: harness foundation, tool governance, RAG v2)

## Completed Work

1. PipelineResult migrated from `rag/pipeline.py` to `rag/schemas.py` — shared contract
2. Wiring guard tests created — prove legacy RAG disconnected from API/harness
3. `rag/pipeline_v2.py` imports from `rag/schemas.py` (not legacy pipeline)
4. `api/app.py` rewritten — removed all legacy branches, `_build_response()`, `_generate_room_message()`, `_generate_kb_answer()`
5. `api/deps.py` replaced `RagBaselineProcedure` with `RagV2Procedure`, added `LeaseWorkflowProcedure` and `AppointmentCancelExecutor`
6. `core/config.py` default `pipeline_version` changed from `"v1"` to `"harness_v1"`
7. `harness/modules/rag/v2.py` created — RagV2Procedure adapter wrapping `run_pipeline_v2()`
8. `appointment.cancel` two-turn confirmation flow implemented (matches `appointment.create` pattern)
9. `LeaseWorkflowProcedure` created and registered for lease list queries
10. `ChatResponse` gains first-class `cards` field for all card types
11. `ResponseComposer` includes standard metadata (card_count, source_count, action_count, has_pending_action, procedure, task, route_confidence, fallback_reason)
12. `build_readiness_report()` verifies `pipeline_version == "harness_v1"`

## Files Changed

### Modified

- `backend/src/aptguide2/rag/pipeline.py` — removed local PipelineResult, imports from schemas
- `backend/src/aptguide2/rag/pipeline_v2.py` — imports PipelineResult from schemas
- `backend/src/aptguide2/rag/schemas.py` — PipelineResult class added
- `backend/src/aptguide2/api/app.py` — harness-only, no legacy branches
- `backend/src/aptguide2/api/deps.py` — RagV2Procedure, LeaseWorkflowProcedure, AppointmentCancelExecutor
- `backend/src/aptguide2/api/schemas.py` — ChatResponse.cards field
- `backend/src/aptguide2/core/config.py` — pipeline_version default
- `backend/src/aptguide2/tools/lease_adapter.py` — cancel_appointment, list_leases methods
- `backend/src/aptguide2/harness/modules/appointment.py` — cancel two-turn confirmation
- `backend/src/aptguide2/harness/modules/lease.py` — LeaseWorkflowProcedure
- `backend/src/aptguide2/harness/tools/lease_tools.py` — AppointmentCancelExecutor
- `backend/src/aptguide2/harness/tools/builtins.py` — appointment.cancel ToolDefinition
- `backend/src/aptguide2/harness/routing.py` — lease terms, pending cancel routing
- `backend/src/aptguide2/harness/contracts.py` — "lease" task type
- `backend/src/aptguide2/harness/composer.py` — standard metadata
- `backend/src/aptguide2/system/readiness.py` — build_readiness_report()

### Created

- `backend/src/aptguide2/harness/modules/rag/v2.py` — RagV2Procedure
- `backend/tests/unit/api/test_mainline_wiring.py` — wiring guard tests
- `backend/tests/unit/harness/modules/test_rag_v2.py` — RagV2Procedure tests
- `backend/tests/unit/harness/modules/test_lease.py` — LeaseWorkflowProcedure tests
- `backend/tests/e2e/test_system_mainline.py` — mainline acceptance tests

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| Session start | test_capability TypeError | `_harness_patches()` helper returned tuple, not context manager | Removed helper, used direct `patch()` in each test | Fixed |
| Mid-session | test_builtins count mismatch | Adding `appointment.cancel` changed expected tool count | Updated EXPECTED_NAMES and confirmed tools assertion | Fixed |
| Mid-session | 55 ruff errors (I001) | Import sorting after bulk edits | `ruff check --fix` auto-resolved | Fixed |
| Late session | e2e mock path failures | Removed imports from app.py broke patch targets | Changed patch targets from `aptguide2.api.app.*` to `aptguide2.api.deps.*` | Fixed |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `cd "AptGuide 2.0/backend" && uv run pytest tests/ -q` | 323 passed | 308 unit + 15 e2e |
| `cd "AptGuide 2.0/backend" && uv run ruff check src/` | clean | No errors |

## Known Issues

- None introduced by this session

## Next Steps

1. RAG retrieval quality improvement (KB hit@3=48.6%, Room hit@5=40%)
   - Optimize query understanding for more kb_qa recognition
   - Adjust confidence gate threshold
   - Fix room retrieval filter precision

## Outcome Notes

- Harness is now the sole product runtime for `/chat` — zero legacy RAG branches remain
- Two-turn confirmation pattern established for both create and cancel appointment flows
- `PipelineResult` shared contract decouples RAG v2 from legacy pipeline at import level
- Wiring guard tests prevent regression (legacy imports would fail tests immediately)
- Standard metadata in composer enables frontend to render cards/actions/pending state uniformly
