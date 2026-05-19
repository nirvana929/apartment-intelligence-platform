# AptGuide 3.0 Data Evidence Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define the exact evidence contract for room search and KB QA before changing retrieval behavior.

**Architecture:** Inventory all IDs and metadata at the system boundaries, then codify what every medium/high-risk result must carry. This plan is documentation plus diagnostic scripts/tests; it does not change ranking or answer generation.

**Tech Stack:** Python, pytest, Milvus client, SQLAlchemy/MySQL, lease internal API, markdown docs.

---

## Files

- Create: `docs/system/evidence-contract.md`
- Create: `docs/system/data-inventory/room-id-alignment.md`
- Create: `backend/tests/unit/rag/test_evidence_contract.py`
- Modify: `docs/plans/current-plan.md`
- Modify: `docs/plans/known-issues.md`
- Read: `backend/src/aptguide3/integrations/vector_client.py`
- Read: `backend/src/aptguide3/rag/room_retrieval.py`
- Read: `backend/src/aptguide3/procedures/kb_qa.py`
- Read: `backend/evals/reports/rag-evaluation-report.md`

## Required Evidence Contract

Room card evidence must include:

```text
room_card.type=room_card
wechat_room_id
lease_room_id
source_collection
source_record_id
district_name
rent or rent_range
matched_query
semantic_score
final_score
lease_validation_status
lease_validation_checked_at
availability_status
evidence_level
```

KB source evidence must include:

```text
kb_source.type=kb_source
chunk_id
doc_id
title
module
content_snippet
score
risk_level
matched_query
evidence_level
```

Final answer metadata must include:

```text
risk_level
confidence_passed
evidence_count
grounded_answer
citations
fallback_reason
```

## Tasks

### Task 1: Inventory Current Room Identity Fields

- [ ] Inspect MySQL/wechat room tables and record available fields in `docs/system/data-inventory/room-id-alignment.md`.
- [ ] Inspect `wechat_room_index` output fields through Milvus and record whether it has `id`, `lease_room_id`, `room_id`, `house_id`, `apartment_id`, `updated_at`, `district`, `rent_min`, `rent_max`.
- [ ] Inspect lease validation API requirements and record the exact ID type it accepts.
- [ ] Mark each field as one of: `available`, `missing`, `derived`, `unsafe_for_business_validation`.

Acceptance:

```text
docs/system/data-inventory/room-id-alignment.md contains a table mapping:
source -> field -> meaning -> example -> used_by -> status
```

### Task 2: Write Evidence Contract Doc

- [ ] Create `docs/system/evidence-contract.md`.
- [ ] Define `evidence_level` values:

```text
vector_only
source_grounded
lease_validated
lease_validated_with_freshness
conservative_fallback
```

- [ ] Define the rule:

```text
medium/high-risk output cannot use vector_only as final evidence.
```

- [ ] Define room search acceptance:

```text
Returned room cards must be lease_validated before production use.
Wechat-only cards may be used only when metadata marks them as non-lease-validated demo data.
```

- [ ] Define KB QA acceptance:

```text
Returned final answer must cite chunk_id/doc_id for medium/high-risk answers.
If citations are insufficient, answer must use conservative fallback.
```

### Task 3: Add Contract Shape Tests

- [ ] Create `backend/tests/unit/rag/test_evidence_contract.py`.
- [ ] Add tests for required room evidence keys.
- [ ] Add tests for required KB evidence keys.
- [ ] Add tests that `vector_only` is rejected for medium/high-risk final evidence.

Suggested test names:

```python
def test_room_evidence_contract_requires_business_identity():
    required = {"wechat_room_id", "lease_room_id", "lease_validation_status", "evidence_level"}
    card = {"wechat_room_id": "wx-1", "lease_room_id": 101, "lease_validation_status": "passed", "evidence_level": "lease_validated"}
    assert required <= set(card)


def test_high_risk_cannot_use_vector_only_evidence():
    risk_level = "high"
    evidence_level = "vector_only"
    assert not (risk_level in {"medium", "high"} and evidence_level == "vector_only")
```

### Task 4: Verification

Run:

```bash
cd backend
uv run pytest tests/unit/rag/test_evidence_contract.py -q
```

Expected:

```text
all evidence contract tests pass
```

### Task 5: Update Harness-Facing Progress

- [ ] Update `docs/plans/current-plan.md` to point next work at Plan 2 after this contract is complete.
- [ ] Update `docs/plans/known-issues.md` so the active issue is not generic “Milvus data missing”; it should be “room search lacks confirmed wechat-to-lease ID validation path” if still true.

