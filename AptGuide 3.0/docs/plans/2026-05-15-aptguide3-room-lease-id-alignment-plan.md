# AptGuide 3.0 Room Lease ID Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align `wechat_room_index` room results with lease business room IDs and restore lease validation for room search cards.

**Prerequisite:** Plan (Room Identity Map) must be complete. This plan depends on `RoomIdentityRepository` for verified identity resolution. Lease validation must only be called for identities with `verification_status=verified` and a valid `business_room_id`.

**Architecture:** Milvus recalls candidate rooms, but lease validates business truth. The retrieval path must stop treating synthetic IDs as validated room IDs and must carry both source identity and lease identity. Only `mapped_verified` identities (from `RoomIdentity`) may be passed to the lease validation API.

**Tech Stack:** Python, Milvus, lease internal API, pytest, existing `RoomSearchProcedure`, `VectorClient`, `retrieve_ranked_rooms`, `RoomIdentityRepository`.

---

## Files

- Modify: `backend/src/aptguide3/integrations/vector_client.py`
- Modify: `backend/src/aptguide3/rag/room_retrieval.py`
- Modify: `backend/src/aptguide3/procedures/room_search.py`
- Modify: `backend/src/aptguide3/rag/diagnostics.py`
- Modify: `backend/tests/unit/rag/test_room_retrieval.py`
- Modify: `backend/tests/unit/procedures/test_room_search.py`
- Modify: `backend/evals/datasets/rag_retrieval_cases.yaml`
- Modify: `backend/evals/runners/run_rag_eval.py`
- Read: `docs/system/data-inventory/room-id-alignment.md`
- Read: `docs/system/evidence-contract.md`

## Data Requirements

`search_wechat_rooms()` must return:

```text
wechat_room_id
lease_room_id
source_collection=wechat_room_index
source_record_id
district_name
rent or rent_range
tags
facilities
metro_stations
distance
updated_at when available
```

If `lease_room_id` is missing:

```text
room card may not be marked lease_validated
medium/high-risk production response must not present it as confirmed available
eval should classify it as data_alignment_gap
```

## Tasks

### Task 1: Replace Synthetic ID Assumption With Explicit Source Identity

- [ ] In `backend/src/aptguide3/integrations/vector_client.py`, keep synthetic internal IDs only as temporary UI identity.
- [ ] Add explicit fields to mapped wechat hits:

```python
{
    "wechat_room_id": str(wechat_id),
    "lease_room_id": entity.get("lease_room_id") or entity.get("room_id") or None,
    "source_collection": WECHAT_ROOM_COLLECTION,
    "source_record_id": str(wechat_id),
}
```

- [ ] If Milvus currently lacks `lease_room_id`, record this in diagnostics rather than hiding it.

### Task 2: Restore Lease Validation When Lease ID Exists

- [ ] In `backend/src/aptguide3/rag/room_retrieval.py`, split candidates into:

```text
lease_mappable_candidates  (mapped_verified via RoomIdentityRepository)
wechat_only_candidates     (vector_only or mapped_candidate)
```

- [ ] Use `RoomIdentityRepository.get_by_source()` to resolve each `source_record_id` to a `RoomIdentity`.
- [ ] Only candidates with `evidence_level_for_identity(identity) == "mapped_verified"` may be passed to `lease_client.validate_rooms()`.
- [ ] For candidates with `mapped_verified` identity, use `identity.business_room_id` (not synthetic ID) for lease validation.
- [ ] Candidates without a verified identity (`vector_only` or `mapped_candidate`) may be returned only if the plan explicitly allows demo fallback; otherwise they become a diagnostic gap with `failure_stage=identity_mapping`.

### Task 3: Update Room Cards

- [ ] In `backend/src/aptguide3/procedures/room_search.py`, include evidence fields in every room card:

```text
wechat_room_id
lease_room_id
source_collection
source_record_id
lease_validation_status
evidence_level
matched_query
semantic_score
final_score
```

- [ ] Make card text avoid “可租/可预约/价格有效” unless `lease_validation_status=passed`.

### Task 4: Update Diagnostics

- [ ] Add diagnostic counters:

```text
wechat_hits_without_lease_id_count
lease_validation_requested_count
lease_validated_count
lease_validation_failed_count
demo_fallback_count
```

- [ ] Add failure stages:

```text
room_id_alignment_missing
lease_validation_empty
lease_validation_error
```

### Task 5: Unit Tests

- [ ] Replace `test_wechat_results_bypass_lease_validation` with a test proving validation is called when `lease_room_id` exists.
- [ ] Add test for missing `lease_room_id` producing `room_id_alignment_missing`.
- [ ] Add test for room cards carrying evidence fields.

Run:

```bash
cd backend
uv run pytest tests/unit/rag/test_room_retrieval.py tests/unit/procedures/test_room_search.py -q
```

Expected:

```text
room retrieval and room procedure tests pass
```

### Task 6: Live Verification

Run:

```bash
cd backend
uv run python evals/runners/run_rag_eval.py --live
```

Expected after data alignment:

```text
room cases have lease_validation_requested_count > 0 when lease_room_id exists
returned room cards contain lease validation evidence
unvalidated room count is 0 for production-mode cases
```

If `lease_room_id` is unavailable in source data, expected result is not green production eval. Expected result is a documented `data_alignment_gap` with no false validation claim.
