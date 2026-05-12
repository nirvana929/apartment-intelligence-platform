# RAG Implementation Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the AptGuide 2.0 RAG MVP retrieval layer: schemas, vector adapters, KB sync, room sync, query understanding, room retrieval with lease validation, KB confidence gate, trace, and MVP eval runner.

**Architecture:** The RAG layer consumes reviewed KB YAML and room data exposed by lease internal tools. Milvus collections store searchable vectors only. Room outputs are never returned from Milvus directly; every displayed room must be validated through `lease`. KB answers must be source-bound or fall back conservatively.

**Tech Stack:** Python 3.12, FastAPI-compatible modules, Pydantic, pymilvus, OpenAI-compatible embeddings, httpx, pytest, YAML.

---

## 0. Scope

This document is for the **RAG Implementation Agent** only.

You are responsible for:

- RAG schemas;
- vector adapter;
- KB chunking and sync;
- room vector sync from lease sync DTO;
- query understanding and rewrite;
- room multi-recall, lease validation, recovery, ranking;
- KB multi-recall, source rerank, confidence gate;
- retrieval trace;
- MVP eval runner.

You are **not** responsible for:

- creating lease seed SQL;
- deciding generated room distributions;
- writing production appointment workflow;
- making frontend UI;
- exposing MCP;
- registering mock runtime tools.

## 1. Required Reading

Read these before editing:

1. `AptGuide 2.0/README.md`
2. `AptGuide 2.0/docs/21-rag-final-implementation-scheme.md`
3. `AptGuide 2.0/docs/22-rag-mvp-data-and-implementation-plan.md`
4. `AptGuide 2.0/docs/23-rag-data-supplement-agent-plan.md`
5. `AptGuide 2.0/evals/reports/data_supplement_handoff_report.md` if it exists
6. `AptGuide 2.0/docs/15-tool-registry-and-error-codes.md`
7. `AptGuide 2.0/docs/10-trace-eval-and-observability.md`

Old AptGuide reference files:

```text
AptGuide/src/aptguide/vector/client.py
AptGuide/src/aptguide/vector/embedding.py
AptGuide/src/aptguide/vector/kb_search.py
AptGuide/src/aptguide/vector/room_index.py
AptGuide/scripts/seed_kb.py
AptGuide/scripts/sync_room_vectors.py
```

Use them as reference only. Do not preserve old collection names or naive RAG behavior.

## 2. Preconditions

Before running room vector sync, confirm the Data Supplement Agent has delivered:

```text
AptGuide 2.0/evals/reports/data_supplement_handoff_report.md
```

It must say:

```text
RAG implementation agent may start room vector sync.
```

If that sentence is missing, you may implement schemas, adapters, KB sync, query understanding, and eval runner, but you must not claim room retrieval MVP is ready.

## 3. Non-Negotiable RAG Rules

1. Do not return Milvus room facts directly to users.
2. Do not skip lease validation.
3. Do not register mock tools in AptGuide 2.0 runtime.
4. Do not mark KB chunks active without reviewed source data.
5. Do not generate final policy facts from HyDE.
6. Do not store PII in vectors, trace, reports, or eval results.
7. Do not weaken eval cases to pass metrics.

## 4. Deliverables

Create these files under `AptGuide 2.0/backend` unless they already exist:

```text
src/aptguide2/rag/schemas.py
src/aptguide2/rag/query_understanding.py
src/aptguide2/rag/chunking.py
src/aptguide2/rag/room_retrieval.py
src/aptguide2/rag/kb_retrieval.py
src/aptguide2/rag/ranking.py
src/aptguide2/rag/confidence.py
src/aptguide2/tools/lease_adapter.py
src/aptguide2/tools/vector_adapter.py
src/aptguide2/trace/retrieval_events.py
scripts/sync_kb_vectors.py
scripts/sync_room_vectors.py
scripts/benchmark_vectors.py
evals/runners/run_rag_mvp.py
tests/unit/rag/test_schemas.py
tests/unit/rag/test_query_understanding.py
tests/unit/rag/test_chunking.py
tests/unit/rag/test_room_retrieval.py
tests/unit/rag/test_kb_retrieval.py
tests/unit/tools/test_lease_adapter.py
tests/unit/tools/test_vector_adapter.py
tests/unit/trace/test_retrieval_events.py
```

Reports:

```text
AptGuide 2.0/evals/reports/vector_sync_report.md
AptGuide 2.0/evals/reports/rag_mvp_eval_report.md
AptGuide 2.0/evals/reports/rag_mvp_smoke_report.md
```

## 5. Task R1: Create RAG Schemas

**Files:**

- Create: `AptGuide 2.0/backend/src/aptguide2/rag/schemas.py`
- Test: `AptGuide 2.0/backend/tests/unit/rag/test_schemas.py`

- [ ] **Step 1: Define Pydantic models.**

Required models:

```python
class QueryUnderstandingResult(BaseModel): ...
class RoomVectorRecord(BaseModel): ...
class KBChunk(BaseModel): ...
class RoomCandidate(BaseModel): ...
class ValidatedRoom(BaseModel): ...
class RankedRoom(BaseModel): ...
class KBSource(BaseModel): ...
class RetrievalTracePayload(BaseModel): ...
class RetrievalEvalCase(BaseModel): ...
```

Minimum `QueryUnderstandingResult` fields:

```python
raw_message: str
task: Literal["room_search", "kb_qa", "fallback"]
reference_resolution: dict[str, Any] | None = None
hard_filters: dict[str, Any] = Field(default_factory=dict)
soft_preferences: list[str] = Field(default_factory=list)
retrieval_queries: list[str] = Field(default_factory=list)
risk_level: Literal["low", "medium", "high"] = "low"
```

Minimum `RoomVectorRecord` fields:

```python
vector_id: str
room_id: int
apartment_id: int
city_id: int | None
district_id: int | None
district_name: str | None
rent: int | None
payment_types: list[str]
lease_terms: list[int]
tags: list[str]
facilities: list[str]
profile_type: Literal["room", "apartment", "audience"] = "room"
content: str
content_hash: str
source_version: int
status: Literal["active", "inactive"]
```

Minimum `KBChunk` fields:

```python
chunk_id: str
doc_id: str
doc_type: str
module: str
title: str
tags: list[str]
content: str
content_hash: str
version: int
release_id: str
status: Literal["candidate", "reviewed", "indexed", "evaluated", "active", "inactive"]
risk_level: Literal["low", "medium", "high"]
```

- [ ] **Step 2: Write tests.**

```python
def test_query_understanding_defaults_to_empty_lists():
    result = QueryUnderstandingResult(raw_message="找安静点的房子", task="room_search")
    assert result.soft_preferences == []
    assert result.retrieval_queries == []

def test_kb_chunk_requires_source_fields():
    chunk = KBChunk(
        chunk_id="KB-LEASE-005#01",
        doc_id="KB-LEASE-005",
        doc_type="rule",
        module="lease",
        title="押金退还规则",
        tags=["押金"],
        content="押金退还以验房和费用结清为前提。",
        content_hash="sha256:test",
        version=1,
        release_id="20260511-001",
        status="active",
        risk_level="high",
    )
    assert chunk.doc_id == "KB-LEASE-005"
```

- [ ] **Step 3: Run tests.**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_schemas.py -q
```

Expected: pass.

## 6. Task R2: Implement Lease Adapter

**Files:**

- Create: `AptGuide 2.0/backend/src/aptguide2/tools/lease_adapter.py`
- Test: `AptGuide 2.0/backend/tests/unit/tools/test_lease_adapter.py`

- [ ] **Step 1: Implement adapter methods.**

Required methods:

```python
async def health(self) -> bool
async def sync_rooms(self, limit: int = 200) -> list[dict]
async def search_rooms(self, payload: dict) -> dict
async def get_room_detail(self, room_id: int) -> dict
```

Endpoints:

```text
GET /internal/ai/tools/health
GET /internal/ai/tools/sync/rooms?limit=...
POST /internal/ai/tools/room/search
GET /internal/ai/tools/room/{room_id}
```

- [ ] **Step 2: Implement snake_case to camelCase conversion.**

Input:

```python
{"district_id": 1005, "max_rent": 1800, "room_ids": [3001]}
```

Outgoing Java JSON:

```python
{"districtId": 1005, "maxRent": 1800, "roomIds": [3001]}
```

- [ ] **Step 3: Normalize Java response to snake_case.**

Java:

```json
{"roomId":3001,"apartmentId":2001,"isAppointable":true}
```

Python:

```python
{"room_id": 3001, "apartment_id": 2001, "is_appointable": True}
```

- [ ] **Step 4: Tests.**

Verify:

- conversion to camelCase;
- response to snake_case;
- failed Java `code` raises or returns a structured tool error;
- timeout is surfaced.

## 7. Task R3: Implement Vector Adapter

**Files:**

- Create: `AptGuide 2.0/backend/src/aptguide2/tools/vector_adapter.py`
- Test: `AptGuide 2.0/backend/tests/unit/tools/test_vector_adapter.py`

- [ ] **Step 1: Define constants.**

```python
ROOM_COLLECTION = "apt_room_vector"
KB_COLLECTION = "apt_rental_kb"
DEFAULT_METRIC = "COSINE"
DEFAULT_INDEX = {
    "index_type": "HNSW",
    "metric_type": "COSINE",
    "params": {"M": 16, "efConstruction": 200},
}
DEFAULT_SEARCH_PARAMS = {"metric_type": "COSINE", "params": {"ef": 64}}
```

- [ ] **Step 2: Implement methods.**

```python
def ensure_room_collection(self) -> None
def ensure_kb_collection(self) -> None
def upsert_room_records(self, records: list[RoomVectorRecord]) -> None
def upsert_kb_chunks(self, chunks: list[KBChunk]) -> None
def search_rooms(self, vector: list[float], filters: dict, top_k: int) -> list[dict]
def search_kb(self, vector: list[float], filters: dict, top_k: int) -> list[dict]
```

- [ ] **Step 3: Tests verify.**

- collection names are `apt_room_vector` and `apt_rental_kb`;
- default index is HNSW;
- default searches include `status == "active"`;
- upsert payload includes `content_hash`.

## 8. Task R4: Implement Chunking And Text Builders

**Files:**

- Create: `AptGuide 2.0/backend/src/aptguide2/rag/chunking.py`
- Test: `AptGuide 2.0/backend/tests/unit/rag/test_chunking.py`

- [ ] **Step 1: Implement KB chunk builder.**

Function:

```python
def build_kb_chunks(rule: dict, release_id: str) -> list[KBChunk]
```

Rules:

- one rule becomes one chunk if `content` <= 800 Chinese characters;
- longer content splits by paragraph;
- `chunk_id` format is `{doc_id}#NN`;
- `content_hash` format is `sha256:{hex}`;
- vector text prefix is `[module][doc_type][title][tags][risk_level]`.

- [ ] **Step 2: Implement room vector record builder.**

Function:

```python
def build_room_vector_record(room: dict, source_version: int) -> RoomVectorRecord
```

Text format:

```text
[room][广州][番禺区][大学城南亭附近]
房间 302，位于大学城南亭寓。月租 1800 元，支持 MONTHLY, QUARTERLY，租期 6, 12 个月。
户型 1室1卫，面积 25 平方米，标签包括 安静、可月付、近大学城、适合考研。
公寓配套包括 空调、洗衣机、热水器、WIFI、床、书桌。
适合希望低预算、安静学习、通勤到大学城附近的租客。
```

- [ ] **Step 3: Tests verify deterministic hash.**

Same input produces same `content_hash`.

## 9. Task R5: Implement KB Vector Sync

**Files:**

- Create: `AptGuide 2.0/backend/scripts/sync_kb_vectors.py`
- Test: `AptGuide 2.0/backend/tests/unit/scripts/test_sync_kb_vectors.py`
- Report: `AptGuide 2.0/evals/reports/vector_sync_report.md`

- [ ] **Step 1: Load YAML rules.**

Path:

```text
AptGuide 2.0/backend/knowledge/rules/*.yaml
```

- [ ] **Step 2: Validate rules.**

Reject if:

- missing `doc_id`;
- duplicate `doc_id`;
- missing `reviewed_by`;
- status is not `reviewed`, `approved`, or `active`;
- content contains phone, ID card, bank card;
- high-risk modules lack `risk_level`.

- [ ] **Step 3: Build chunks and embed changed chunks only.**

Use `content_hash` to skip unchanged chunks.

- [ ] **Step 4: Mark deleted chunks inactive.**

Do not hard delete during MVP.

- [ ] **Step 5: Run.**

```bash
cd "AptGuide 2.0/backend"
uv run python scripts/sync_kb_vectors.py --release-id 20260511-rag-mvp
```

Expected:

- active chunks >= 70;
- no unreviewed chunks active;
- sync report written.

## 10. Task R6: Implement Room Vector Sync

**Files:**

- Create: `AptGuide 2.0/backend/scripts/sync_room_vectors.py`
- Test: `AptGuide 2.0/backend/tests/unit/scripts/test_sync_room_vectors.py`
- Report: `AptGuide 2.0/evals/reports/vector_sync_report.md`

- [ ] **Step 1: Check data handoff report.**

If `data_supplement_handoff_report.md` does not allow room vector sync, stop after reporting blocker.

- [ ] **Step 2: Fetch rooms from lease.**

Call:

```text
GET /internal/ai/tools/sync/rooms?limit=1000
```

- [ ] **Step 3: Build `RoomVectorRecord`.**

Use `build_room_vector_record`.

- [ ] **Step 4: Embed changed records only.**

Skip unchanged records by `content_hash`.

- [ ] **Step 5: Run.**

```bash
cd "AptGuide 2.0/backend"
uv run python scripts/sync_room_vectors.py --limit 1000
```

Expected:

- active room vectors >= 150 after data seed;
- each active vector has `room_id`, `content_hash`, `status`;
- no sensitive fields in report.

## 11. Task R7: Implement Query Understanding

**Files:**

- Create: `AptGuide 2.0/backend/src/aptguide2/rag/query_understanding.py`
- Test: `AptGuide 2.0/backend/tests/unit/rag/test_query_understanding.py`

- [ ] **Step 1: Implement deterministic MVP parser.**

Detect:

- budget: `1500以内`, `两千以内`, `3000左右`, `预算不限`, `预算我都接受`;
- districts/areas: 天河、越秀、海珠、番禺、白云、大学城、南亭;
- payment: 月付、季付、半年付、年付;
- soft preferences: 安静、近地铁、独卫、朝南、考研、通勤、采光、家电、短租;
- references: 第一个、第二个、刚才那个.

- [ ] **Step 2: Generate up to 3 retrieval queries.**

Input:

```text
找大学城南亭附近1500以内安静点的
```

Expected:

```python
hard_filters = {"area_text": "大学城南亭", "max_rent": 1500}
soft_preferences = ["安静", "适合学习", "低噪音"]
retrieval_queries = [
    "大学城南亭附近 安静 适合学习 低噪音 房源",
    "番禺大学城 低预算 安静 单间",
    "适合考研学生 居住安静 配套便利 公寓",
]
```

- [ ] **Step 3: Test budget clearing.**

If previous state had `max_rent=1500` and user says `预算我都接受`, result `max_rent` must be `None`.

## 12. Task R8: Implement Room Retrieval With Lease Validation

**Files:**

- Create: `AptGuide 2.0/backend/src/aptguide2/rag/room_retrieval.py`
- Create: `AptGuide 2.0/backend/src/aptguide2/rag/ranking.py`
- Test: `AptGuide 2.0/backend/tests/unit/rag/test_room_retrieval.py`

- [ ] **Step 1: Implement retrieval flow.**

```text
exact_search via lease
vector_recall via Milvus
merge room_ids
coarse rank
lease validation through room.search(room_ids=...)
fine rank
return RankedRoom[]
```

- [ ] **Step 2: Implement recovery.**

If validation returns zero:

1. remove `max_rent` if present and retry;
2. relax strict district if present;
3. return empty result with recovery reason if still empty.

Never return raw Milvus room data.

- [ ] **Step 3: Implement ranking formula.**

```text
final_score =
  0.30 * semantic_score
  + 0.25 * budget_score
  + 0.20 * area_score
  + 0.15 * tag_score
  + 0.10 * availability_score
```

- [ ] **Step 4: Tests verify.**

- vector result is not returned if lease validation fails;
- card facts come from lease payload;
- duplicates are removed by `room_id`;
- recovery triggers on empty validation.

## 13. Task R9: Implement KB Retrieval And Confidence Gate

**Files:**

- Create: `AptGuide 2.0/backend/src/aptguide2/rag/kb_retrieval.py`
- Create: `AptGuide 2.0/backend/src/aptguide2/rag/confidence.py`
- Test: `AptGuide 2.0/backend/tests/unit/rag/test_kb_retrieval.py`

- [ ] **Step 1: Implement multi-recall.**

Channels:

- original query;
- normalized query;
- step-back query for lease/payment/policy questions;
- optional HyDE only for recall when top score is below threshold.

- [ ] **Step 2: Merge by `chunk_id`.**

Preserve:

- best score;
- matched query;
- recall source;
- module;
- risk_level.

- [ ] **Step 3: Confidence gate.**

| Risk | Gate |
| --- | --- |
| low | top score >= low threshold |
| medium | top score >= medium threshold and module match |
| high | top score >= high threshold and source has `risk_level=high` |

- [ ] **Step 4: Tests verify.**

- high-risk deposit question without source returns low-confidence fallback;
- source list includes `doc_id`, `chunk_id`, `title`, `module`, `score`;
- no grounded answer is generated without source.

## 14. Task R10: Implement Retrieval Trace

**Files:**

- Create: `AptGuide 2.0/backend/src/aptguide2/trace/retrieval_events.py`
- Test: `AptGuide 2.0/backend/tests/unit/trace/test_retrieval_events.py`

- [ ] **Step 1: Implement `build_retrieval_finished_event`.**

Payload:

```json
{
  "task": "room_search",
  "rewrite_count": 3,
  "collections": ["apt_room_vector"],
  "top_k": 50,
  "filters": {"district_id": 1005, "max_rent": 1800},
  "candidate_count": 42,
  "validated_count": 5,
  "latency": {
    "rewrite_latency_ms": 10,
    "embedding_latency_ms": 80,
    "vector_search_latency_ms": 25,
    "merge_latency_ms": 3,
    "lease_validation_latency_ms": 130,
    "rerank_latency_ms": 8,
    "retrieval_total_latency_ms": 256
  }
}
```

- [ ] **Step 2: Reject PII keys.**

Tests must reject:

```text
phone
id_card
contract_no
address_detail
bank_card
```

## 15. Task R11: Implement MVP Eval Runner

**Files:**

- Create: `AptGuide 2.0/backend/evals/runners/run_rag_mvp.py`
- Input: `AptGuide 2.0/backend/evals/datasets/rag_mvp_retrieval_cases.yaml`
- Output: `AptGuide 2.0/evals/reports/rag_mvp_eval_report.md`

- [ ] **Step 1: Load YAML cases.**

- [ ] **Step 2: Execute room or KB retrieval.**

- [ ] **Step 3: Compute metrics.**

```text
hit@3
hit@5
MRR
empty_result_rate
low_confidence_fallback_rate
unvalidated_room_return_count
source_missing_count
```

- [ ] **Step 4: Write Markdown report.**

```markdown
# RAG MVP Eval Report

## Summary

| Metric | Value | Gate | Pass |
| --- | ---: | ---: | --- |

## Room Retrieval

## KB Retrieval

## Fallback

## Failed Cases
```

- [ ] **Step 5: Gates.**

| Metric | Gate |
| --- | ---: |
| room hit@5 | >= 80% |
| KB source hit@3 | >= 85% |
| high-risk fallback correctness | 100% |
| unvalidated room return count | 0 |
| source missing count for KB answers | 0 |

## 16. Task R12: End-To-End RAG Smoke

**Files:**

- Create: `AptGuide 2.0/evals/reports/rag_mvp_smoke_report.md`

- [ ] **Step 1: Start lease and Milvus.**

```bash
cd lease
mvn -pl web/web-app spring-boot:run
```

Start Milvus using the project’s existing local Milvus setup.

- [ ] **Step 2: Run sync.**

```bash
cd "AptGuide 2.0/backend"
uv run python scripts/sync_kb_vectors.py --release-id 20260511-rag-mvp
uv run python scripts/sync_room_vectors.py --limit 1000
```

- [ ] **Step 3: Run eval.**

```bash
uv run python evals/runners/run_rag_mvp.py \
  --cases evals/datasets/rag_mvp_retrieval_cases.yaml \
  --report ../evals/reports/rag_mvp_eval_report.md
```

- [ ] **Step 4: Smoke these queries.**

```text
找大学城南亭附近1500以内安静点的房子
天河区3000以内可月付，通勤方便
预算我都接受，还是想要安静点
押金退还多久到账
提前退租会扣多少钱
能查一下别人租约吗
```

- [ ] **Step 5: Report.**

`rag_mvp_smoke_report.md` must include:

- command summary;
- pass/fail for each query;
- trace IDs;
- failed cases;
- whether chat integration may start.

## 17. Definition Of Done

RAG Implementation Agent is done when:

- RAG schemas pass unit tests;
- lease adapter can call health, sync rooms, search rooms, and room detail;
- vector adapter uses `apt_room_vector`, `apt_rental_kb`, and HNSW defaults;
- KB sync creates at least 70 active reviewed chunks;
- room sync creates at least 150 active vectors after Data Agent handoff;
- query understanding handles budget, area, payment, soft preference, and reference cases;
- room retrieval never returns unvalidated Milvus rooms;
- KB retrieval returns sources or low-confidence fallback;
- retrieval trace includes rewrite, embedding, vector search, merge, lease validation, rerank, and total latency;
- MVP eval report passes gates;
- smoke report says whether chat integration may start.
