# Vector Collections -- AptGuide 3.0

Engine: Milvus | Client: `pymilvus.MilvusClient` | Default URI: `http://localhost:19530`

---

## Collection 1: apt_room_vector

Vectorized room listings for semantic search.

### Output Fields (returned by search)

| Field | Type | Notes |
|---|---|---|
| room_id | int | Room identifier |
| apartment_id | int | Parent apartment |
| apartment_name | str | Display name |
| district_id | int | Geographic district |
| district_name | str | District display name |
| rent | float | Monthly rent in CNY |
| payment_types | list[str] | JSON-deserialized; e.g., monthly, quarterly |
| lease_terms | list[str] | JSON-deserialized |
| tags | list[str] | JSON-deserialized |
| facilities | list[str] | JSON-deserialized |
| content_hash | str | SHA-256 hash of source room JSON |
| distance | float | Cosine distance from query vector |

### Filters Supported

- `status == "active"` (always applied)
- `district_id == {id}` (optional)
- `rent <= {max_rent}` (optional)
- `rent >= {min_rent}` (optional)

### Search Parameters

- Metric: COSINE
- ef: 64
- Default top_k: 50

### Chunking Strategy

Each room produces one vector record. The text representation is built by `build_room_vector_text()`:

```raw
[room][{city_name}][{district_name}][{area_label}]
Room {room_number}, in {apartment_name}. Monthly rent {rent}, payment: {payment_types}, lease terms: {lease_terms}.
Layout: {layout}, area: {area}. Tags: {tags}. Facilities: {facilities}.
```

A `content_hash` (SHA-256 of the serialized room dict) enables incremental sync: only rooms whose hash changed need re-embedding.

---

## Collection 2: apt_rental_kb

Knowledge-base chunks for policy/rule Q&A.

### Output Fields (returned by search)

| Field | Type | Notes |
|---|---|---|
| chunk_id | str | Unique chunk identifier |
| doc_id | str | Source document ID |
| title | str | Document or section title |
| module | str | Domain module (e.g., lease, payment, account) |
| content | str | **[SENSITIVE]** -- full chunk text |
| risk_level | str | `low`, `medium`, `high` |
| distance | float | Cosine distance from query vector |

### Chunking Strategy

Each knowledge-base rule produces one chunk. The text representation is built by `build_kb_chunk_text()`:

```raw
[{module}][{doc_type}][{title}][{tags}][{risk_level}]
{content}
```

### Validation Rules

Before a rule can be chunked, `validate_kb_rule()` enforces:

- `doc_id` must be present
- `status` must be one of: `reviewed`, `approved`, `active`
- `reviewed_by` must be present
- High-risk modules (`lease`, `payment`, `account`) must have a `risk_level`
- Content must not match PII patterns (phone numbers, ID cards, bank cards)

---

## Export Rule

**Vectors and full content must NEVER be exported.** Inventory reports may document collection names, field names, row counts, and index configuration only.
