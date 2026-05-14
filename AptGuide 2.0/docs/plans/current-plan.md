# Current Plan

## Goal

System feature completion and mainline integration: harness is the only `/chat` runtime, legacy RAG disconnected, RAG v2 mounted as internal harness module.

## Context

Plan `2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md` executed and completed. All 11 tasks done. 323 tests passing (308 unit + 15 e2e). ruff clean.

## Completed (this session)

1. PipelineResult migrated from `rag/pipeline.py` to `rag/schemas.py`
2. Wiring guard tests created (prove legacy RAG disconnected)
3. `rag/pipeline_v2.py` imports from `rag/schemas.py` (not legacy pipeline)
4. `api/app.py` rewritten — all legacy branches removed, harness-only
5. `api/deps.py` registers `RagV2Procedure` instead of `RagBaselineProcedure`
6. `core/config.py` default `pipeline_version = "harness_v1"`
7. `harness/modules/rag/v2.py` created — RagV2Procedure adapter
8. `appointment.cancel` two-turn confirmation flow implemented
9. `LeaseWorkflowProcedure` created and registered
10. `ChatResponse.cards` first-class field added
11. `ResponseComposer` standard metadata added
12. `build_readiness_report()` pipeline version check added

## Current State

- `/chat` enters `AptGuideHarness` by default — no legacy RAG branch
- `api/app.py` has no imports from `aptguide2.rag.pipeline`
- `api/deps.py` registers `RagV2Procedure` and `LeaseWorkflowProcedure`
- `rag/schemas.py` owns `PipelineResult` — shared contract
- `appointment.cancel` uses two-turn confirmation with `confirmation_id`
- 323 tests all passing (308 unit + 15 e2e)
- ruff clean

## Verification

```
cd "AptGuide 2.0/backend" && uv run pytest tests/ -q
# 323 passed
```

## Next Step

RAG retrieval quality improvement (KB hit@3=48.6%, Room hit@5=40%).
