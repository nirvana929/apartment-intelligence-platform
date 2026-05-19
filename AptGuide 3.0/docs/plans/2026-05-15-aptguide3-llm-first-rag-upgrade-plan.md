# AptGuide 3.0 LLM-First RAG Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade AptGuide 3.0 from thin RAG procedures into a full LLM-first retrieval system for room recommendation and KB QA, reusing AptGuide 2.0's proven retrieval, validation, ranking, sync, trace, and eval ideas without reintroducing keyword/regex intent understanding.

**Architecture:** The LLM remains the only natural-language understanding layer. RAG consumes `UnderstandingResult` and builds a deterministic `RetrievalPlan`, then runs either room retrieval or KB retrieval. Rules are allowed for safety, schema validation, source/lease validation, confidence gates, dedupe, filtering, tracing, and eval; rules are not allowed to classify intent or replace semantic scoring.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, OpenAI-compatible LLM and embedding APIs, pymilvus, httpx, SQLAlchemy async, MySQL, Redis, pytest, ruff.

---

## Source Inputs

This plan is based on:

- AptGuide 3.0 current implementation:
  - `backend/src/aptguide3/understanding/llm_understanding.py`
  - `backend/src/aptguide3/understanding/validation.py`
  - `backend/src/aptguide3/procedures/room_search.py`
  - `backend/src/aptguide3/procedures/kb_qa.py`
  - `backend/src/aptguide3/integrations/vector_client.py`
  - `backend/src/aptguide3/integrations/embedding_client.py`
  - `backend/src/aptguide3/integrations/lease_client.py`
- AptGuide 2.0 RAG design docs:
  - `AptGuide 2.0/docs/20-rag-retrieval-vector-mcp-evaluation-upgrade.md`
  - `AptGuide 2.0/docs/21-rag-final-implementation-scheme.md`
  - `AptGuide 2.0/docs/22-rag-mvp-data-and-implementation-plan.md`
  - `AptGuide 2.0/docs/27-current-implementation-guide.md`
  - `AptGuide 2.0/docs/28-rag-mvp-achievement-report.md`

## Design Decision

Use AptGuide 2.0's RAG engineering pattern, but replace the 2.0 rule-based `QueryUnderstanding` stage with AptGuide 3.0's LLM structured understanding.

```text
AptGuide 2.0 pattern to keep:
  RetrievalPlan
  room vector recall
  lease validation gate
  multi-dimensional ranking
  KB multi-query recall
  source rerank
  confidence gate
  content_hash sync
  trace and eval gates

AptGuide 2.0 pattern to reject:
  keyword task detection
  regex/keyword budget extraction as the understanding source
  dictionary-based district/preference/risk understanding as the understanding source
  character-overlap as primary semantic ranking
```

## Rule and String-Matching Boundary

### Allowed Deterministic Rules

These rules are allowed because they do not interpret natural language intent:

| Area | Mechanism | Reason |
| --- | --- | --- |
| Safety | hard privacy blocking | Blocks obvious privacy requests before LLM |
| Schema | Pydantic validation | Ensures LLM output shape is usable |
| Enum validation | allowed route/task/filter values | Prevents invalid tool calls |
| Lease validation | lease confirms room existence, status, rent, appointability | lease remains source of truth |
| KB confidence | source score/risk threshold | Prevents weak evidence from becoming policy answer |
| PII scan | regex for phone, ID card, bank card during KB sync | Prevents sensitive data entering vectors |
| Data processing | camelCase/snake_case conversion, content_hash, ID dedupe | Engineering plumbing |
| Milvus filters | `status == active`, `rent <= max_rent`, `district_id == value` | Applies hard filters from LLM output |

### Replaced 2.0 Rules

These 2.0 mechanisms must not be copied into 3.0 runtime:

| 2.0 Mechanism | 3.0 Replacement |
| --- | --- |
| keyword route detection | `LLMUnderstanding.route/task` |
| keyword/regex budget extraction | `LLMUnderstanding.hard_filters.max_rent/min_rent` |
| district keyword dictionary as understanding source | `LLMUnderstanding.hard_filters.district_id/district_name/area_text` |
| preference synonym dictionary as understanding source | `LLMUnderstanding.soft_preferences` |
| keyword risk detection | `LLMUnderstanding.risk` |
| tag/facility string containment as main preference score | LLM structured preference scorer |
| character-overlap as primary KB relevance | dense vector + rerank + confidence gate |

## Target Runtime Flow

```text
POST /chat
  -> auth
  -> SafetyBoundary
  -> LLMUnderstanding
      -> route/task/domain/action
      -> hard_filters
      -> soft_preferences
      -> retrieval_queries
      -> risk
  -> validate_or_clarify
  -> ProcedureRuntime
      -> RoomSearchProcedure
          -> RetrievalPlanBuilder
          -> room vector recall
          -> lease validation
          -> LLM preference scoring
          -> deterministic final ranking
          -> room cards
      -> KbQaProcedure
          -> RetrievalPlanBuilder
          -> KB multi-query recall
          -> source rerank
          -> confidence gate
          -> grounded answer or conservative fallback
  -> trace
  -> response
```

## File Structure

Create focused RAG modules under `backend/src/aptguide3/rag/`:

```text
backend/src/aptguide3/rag/
  __init__.py
  schemas.py              # RetrievalPlan, room candidates, KB sources, trace payloads
  planning.py             # Build RetrievalPlan from UnderstandingResult
  room_retrieval.py       # Room vector recall, merge, lease validation orchestration
  room_ranking.py         # Deterministic score fusion after LLM preference score
  preference_scorer.py    # LLM structured room preference scoring
  kb_retrieval.py         # KB multi-query recall, merge, source conversion
  kb_rerank.py            # Governed KB rerank
  confidence.py           # KB confidence gates
  eval_metrics.py         # hit@k, MRR, nDCG
```

Upgrade integrations:

```text
backend/src/aptguide3/integrations/vector_client.py
backend/src/aptguide3/integrations/lease_client.py
```

Upgrade procedures:

```text
backend/src/aptguide3/procedures/room_search.py
backend/src/aptguide3/procedures/kb_qa.py
backend/src/aptguide3/api/deps.py
```

Add sync and eval:

```text
backend/scripts/sync_room_vectors.py
backend/scripts/sync_kb_vectors.py
backend/evals/datasets/rag_retrieval_cases.yaml
backend/evals/runners/run_rag_eval.py
```

Add tests:

```text
backend/tests/unit/rag/test_planning.py
backend/tests/unit/rag/test_room_retrieval.py
backend/tests/unit/rag/test_room_ranking.py
backend/tests/unit/rag/test_preference_scorer.py
backend/tests/unit/rag/test_kb_retrieval.py
backend/tests/unit/rag/test_kb_rerank.py
backend/tests/unit/rag/test_confidence.py
backend/tests/unit/rag/test_eval_metrics.py
backend/tests/unit/procedures/test_room_search.py
backend/tests/unit/procedures/test_kb_qa.py
backend/tests/unit/test_no_keyword_fallback.py
backend/tests/integration/test_rag_live.py
```

## Core Schemas

Add `backend/src/aptguide3/rag/schemas.py`:

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

TaskName = Literal["room_search", "kb_qa", "fallback"]
ValidationMode = Literal["none", "lease_required", "source_required"]
SourcePolicy = Literal["none", "source_required", "high_risk_source_required"]


class RetrievalPlan(BaseModel):
    task: TaskName
    raw_message: str
    hard_filters: dict[str, Any] = Field(default_factory=dict)
    soft_preferences: list[str] = Field(default_factory=list)
    semantic_queries: list[str] = Field(default_factory=list)
    sparse_queries: list[str] = Field(default_factory=list)
    module_intent: str | None = None
    risk_level: Literal["low", "medium", "high"] = "low"
    validation_mode: ValidationMode = "none"
    source_policy: SourcePolicy = "none"


class RoomCandidate(BaseModel):
    room_id: int
    apartment_id: int | None = None
    semantic_score: float = 0.0
    matched_query: str = ""
    recall_source: str = "vector"


class ValidatedRoom(BaseModel):
    room_id: int
    apartment_id: int = 0
    apartment_name: str = ""
    room_number: str = ""
    district_id: int | None = None
    district_name: str = ""
    rent: int = 0
    payment_types: list[str] = Field(default_factory=list)
    lease_terms: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    facilities: list[str] = Field(default_factory=list)
    is_appointable: bool = False
    semantic_score: float = 0.0
    matched_query: str = ""


class PreferenceScore(BaseModel):
    room_id: int
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_preferences: list[str] = Field(default_factory=list)
    missing_preferences: list[str] = Field(default_factory=list)
    reason: str = ""


class RankedRoom(BaseModel):
    room_id: int
    apartment_id: int = 0
    apartment_name: str = ""
    room_number: str = ""
    district_name: str = ""
    rent: int = 0
    payment_types: list[str] = Field(default_factory=list)
    lease_terms: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    facilities: list[str] = Field(default_factory=list)
    is_appointable: bool = False
    final_score: float = 0.0
    semantic_score: float = 0.0
    budget_score: float = 0.0
    area_score: float = 0.0
    preference_score: float = 0.0
    availability_score: float = 0.0
    matched_query: str = ""
    recommendation_reason: str = ""


class KBSource(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    module: str
    content: str
    score: float
    risk_level: Literal["low", "medium", "high"] = "low"
    matched_query: str = ""
    recall_source: str = "dense"
```

## Task 1: Retrieval Plan Builder

**Files:**
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/__init__.py`
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/schemas.py`
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/planning.py`
- Test: `AptGuide 3.0/backend/tests/unit/rag/test_planning.py`

- [ ] **Step 1: Write failing tests for room and KB planning**

```python
from aptguide3.domain.understanding import RiskDecision, UnderstandingResult
from aptguide3.rag.planning import build_retrieval_plan


def test_room_search_plan_uses_llm_understanding_fields():
    understanding = UnderstandingResult(
        raw_message="找番禺1500以内安静的房子",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.92,
        hard_filters={"district_name": "番禺区", "max_rent": 1500},
        soft_preferences=["安静", "低噪音"],
        retrieval_queries=["番禺 1500以内 安静 房源", "低噪音 适合学习 公寓"],
        risk=RiskDecision(level="low", response_mode="normal_answer"),
    )

    plan = build_retrieval_plan(understanding)

    assert plan.task == "room_search"
    assert plan.hard_filters["max_rent"] == 1500
    assert plan.soft_preferences == ["安静", "低噪音"]
    assert plan.semantic_queries[:2] == ["找番禺1500以内安静的房子", "番禺 1500以内 安静 房源"]
    assert plan.validation_mode == "lease_required"


def test_high_risk_kb_plan_requires_high_risk_sources():
    understanding = UnderstandingResult(
        raw_message="押金不退怎么办",
        route="rag",
        task="kb_qa",
        domain="lease",
        action="ask_policy",
        confidence=0.9,
        retrieval_queries=["押金退还规则", "押金扣除和退租流程"],
        risk=RiskDecision(level="high", response_mode="kb_grounded_answer"),
    )

    plan = build_retrieval_plan(understanding)

    assert plan.task == "kb_qa"
    assert plan.module_intent == "lease"
    assert plan.risk_level == "high"
    assert "租房规则 流程 风险说明 押金不退怎么办" in plan.semantic_queries
    assert plan.source_policy == "high_risk_source_required"
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/rag/test_planning.py -q
```

Expected: fails because `aptguide3.rag.planning` does not exist.

- [ ] **Step 3: Implement schemas and plan builder**

Create `schemas.py` using the Core Schemas section above.

Create `planning.py`:

```python
from __future__ import annotations

from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.rag.schemas import RetrievalPlan


def build_retrieval_plan(understanding: UnderstandingResult) -> RetrievalPlan:
    if understanding.route != "rag":
        return RetrievalPlan(
            task="fallback",
            raw_message=understanding.raw_message,
            risk_level=understanding.risk.level,
        )

    if understanding.task == "room_search":
        semantic_queries = _dedupe([understanding.raw_message, *understanding.retrieval_queries])
        return RetrievalPlan(
            task="room_search",
            raw_message=understanding.raw_message,
            hard_filters=dict(understanding.hard_filters),
            soft_preferences=list(understanding.soft_preferences),
            semantic_queries=semantic_queries,
            sparse_queries=_build_sparse_queries(understanding),
            risk_level=understanding.risk.level,
            validation_mode="lease_required",
            source_policy="none",
        )

    if understanding.task == "kb_qa":
        module_intent = (
            understanding.domain
            if understanding.domain in {"payment", "lease", "life", "appointment", "account", "policy"}
            else None
        )
        semantic_queries = _dedupe([
            understanding.raw_message,
            *understanding.retrieval_queries,
            _step_back_query(understanding.raw_message, module_intent),
        ])
        return RetrievalPlan(
            task="kb_qa",
            raw_message=understanding.raw_message,
            hard_filters=dict(understanding.hard_filters),
            soft_preferences=list(understanding.soft_preferences),
            semantic_queries=semantic_queries,
            sparse_queries=_build_sparse_queries(understanding),
            module_intent=module_intent,
            risk_level=understanding.risk.level,
            validation_mode="source_required",
            source_policy="high_risk_source_required"
            if understanding.risk.level == "high"
            else "source_required",
        )

    return RetrievalPlan(
        task="fallback",
        raw_message=understanding.raw_message,
        risk_level=understanding.risk.level,
    )


def _build_sparse_queries(understanding: UnderstandingResult) -> list[str]:
    values = [understanding.raw_message, *understanding.soft_preferences]
    area = understanding.hard_filters.get("area_text") or understanding.hard_filters.get("district_name")
    if area:
        values.append(str(area))
    return _dedupe(values)


def _step_back_query(message: str, module_intent: str | None) -> str:
    if module_intent == "lease":
        return f"租赁合同 押金 退租 违约 规则 {message}"
    if module_intent == "payment":
        return f"租金 支付 费用 退款 规则 {message}"
    if module_intent == "appointment":
        return f"看房预约 取消 改期 流程 {message}"
    return f"租房规则 流程 风险说明 {message}"


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result[:4]
```

- [ ] **Step 4: Verify tests pass**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/rag/test_planning.py -q
```

Expected: `2 passed`.

## Task 2: Vector Client Upgrade

**Files:**
- Modify: `AptGuide 3.0/backend/src/aptguide3/integrations/vector_client.py`
- Test: `AptGuide 3.0/backend/tests/unit/integrations/test_vector_client.py`

- [ ] **Step 1: Write failing tests for room and KB search methods**

```python
from aptguide3.integrations.vector_client import VectorClient


class FakeMilvus:
    def __init__(self):
        self.search_calls = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return [[{
            "id": "room-1",
            "distance": 0.2,
            "entity": {
                "room_id": 1,
                "apartment_id": 10,
                "district_id": 4,
                "district_name": "番禺区",
                "rent": 1500,
                "tags": "[\"安静\"]",
                "facilities": "[\"空调\"]",
            },
        }]]

    def load_collection(self, collection_name):
        self.loaded = collection_name


def test_search_rooms_uses_room_collection_and_filters(monkeypatch):
    fake = FakeMilvus()
    vc = VectorClient.__new__(VectorClient)
    vc._client = fake

    hits = vc.search_rooms([0.1, 0.2], filters={"district_id": 4, "max_rent": 1800}, top_k=3)

    assert hits[0]["room_id"] == 1
    call = fake.search_calls[0]
    assert call["collection_name"] == "apt_room_vector"
    assert 'status == "active"' in call["filter"]
    assert "district_id == 4" in call["filter"]
    assert "rent <= 1800" in call["filter"]
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/integrations/test_vector_client.py -q
```

Expected: fails because `search_rooms()` does not exist.

- [ ] **Step 3: Implement `search_rooms()` and improve `search_kb()` normalization**

Extend `VectorClient` with:

```python
import json

ROOM_COLLECTION = "apt_room_vector"


def search_rooms(self, vector: list[float], filters: dict[str, Any] | None = None, top_k: int = 50) -> list[dict[str, Any]]:
    try:
        self._client.load_collection(ROOM_COLLECTION)
        filter_parts = ['status == "active"']
        if filters:
            if filters.get("district_id") is not None:
                filter_parts.append(f'district_id == {int(filters["district_id"])}')
            if filters.get("max_rent") is not None:
                filter_parts.append(f'rent <= {int(filters["max_rent"])}')
            if filters.get("min_rent") is not None:
                filter_parts.append(f'rent >= {int(filters["min_rent"])}')
        results = self._client.search(
            collection_name=ROOM_COLLECTION,
            data=[vector],
            limit=top_k,
            output_fields=[
                "room_id", "apartment_id", "apartment_name", "district_id", "district_name",
                "rent", "payment_types", "lease_terms", "tags", "facilities", "content_hash",
            ],
            filter=" and ".join(filter_parts),
            search_params={"metric_type": "COSINE", "params": {"ef": 64}},
        )
    except Exception:
        return []
    return _normalize_results(results)


def _normalize_json_field(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _normalize_results(results: list) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    if not results:
        return normalized
    for batch in results:
        for hit in batch:
            entity = dict(hit.get("entity", {}))
            for key in ("payment_types", "lease_terms", "tags", "facilities"):
                if key in entity:
                    entity[key] = _normalize_json_field(entity[key])
            entity["distance"] = hit.get("distance", 0.0)
            normalized.append(entity)
    return normalized
```

- [ ] **Step 4: Verify vector tests pass**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/integrations/test_vector_client.py -q
```

Expected: all vector client tests pass.

## Task 3: LLM Preference Scorer

**Files:**
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/preference_scorer.py`
- Test: `AptGuide 3.0/backend/tests/unit/rag/test_preference_scorer.py`

- [ ] **Step 1: Write tests for structured LLM scoring**

```python
from aptguide3.rag.preference_scorer import LLMPreferenceScorer
from aptguide3.rag.schemas import ValidatedRoom


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def create(self, **kwargs):
        return FakeResponse("""
        {
          "scores": [
            {
              "room_id": 1,
              "score": 0.86,
              "matched_preferences": ["安静"],
              "missing_preferences": ["近地铁"],
              "reason": "房源标签显示安静，但未明确近地铁。"
            }
          ]
        }
        """)


class FakeClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeCompletions()})()


def test_llm_preference_scorer_returns_structured_scores():
    scorer = LLMPreferenceScorer(FakeClient(), model="fake")
    rooms = [ValidatedRoom(room_id=1, rent=1500, tags=["安静"], facilities=["空调"])]

    scores = scorer.score("找安静近地铁的房子", ["安静", "近地铁"], rooms)

    assert scores[1].score == 0.86
    assert scores[1].matched_preferences == ["安静"]
    assert scores[1].missing_preferences == ["近地铁"]
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/rag/test_preference_scorer.py -q
```

Expected: fails because `preference_scorer.py` does not exist.

- [ ] **Step 3: Implement LLM preference scorer with safe fallback**

```python
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from aptguide3.rag.schemas import PreferenceScore, ValidatedRoom


class PreferenceScoreBatch(BaseModel):
    scores: list[PreferenceScore] = Field(default_factory=list)


class LLMPreferenceScorer:
    def __init__(self, client: Any | None, model: str) -> None:
        self.client = client
        self.model = model

    def score(
        self,
        raw_message: str,
        soft_preferences: list[str],
        rooms: list[ValidatedRoom],
    ) -> dict[int, PreferenceScore]:
        if self.client is None or not soft_preferences or not rooms:
            return {
                room.room_id: PreferenceScore(room_id=room.room_id, score=0.5, reason="无偏好评分，使用中性分。")
                for room in rooms
            }
        payload = {
            "user_message": raw_message,
            "soft_preferences": soft_preferences,
            "rooms": [
                {
                    "room_id": room.room_id,
                    "rent": room.rent,
                    "district_name": room.district_name,
                    "tags": room.tags,
                    "facilities": room.facilities,
                    "payment_types": room.payment_types,
                    "lease_terms": room.lease_terms,
                }
                for room in rooms
            ],
        }
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是租房推荐偏好匹配评分器。只根据输入的房源公开字段评分，"
                            "不要编造价格、地址、上架状态或可预约状态。返回 JSON: "
                            "{\"scores\":[{\"room_id\":1,\"score\":0.0,\"matched_preferences\":[],"
                            "\"missing_preferences\":[],\"reason\":\"\"}]}"
                        ),
                    },
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content or "{}"
            batch = PreferenceScoreBatch.model_validate_json(content)
        except (ValidationError, Exception):
            batch = PreferenceScoreBatch()

        by_id = {score.room_id: score for score in batch.scores}
        for room in rooms:
            by_id.setdefault(
                room.room_id,
                PreferenceScore(room_id=room.room_id, score=0.5, reason="偏好评分不可用，使用中性分。"),
            )
        return by_id
```

- [ ] **Step 4: Verify tests pass**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/rag/test_preference_scorer.py -q
```

Expected: all preference scorer tests pass.

## Task 4: Room Retrieval and Ranking

**Files:**
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/room_retrieval.py`
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/room_ranking.py`
- Modify: `AptGuide 3.0/backend/src/aptguide3/procedures/room_search.py`
- Test: `AptGuide 3.0/backend/tests/unit/rag/test_room_retrieval.py`
- Test: `AptGuide 3.0/backend/tests/unit/rag/test_room_ranking.py`
- Test: `AptGuide 3.0/backend/tests/unit/procedures/test_room_search.py`

- [ ] **Step 1: Test vector recall, lease validation, and LLM preference scoring**

```python
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.rag.planning import build_retrieval_plan
from aptguide3.rag.room_retrieval import retrieve_ranked_rooms
from aptguide3.rag.schemas import PreferenceScore


class StubEmbedding:
    def embed(self, text):
        return [0.1, 0.2, 0.3]


class StubVector:
    def search_rooms(self, vector, filters, top_k=30):
        return [
            {"room_id": 1, "apartment_id": 10, "distance": 0.1},
            {"room_id": 2, "apartment_id": 20, "distance": 0.4},
        ]


class StubLease:
    async def validate_rooms(self, room_ids, filters):
        return [
            {
                "room_id": 1,
                "apartment_id": 10,
                "apartment_name": "大学城南亭寓",
                "room_number": "302",
                "district_id": 4,
                "district_name": "番禺区",
                "rent": 1500,
                "payment_types": ["MONTHLY"],
                "lease_terms": [6, 12],
                "tags": ["安静"],
                "facilities": ["空调"],
                "is_appointable": True,
            }
        ]


class StubScorer:
    def score(self, raw_message, soft_preferences, rooms):
        return {1: PreferenceScore(room_id=1, score=0.9, reason="符合安静偏好。")}


def test_retrieve_ranked_rooms_validates_with_lease_before_ranking():
    understanding = UnderstandingResult(
        raw_message="找番禺1500以内安静房源",
        route="rag",
        task="room_search",
        confidence=0.9,
        hard_filters={"district_id": 4, "max_rent": 1500},
        soft_preferences=["安静"],
        retrieval_queries=["番禺 安静 房源"],
    )
    plan = build_retrieval_plan(understanding)

    rooms = retrieve_ranked_rooms(plan, StubVector(), StubEmbedding(), StubLease(), StubScorer(), top_n=5)

    assert [room.room_id for room in rooms] == [1]
    assert rooms[0].preference_score == 0.9
    assert rooms[0].recommendation_reason == "符合安静偏好。"
```

- [ ] **Step 2: Implement retrieval**

```python
from __future__ import annotations

import asyncio
from typing import Any

from aptguide3.rag.room_ranking import rank_rooms
from aptguide3.rag.schemas import RetrievalPlan, RoomCandidate, ValidatedRoom


def retrieve_ranked_rooms(
    plan: RetrievalPlan,
    vector_client: Any,
    embedding_client: Any,
    lease_client: Any,
    preference_scorer: Any,
    top_n: int = 5,
    top_k: int = 30,
) -> list:
    if plan.task != "room_search":
        return []
    best_by_room: dict[int, RoomCandidate] = {}
    for query in plan.semantic_queries:
        vector = embedding_client.embed(query)
        if not vector:
            continue
        for hit in vector_client.search_rooms(vector, filters=plan.hard_filters, top_k=top_k):
            room_id = int(hit.get("room_id", 0))
            if room_id <= 0:
                continue
            distance = float(hit.get("distance", 1.0))
            semantic_score = max(0.0, min(1.0, 1.0 - distance))
            existing = best_by_room.get(room_id)
            if existing is None or semantic_score > existing.semantic_score:
                best_by_room[room_id] = RoomCandidate(
                    room_id=room_id,
                    apartment_id=hit.get("apartment_id"),
                    semantic_score=semantic_score,
                    matched_query=query,
                )
    if not best_by_room:
        return []
    validated_payloads = _run_async(
        lease_client.validate_rooms([c.room_id for c in best_by_room.values()], plan.hard_filters)
    )
    validated = []
    for payload in validated_payloads:
        room_id = int(payload.get("room_id", 0))
        candidate = best_by_room.get(room_id)
        if candidate is None:
            continue
        validated.append(ValidatedRoom(
            **payload,
            semantic_score=candidate.semantic_score,
            matched_query=candidate.matched_query,
        ))
    if not validated:
        return []
    preference_scores = preference_scorer.score(plan.raw_message, plan.soft_preferences, validated)
    return rank_rooms(validated, plan, preference_scores, top_n=top_n)


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)
```

- [ ] **Step 3: Implement deterministic score fusion**

```python
from __future__ import annotations

from aptguide3.rag.schemas import PreferenceScore, RankedRoom, RetrievalPlan, ValidatedRoom

W_SEMANTIC = 0.35
W_BUDGET = 0.25
W_AREA = 0.15
W_PREFERENCE = 0.20
W_AVAILABILITY = 0.05


def rank_rooms(
    rooms: list[ValidatedRoom],
    plan: RetrievalPlan,
    preference_scores: dict[int, PreferenceScore],
    top_n: int = 5,
) -> list[RankedRoom]:
    ranked: list[RankedRoom] = []
    for room in rooms:
        pref = preference_scores.get(room.room_id, PreferenceScore(room_id=room.room_id, score=0.5))
        budget_score = _score_budget(room.rent, plan.hard_filters.get("max_rent"))
        area_score = _score_area(room.district_id, plan.hard_filters.get("district_id"))
        availability_score = 1.0 if room.is_appointable else 0.5
        final_score = (
            W_SEMANTIC * room.semantic_score
            + W_BUDGET * budget_score
            + W_AREA * area_score
            + W_PREFERENCE * pref.score
            + W_AVAILABILITY * availability_score
        )
        ranked.append(RankedRoom(
            room_id=room.room_id,
            apartment_id=room.apartment_id,
            apartment_name=room.apartment_name,
            room_number=room.room_number,
            district_name=room.district_name,
            rent=room.rent,
            payment_types=room.payment_types,
            lease_terms=room.lease_terms,
            tags=room.tags,
            facilities=room.facilities,
            is_appointable=room.is_appointable,
            final_score=round(final_score, 4),
            semantic_score=round(room.semantic_score, 4),
            budget_score=round(budget_score, 4),
            area_score=round(area_score, 4),
            preference_score=round(pref.score, 4),
            availability_score=round(availability_score, 4),
            matched_query=room.matched_query,
            recommendation_reason=pref.reason or "综合匹配度较高。",
        ))
    return sorted(ranked, key=lambda item: item.final_score, reverse=True)[:top_n]


def _score_budget(rent: int, max_rent: int | None) -> float:
    if max_rent is None or max_rent <= 0 or rent <= 0:
        return 0.5
    ratio = rent / max_rent
    if ratio <= 0.8:
        return 1.0
    if ratio <= 1.0:
        return 0.75
    if ratio <= 1.1:
        return 0.3
    return 0.0


def _score_area(room_district_id: int | None, target_district_id: int | None) -> float:
    if target_district_id is None:
        return 0.5
    return 1.0 if room_district_id == target_district_id else 0.0
```

- [ ] **Step 4: Wire RoomSearchProcedure**

Update constructor dependencies:

```python
class RoomSearchProcedure:
    name = "room_search"

    def __init__(self, lease_client=None, vector_client=None, embedding_client=None, preference_scorer=None):
        self._lease_client = lease_client
        self._vector_client = vector_client
        self._embedding_client = embedding_client
        self._preference_scorer = preference_scorer
```

Use `build_retrieval_plan()` and `retrieve_ranked_rooms()` when all dependencies exist. Keep the existing conservative placeholder when vector, embedding, or lease is unavailable.

- [ ] **Step 5: Verify room RAG tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/rag/test_room_retrieval.py tests/unit/rag/test_room_ranking.py tests/unit/procedures/test_room_search.py -q
```

Expected: all room RAG tests pass.

## Task 5: KB Retrieval, Rerank, and Confidence Gate

**Files:**
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/kb_retrieval.py`
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/kb_rerank.py`
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/confidence.py`
- Modify: `AptGuide 3.0/backend/src/aptguide3/procedures/kb_qa.py`
- Test: `AptGuide 3.0/backend/tests/unit/rag/test_kb_retrieval.py`
- Test: `AptGuide 3.0/backend/tests/unit/rag/test_kb_rerank.py`
- Test: `AptGuide 3.0/backend/tests/unit/rag/test_confidence.py`

- [ ] **Step 1: Implement confidence gate tests**

```python
from aptguide3.rag.confidence import check_confidence
from aptguide3.rag.schemas import KBSource


def test_high_risk_requires_high_risk_lease_or_payment_source():
    sources = [
        KBSource(chunk_id="1", doc_id="KB-LIFE-001", title="生活", module="life", content="x", score=0.9, risk_level="low"),
        KBSource(chunk_id="2", doc_id="KB-LEASE-005", title="押金", module="lease", content="x", score=0.8, risk_level="high"),
    ]

    assert check_confidence(sources, "high") is True


def test_high_risk_rejects_low_risk_source_even_with_score():
    sources = [
        KBSource(chunk_id="1", doc_id="KB-LIFE-001", title="生活", module="life", content="x", score=0.9, risk_level="low"),
    ]

    assert check_confidence(sources, "high") is False
```

- [ ] **Step 2: Implement confidence gate**

```python
from __future__ import annotations

from aptguide3.rag.schemas import KBSource

THRESHOLDS = {"low": 0.45, "medium": 0.55, "high": 0.65}
HIGH_RISK_MODULES = {"lease", "payment", "account"}


def check_confidence(sources: list[KBSource], risk_level: str) -> bool:
    if not sources:
        return False
    top = sources[0]
    if top.score < THRESHOLDS.get(risk_level, THRESHOLDS["low"]):
        return False
    if risk_level == "medium":
        return any(source.module in HIGH_RISK_MODULES for source in sources[:3])
    if risk_level == "high":
        return any(
            source.risk_level == "high" and source.module in HIGH_RISK_MODULES
            for source in sources[:3]
        )
    return True


def fallback_message(risk_level: str) -> str:
    if risk_level == "high":
        return "这个问题涉及合同、押金、退款或账户安全，我暂时没有足够可靠的规则来源，建议联系门店或人工客服确认。"
    if risk_level == "medium":
        return "这个问题需要进一步确认，我暂时无法给出确定答复，建议联系门店客服核实。"
    return "我暂时没有找到足够相关的规则来源，请换个问法或联系人工客服。"
```

- [ ] **Step 3: Implement KB retrieval and rerank**

`kb_retrieval.py` should:

```text
for each semantic query:
  embed query
  vector_client.search_kb(vector, top_k=10)
merge by chunk_id
rerank by dense score, module match, risk match, content presence
convert to KBSource
run confidence gate
```

Keep lexical overlap out of the main semantic decision. If sparse score is added later, cap it at a documented weak weight.

- [ ] **Step 4: Wire KbQaProcedure**

`KbQaProcedure.run()` should:

```text
build RetrievalPlan
retrieve KB sources
if confidence false -> conservative fallback
if confidence true -> return source cards
```

This phase can return source cards without a final answer generation pass. A later task may add source-bound answer generation if the product needs prose answers instead of cards.

- [ ] **Step 5: Verify KB RAG tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/rag/test_kb_retrieval.py tests/unit/rag/test_kb_rerank.py tests/unit/rag/test_confidence.py tests/unit/procedures/test_kb_qa.py -q
```

Expected: all KB RAG tests pass.

## Task 6: Dependency Wiring

**Files:**
- Modify: `AptGuide 3.0/backend/src/aptguide3/api/deps.py`
- Modify: `AptGuide 3.0/backend/src/aptguide3/config.py`
- Test: `AptGuide 3.0/backend/tests/unit/api/test_deps.py`
- Test: `AptGuide 3.0/backend/tests/unit/test_config.py`

- [ ] **Step 1: Add RAG settings**

Add settings:

```python
rag_room_top_k: int = 30
rag_room_top_n: int = 5
rag_kb_top_k: int = 10
rag_preference_scorer_enabled: bool = True
```

- [ ] **Step 2: Wire vector, embedding, and preference scorer into runtime**

Update `build_runtime()`:

```python
vc, ec = get_kb_clients(settings)
preference_scorer = LLMPreferenceScorer(get_llm_client(settings), settings.llm_model)

runtime.register(RoomSearchProcedure(
    lease_client=lease,
    vector_client=vc,
    embedding_client=ec,
    preference_scorer=preference_scorer,
))
runtime.register(KbQaProcedure(vector_client=vc, embedding_client=ec))
```

If LLM preference scoring is disabled or no LLM client exists, pass a neutral scorer that returns `0.5` for every room.

- [ ] **Step 3: Verify dependency tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/api/test_deps.py tests/unit/test_config.py -q
```

Expected: all dependency/config tests pass.

## Task 7: Sync Scripts

**Files:**
- Create: `AptGuide 3.0/backend/scripts/sync_room_vectors.py`
- Create: `AptGuide 3.0/backend/scripts/sync_kb_vectors.py`
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/chunking.py`
- Test: `AptGuide 3.0/backend/tests/unit/rag/test_chunking.py`

- [ ] **Step 1: Add room and KB chunk builders**

`chunking.py` should provide:

```python
from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _list_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "、".join(str(item) for item in value if item)
    return str(value)

def build_room_vector_text(room: dict) -> str:
    tags = _list_text(room.get("tags"))
    facilities = _list_text(room.get("facilities"))
    payment_types = _list_text(room.get("payment_types"))
    lease_terms = _list_text(room.get("lease_terms"))
    return "\n".join([
        (
            f"[room][{room.get('city_name', '')}][{room.get('district_name', '')}]"
            f"[{room.get('area_label', '')}]"
        ),
        (
            f"房间 {room.get('room_number', '')}，位于 {room.get('apartment_name', '')}。"
            f"月租 {room.get('rent', '')} 元，支持付款方式：{payment_types}，"
            f"租期：{lease_terms}。"
        ),
        (
            f"户型 {room.get('layout', '')}，面积 {room.get('area', '')}。"
            f"标签：{tags}。设施：{facilities}。"
        ),
    ]).strip()

def build_kb_chunk_text(rule: dict) -> str:
    tags = _list_text(rule.get("tags"))
    return (
        f"[{rule.get('module', '')}][{rule.get('doc_type', '')}]"
        f"[{rule.get('title', '')}][{tags}][{rule.get('risk_level', 'low')}]\n"
        f"{rule.get('content', '')}"
    ).strip()


def build_room_vector_record(room: dict, source_version: int) -> dict:
    content = build_room_vector_text(room)
    return {
        "vector_id": f"room-{room.get('room_id')}",
        "room_id": int(room.get("room_id", 0)),
        "apartment_id": int(room.get("apartment_id", 0)),
        "apartment_name": room.get("apartment_name", ""),
        "city_id": room.get("city_id"),
        "district_id": room.get("district_id"),
        "district_name": room.get("district_name", ""),
        "rent": room.get("rent"),
        "payment_types": room.get("payment_types") or [],
        "lease_terms": room.get("lease_terms") or [],
        "tags": room.get("tags") or [],
        "facilities": room.get("facilities") or [],
        "profile_type": "room",
        "content": content,
        "content_hash": compute_content_hash(json.dumps(room, ensure_ascii=False, sort_keys=True)),
        "source_version": source_version,
        "status": "active",
    }
```

Room text must contain only public fields from lease sync DTO. KB text must include module, title, tags, risk level, and reviewed content.

- [ ] **Step 2: Add KB validation gates**

`sync_kb_vectors.py` must reject:

```text
missing doc_id
duplicate doc_id
status not in reviewed/approved/active
missing reviewed_by
phone / ID card / bank card patterns
high-risk module without risk_level
```

PII regex is allowed here because it is an ingestion safety gate, not user intent understanding.

- [ ] **Step 3: Add room sync path**

`sync_room_vectors.py` must:

```text
call lease /internal/ai/tools/sync/rooms
build vector text
compute content_hash
embed changed records only
upsert apt_room_vector
mark stale rooms inactive
write sync report
```

- [ ] **Step 4: Verify sync unit tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/rag/test_chunking.py -q
```

Expected: all chunking and ingestion validation tests pass.

## Task 8: Eval Gates

**Files:**
- Create: `AptGuide 3.0/backend/src/aptguide3/rag/eval_metrics.py`
- Create: `AptGuide 3.0/backend/evals/datasets/rag_retrieval_cases.yaml`
- Create: `AptGuide 3.0/backend/evals/runners/run_rag_eval.py`
- Test: `AptGuide 3.0/backend/tests/unit/rag/test_eval_metrics.py`

- [ ] **Step 1: Implement metrics**

```python
from __future__ import annotations

import math


def hit_at_k(actual_ids: list[str | int], expected_ids: set[str | int], k: int) -> bool:
    return bool(set(actual_ids[:k]) & expected_ids)


def mean_reciprocal_rank(actual_ids: list[str | int], expected_ids: set[str | int]) -> float:
    for rank, item_id in enumerate(actual_ids, 1):
        if item_id in expected_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(actual_ids: list[str | int], expected_ids: set[str | int], k: int) -> float:
    dcg = 0.0
    for index, item_id in enumerate(actual_ids[:k], 1):
        if item_id in expected_ids:
            dcg += 1.0 / math.log2(index + 1)
    ideal_hits = min(len(expected_ids), k)
    if ideal_hits == 0:
        return 0.0
    idcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    return round(dcg / idcg, 6)
```

- [ ] **Step 2: Seed minimal eval dataset**

Add representative cases:

```yaml
- id: room-panyu-quiet-001
  task: room_search
  query: 找番禺1500以内安静一点的房子
  expected_room_ids: []
  expected:
    must_validate_with_lease: true
    must_not_return_unvalidated_vector_room: true

- id: kb-lease-deposit-001
  task: kb_qa
  query: 押金不退怎么办
  expected_doc_ids:
    - KB-LEASE-005
  risk_level: high
  expected:
    must_cite_source: true
    must_not_make_unverified_commitment: true
```

Empty `expected_room_ids` is valid for the first committed dataset until live AptGuide 3.0 room vectors are synced and IDs are known. The runner must report such cases as smoke cases, not as retrieval quality gates.

- [ ] **Step 3: Add eval runner**

Runner output:

```text
reports/rag-evaluation-report.md
```

Report fields:

```text
case_count
room_hit_at_5
kb_source_hit_at_3
high_risk_fallback_pass_rate
unvalidated_room_count
latency summary
```

- [ ] **Step 4: Verify eval metrics**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/rag/test_eval_metrics.py -q
```

Expected: all metric tests pass.

## Task 9: Anti-Regression Guardrails

**Files:**
- Modify: `AptGuide 3.0/backend/tests/unit/test_no_keyword_fallback.py`
- Test: `AptGuide 3.0/backend/tests/unit/test_no_keyword_fallback.py`

- [ ] **Step 1: Extend source scan**

Scan these runtime files:

```text
src/aptguide3/understanding/llm_understanding.py
src/aptguide3/understanding/validation.py
src/aptguide3/application/chat_service.py
src/aptguide3/rag/planning.py
src/aptguide3/rag/room_retrieval.py
src/aptguide3/rag/room_ranking.py
src/aptguide3/rag/preference_scorer.py
src/aptguide3/rag/kb_retrieval.py
src/aptguide3/rag/kb_rerank.py
src/aptguide3/procedures/room_search.py
src/aptguide3/procedures/kb_qa.py
```

Forbidden examples:

```text
_detect_task
_extract_budget
_extract_district
_extract_preferences
keyword
fallback_patterns
room_keywords
kb_keywords
```

Do not forbid `regex` globally because sync ingestion needs PII regex and lease client needs key conversion. Scope regex prohibition to understanding and RAG runtime files only.

- [ ] **Step 2: Verify guardrail**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/test_no_keyword_fallback.py -q
```

Expected: guardrail test passes.

## Task 10: Live RAG Smoke

**Files:**
- Create: `AptGuide 3.0/backend/tests/integration/test_rag_live.py`
- Modify: `AptGuide 3.0/docs/tests/verification-log.md`
- Modify: `AptGuide 3.0/docs/tests/evaluation-report.md`

- [ ] **Step 1: Add skip-safe live test**

Test should skip unless all are configured:

```text
APTGUIDE3_LIVE_TESTS=1
APTGUIDE3_LLM_API_KEY
APTGUIDE3_EMBEDDING_API_KEY
APTGUIDE3_VECTOR_URI
APTGUIDE3_LEASE_BASE_URL
```

Coverage:

```text
room_search request returns either validated cards or conservative no-result response
kb_qa request returns source cards or confidence fallback
no unvalidated room cards are returned
```

- [ ] **Step 2: Run unit regression**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest -q
uv run ruff check src tests
```

Expected: all non-live tests pass and ruff is clean.

- [ ] **Step 3: Run live smoke when dependencies are available**

Run:

```bash
cd "AptGuide 3.0/backend"
APTGUIDE3_LIVE_TESTS=1 uv run pytest tests/integration/test_rag_live.py -q
```

Expected: pass with live services, or skip with explicit missing dependency reason.

## Acceptance Criteria

Milestone 4 is complete only when all criteria are met:

- LLM remains the only natural-language understanding layer.
- Room search uses vector recall when vector and embedding clients are configured.
- Room cards are returned only after lease validation.
- Room preference matching uses LLM structured scoring, not string containment as the primary score.
- KB QA uses multi-query recall, rerank, confidence gate, and source cards.
- High-risk KB questions do not receive unsupported policy commitments.
- Sync scripts support content hash, incremental embedding, and inactive marking.
- RAG eval runner exists and writes a report.
- Anti-regression source scan prevents keyword fallback from returning to runtime.
- `uv run pytest -q` and `uv run ruff check src tests` pass, or skipped live tests are recorded explicitly.

## Known Risks

- The LLM preference scorer adds latency and token cost. Keep batch size small and return neutral score on failure.
- Room vector quality depends on sync text quality. Poor room profiles will reduce recall even if ranking is correct.
- KB quality depends on reviewed source coverage. Confidence gates will produce conservative fallback if sources are missing.
- Current 3.0 `LeaseClient.validate_rooms()` only supports limited filters. Expanding lease search contract may be required for full production behavior.
- Main-system chain test remains necessary after RAG works directly against AptGuide 3.0.

## Verification Commands

Run after implementation:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/rag -q
uv run pytest tests/unit/procedures/test_room_search.py tests/unit/procedures/test_kb_qa.py -q
uv run pytest tests/unit/test_no_keyword_fallback.py -q
uv run pytest -q
uv run ruff check src tests
```

Live verification when dependencies are configured:

```bash
cd "AptGuide 3.0/backend"
APTGUIDE3_LIVE_TESTS=1 uv run pytest tests/integration/test_rag_live.py -q
```

## Execution Order

1. Task 1: RetrievalPlan.
2. Task 2: VectorClient upgrade.
3. Task 3: LLM preference scorer.
4. Task 4: Room retrieval and ranking.
5. Task 5: KB retrieval and confidence.
6. Task 6: dependency wiring.
7. Task 7: sync scripts.
8. Task 8: eval gates.
9. Task 9: anti-regression guardrails.
10. Task 10: live smoke and docs verification.

Do not start with sync scripts. Runtime contracts and tests must exist first so ingestion work has a stable target schema.
