# AptGuide 3.0 Room Identity Map Prerequisite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce an enterprise-style room identity mapping layer before room lease validation, grounded risk answers, and comprehensive RAG evaluation depend on room IDs.

**Architecture:** Database primary keys may remain internal random/autoincrement IDs. The important requirement is that each room record preserves source identity and, when available, a verified pointer to the lease business room identity. Milvus remains a recall index; MySQL stores identity mapping and verification state; lease API remains the business truth for availability, price validity, and appointmentability.

**Tech Stack:** Python 3.12, SQLAlchemy/MySQL, Milvus, lease internal API, pytest, existing AptGuide 3.0 repository and RAG modules.

---

## Why This Plan Blocks Plan 2, Plan 3, And Plan 5

Plan 1 and Plan 4 are complete, and they exposed a production blocker:

```text
wechat-to-lease ID mapping path does not exist.
room_retrieval.py uses a hash-generated synthetic ID.
the original wechat_room_id is discarded in the retrieval path.
```

This does not mean database primary keys must be replaced. Internal database IDs can stay as they are. The missing piece is a stable business identity pointer:

```text
internal_db_id      can be random/autoincrement; used only inside the DB
source_record_id    original wechat_room_id; must be preserved
canonical_room_id   AptGuide internal normalized room entity ID
business_room_id    lease_room_id; used for lease validation
```

This plan must finish before:

- Plan 2, because lease validation must use verified `business_room_id`, not synthetic IDs.
- Plan 3, because medium/high-risk room answers must not cite synthetic IDs as business evidence.
- Plan 5, because full RAG evaluation cannot score `lease_validation_pass_rate`, `invalid_room_rate`, or production-grade room correctness without verified identity mapping.

## Files

- Create: `backend/src/aptguide3/database/room_identity_schema.sql`
- Create: `backend/src/aptguide3/persistence/room_identity_repo.py`
- Create: `backend/src/aptguide3/rag/room_identity.py`
- Create: `backend/scripts/inspect_room_identity_sources.py`
- Create: `backend/tests/unit/rag/test_room_identity.py`
- Create: `backend/tests/unit/persistence/test_room_identity_repo.py`
- Modify: `backend/src/aptguide3/integrations/vector_client.py`
- Modify: `backend/src/aptguide3/rag/diagnostics.py`
- Modify: `backend/evals/runners/run_rag_eval.py`
- Modify: `docs/system/evidence-contract.md`
- Modify: `docs/system/data-inventory/room-id-alignment.md`
- Modify: `docs/plans/2026-05-15-aptguide3-room-lease-id-alignment-plan.md`
- Modify: `docs/plans/2026-05-15-aptguide3-grounded-risk-answer-plan.md`
- Modify: `docs/plans/2026-05-15-aptguide3-comprehensive-rag-evaluation-plan.md`

## Data Model

Create a room identity map table:

```sql
CREATE TABLE IF NOT EXISTS aptguide3_room_identity_map (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  canonical_room_id VARCHAR(64) NOT NULL,
  source_system VARCHAR(32) NOT NULL,
  source_record_id VARCHAR(128) NOT NULL,
  business_system VARCHAR(32) NOT NULL DEFAULT 'lease',
  business_room_id VARCHAR(128) NULL,
  match_method VARCHAR(64) NOT NULL,
  match_confidence DECIMAL(5,4) NOT NULL,
  matched_fields JSON NULL,
  verification_status VARCHAR(32) NOT NULL,
  verified_by VARCHAR(64) NULL,
  verified_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_source_identity (source_system, source_record_id),
  KEY idx_canonical_room_id (canonical_room_id),
  KEY idx_business_identity (business_system, business_room_id),
  KEY idx_verification_status (verification_status)
);
```

Allowed `verification_status` values:

```text
unmapped
candidate
verified
conflict
rejected
```

Allowed `match_method` values:

```text
direct_id
exact_business_key
field_similarity
manual_review
unmapped
```

## Tasks

### Task 1: Preserve Source Identity In Vector Mapping

- [x] Update `backend/src/aptguide3/integrations/vector_client.py` so `_map_wechat_room_results()` never discards the original Milvus entity ID.
- [x] Every mapped hit must include:

```python
{
    "wechat_room_id": str(wechat_id),
    "source_system": "wechat",
    "source_collection": "wechat_room_index",
    "source_record_id": str(wechat_id),
    "synthetic_room_id": synthetic_id,
    "lease_room_id": entity.get("lease_room_id") or entity.get("room_id") or None,
    "identity_mapping_status": "unmapped",
}
```

- [x] Keep `room_id` only as temporary UI/internal ID until a verified lease ID exists.

Acceptance:

```text
No wechat vector hit enters room_retrieval without source_record_id.
No code treats synthetic_room_id as lease_room_id.
```

### Task 2: Add Identity Mapping Domain Helpers

- [x] Create `backend/src/aptguide3/rag/room_identity.py`.
- [x] Add:

```python
from pydantic import BaseModel


class RoomIdentity(BaseModel):
    source_system: str
    source_record_id: str
    canonical_room_id: str = ""
    business_system: str = "lease"
    business_room_id: str | None = None
    verification_status: str = "unmapped"
    match_method: str = "unmapped"
    match_confidence: float = 0.0


def is_lease_verifiable(identity: RoomIdentity) -> bool:
    return (
        identity.business_system == "lease"
        and bool(identity.business_room_id)
        and identity.verification_status == "verified"
    )


def evidence_level_for_identity(identity: RoomIdentity) -> str:
    if is_lease_verifiable(identity):
        return "mapped_verified"
    if identity.verification_status == "candidate":
        return "mapped_candidate"
    return "vector_only"
```

### Task 3: Add Repository Contract

- [x] Create `backend/src/aptguide3/persistence/room_identity_repo.py`.
- [x] Define:

```python
from typing import Protocol

from aptguide3.rag.room_identity import RoomIdentity


class RoomIdentityRepository(Protocol):
    async def get_by_source(self, source_system: str, source_record_id: str) -> RoomIdentity | None:
        raise NotImplementedError

    async def upsert_mapping(self, identity: RoomIdentity) -> None:
        raise NotImplementedError


class InMemoryRoomIdentityRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], RoomIdentity] = {}

    async def get_by_source(self, source_system: str, source_record_id: str) -> RoomIdentity | None:
        return self._items.get((source_system, source_record_id))

    async def upsert_mapping(self, identity: RoomIdentity) -> None:
        self._items[(identity.source_system, identity.source_record_id)] = identity
```

### Task 4: Add Source Inspection Script

- [x] Create `backend/scripts/inspect_room_identity_sources.py`.
- [x] The script must print:

```text
Milvus wechat_room_index fields
sample source_record_id values
whether lease_room_id / room_id / house_id / apartment_id exists
candidate MySQL/wechat table fields if configured
lease validation accepted ID shape
```

- [x] The script must not mutate data.

Run:

```bash
cd backend
uv run python scripts/inspect_room_identity_sources.py
```

Expected:

```text
Human-readable inventory output with missing/present ID fields.
```

### Task 5: Update Diagnostics And Eval Failure Owner

- [x] Add diagnostic fields:

```text
source_record_ids
identity_mapping_status_counts
mapped_verified_count
mapped_candidate_count
unmapped_count
synthetic_id_used_count
```

- [x] Add eval failure owner:

```text
identity_mapping
```

- [x] If room results have only synthetic IDs, eval must classify this as `identity_mapping`, not as successful lease validation.

### Task 6: Tests

- [x] Add `backend/tests/unit/rag/test_room_identity.py`.
- [x] Add:

```python
from aptguide3.rag.room_identity import RoomIdentity, evidence_level_for_identity, is_lease_verifiable


def test_verified_identity_is_lease_verifiable():
    identity = RoomIdentity(
        source_system="wechat",
        source_record_id="wx-1",
        canonical_room_id="room-canon-1",
        business_room_id="101",
        verification_status="verified",
        match_method="direct_id",
        match_confidence=1.0,
    )
    assert is_lease_verifiable(identity) is True


def test_unmapped_identity_is_vector_only():
    identity = RoomIdentity(source_system="wechat", source_record_id="wx-1")
    assert evidence_level_for_identity(identity) == "vector_only"
```

- [x] Add `backend/tests/unit/persistence/test_room_identity_repo.py`.
- [x] Add get/upsert tests for `InMemoryRoomIdentityRepository`.

Run:

```bash
cd backend
uv run pytest tests/unit/rag/test_room_identity.py tests/unit/persistence/test_room_identity_repo.py -q
```

Expected:

```text
room identity domain and repository tests pass
```

### Task 7: Update Downstream Plans

- [x] Update Plan 2 so it depends on `RoomIdentityRepository` and only calls lease validation for `verified` identities.
- [x] Update Plan 3 so medium/high-risk room language treats `vector_only` and `mapped_candidate` as insufficient for availability/price/appointment claims.
- [x] Update Plan 5 so comprehensive evaluation is blocked until identity mapping exposes verified business IDs for production room cases.

## Acceptance Criteria

- `wechat_room_id` / `source_record_id` is preserved from Milvus through diagnostics.
- Synthetic IDs are never used as lease IDs.
- A formal identity map contract exists.
- Code can distinguish `vector_only`, `mapped_candidate`, and `mapped_verified`.
- Plan 2 can safely build lease validation on `mapped_verified` identities only.
- Plan 3 can safely block unsupported medium/high-risk room claims.
- Plan 5 can evaluate production room quality only after verified identity mapping exists.
