# Room Identity Field Alignment -- AptGuide 3.0

> Inventory of every identity and metadata field flowing through the room search and KB QA pipelines.
> Status values: `available`, `missing`, `derived`, `unsafe_for_business_validation`

---

## 1. Room Search Pipeline

The live room search path (`room_retrieval.py`) calls `vector_client.search_wechat_rooms()` exclusively. The `search_rooms()` method (against `room_index`) exists but is not called by the current retrieval pipeline.

### 1.1 wechat_room_index (Milvus collection)

| Source | Field | Meaning | Example | Used By | Status |
|---|---|---|---|---|---|
| wechat_room_index | `id` | Wechat platform room identifier (string) | `"wx_room_abc123"` | `_map_wechat_room_results` -> synthetic `room_id` | `available` (as wechat_room_id) |
| wechat_room_index | `district` | District name with suffix | `"番禺区"` | `district_name` | `available` |
| wechat_room_index | `area_label` | Sub-district or neighborhood label | `"万博"` | `apartment_name` (concatenated) | `available` |
| wechat_room_index | `rent_min` | Minimum monthly rent in CNY | `1200` | `rent` | `available` |
| wechat_room_index | `rent_max` | Maximum monthly rent in CNY | `1800` | `rent_range` | `available` |
| wechat_room_index | `tags` | Room feature tags (JSON array) | `["近地铁","独卫"]` | `tags` | `available` |
| wechat_room_index | `metro_stations` | Nearby metro stations (JSON array) | `["万博站"]` | `metro_stations` | `available` |
| wechat_room_index | `facility_tags` | Facility features (JSON array) | `["空调","洗衣机"]` | `facilities` | `available` |
| wechat_room_index | `payment_tags` | Payment option tags (JSON array) | `["月付","押一付一"]` | `payment_types` | `available` |

### 1.2 room_index (Milvus collection -- exists but NOT used by current retrieval)

| Source | Field | Meaning | Example | Used By | Status |
|---|---|---|---|---|---|
| room_index | `id` | Lease system room ID (int) | `10234` | `room_id` | `available` |
| room_index | `title` | Apartment/room display name | `"万博公寓A301"` | `apartment_name` | `available` |
| room_index | `rent` | Monthly rent in CNY | `1500` | `rent` | `available` |
| room_index | `district` | District name with suffix | `"番禺区"` | `district_name` | `available` |
| room_index | `tags` | Room feature tags (JSON array) | `["近地铁"]` | `tags` | `available` |
| room_index | `payment_type` | Payment option (single string) | `"monthly"` | `payment_types` | `available` |
| room_index | `status` | Room availability status | `"available"` | filter only | `available` |

### 1.3 Synthetic ID Generation (vector_client.py line 202)

| Source | Field | Meaning | Example | Used By | Status |
|---|---|---|---|---|---|
| derived | `room_id` | `abs(hash(wechat_id)) % 1000000 + 900000` | `952341` | RoomCandidate, ValidatedRoom, RankedRoom | `derived` |
| derived | `apartment_id` | Hardcoded `0` | `0` | RoomCandidate | `missing` |
| derived | `district_id` | Hardcoded `0` | `0` | ValidatedRoom | `missing` |

### 1.4 Lease Validation Gap (room_retrieval.py lines 87-103)

| Source | Field | Meaning | Example | Used By | Status |
|---|---|---|---|---|---|
| lease API | `lease_room_id` | Lease-system room identifier accepted by `/room/{room_id}` | `10234` | NOT used | `missing` |
| lease API | `lease_validation_status` | Result of lease API lookup | `"passed"/"failed"` | NOT used | `missing` |
| lease API | `availability_status` | Whether room is currently available from lease system | `"available"/"rented"` | NOT used | `missing` |
| lease API | `wechat_room_id` | Original wechat ID before synthetic hashing | `"wx_room_abc123"` | NOT preserved | `missing` |

### 1.5 Missing Critical Fields for Production

| Field | Why Needed | Current State |
|---|---|---|
| `wechat_room_id` | Original wechat ID for cross-reference and dedup | Lost after synthetic hash in `_map_wechat_room_results` |
| `lease_room_id` | Required by lease API `GET /room/{room_id}` for validation | No mapping path exists from wechat_room_id to lease_room_id |
| `lease_validation_status` | Must confirm room exists and is active in lease system | Pipeline skips lease validation entirely for wechat data |
| `availability_status` | Real-time availability from lease system | Not checked |
| `evidence_level` | Contract field indicating confidence tier | Not produced by any pipeline stage |

---

## 2. KB QA Pipeline

### 2.1 apt_rental_kb (Milvus collection)

| Source | Field | Meaning | Example | Used By | Status |
|---|---|---|---|---|---|
| apt_rental_kb | `id` | Chunk identifier (also used as doc_id) | `"lease_001_chunk3"` | `chunk_id`, `doc_id` | `available` |
| apt_rental_kb | `title` | Document or section title | `"退租违约金规则"` | `title` | `available` |
| apt_rental_kb | `category` | Domain module | `"lease"` | `module`, `risk_level` derivation | `available` |
| apt_rental_kb | `content` | Full chunk text | `"退租需提前30天..."` | `content`, `content_snippet` | `available` |
| derived | `distance` | Cosine distance from query | `0.32` | `score` (1 - distance) | `available` |
| derived | `risk_level` | From `_CATEGORY_RISK_LEVEL` map | `"high"` | `risk_level` | `derived` |

### 2.2 Missing KB Fields for Evidence Contract

| Field | Why Needed | Current State |
|---|---|---|
| `evidence_level` | Contract field indicating confidence tier | Not produced; source card has no evidence_level |
| `matched_query` | Which retrieval query matched this source | Available in `KBSource.matched_query` but not in final `_source_card` output |

---

## 3. Key Finding

**The wechat-to-lease ID mapping path does not exist.** The `room_retrieval.py` pipeline:

1. Queries `wechat_room_index` (wechat IDs as strings)
2. Generates a synthetic integer `room_id` via `abs(hash(wechat_id)) % 1000000 + 900000`
3. Passes these synthetic IDs directly into `ValidatedRoom` without calling the lease API
4. The lease API (`GET /room/{room_id}`) expects a lease-system room ID (int), not a synthetic hash

There is no code path that resolves `wechat_room_id` -> `lease_room_id`. The "validated" rooms are actually wechat-only data with no lease system confirmation.
