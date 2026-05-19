# Checkpoint: Milestone 6: LangSmith tracing and understanding diagnostics

## Metadata

- Created at: 2026-05-15T18:17:00+08:00
- Task: Milestone 6: LangSmith tracing and understanding diagnostics
- Status: complete
- Test status: 22 unit tests passed, smoke eval passed, live eval 2 passed / 2 failed / 0 errors

## Goal

Add LangSmith tracing and local diagnostic reporting so whole RAG/rec-system eval failures can distinguish raw LLM understanding output, validator-driven `clarify` decisions, recall failures, lease-validation drops, ranking behavior, source-confidence failures, and final response rendering.

## Context

- Plan: `docs/plans/2026-05-15-aptguide3-langsmith-understanding-diagnostics-plan.md`
- Prior milestone: Milestone 5 (Frontend E2E + Live RAG Evaluation)
- All 4 seed eval cases were routing to `clarify` — root cause was ResponseMode Literal validation rejecting LLM's "direct"/"normal" values (fixed in Milestone 5)
- This phase is diagnostic only — no RAG optimization

## Completed Work

1. **Task 1: LangSmith settings** — Added `langsmith_tracing`, `langsmith_project`, `langsmith_endpoint`, `understanding_diagnostics_enabled` to `config.py`. Updated `.env.example`. Added config tests.

2. **Task 2: Opt-in client wrapping** — Added `_maybe_wrap_langsmith()` helper in `deps.py` that wraps OpenAI client only when `langsmith_tracing=True`. Removed always-on wrapping. Added tests.

3. **Task 3: Understanding diagnostic data structures** — Created `understanding/diagnostics.py` with `UnderstandingDiagnostic` dataclass and `sanitize_for_report()`. Added tests.

4. **Task 4: Validator reasons** — Added `validation_failure_reason()` to `validation.py` that returns reason string without changing routing semantics. Added tests.

5. **Task 5: Raw LLM capture** — Modified `LLMUnderstanding` to capture raw LLM JSON, parsed fields, validator reason, final result in `last_diagnostic`. Added tests.

6. **Task 6: Wire diagnostics to deps** — Passed `understanding_diagnostics_enabled` setting to `LLMUnderstanding` constructor.

7. **Task 7: Rec-stage diagnostics** — Created `rag/diagnostics.py` with `RoomRecDiagnostic` and `KbRecDiagnostic`. Instrumented `room_retrieval.py` and `kb_retrieval.py` to populate diagnostic fields. Attached `rec_diagnostic` to procedure metadata. Added tests.

8. **Task 8: Eval report integration** — Modified `run_rag_eval.py` to capture and render understanding + rec diagnostics per case. Fixed eval runner `user_id` null issue.

9. **Task 9: LangSmith verification** — Ran live eval with diagnostics. Verified diagnostic output in report. LangSmith trace visibility cannot be confirmed from CLI but wrapping is functional.

10. **Task 10: Harness state** — Updated `current-plan.md`, `next-steps.md`, verification log, this checkpoint.

## Files Changed

- `backend/src/aptguide3/config.py` — Added 4 new settings fields
- `backend/.env.example` — Added LangSmith and diagnostic env var docs
- `backend/src/aptguide3/api/deps.py` — Added `_maybe_wrap_langsmith()`, passed `diagnostics_enabled` to LLMUnderstanding
- `backend/src/aptguide3/understanding/diagnostics.py` — NEW: UnderstandingDiagnostic dataclass
- `backend/src/aptguide3/understanding/validation.py` — Added `validation_failure_reason()`
- `backend/src/aptguide3/understanding/llm_understanding.py` — Added diagnostic capture
- `backend/src/aptguide3/rag/diagnostics.py` — NEW: RoomRecDiagnostic, KbRecDiagnostic
- `backend/src/aptguide3/rag/room_retrieval.py` — Added diagnostic parameter and population
- `backend/src/aptguide3/rag/kb_retrieval.py` — Added diagnostic parameter and population
- `backend/src/aptguide3/procedures/room_search.py` — Attach rec_diagnostic to metadata
- `backend/src/aptguide3/procedures/kb_qa.py` — Attach rec_diagnostic to metadata
- `backend/evals/runners/run_rag_eval.py` — Capture and render diagnostics, fix user_id
- `backend/tests/unit/test_config.py` — Added LangSmith config tests
- `backend/tests/unit/api/test_langsmith_config.py` — NEW: wrapper opt-in tests
- `backend/tests/unit/understanding/test_diagnostics.py` — NEW: sanitization tests
- `backend/tests/unit/understanding/test_validation.py` — Added validation_failure_reason tests
- `backend/tests/unit/understanding/test_llm_understanding.py` — Added diagnostic capture tests
- `backend/tests/unit/rag/test_rec_diagnostics.py` — NEW: rec diagnostic tests
- `docs/tests/verification-log.md` — Appended Milestone 6 verification
- `docs/plans/current-plan.md` — Updated to Milestone 6 complete
- `docs/plans/next-steps.md` — Updated next decision point

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| 2026-05-15 18:14 | Live eval: 4 errors — Column 'user_id' cannot be null | Eval runner creates ConversationFrame without user_id, MySQL requires it | Added `user_id="eval-runner"` to eval frame | fixed |
| 2026-05-15 18:15 | Live eval: room_search failure_stage=vector_recall_empty | Milvus collection `apt_room_vector` does not exist | Data issue, not code issue — need to sync vectors | deferred |
| 2026-05-15 18:15 | Live eval: kb_qa failure_stage=kb_vector_recall_empty | Vector hits=40 but chunk_id metadata missing, deduplicated to 0 | Data issue — need to sync KB vectors with chunk_id metadata | deferred |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `uv run pytest tests/unit/test_config.py tests/unit/understanding/ tests/unit/api/test_langsmith_config.py tests/unit/rag/test_rec_diagnostics.py -q` | 22 passed | All unit tests pass |
| `uv run python evals/runners/run_rag_eval.py` | Smoke report generated | 4 cases, N/A metrics |
| `uv run python evals/runners/run_rag_eval.py --live` | 2 passed, 2 failed, 0 errors | Diagnostics visible in report |
| `uv run ruff check src tests` | All checks passed | Clean |

## Known Issues

- Milvus collections not populated (room vectors and KB vectors need syncing)
- 35 pre-existing asyncio runner failures in full test suite
- LangSmith trace visibility cannot be confirmed from CLI (requires web UI check)

## Next Steps

1. Sync room and KB vectors to Milvus
2. Re-run live RAG eval with populated vectors
3. Use diagnostic output to classify each failure root cause
4. Plan RAG optimization based on failure classification

## Outcome Notes

- Milestone 6 demonstrates a diagnostic-first approach: instrument the pipeline before optimizing
- The 4 seed eval cases now correctly reach the RAG pipeline (no longer stuck in `clarify`)
- Understanding diagnostics cleanly separate LLM intent parsing from validator routing decisions
- Rec-stage diagnostics pinpoint exactly where in the pipeline each query fails
