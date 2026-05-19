# Evidence Contract -- AptGuide 3.0

> Every result returned to the user must carry an evidence level that indicates how well-grounded it is. This document defines the contract for room search and KB QA pipelines.

---

## 1. Evidence Levels

| Level | Meaning | When Used |
|---|---|---|
| `vector_only` | Result came from vector similarity search only; no external validation | Initial recall, before any validation step |
| `source_grounded` | Result is grounded in a specific document/chunk with traceable chunk_id and doc_id | KB QA answers with confirmed source retrieval |
| `lease_validated` | Room existence and status confirmed via lease system API | Room cards that passed lease API validation |
| `lease_validated_with_freshness` | Room confirmed via lease API with freshness guarantee (checked within defined TTL) | Future: room cards with time-bounded lease cache |
| `conservative_fallback` | System declined to answer with high confidence; returned a safe fallback message | Confidence check failure, missing evidence, risk escalation |

---

## 2. Evidence Level Assignment Rules

### 2.1 Room Search Pipeline

| Pipeline Stage | Evidence Level | Notes |
|---|---|---|
| After vector recall (`search_wechat_rooms`) | `vector_only` | No lease validation yet |
| After lease API validation passes | `lease_validated` | Room confirmed in lease system |
| After lease API validation with freshness check | `lease_validated_with_freshness` | Future: TTL-based freshness |
| Lease API call fails or room not found | `conservative_fallback` | Cannot confirm room exists |

### 2.2 KB QA Pipeline

| Pipeline Stage | Evidence Level | Notes |
|---|---|---|
| After vector recall (`search_kb`) | `vector_only` | Sources retrieved but not yet checked |
| After confidence check passes with citations | `source_grounded` | At least one chunk_id/doc_id pair is present |
| Confidence check fails or no sources | `conservative_fallback` | System returns safe fallback message |

---

## 3. Risk Level Rules

### 3.1 Risk Level Derivation

Risk levels are derived from the domain module/category:

| Module | Risk Level |
|---|---|
| `lease` | `high` |
| `payment` | `high` |
| `account` | `high` |
| `appointment` | `medium` |
| `policy` | `medium` |
| `life` | `low` |
| `room_search` | `low` |

### 3.2 Core Rule

**Medium/high-risk output MUST NOT use `vector_only` as its final evidence level.**

If the pipeline cannot upgrade from `vector_only` to a validated level, it must return `conservative_fallback` instead of presenting unvalidated data as a final answer.

---

## 4. Room Search Acceptance Criteria

### 4.1 Required Room Card Fields

Every room card returned to the user MUST contain:

```
wechat_room_id          -- Original wechat platform ID (string)
lease_room_id           -- Lease system room ID (int), or null if not yet mapped
lease_validation_status -- "passed" | "failed" | "not_checked"
evidence_level          -- One of the defined evidence levels
```

### 4.2 Additional Recommended Fields

```
room_card.type          -- "room_card" (discriminator)
source_collection       -- "wechat_room_index" | "room_index"
district_name           -- District name
rent or rent_range      -- Price information
matched_query           -- Which user query matched this room
semantic_score          -- Vector similarity score
final_score             -- Combined ranking score
availability_status     -- From lease system, if available
```

### 4.3 Production Gate

- Room cards MUST be `lease_validated` (or `lease_validated_with_freshness`) before production use.
- Wechat-only cards (`vector_only` or `source_grounded`) may be used ONLY when metadata explicitly marks them as non-lease-validated demo data.
- `conservative_fallback` room cards must not be shown as search results.

---

## 5. KB QA Acceptance Criteria

### 5.1 Required Source Card Fields

Every KB source card returned to the user MUST contain:

```
chunk_id                -- Unique chunk identifier
doc_id                  -- Source document ID
title                   -- Document or section title
module                  -- Domain module (e.g., lease, payment)
score                   -- Relevance score (1 - cosine_distance)
risk_level              -- Derived from module
evidence_level          -- One of the defined evidence levels
```

### 5.2 Final Answer Metadata

Every KB QA final answer MUST carry:

```
risk_level              -- Highest risk level among cited sources
confidence_passed       -- Boolean, whether confidence check passed
evidence_count          -- Number of sources backing the answer
grounded_answer         -- Boolean, whether answer text is grounded in citations
citations               -- List of chunk_id/doc_id pairs
fallback_reason         -- If conservative_fallback, why (null otherwise)
```

### 5.3 Production Gate

- Medium/high-risk final answers MUST cite at least one `chunk_id`/`doc_id` pair.
- If citations are insufficient, the answer MUST use `conservative_fallback` with an explanation.
- `vector_only` is NOT an acceptable final evidence level for medium/high-risk answers.

---

## 6. Enforcement

These rules are enforced at two levels:

1. **Shape tests** (`backend/tests/unit/rag/test_evidence_contract.py`): Verify that data structures carry the required fields and that `vector_only` is rejected for medium/high-risk outputs.
2. **Runtime checks** (future): Confidence module and validation pipeline will reject non-conforming results before they reach the user.

---

## 7. Current Gaps

| Gap | Impact | Plan |
|---|---|---|
| No `wechat_room_id -> lease_room_id` mapping | Room cards cannot be lease-validated | Plan 2: room-lease-id-alignment |
| `evidence_level` not produced by any pipeline | Contract cannot be checked at runtime | Plan 3: grounded-risk-answer |
| KB final answer not generated from evidence | Only source cards returned, no grounded answer | Plan 3: grounded-risk-answer |
| No `matched_query` in KB source card output | Cannot trace which query matched which source | Minor: add to `_source_card` |
