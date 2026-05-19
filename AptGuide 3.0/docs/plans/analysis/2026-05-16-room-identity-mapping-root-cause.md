# Room Identity Mapping Root Cause Analysis

Date: 2026-05-16

## Symptom

Live room-search RAG returned room cards, but every card stayed `vector_only`:

- `lease_validation_requested_count=0`
- `lease_validated_count=0`
- `aptguide3_room_identity_map` had 0 rows
- returned `wechat_room_id` values had no `lease_room_id`

This made the room gate fail regardless of Hit@K tuning.

## Confirmed Evidence

- `wechat_room_index` fields are only source listing fields:
  `id`, `content`, `district`, `area_label`, `rent_min`, `rent_max`, `tags`,
  `metro_stations`, `facility_tags`, `payment_tags`, `vector`.
- `wechat_room_index` does not contain `lease_room_id`, `room_id`,
  `house_id`, or `apartment_id`.
- live source IDs look like `wechat-001`, `wechat-002`, etc.
- `aptguide3_room_identity_map` exists but currently has 0 rows.
- local lease DB has real lease rooms and `/internal/ai/tools/room/search`
  can validate real lease IDs such as `15`, `44`, `49`, `50`, and `200079`.

## Root Causes

### 1. Validation Client Silently Dropped Valid Lease Responses

`LeaseClient.validate_rooms()` parsed the lease response correctly, then called
`_to_snake(r)` for each returned room dict. `_to_snake()` is a string helper,
so passing a dict raised a `TypeError`. The broad exception handler swallowed
the error and returned `[]`.

Impact: even a correct `wechat_room_id -> lease_room_id` mapping would not have
produced `lease_validated` rooms.

Fix: use `_to_snake_dict(r)` for returned room dicts.

### 2. WeChat Vector Records Have No Business Identity

`wechat_room_index.id` is a source listing ID, not a lease room ID. The current
pipeline correctly preserves it as `source_record_id`, but no automatic mapping
source exists in the live data.

Impact: `RoomIdentityRepository.get_by_source("wechat", source_record_id)`
returns `None`, so candidates are correctly downgraded to `vector_only`.

### 3. Synthetic WeChat Room IDs Were Process-Random

`_map_wechat_room_results()` used Python's built-in `hash(wechat_id)` to create
temporary integer room IDs. Python salts `hash()` per process, so the same
`wechat-001` could produce different `room_id` values in different eval runs.

Impact: `expected_room_ids` generated from one run could not reliably match a
later run, making mapping and retrieval diagnosis noisy.

Fix: derive synthetic IDs with a deterministic SHA-256 prefix.

### 4. `room_index` Is Lease-Shaped But Stale Relative To Live Lease DB

Milvus `room_index` currently contains IDs like `3001`, but the live lease DB
does not have those room IDs. The DB has valid room ranges including `2..51`
and `200001..200119`.

Impact: switching blindly from `wechat_room_index` to `room_index` would still
fail lease validation until `room_index` is rebuilt from current lease data.

## What Is Fixed Now

- Lease validation client now returns valid snake_case room records.
- WeChat synthetic room IDs are deterministic.
- Room eval expected IDs and candidate report were updated to the deterministic
  synthetic IDs for the same `wechat_room_id` values.
- Local eval mapping seed added at
  `backend/evals/datasets/local_room_identity_mappings.csv`.

The local seed uses `match_method=local_eval_seed`. It is only for local/test
RAG gate execution and must not be treated as production identity proof.

## Remaining Data Requirement

No code can honestly mark WeChat listings as `lease_validated` until one of
these is true:

1. `aptguide3_room_identity_map` is populated with verified
   `source_system=wechat`, `source_record_id=wechat-*`,
   `business_room_id=<lease room id>` rows.
2. `wechat_room_index` is rebuilt to include a verified `lease_room_id` field.
3. room search uses a refreshed lease-native `room_index` as the production
   source, with WeChat listings kept as unverified leads.

Until then, returning WeChat cards as `vector_only` is the correct behavior.
