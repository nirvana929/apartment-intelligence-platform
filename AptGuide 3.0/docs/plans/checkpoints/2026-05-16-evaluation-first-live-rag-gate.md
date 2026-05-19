# Checkpoint: evaluation-first live RAG gate

## Metadata
- Created at: 2026-05-16
- Task: Execute evaluation-first live RAG gate plan
- Status: PARTIAL PASS
- Test status: 44 eval runner tests passed, 147 focused RAG/procedure tests passed, smoke eval clean

## Completed Work

- Task 1: Project harness snapshot — confirmed project state, branch, and state files.
- Task 2: Preflight verification — smoke eval (9 cases), eval runner unit tests (44 passed), RAG/procedure tests (147 passed).
- Task 3: Live dependency readiness — all env vars SET (LLM, embedding, vector_uri, lease, MySQL, Redis, persistence_mode=hybrid). Integration tests 6/6 skipped (live services not running in test context).
- Task 4: Live RAG evaluation — `run_rag_eval.py --live` completed: 4 passed, 5 failed, 0 errors.
- Task 5: Findings interpreted and classified into 3 owners.
- Task 6: Evaluation reports updated (docs/tests/evaluation-report.md, reports/evaluation-report.md).

## Verification

- Smoke eval: 9 cases, no import errors, schema validation clean.
- Eval runner unit tests: 44 passed (0.08s).
- RAG + KB + room search tests: 147 passed (0.26s).
- Live RAG eval: 4/9 passed, 5/9 failed, 0 errors.
- KB QA: Hit@3=100%, high-risk citation=100%, unverified_commitment=0%.
- Room search: 5/5 returning cards from live Milvus, but all classified as dataset_gap.
- Latency: avg=9166ms, p95=18220ms.

## Findings

| Priority | Finding | Owner | Evidence | Next action |
|----------|---------|-------|----------|-------------|
| P0 | Room search expected_room_ids empty — cannot measure retrieval quality | dataset_gap | 5 room_search cases with empty expected_ids | Expand dataset with expected room IDs for known seeded rooms |
| P1 | Lease validation never triggered for room cards | identity_mapping | lease_validation_requested=0 across all room cases | Populate RoomIdentityRepository with wechat→lease ID mappings |
| P2 | Trace output visibility 0% | trace_visibility | trace_output_visibility_rate=0/9 | Enable langsmith_tracing or implement local trace recording |

## Known Issues

- Room search dataset has no expected_room_ids — Hit@5/MRR/nDCG cannot be computed.
- Wechat room data uses synthetic IDs without lease mapping — lease validation cannot trigger.
- LangSmith tracing disabled by default — trace visibility rate always 0%.
- Latency ~9s average — embedding + LLM bottleneck.
- 35 pre-existing asyncio runner failures in full suite (not regressions).

## Next Steps

1. Expand `backend/evals/datasets/rag_retrieval_cases.yaml` with `expected_room_ids` for room_search cases.
2. Populate `RoomIdentityRepository` with real `wechat_room_id -> canonical_room_id -> lease_room_id` mappings.
3. Re-run live RAG eval to verify room search quality becomes measurable.
4. If room search quality passes gate, move to main-chain integration: `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`.
