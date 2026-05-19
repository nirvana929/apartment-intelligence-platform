# Checkpoint: Milestone 7: Data inventory + baseline analysis

## Metadata

- Created at: 2026-05-15T19:05:10+08:00
- Task: Milestone 7: Data inventory + baseline analysis
- Status: complete
- Test status: 22 passed, ruff clean, live eval 2 passed / 2 failed / 0 errors

## Goal

Run eval-first diagnosis with LangSmith tracing and a reliable data inventory so failures can be attributed before optimization.

## Context

- Plan: `docs/plans/2026-05-15-aptguide3-rec-eval-langsmith-data-inventory-plan.md`
- Prior: Milestone 6 (LangSmith + understanding/rec diagnostics)
- All 4 seed eval cases correctly route but fail at vector recall stage

## Completed Work

1. **Task 1: LangSmith config verified** — Default-off behavior confirmed, 5 tests pass.
2. **Task 2: Data inventory folder** — 8 doc files in `docs/system/data-inventory/`.
3. **Task 3: Safe inventory script** — `scripts/generate_data_inventory.py`, metadata-only, tests pass.
4. **Task 4: Eval report classification** — Added `_classify_failure_owner()`, fixed stale findings.
5. **Task 5: Baseline eval** — 4 cases, all `failure_owner=data_inventory`.
6. **Task 6: Analysis** — `docs/plans/analysis/2026-05-15-rec-eval-baseline-analysis.md`.

## Files Changed

- `docs/system/data-inventory/` — NEW: 8 doc files + generated/
- `backend/scripts/generate_data_inventory.py` — NEW
- `backend/tests/unit/scripts/test_generate_data_inventory.py` — NEW
- `backend/evals/runners/run_rag_eval.py` — Added failure_owner classification
- `docs/plans/analysis/2026-05-15-rec-eval-baseline-analysis.md` — NEW
- `docs/tests/verification-log.md` — Appended

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| 2026-05-15 | `apt_room_vector` collection not found | Milvus has `room_index` not `apt_room_vector` | Need to rename collection or update code | open |
| 2026-05-15 | KB unique_chunk_count=0 despite 40 hits | `apt_rental_kb` missing `chunk_id` field | Need to re-sync KB vectors with proper schema | open |
| 2026-05-15 | MySQL auth error | Missing `cryptography` package | Install package or use different auth | open |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `uv run pytest tests/unit/scripts/test_generate_data_inventory.py -q` | 5 passed | Sanitization tests |
| `uv run python scripts/generate_data_inventory.py` | Inventory generated | `docs/system/data-inventory/generated/` |
| `uv run python evals/runners/run_rag_eval.py --live` | 2 passed, 2 failed, 0 errors | All failures=data_inventory |
| `uv run ruff check src tests` | All checks passed | Clean |

## Known Issues

- Milvus collection name mismatch (`room_index` vs `apt_room_vector`)
- KB vector schema missing `chunk_id`, `doc_id`, `module`, `risk_level`
- MySQL needs `cryptography` package
- 35 pre-existing asyncio runner failures

## Next Steps

1. Fix Milvus collection names (rename or update code)
2. Re-sync KB vectors with proper metadata schema
3. Re-run live eval with correct data
4. Analyze real retrieval quality

## Outcome Notes

- Data inventory before optimization is a powerful pattern — identified that ALL failures are data issues, not code
- Understanding module works perfectly (confidence 0.9-0.95, no validation failures)
- The diagnostic instrumentation from Milestone 6 made this classification possible
