# Checkpoint: WeChat data pipeline + live RAG re-evaluation

## Metadata

- Created at: 2026-05-15T21:57:50+08:00
- Task: WeChat data pipeline + live RAG re-evaluation
- Status: complete
- Test status: 7 unit tests passed, 4 live eval passed/0 failed/0 errors

## Goal

Verify the WeChat data pipeline works end-to-end after switching room_retrieval.py to use wechat_room_index instead of room_index, and report live RAG evaluation metrics.

## Context

Previous session completed Milestone 7 with live eval showing 2/4 passed — both room_search cases failed with `failure_stage=vector_recall_empty` because Milvus collection `apt_room_vector` didn't exist. The fix was to:
1. Add `wechat_room_index` collection to Milvus (44 rows, dim=1024)
2. Switch `room_retrieval.py` to use `search_wechat_rooms()` instead of `search_rooms()`
3. Skip lease validation for wechat data (no lease room_id mapping)
4. Update test stubs with both `search_rooms` and `search_wechat_rooms` methods

## Completed Work

- Room retrieval unit tests: 7/7 passed (including new `test_wechat_results_bypass_lease_validation`)
- Live RAG evaluation: 4/4 passed
  - Room search: 2/2 — wechat data returns real rooms with scores
  - KB QA: 2/2 — confidence gate working correctly
- Updated verification-log.md with new test results
- Updated evaluation-report.md with detailed metrics

## Files Changed

- `backend/src/aptguide3/rag/room_retrieval.py` — uses `search_wechat_rooms()`, bypasses lease validation
- `backend/src/aptguide3/integrations/vector_client.py` — added `WECHAT_ROOM_COLLECTION`, `search_wechat_rooms()`, `_normalize_district()`, `_map_wechat_room_results()`
- `backend/tests/unit/rag/test_room_retrieval.py` — added `search_wechat_rooms` to StubVector, new test for wechat bypass
- `docs/tests/verification-log.md` — added verification entry
- `docs/tests/evaluation-report.md` — added evaluation metrics

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| Previous session | room_search failure_stage=vector_recall_empty | Milvus collection `apt_room_vector` missing | Use `wechat_room_index` (44 rows) | RESOLVED |
| Previous session | Lease validation expects room_id from lease DB | Wechat data has no lease room_id | Bypass lease validation, build ValidatedRoom directly | RESOLVED |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `uv run pytest tests/unit/rag/test_room_retrieval.py -v` | 7 passed | All room retrieval tests green |
| `uv run python evals/runners/run_rag_eval.py --live` | 4 passed, 0 failed, 0 errors | avg=11891ms, p95=20545ms |

## Known Issues

- `expected_room_ids` empty for room_search cases → Hit@K/MRR/nDCG cannot be computed
- `expected_doc_ids` empty for 1 KB QA case
- KB confidence gate may be too aggressive (blocks medium-risk queries with many sources)
- Avg latency 11.9s is high — embedding + LLM calls are the bottleneck

## Next Steps

1. Add expected room/doc IDs to eval dataset for proper Hit@K/MRR/nDCG measurement
2. Investigate KB confidence gate threshold (may be blocking valid answers)
3. Optimize latency (parallel embedding calls, caching)
4. Consider adding more wechat data rows (currently only 44)

## Outcome Notes

The wechat data pipeline is fully operational. Room search now returns real results from 44 wechat listings. The RAG pipeline correctly handles: LLM understanding → semantic query generation → vector recall → ranking → confidence gating. All 4 eval cases pass with correct routing and reasonable scores.
