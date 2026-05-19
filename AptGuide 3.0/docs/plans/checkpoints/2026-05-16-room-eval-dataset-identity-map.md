# Checkpoint: room eval dataset and identity map

## Metadata
- Created at: 2026-05-16
- Task: Room eval dataset + identity map implementation
- Status: PARTIAL PASS (P0 resolved, new P1.5 discovered)
- Test status: 189 passed (3 new: room identity repo, 2 new: import script, 44 eval runner, 140 existing RAG/procedure)

## Completed Work

- Task 1: `aptguide3_room_identity_map` table + `RoomIdentityMapRecord` model created
- Task 2: `MySqlRoomIdentityRepository` implementing `get_by_source()` and `upsert_mapping()`
- Task 3: `RepoBundle.room_identity_repo` wired in memory/mysql/hybrid modes, passed to `RoomSearchProcedure`
- Task 4: `scripts/import_room_identity_mappings.py` with CSV parser + unit tests
- Task 5: `scripts/export_room_eval_candidates.py` with live RAG export
- Task 6: `rag_retrieval_cases.yaml` updated with non-empty `expected_room_ids` for all 5 room cases
- Task 7: Deferred — no verified wechat→lease ID mappings available yet
- Task 8: Live RAG eval re-run: 4/9 passed, 5/9 failed (failure_owner upgraded: dataset_gap → vector_recall)

## Verification

- Model import: `RoomIdentityMapRecord.__tablename__` = `aptguide3_room_identity_map`
- MySQL schema: table applied to `least` database
- MySQL repo tests: 3 passed (upsert, missing lookup, overwrite)
- Import script tests: 2 passed (valid CSV, missing columns)
- Eval runner tests: 44 passed
- RAG/procedure tests: 140 passed
- Live RAG eval: 4/9 passed, 5/9 failed, 0 errors
- KB QA: Hit@3=100%, all high-risk criteria pass
- Room search: Hit@5=False for all cases (failure_owner=vector_recall)

## Findings

| Priority | Finding | Owner | Status |
|----------|---------|-------|--------|
| P0 | expected_room_ids empty | dataset_gap | RESOLVED |
| P1 | Lease validation never triggered | identity_mapping | Active — need wechat→lease mappings |
| P1.5 | Room search results non-deterministic | vector_recall | NEW — LLM generates different queries each run |
| P2 | Trace visibility 0% | trace_visibility | Deferred |

## Known Issues

- Room search results are non-deterministic: LLM generates different semantic queries each run, returning different rooms. Expected IDs from one run don't match subsequent runs.
- No verified wechat→lease ID mappings exist yet — lease validation still cannot trigger.
- `room_identity_map` table exists but is empty — needs data import.

## Next Steps

1. Decide on room search evaluation strategy for non-deterministic results (relax Hit@K, use overlap metrics, or fix seed queries).
2. Populate `aptguide3_room_identity_map` with real wechat→lease ID mappings when available.
3. If room search quality remains poor after deterministic evaluation, create retrieval optimization plan.
