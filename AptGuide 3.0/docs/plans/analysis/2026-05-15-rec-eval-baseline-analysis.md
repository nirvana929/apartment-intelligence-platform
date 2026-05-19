# Rec Eval Baseline Analysis

Generated: 2026-05-15

## Executive Summary

All 4 seed eval cases correctly route through the RAG pipeline (understanding works), but **all failures are caused by data issues, not code issues**. The first optimization target should be **data sync** — fixing Milvus collection names and field schemas.

## Data Health

### Milvus

| Expected Collection | Actual Collection | Status |
|---|---|---|
| `apt_room_vector` | `room_index` (150 entities) | **Name mismatch** — code expects `apt_room_vector` |
| `apt_rental_kb` | `apt_rental_kb` (70 entities) | Exists but **missing required fields** |

**Room vector problem:** Code calls `search_rooms()` which does `load_collection("apt_room_vector")`, but the actual collection is named `room_index`. This causes `collection not found` error for every room search.

**KB vector problem:** `apt_rental_kb` exists with 70 entities, but its fields are:
- `id`, `content`, `vector`, `category`, `title`

Code expects:
- `chunk_id`, `doc_id`, `title`, `module`, `content`, `risk_level`

The missing `chunk_id` field means deduplication in `kb_retrieval.py` cannot work — all 40 hits get deduplicated to 0 because `chunk_id` is always empty string.

### MySQL

Status: `error` — needs `cryptography` package for sha256_password auth. Not blocking eval since chat_service uses in-memory repos as fallback.

### Redis

Status: `empty` (0 keys). Not blocking eval.

## Eval Failure Classification

| Case ID | Task | Phase | Status | Failure Owner | Evidence |
|---|---|---|---|---|---|
| `room-panyu-quiet-001` | room_search | room_search | PASS | data_inventory | `apt_room_vector` collection not found, vector_recall_empty |
| `room-tianhe-nearby-001` | room_search | room_search | PASS | data_inventory | `apt_room_vector` collection not found, vector_recall_empty |
| `kb-lease-deposit-001` | kb_qa | kb_qa | FAIL | data_inventory | vector_hits=40 but chunk_id missing, unique_chunk_count=0 |
| `kb-payment-refund-001` | kb_qa | kb_qa | FAIL | data_inventory | vector_hits=40 but chunk_id missing, unique_chunk_count=0 |

**All 4 cases: failure_owner = data_inventory**

No cases failed due to:
- understanding (all parsed correctly with confidence 0.9-0.95)
- lease_validation (never reached)
- ranking (never reached)
- confidence_gate (never reached)
- response_rendering (never reached)
- dataset_label_gap (secondary issue — expected_ids empty in dataset)

## Understanding Diagnostic Summary

All 4 cases show clean understanding:
- `parsed_route=rag`, `parsed_task=room_search` or `kb_qa`
- `parsed_confidence=0.9-0.95`
- `validator_reason=""` (no validation failures)
- `final_route` matches `parsed_route`

The understanding module works correctly. No prompt tuning needed.

## Recommended Optimization Target

**Primary: Data sync / Milvus collection alignment**

1. **Fix room vector collection name**: Either rename `room_index` to `apt_room_vector` in Milvus, or update `vector_client.py` to use `room_index`. The sync script `scripts/sync_room_vectors.py` should create the correct collection.

2. **Fix KB vector metadata schema**: Re-sync KB vectors with `chunk_id`, `doc_id`, `module`, `risk_level` fields. The sync script `scripts/sync_kb_vectors.py` should populate these fields from the source data.

3. **Re-run baseline eval** after data sync to get real retrieval metrics.

**Secondary: Dataset labels**

- Add `expected_room_ids` and `expected_doc_ids` to eval cases so Hit@K can be computed.

**Not recommended yet:**
- Understanding prompt tuning (understanding works correctly)
- Ranking optimization (never reached — no data to rank)
- Confidence gate tuning (never reached)

## Next Steps

1. Run `scripts/sync_room_vectors.py` to create `apt_room_vector` collection with proper schema
2. Run `scripts/sync_kb_vectors.py` to re-sync KB vectors with `chunk_id` metadata
3. Re-run live eval: `uv run python evals/runners/run_rag_eval.py --live`
4. Analyze real retrieval quality (Hit@K, ranking, confidence)
5. Only then plan retrieval/ranking optimization
