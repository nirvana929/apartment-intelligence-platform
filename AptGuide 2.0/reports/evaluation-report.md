# Evaluation Report

## Current Status

Harness Foundation (Phase 1), Tool Registry Governance (Phase 2), Enterprise RAG v2 (Phase 3), Harness Correction (Phase 4/5), System Integration, and System Feature Completion/Mainline Integration are complete. The current blocker is RAG v2 retrieval quality.

## Phase 1: Harness Foundation — Verification

- `uv run pytest tests/unit/harness -q` — 33 passed
- `uv run pytest tests/unit/rag tests/e2e -q` — 114 passed
- `aptguide2.harness` package: 17 Python files
- `project/feature-list.json`: 16/16 harness features `passes: true`
- `project/sprint-plan.json`: 5/5 sprints `completed`
- Historical phase note: `/chat` default behavior was intentionally unchanged during Phase 1. This has since been superseded by System Feature Completion/Mainline Integration, where `/chat` now enters harness mainline and legacy RAG is disconnected from public interfaces.
- `APTGUIDE_PIPELINE_VERSION=harness_v1` works

## Phase 2: Tool Registry — Verification

- `uv run pytest tests/unit/harness/tools -q` — 59 passed
- `uv run pytest tests/unit/harness -q` — 33 passed
- `uv run pytest tests/unit/rag tests/e2e -q` — 114 passed
- Total: 206 tests all passed
- `aptguide2.harness.tools` package: 8 Python files
- `project/feature-list.json`: 8/8 tool features `passes: true`
- `project/sprint-plan.json`: 6/6 sprints `completed`

## Phase 3: RAG v2 — Verification

- `uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/e2e -q` — 246 passed
- `aptguide2.rag` package: 8 new Python files
- `project/feature-list.json`: RAG v2 features all `passes: true`
- `APTGUIDE_PIPELINE_VERSION=rag_v2` works
- Character-match audit: `reports/rag-v2-character-match-audit.md`
- Eval gates: `docs/tests/rag-v2-evaluation-gates.md`
- Eval report: `reports/rag-v2-evaluation-report.md`

## Phase 4: Harness Correction — Verification

- Appointment create now uses a two-turn pending-action confirmation flow.
- `appointment.create` is not executed on first turn.
- Confirmed execution sends `confirmation_id` through `ToolCallRequest`.
- Pending appointment confirmation survives across orchestrator turns.
- Repeated tool failures can route to `handoff.tool_failure`.
- Missing `user_id` blocks appointment listing and creation before tool execution.
- Routing is pending-action aware (confirmation/cancel messages route to appointment workflow).

Verification command:

```bash
uv run pytest tests/unit/harness tests/unit/tools tests/unit/rag tests/e2e -q
```

## Result

```json
{
  "harness_foundation_passes": true,
  "tool_registry_passes": true,
  "rag_v2_passes": true,
  "harness_correction_passes": true,
  "system_integration_passes": true,
  "total_tests": 323,
  "unit_tests": 308,
  "e2e_tests": 15,
  "new_rag_v2_tests": 19,
  "new_rag_v2_modules": 8,
  "total_features": 33,
  "features_passing": 33,
  "total_sprints": 7,
  "sprints_completed": 7,
  "next_step": "Improve RAG v2 retrieval quality: KB hit@3 48.6% -> 90%+, Room hit@5 40% -> 85%+"
}
```

## System Integration And Production Hardening

Plan: `docs/plans/2026-05-14-aptguide2-system-integration-production-hardening-agent-plan.md`

Verification:

```bash
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/unit/evals tests/unit/system tests/e2e -q
uv run ruff check src tests
```

Reports:

- `reports/live-dependency-readiness-report.md`
- `reports/rag-v2-live-evaluation-report.md`

API contract:

- `ChatRequest.user_id`
- `ChatRequest.action`
- `ChatRequest.client_context`
- `ChatResponse.phase`
- `ChatResponse.cards`
- `ChatResponse.actions`
- `ChatResponse.pending_action`
- `ChatResponse.metadata`

Outcome:

- Local regression: 323 passed (308 unit + 15 e2e)
- Live dependency readiness: ALL READY (Milvus, embedding, lease)
- RAG v2 live eval gates: FAIL

## System Feature Completion And Mainline Integration

Plan: `docs/plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md`

Outcome:

- `/chat` only enters harness mainline.
- Legacy RAG MVP is disconnected from public API, harness wiring, and system e2e acceptance.
- RAG v2 is mounted as an internal harness module through `RagV2Procedure`.
- `appointment.cancel` uses two-turn confirmation with `confirmation_id`.
- `ChatResponse.cards` is a first-class response field.
- `ResponseComposer` includes standard metadata: `card_count`, `source_count`, `action_count`, `has_pending_action`.
- Readiness report includes pipeline version check.
- Regression: 323 tests all passed (308 unit + 15 e2e).
- Ruff: clean.

## Live RAG v2 Evaluation

Report: `reports/rag-v2-live-evaluation-report.md`

Result (after eval case correction):

- All gates passed: NO
- KB source hit@3: 48.6% (gate: >= 90%)
- KB source hit@5: 51.4%
- Room hit@5: 40.0% (gate: >= 85%)
- High-risk fallback: 100.0% (gate: >= 100%) — PASS
- Unvalidated rooms: 0 (gate: = 0) — PASS

Failure classification:

- `retrieval_quality`: 11 KB cases return no sources — pipeline retrieval misses queries in PAY, LIFE, APPT, LEASE categories
- `retrieval_quality`: 6 KB cases have expected doc in Milvus but not in top-5 — ranking/recall quality
- `retrieval_quality`: 3 room cases fail — pipeline room retrieval with district/rent filters returns wrong or no rooms
- Immediate next step: create and execute a focused RAG retrieval quality tuning plan. The target is KB hit@3 >= 90% and Room hit@5 >= 85%, while preserving High-risk fallback at 100% and Unvalidated rooms at 0.
