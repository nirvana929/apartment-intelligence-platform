# AptGuide 3.0 Room Eval Dataset And Identity Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the live RAG gate room-search blockers by making room retrieval measurable and lease-verifiable.

**Architecture:** Keep the existing eval runner and RAG pipeline. Add a durable room identity mapping table/repository, create scripts that inspect live Milvus/lease data and generate reviewable mapping/eval artifacts, then update the RAG dataset with expected room IDs and rerun the live gate.

**Tech Stack:** Python 3.13, uv, pytest, SQLAlchemy async, MySQL 8, Milvus, YAML eval datasets, existing `RoomIdentityRepository`, existing `run_rag_eval.py`.

---

## Current Baseline

- Latest checkpoint: `docs/plans/checkpoints/2026-05-16-evaluation-first-live-rag-gate.md`
- Live RAG gate result: PARTIAL PASS
- KB QA: 4/4 PASS, Hit@3=100%, high-risk citations pass
- Room search: 5/5 FAIL, owner=`dataset_gap`
- Secondary blocker: owner=`identity_mapping`, `lease_validation_requested=0`
- Deferred issue: owner=`trace_visibility`, LangSmith disabled so trace visibility is 0%

## Scope

This plan fixes P0 and P1:

```text
P0 dataset_gap:
  room_search expected_room_ids are empty, so Hit@K/MRR/nDCG cannot be computed.

P1 identity_mapping:
  wechat_room_id values are not mapped to lease_room_id, so lease validation never triggers.
```

This plan does not tune ranking, prompts, chunking, or LLM behavior. If room quality remains poor after measurable IDs exist, create a separate retrieval optimization plan.

## Files

- Modify: `backend/src/aptguide3/database/schema.sql`
- Modify: `backend/src/aptguide3/database/models.py`
- Modify: `backend/src/aptguide3/persistence/mysql_repos.py`
- Modify: `backend/src/aptguide3/api/deps.py`
- Modify: `backend/evals/datasets/rag_retrieval_cases.yaml`
- Create: `backend/scripts/export_room_eval_candidates.py`
- Create: `backend/scripts/import_room_identity_mappings.py`
- Create: `backend/evals/reports/room-eval-candidates.md`
- Create: `backend/tests/unit/persistence/test_mysql_room_identity_repo.py`
- Create: `backend/tests/unit/scripts/test_import_room_identity_mappings.py`
- Update after execution: `docs/tests/evaluation-report.md`
- Update after execution: `reports/evaluation-report.md`
- Create after execution: `docs/plans/checkpoints/YYYY-MM-DD-room-eval-dataset-identity-map.md`

## Acceptance Criteria

- `aptguide3_room_identity_map` exists in schema and SQLAlchemy models.
- MySQL repository implements `RoomIdentityRepository`.
- `api/deps.py` wires the MySQL room identity repository in `mysql` and `hybrid` modes.
- A script can import reviewed mappings into `RoomIdentityRepository`.
- A script can export room eval candidates from live RAG results for human review.
- `backend/evals/datasets/rag_retrieval_cases.yaml` has non-empty `expected_room_ids` for room search cases.
- Live RAG eval no longer classifies all room cases as `dataset_gap`.
- Lease validation is requested for mapped room candidates.

## Task 1: Add Durable Room Identity Map Schema

**Files:**
- Modify: `backend/src/aptguide3/database/schema.sql`
- Modify: `backend/src/aptguide3/database/models.py`
- Test: `backend/tests/unit/persistence/test_mysql_room_identity_repo.py`

- [ ] Add table SQL to `backend/src/aptguide3/database/schema.sql`.

```sql
CREATE TABLE IF NOT EXISTS aptguide3_room_identity_map (
  source_system VARCHAR(32) NOT NULL,
  source_record_id VARCHAR(128) NOT NULL,
  canonical_room_id VARCHAR(128) NOT NULL DEFAULT '',
  business_system VARCHAR(32) NOT NULL DEFAULT 'lease',
  business_room_id VARCHAR(128) NULL,
  verification_status VARCHAR(32) NOT NULL DEFAULT 'unmapped',
  match_method VARCHAR(64) NOT NULL DEFAULT 'unmapped',
  match_confidence DECIMAL(5,4) NOT NULL DEFAULT 0.0000,
  metadata JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (source_system, source_record_id),
  INDEX idx_aptguide3_room_identity_business_room_id (business_room_id),
  INDEX idx_aptguide3_room_identity_verification_status (verification_status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

- [ ] Add SQLAlchemy model to `backend/src/aptguide3/database/models.py`.

```python
class RoomIdentityMapRecord(Base):
    __tablename__ = "aptguide3_room_identity_map"

    source_system: Mapped[str] = mapped_column(String(32), primary_key=True)
    source_record_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    canonical_room_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    business_system: Mapped[str] = mapped_column(String(32), nullable=False, default="lease")
    business_room_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unmapped", index=True)
    match_method: Mapped[str] = mapped_column(String(64), nullable=False, default="unmapped")
    match_confidence: Mapped[float] = mapped_column(DECIMAL(5, 4), nullable=False, default=0.0)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
```

Add `DECIMAL` to the SQLAlchemy import line:

```python
from sqlalchemy import DECIMAL, JSON, DateTime, Integer, String, Text
```

- [ ] Run focused import check.

```bash
cd backend
uv run python - <<'PY'
from aptguide3.database.models import RoomIdentityMapRecord
print(RoomIdentityMapRecord.__tablename__)
PY
```

Expected:

```text
aptguide3_room_identity_map
```

## Task 2: Add MySQL RoomIdentityRepository

**Files:**
- Modify: `backend/src/aptguide3/persistence/mysql_repos.py`
- Test: `backend/tests/unit/persistence/test_mysql_room_identity_repo.py`

- [ ] Add `MySqlRoomIdentityRepository` that implements `get_by_source()` and `upsert_mapping()` using `RoomIdentityMapRecord`.

```python
class MySqlRoomIdentityRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    async def get_by_source(self, source_system: str, source_record_id: str) -> RoomIdentity | None:
        async with self.sessionmaker() as session:
            record = await session.get(
                RoomIdentityMapRecord,
                {"source_system": source_system, "source_record_id": source_record_id},
            )
            if record is None:
                return None
            return RoomIdentity(
                source_system=record.source_system,
                source_record_id=record.source_record_id,
                canonical_room_id=record.canonical_room_id,
                business_system=record.business_system,
                business_room_id=record.business_room_id,
                verification_status=record.verification_status,
                match_method=record.match_method,
                match_confidence=float(record.match_confidence),
            )

    async def upsert_mapping(self, identity: RoomIdentity) -> None:
        async with self.sessionmaker() as session:
            key = {"source_system": identity.source_system, "source_record_id": identity.source_record_id}
            record = await session.get(RoomIdentityMapRecord, key)
            if record is None:
                session.add(RoomIdentityMapRecord(
                    source_system=identity.source_system,
                    source_record_id=identity.source_record_id,
                    canonical_room_id=identity.canonical_room_id,
                    business_system=identity.business_system,
                    business_room_id=identity.business_room_id,
                    verification_status=identity.verification_status,
                    match_method=identity.match_method,
                    match_confidence=identity.match_confidence,
                    metadata_json={},
                ))
            else:
                record.canonical_room_id = identity.canonical_room_id
                record.business_system = identity.business_system
                record.business_room_id = identity.business_room_id
                record.verification_status = identity.verification_status
                record.match_method = identity.match_method
                record.match_confidence = identity.match_confidence
            await session.commit()
```

- [ ] Add unit tests covering upsert, overwrite, and missing lookup.

Run:

```bash
cd backend
uv run pytest tests/unit/persistence/test_mysql_room_identity_repo.py -q
```

Expected:

```text
3 passed
```

## Task 3: Wire RoomIdentityRepository In Dependencies

**Files:**
- Modify: `backend/src/aptguide3/api/deps.py`
- Test: existing API/RAG tests

- [ ] Import and wire `MySqlRoomIdentityRepository` in `mysql` and `hybrid` modes.
- [ ] Keep `InMemoryRoomIdentityRepository` in memory mode.
- [ ] Confirm `RoomRetrievalPipeline` receives the repository through existing dependencies.

Run:

```bash
cd backend
uv run pytest tests/unit/api tests/unit/rag/test_room_retrieval.py tests/unit/procedures/test_room_search.py -q
```

Expected:

```text
tests pass
```

## Task 4: Create Mapping Import Script

**Files:**
- Create: `backend/scripts/import_room_identity_mappings.py`
- Test: `backend/tests/unit/scripts/test_import_room_identity_mappings.py`

- [ ] Create a CSV parser that requires:

```text
source_system,source_record_id,canonical_room_id,business_system,business_room_id,verification_status,match_method,match_confidence
```

- [ ] Convert each row to `RoomIdentity`.
- [ ] Import rows by calling `repos.room_identity_repo.upsert_mapping()`.
- [ ] Add tests for valid CSV and missing required columns.

Run:

```bash
cd backend
uv run pytest tests/unit/scripts/test_import_room_identity_mappings.py -q
```

Expected:

```text
2 passed
```

## Task 5: Export Room Eval Candidates From Live RAG

**Files:**
- Create: `backend/scripts/export_room_eval_candidates.py`
- Create: `backend/evals/reports/room-eval-candidates.md`

- [ ] Read room cases from `backend/evals/datasets/rag_retrieval_cases.yaml`.
- [ ] Run each query through `ChatService`.
- [ ] Write returned room cards into `backend/evals/reports/room-eval-candidates.md`.
- [ ] Include `room_id`, `title`, `district_name`, `rent`, `wechat_room_id`, `lease_room_id`, and `evidence_level`.

Run:

```bash
cd backend
uv run python scripts/export_room_eval_candidates.py
```

Expected:

```text
wrote backend/evals/reports/room-eval-candidates.md
```

## Task 6: Update Room Eval Dataset

**Files:**
- Modify: `backend/evals/datasets/rag_retrieval_cases.yaml`
- Test: `backend/tests/unit/evals/test_rag_eval_runner.py`

- [ ] Replace empty `expected_room_ids: []` with reviewed IDs for every room-search case.
- [ ] Keep `expected.must_validate_with_lease: true`.
- [ ] Do not add irrelevant returned rooms as expected IDs just because they appeared in one run.

Run:

```bash
cd backend
uv run pytest tests/unit/evals/test_rag_eval_runner.py -q
```

Expected:

```text
44 passed
```

## Task 7: Import Verified Room Identity Mappings

**Files:**
- Create: `backend/evals/datasets/room_identity_mappings.csv`
- Run: `backend/scripts/import_room_identity_mappings.py`

- [ ] Create reviewed mapping CSV from real lease data. Do not fabricate lease IDs.
- [ ] Import mappings.

```bash
cd backend
uv run python scripts/import_room_identity_mappings.py --csv evals/datasets/room_identity_mappings.csv
```

Expected:

```text
imported N room identity mappings
```

- [ ] Spot-check one imported mapping through `repos.room_identity_repo.get_by_source()`.

## Task 8: Re-run Live RAG Gate

**Files:**
- Generate: `backend/evals/reports/rag-evaluation-report.md`
- Update: `docs/tests/evaluation-report.md`
- Update: `reports/evaluation-report.md`

Run focused tests:

```bash
cd backend
uv run pytest tests/unit/evals/test_rag_eval_runner.py tests/unit/persistence/test_mysql_room_identity_repo.py tests/unit/scripts/test_import_room_identity_mappings.py -q
```

Run live eval:

```bash
cd backend
uv run python evals/runners/run_rag_eval.py --live
```

Expected:

```text
room_search cases are no longer all dataset_gap
room Hit@5 is numeric
lease_validation_requested is greater than 0 when mapped room candidates are returned
KB QA remains 4/4 PASS
```

## Task 9: Update Project State And Checkpoint

**Files:**
- Update: `progress/current-plan.md`
- Update: `progress/completed.md`
- Update: `progress/known-issues.md`
- Update: `progress/next-steps.md`
- Update: `docs/plans/current-plan.md`
- Update: `docs/plans/next-steps.md`
- Update: `docs/plans/execution-log.md`
- Create: `docs/plans/checkpoints/YYYY-MM-DD-room-eval-dataset-identity-map.md`

Checkpoint must include:

```markdown
# Checkpoint: room eval dataset and identity map

## Metadata
- Created at:
- Task:
- Status:
- Test status:

## Completed Work

## Verification

## Findings

## Known Issues

## Next Steps
```

Run:

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Expected:

```text
current_plan_preview references room eval dataset and identity map result
next_steps_preview reflects either main-chain integration or the remaining classified blocker
```

## Final Gate Before H5/Lease Integration

Do not start `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat` integration until one of these is true:

```text
Preferred:
  live RAG eval PASS with measurable room Hit@K and lease validation activity.

Acceptable for limited demo:
  KB QA production-ready, room search explicitly labeled limited because identity mapping is incomplete.
```
