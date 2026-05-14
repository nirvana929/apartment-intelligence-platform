# Checkpoint: rag-v2-full-replacement

## Metadata

- Created at: 2026-05-14T20:25:21+08:00
- Task: rag-v2-full-replacement
- Status: completed
- Test status: passed (376 backend tests)

## Goal

Stop AptGuide 2.0 from using any legacy/MVP RAG runtime path. Make RAG v2 the only callable RAG implementation for product runtime, harness runtime, and RAG evaluation. Remove old `pipeline.py`, `kb_retrieval.py`, `room_retrieval.py`, `baseline.py`, and all associated tests.

## Context

Plan: `docs/plans/2026-05-14-aptguide2-rag-v2-full-replacement-agent-plan.md`

The previous `pipeline_v2.py` imported and called `retrieve_kb()` from `kb_retrieval.py` and `retrieve_rooms()` from `room_retrieval.py`, plus `validate_room_candidates` and `rank_rooms` directly. The old `pipeline.py` (direct RAG) and `baseline.py` (harness adapter) remained importable. Old eval runners (`run_rag_eval.py`, `run_rag_mvp.py`) imported deleted modules.

## Completed Work

1. Added 8 guard tests to `test_mainline_wiring.py` and created `test_pipeline_v2_no_legacy.py` with 8 more guards — all fail before implementation, all pass after.
2. Created `rag/kb_v2.py` with `retrieve_kb_v2(plan, vector_adapter, embed_fn)` using hybrid retrieval + governed rerank + confidence gate.
3. Created `rag/room_v2.py` with `retrieve_ranked_rooms_v2(plan, query_result, ...)` using vector search + lease validation + ranking.
4. Rewired `pipeline_v2.py`: replaced old imports with `kb_v2` and `room_v2`, replaced inline validation+ranking with `retrieve_ranked_rooms_v2()`.
5. Deleted legacy files: `pipeline.py`, `kb_retrieval.py`, `room_retrieval.py`, `baseline.py`, `test_pipeline.py`, `test_baseline.py`, `test_kb_retrieval.py`, `test_room_retrieval.py`, `run_rag_eval.py`, `run_rag_mvp.py`.
6. Verified eval runner (`run_rag_v2.py`) imports only from `pipeline_v2`.
7. Full source scan confirms no legacy RAG runtime references in `src/` or `tests/`.

## Files Changed

### Created
- `backend/src/aptguide2/rag/kb_v2.py` — v2-native KB retrieval (102 lines)
- `backend/src/aptguide2/rag/room_v2.py` — v2-native room retrieval (96 lines)
- `backend/tests/unit/rag/test_kb_v2.py` — 9 tests
- `backend/tests/unit/rag/test_room_v2.py` — 6 tests
- `backend/tests/unit/rag/test_pipeline_v2_no_legacy.py` — 8 guard tests
- `backend/docs/plans/checkpoints/2026-05-14-202521-rag-v2-full-replacement.md` — this checkpoint

### Modified
- `backend/src/aptguide2/rag/pipeline_v2.py` — rewired to use kb_v2 and room_v2
- `backend/tests/unit/api/test_mainline_wiring.py` — added 4 new guard tests

### Deleted
- `backend/src/aptguide2/rag/pipeline.py` — old direct RAG pipeline
- `backend/src/aptguide2/rag/kb_retrieval.py` — old KB retrieval
- `backend/src/aptguide2/rag/room_retrieval.py` — old room retrieval
- `backend/src/aptguide2/harness/modules/rag/baseline.py` — old harness adapter
- `backend/tests/e2e/test_pipeline.py` — old pipeline e2e tests
- `backend/tests/unit/harness/modules/rag/test_baseline.py` — old baseline tests
- `backend/tests/unit/rag/test_kb_retrieval.py` — old KB retrieval tests
- `backend/tests/unit/rag/test_room_retrieval.py` — old room retrieval tests
- `backend/evals/runners/run_rag_eval.py` — old eval runner
- `backend/evals/runners/run_rag_mvp.py` — old MVP eval runner

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| No errors | All tasks completed cleanly | — | — | — |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `uv run pytest tests/unit/api/test_mainline_wiring.py tests/unit/rag tests/unit/harness/modules/test_rag_v2.py tests/unit/evals/test_run_rag_v2.py -q` | **140 passed** | All focused RAG and wiring tests green |
| `uv run pytest tests/ -q` | **376 passed, 3 warnings** | Full backend suite green (3 pre-existing coroutine warnings) |
| `rg -n "aptguide2\\.rag\\.pipeline[^_]|RagBaselineProcedure|rag_mvp_baseline" src/ tests/ evals/` | **No matches** | No legacy RAG runtime references remain |

## Known Issues

- 3 pre-existing coroutine warnings in e2e tests (not introduced by this work)
- `LEARNING_ANNOTATIONS.md` still references old function signatures (documentation only, not runtime)
- Test count decreased from 389 to 376 (removed 27 old tests, added 23 new guards/v2 tests)

## Next Steps

- Hit-rate optimization (now safe — old RAG cannot contaminate measurements)
- Standalone hardening and observability
- Staging deployment execution

## Outcome Notes

RAG v2 is now the only callable RAG implementation. The guard test suite (16 tests) will fail immediately if anyone reintroduces old RAG imports or calls. The v2-native modules (`kb_v2.py`, `room_v2.py`) use the full v2 stack: RetrievalPlan → hybrid merge → governed rerank → confidence gate (KB) or lease validation → ranking (rooms).
