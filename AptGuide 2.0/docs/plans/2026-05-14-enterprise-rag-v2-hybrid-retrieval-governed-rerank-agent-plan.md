# Enterprise RAG v2 Hybrid Retrieval And Governed Rerank Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade AptGuide 2.0 from character-match-heavy MVP RAG into an enterprise-grade, eval-gated hybrid retrieval system with governed rerank, lease validation, trace evidence, and rollback-safe feature gating.

**Architecture:** Keep deterministic rules only for hard constraints and safety control, move semantic decisions into explicit planning, hybrid retrieval, calibrated rerank, and business validation layers. Preserve default `/chat` MVP behavior; expose RAG v2 only behind configuration until eval gates pass.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest, existing `VectorAdapter`, existing `LeaseAdapter`, existing `aptguide2.harness.tools.ToolRuntime`, Milvus, YAML eval datasets.

---

## 0. Core Enterprise Principle

Do not treat "remove character matching" as a blanket rule.

Enterprise RAG separates decision types:

| Decision | Correct mechanism | Reason |
| --- | --- | --- |
| Budget, district, payment type, lease term | Deterministic parser | These are hard filters and must be explainable. |
| Safety boundary, write-operation confirmation, user data access | Deterministic policy | These are governance controls, not ranking signals. |
| KB relevance, source ordering, soft preference match, module intent | Hybrid retrieval + calibrated rerank | These are semantic relevance decisions and must not be led by ad hoc character overlap. |
| Room facts, price, listing status, appointment availability | Lease validation | Milvus is only candidate recall, never the fact source. |
| Thresholds and rollout readiness | Eval gates and trace evidence | Quality must be measured, not guessed. |

This plan upgrades the semantic path without removing deterministic controls that belong in an enterprise product.

## 1. Reality Audit Gate

The executing agent must start here before changing code.

- [ ] **Step 1: Check worktree and current project state**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform"
git status --short
sed -n '1,220p' "AptGuide 2.0/progress/current-plan.md"
sed -n '1,260p' "AptGuide 2.0/docs/README.md"
```

Expected:

- There may be existing uncommitted changes.
- Do not revert unrelated changes.
- Current objective should mention RAG Module Integration v2 / Quality Upgrade.

- [ ] **Step 2: Verify baseline tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/e2e -q
```

Expected:

- Passes with the current baseline.
- If this fails before your edits, stop and write `reports/rag-v2-reality-addendum.md` with failing commands and observed failures.

- [ ] **Step 3: Inspect the current character-match surface**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
rg -n "keyword|keywords|overlap|in message|in query|in room_text|set\\(|PREFERENCE_SYNONYMS|fallback_patterns|kb_keywords|room_keywords|module_keywords" src/aptguide2/rag tests/unit/rag
```

Expected:

- Matches in `query_understanding.py`, `kb_retrieval.py`, and `ranking.py`.
- Use the results to fill the audit table in Task 1.

## 2. Non-Negotiable Constraints

- [ ] Keep default `/chat` behavior as current MVP unless a task explicitly says to add a feature-flagged branch.
- [ ] Keep existing `aptguide2.rag` public behavior passing until RAG v2 is explicitly selected.
- [ ] Do not call real Milvus, lease, or LLM services in unit tests.
- [ ] Do not add a production-registerable mock backend.
- [ ] Do not display a room unless it has passed lease validation in RAG v2.
- [ ] Do not let character overlap be the primary KB source ranking signal in RAG v2.
- [ ] Do not use LLM-generated text as a policy fact.
- [ ] Do not mark feature/project state as passed without test and eval evidence.

## 3. Target File Map

Create or modify only these areas unless the Reality Audit Gate proves a variance is needed.

| Path | Responsibility |
| --- | --- |
| `backend/src/aptguide2/rag/planning.py` | `RetrievalPlan`, query rewrite strategy, module intent, replacement boundary for semantic decisions. |
| `backend/src/aptguide2/rag/hybrid.py` | Dense + sparse result merge, score normalization, dedupe, retrieval channel attribution. |
| `backend/src/aptguide2/rag/sparse.py` | Local sparse lexical retrieval/ranking helpers for offline tests and fallback lexical signal. |
| `backend/src/aptguide2/rag/rerank.py` | Governed rerank with explicit feature weights and no primary character-overlap dependency. |
| `backend/src/aptguide2/rag/validation.py` | Lease validation gate for room candidates. |
| `backend/src/aptguide2/rag/pipeline_v2.py` | RAG v2 orchestration behind feature flag. |
| `backend/src/aptguide2/rag/eval_metrics.py` | hit@k, MRR, nDCG, source gate metrics, fact mismatch counters. |
| `backend/evals/runners/run_rag_v2.py` | Offline RAG v2 eval runner. |
| `backend/tests/unit/rag/test_planning.py` | Planning and rewrite tests. |
| `backend/tests/unit/rag/test_hybrid.py` | Hybrid merge and score normalization tests. |
| `backend/tests/unit/rag/test_rerank.py` | Governed rerank tests. |
| `backend/tests/unit/rag/test_validation.py` | Lease validation tests with fake adapter/runtime only. |
| `backend/tests/e2e/test_api.py` | Feature-flagged RAG v2 API behavior tests. |
| `docs/tests/rag-v2-evaluation-gates.md` | Eval gate documentation. |
| `reports/rag-v2-character-match-audit.md` | Audit evidence and replacement decisions. |
| `reports/rag-v2-evaluation-report.md` | Final execution evidence. |
| `progress/current-plan.md` | Current active plan reference and guardrails. |

## 4. Character-Match Governance Boundary

Use this taxonomy throughout implementation:

| Class | Meaning | Examples | Allowed in RAG v2 |
| --- | --- | --- | --- |
| `keep` | Deterministic control-plane extraction or policy | budget regex, district dictionary, payment type, safety refusal | Yes, with tests. |
| `weaken` | Useful weak signal but must not dominate ranking | title token overlap, tag text overlap | Yes, capped feature weight only. |
| `replace` | Semantic decision currently driven by brittle text matching | KB relevance, module relevance, source ranking, soft preference fit | Replace with hybrid retrieval/rerank. |

RAG v2 should make these boundaries visible in code comments, tests, and the audit report.

## 5. Task 1: Character-Match Dependency Audit

**Files:**

- Create: `reports/rag-v2-character-match-audit.md`

- [ ] **Step 1: Create the audit report**

Write this exact structure:

```markdown
# RAG v2 Character-Match Dependency Audit

## Summary

This report classifies character-match logic in the current RAG MVP into keep, weaken, and replace categories.

## Audit Table

| File | Function | Current mechanism | Class | RAG v2 decision | Test evidence required |
| --- | --- | --- | --- | --- | --- |
| backend/src/aptguide2/rag/query_understanding.py | _extract_budget | regex budget extraction | keep | Keep as hard-filter extraction | parser unit tests |
| backend/src/aptguide2/rag/query_understanding.py | _extract_district | district dictionary | keep | Keep as hard-filter extraction | parser unit tests |
| backend/src/aptguide2/rag/query_understanding.py | _extract_payment | payment dictionary | keep | Keep as hard-filter extraction | parser unit tests |
| backend/src/aptguide2/rag/query_understanding.py | _detect_task | keyword task routing | weaken | Keep for MVP path; RAG v2 planning must produce explicit routing evidence and eval coverage | planning tests |
| backend/src/aptguide2/rag/query_understanding.py | _extract_preferences | synonym dictionary | weaken | Use only as seed terms for retrieval plan, not final preference relevance | planning/rerank tests |
| backend/src/aptguide2/rag/kb_retrieval.py | _source_rerank | title character overlap and module keyword boosts | replace | Move to governed rerank using normalized dense, sparse, module, and risk features | rerank tests and KB eval |
| backend/src/aptguide2/rag/ranking.py | _score_tags | string inclusion in tags/facilities | weaken | Cap as weak metadata feature; final ranking must include semantic and validation signals | rerank tests and room eval |

## RAG v2 Policy

1. Character matching may extract hard filters and safety controls.
2. Character matching may be a weak feature with a documented maximum weight.
3. Character matching must not be the primary source ranking or semantic relevance mechanism.
4. Any replacement must be proven by eval gates, not subjective inspection.
```

- [ ] **Step 2: Verify audit report exists**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0"
test -f reports/rag-v2-character-match-audit.md
```

Expected: command exits with status 0.

## 6. Task 2: Add Retrieval Planning Contracts

**Files:**

- Create: `backend/src/aptguide2/rag/planning.py`
- Test: `backend/tests/unit/rag/test_planning.py`

- [ ] **Step 1: Write failing planning tests**

```python
from aptguide2.rag.planning import build_retrieval_plan
from aptguide2.rag.query_understanding import understand_query


def test_room_plan_separates_hard_filters_from_semantic_queries():
    qr = understand_query("番禺1500以内别太吵，最好适合学习")

    plan = build_retrieval_plan(qr)

    assert plan.task == "room_search"
    assert plan.hard_filters["district_id"] == 4
    assert plan.hard_filters["max_rent"] == 1500
    assert plan.semantic_queries
    assert any("安静" in q or "低噪音" in q for q in plan.semantic_queries)
    assert plan.validation_mode == "lease_required"


def test_kb_plan_adds_step_back_for_high_risk_policy_question():
    qr = understand_query("提前退租会扣多少钱")

    plan = build_retrieval_plan(qr)

    assert plan.task == "kb_qa"
    assert plan.risk_level == "high"
    assert plan.module_intent in {"lease", "payment"}
    assert "step_back" in plan.recall_channels
    assert plan.source_policy == "high_risk_source_required"


def test_fallback_plan_does_not_retrieve():
    qr = understand_query("帮我查其他租户手机号")

    plan = build_retrieval_plan(qr)

    assert plan.task == "fallback"
    assert plan.semantic_queries == []
    assert plan.recall_channels == []
```

- [ ] **Step 2: Run the failing tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_planning.py -q
```

Expected: fails because `aptguide2.rag.planning` does not exist.

- [ ] **Step 3: Implement planning contracts**

Create `backend/src/aptguide2/rag/planning.py`:

```python
"""Retrieval planning for RAG v2.

This module separates deterministic control-plane parsing from semantic
retrieval planning. Character matching may seed hard filters and policy, but
semantic relevance must be handled downstream by hybrid retrieval and rerank.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from aptguide2.rag.schemas import QueryUnderstandingResult


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
    recall_channels: list[str] = Field(default_factory=list)
    module_intent: str | None = None
    risk_level: Literal["low", "medium", "high"] = "low"
    validation_mode: ValidationMode = "none"
    source_policy: SourcePolicy = "none"


def build_retrieval_plan(qr: QueryUnderstandingResult) -> RetrievalPlan:
    if qr.task == "fallback":
        return RetrievalPlan(
            task="fallback",
            raw_message=qr.raw_message,
            risk_level=qr.risk_level,
        )

    if qr.task == "room_search":
        semantic_queries = _dedupe([qr.raw_message, *qr.retrieval_queries])
        return RetrievalPlan(
            task="room_search",
            raw_message=qr.raw_message,
            hard_filters=dict(qr.hard_filters),
            soft_preferences=list(qr.soft_preferences),
            semantic_queries=semantic_queries,
            sparse_queries=_build_sparse_queries(qr),
            recall_channels=["dense", "sparse", "metadata"],
            risk_level=qr.risk_level,
            validation_mode="lease_required",
            source_policy="none",
        )

    module_intent = _infer_kb_module_intent(qr.raw_message)
    semantic_queries = _dedupe([qr.raw_message, *_build_kb_rewrite_queries(qr, module_intent)])
    recall_channels = ["dense", "sparse"]
    if qr.risk_level in ("medium", "high"):
        recall_channels.append("step_back")

    return RetrievalPlan(
        task="kb_qa",
        raw_message=qr.raw_message,
        hard_filters=dict(qr.hard_filters),
        soft_preferences=list(qr.soft_preferences),
        semantic_queries=semantic_queries,
        sparse_queries=_build_sparse_queries(qr),
        recall_channels=recall_channels,
        module_intent=module_intent,
        risk_level=qr.risk_level,
        validation_mode="source_required",
        source_policy="high_risk_source_required" if qr.risk_level == "high" else "source_required",
    )


def _build_sparse_queries(qr: QueryUnderstandingResult) -> list[str]:
    terms = [qr.raw_message, *qr.soft_preferences]
    area = qr.hard_filters.get("area_text")
    if area:
        terms.append(str(area))
    return _dedupe([t for t in terms if t])


def _build_kb_rewrite_queries(qr: QueryUnderstandingResult, module_intent: str | None) -> list[str]:
    queries: list[str] = []
    if module_intent:
        queries.append(f"{module_intent} {qr.raw_message}")
    if qr.risk_level in ("medium", "high"):
        queries.append(_step_back_query(qr.raw_message, module_intent))
    return [q for q in queries if q]


def _infer_kb_module_intent(message: str) -> str | None:
    # Enterprise boundary: this is a coarse policy hint, not final relevance ranking.
    module_terms = {
        "lease": ("合同", "租约", "签约", "退租", "押金", "续租", "违约", "转租"),
        "payment": ("支付", "租金", "水电", "退款", "发票", "逾期", "花呗"),
        "appointment": ("预约", "看房", "取消", "改期", "迟到"),
        "life": ("报修", "维修", "噪音", "宠物", "电器", "卫生", "快递"),
        "account": ("注册", "密码", "实名", "隐私", "注销", "账号"),
        "policy": ("优惠", "投诉", "换锁", "安全", "同住", "节假日"),
    }
    for module, terms in module_terms.items():
        if any(term in message for term in terms):
            return module
    return None


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

- [ ] **Step 4: Run planning tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_planning.py -q
```

Expected: pass.

## 7. Task 3: Add Hybrid Retrieval Merge And Sparse Signal

**Files:**

- Create: `backend/src/aptguide2/rag/sparse.py`
- Create: `backend/src/aptguide2/rag/hybrid.py`
- Test: `backend/tests/unit/rag/test_hybrid.py`

- [ ] **Step 1: Write failing hybrid tests**

```python
from aptguide2.rag.hybrid import HybridCandidate, merge_hybrid_candidates, normalize_scores
from aptguide2.rag.sparse import sparse_score


def test_sparse_score_rewards_token_overlap_without_being_the_only_signal():
    score = sparse_score("押金退还多久到账", "押金退还规则")

    assert 0.0 < score <= 1.0


def test_normalize_scores_handles_equal_values():
    assert normalize_scores([0.5, 0.5]) == [1.0, 1.0]


def test_merge_hybrid_candidates_dedupes_and_preserves_channels():
    dense = [
        HybridCandidate(id="KB-LEASE-005#01", dense_score=0.82, channel="dense", payload={"doc_id": "KB-LEASE-005"}),
    ]
    sparse = [
        HybridCandidate(id="KB-LEASE-005#01", sparse_score=0.6, channel="sparse", payload={"doc_id": "KB-LEASE-005"}),
        HybridCandidate(id="KB-PAY-001#01", sparse_score=0.7, channel="sparse", payload={"doc_id": "KB-PAY-001"}),
    ]

    merged = merge_hybrid_candidates([dense, sparse])

    assert [c.id for c in merged] == ["KB-LEASE-005#01", "KB-PAY-001#01"]
    assert set(merged[0].recall_channels) == {"dense", "sparse"}
    assert merged[0].dense_score == 0.82
    assert merged[0].sparse_score == 0.6
```

- [ ] **Step 2: Run failing tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_hybrid.py -q
```

Expected: fails because modules do not exist.

- [ ] **Step 3: Implement sparse and hybrid helpers**

Create `backend/src/aptguide2/rag/sparse.py`:

```python
"""Sparse lexical signal for RAG v2.

This is not the primary relevance mechanism. It is a transparent lexical
baseline used inside hybrid retrieval and eval tests.
"""

from __future__ import annotations

import re


def sparse_score(query: str, text: str) -> float:
    query_terms = _tokenize(query)
    text_terms = _tokenize(text)
    if not query_terms or not text_terms:
        return 0.0
    overlap = query_terms & text_terms
    return min(len(overlap) / max(len(query_terms), 1), 1.0)


def _tokenize(text: str) -> set[str]:
    ascii_terms = set(re.findall(r"[A-Za-z0-9_]+", text.lower()))
    cjk_terms = {ch for ch in text if "\u4e00" <= ch <= "\u9fff"}
    return ascii_terms | cjk_terms
```

Create `backend/src/aptguide2/rag/hybrid.py`:

```python
"""Hybrid retrieval merge helpers for RAG v2."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HybridCandidate(BaseModel):
    id: str
    dense_score: float = 0.0
    sparse_score: float = 0.0
    metadata_score: float = 0.0
    channel: str = ""
    recall_channels: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


def normalize_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if high == low:
        return [1.0 for _ in values]
    return [(v - low) / (high - low) for v in values]


def merge_hybrid_candidates(groups: list[list[HybridCandidate]]) -> list[HybridCandidate]:
    merged: dict[str, HybridCandidate] = {}
    order: list[str] = []
    for group in groups:
        for candidate in group:
            if candidate.id not in merged:
                item = candidate.model_copy(deep=True)
                item.recall_channels = [candidate.channel] if candidate.channel else []
                merged[candidate.id] = item
                order.append(candidate.id)
                continue
            current = merged[candidate.id]
            current.dense_score = max(current.dense_score, candidate.dense_score)
            current.sparse_score = max(current.sparse_score, candidate.sparse_score)
            current.metadata_score = max(current.metadata_score, candidate.metadata_score)
            if candidate.channel and candidate.channel not in current.recall_channels:
                current.recall_channels.append(candidate.channel)
            current.payload.update(candidate.payload)
    return [merged[key] for key in order]
```

- [ ] **Step 4: Run hybrid tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_hybrid.py -q
```

Expected: pass.

## 8. Task 4: Add Governed Rerank Without Primary Character Overlap

**Files:**

- Create: `backend/src/aptguide2/rag/rerank.py`
- Test: `backend/tests/unit/rag/test_rerank.py`

- [ ] **Step 1: Write failing rerank tests**

```python
from aptguide2.rag.hybrid import HybridCandidate
from aptguide2.rag.planning import RetrievalPlan
from aptguide2.rag.rerank import RerankWeights, rerank_kb_sources


def test_rerank_uses_dense_sparse_module_and_risk_features():
    plan = RetrievalPlan(
        task="kb_qa",
        raw_message="押金退还多久到账",
        semantic_queries=["押金退还多久到账"],
        recall_channels=["dense", "sparse", "step_back"],
        module_intent="lease",
        risk_level="high",
        validation_mode="source_required",
        source_policy="high_risk_source_required",
    )
    candidates = [
        HybridCandidate(
            id="bad",
            dense_score=0.9,
            sparse_score=0.0,
            payload={"module": "life", "risk_level": "low", "title": "生活维修"},
        ),
        HybridCandidate(
            id="good",
            dense_score=0.82,
            sparse_score=0.7,
            payload={"module": "lease", "risk_level": "high", "title": "押金退还规则"},
        ),
    ]

    ranked = rerank_kb_sources(candidates, plan)

    assert ranked[0].id == "good"
    assert ranked[0].payload["rerank_features"]["module_score"] == 1.0
    assert ranked[0].payload["rerank_features"]["risk_score"] == 1.0


def test_character_overlap_weight_is_capped():
    weights = RerankWeights()

    assert weights.lexical_score <= 0.20
```

- [ ] **Step 2: Run failing tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_rerank.py -q
```

Expected: fails because `rag.rerank` does not exist.

- [ ] **Step 3: Implement governed rerank**

Create `backend/src/aptguide2/rag/rerank.py`:

```python
"""Governed rerank for RAG v2.

Character overlap is capped as a weak lexical feature. It must not dominate
semantic, module, risk, and validation signals.
"""

from __future__ import annotations

from pydantic import BaseModel

from aptguide2.rag.hybrid import HybridCandidate
from aptguide2.rag.planning import RetrievalPlan


class RerankWeights(BaseModel):
    dense_score: float = 0.35
    sparse_score: float = 0.15
    module_score: float = 0.20
    risk_score: float = 0.15
    validation_score: float = 0.10
    lexical_score: float = 0.05


def rerank_kb_sources(
    candidates: list[HybridCandidate],
    plan: RetrievalPlan,
    weights: RerankWeights | None = None,
) -> list[HybridCandidate]:
    weights = weights or RerankWeights()
    ranked: list[HybridCandidate] = []
    for candidate in candidates:
        module_score = _module_score(candidate, plan)
        risk_score = _risk_score(candidate, plan)
        validation_score = 1.0 if candidate.payload.get("content") or candidate.payload.get("title") else 0.0
        lexical_score = min(candidate.sparse_score, 1.0)
        final_score = (
            weights.dense_score * candidate.dense_score
            + weights.sparse_score * candidate.sparse_score
            + weights.module_score * module_score
            + weights.risk_score * risk_score
            + weights.validation_score * validation_score
            + weights.lexical_score * lexical_score
        )
        item = candidate.model_copy(deep=True)
        item.payload["rerank_score"] = round(final_score, 6)
        item.payload["rerank_features"] = {
            "dense_score": candidate.dense_score,
            "sparse_score": candidate.sparse_score,
            "module_score": module_score,
            "risk_score": risk_score,
            "validation_score": validation_score,
            "lexical_score": lexical_score,
        }
        ranked.append(item)
    return sorted(ranked, key=lambda c: c.payload.get("rerank_score", 0.0), reverse=True)


def _module_score(candidate: HybridCandidate, plan: RetrievalPlan) -> float:
    if not plan.module_intent:
        return 0.5
    return 1.0 if candidate.payload.get("module") == plan.module_intent else 0.0


def _risk_score(candidate: HybridCandidate, plan: RetrievalPlan) -> float:
    source_risk = candidate.payload.get("risk_level", "low")
    if plan.risk_level == "high":
        return 1.0 if source_risk == "high" else 0.0
    if plan.risk_level == "medium":
        return 1.0 if source_risk in {"medium", "high"} else 0.3
    return 0.8
```

- [ ] **Step 4: Run rerank tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_rerank.py -q
```

Expected: pass.

## 9. Task 5: Add Room Lease Validation Gate

**Files:**

- Create: `backend/src/aptguide2/rag/validation.py`
- Test: `backend/tests/unit/rag/test_validation.py`

- [ ] **Step 1: Write failing validation tests**

```python
from aptguide2.rag.schemas import RoomCandidate
from aptguide2.rag.validation import validate_room_candidates


class FakeLeaseValidator:
    def __init__(self, rooms):
        self.rooms = rooms
        self.called_with = None

    def search_rooms(self, payload):
        self.called_with = payload
        return {"rooms": self.rooms}


def test_validation_keeps_only_lease_returned_rooms():
    validator = FakeLeaseValidator([
        {"room_id": 101, "apartment_id": 1, "apartment_name": "南亭寓", "rent": 1500, "is_appointable": True}
    ])
    candidates = [
        RoomCandidate(room_id=101, semantic_score=0.9, matched_query="安静"),
        RoomCandidate(room_id=999, semantic_score=0.95, matched_query="安静"),
    ]

    validated = validate_room_candidates(candidates, {"max_rent": 1600}, validator)

    assert [room["room_id"] for room in validated] == [101]
    assert validated[0]["semantic_score"] == 0.9
    assert validator.called_with["room_ids"] == [101, 999]


def test_validation_returns_empty_when_lease_returns_no_rooms():
    validator = FakeLeaseValidator([])
    candidates = [RoomCandidate(room_id=999, semantic_score=0.95)]

    validated = validate_room_candidates(candidates, {}, validator)

    assert validated == []
```

- [ ] **Step 2: Run failing tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_validation.py -q
```

Expected: fails because `rag.validation` does not exist.

- [ ] **Step 3: Implement validation gate**

Create `backend/src/aptguide2/rag/validation.py`:

```python
"""Lease validation gate for room candidates."""

from __future__ import annotations

from typing import Protocol

from aptguide2.rag.schemas import RoomCandidate


class LeaseRoomValidator(Protocol):
    def search_rooms(self, payload: dict) -> dict:
        ...


def validate_room_candidates(
    candidates: list[RoomCandidate],
    hard_filters: dict,
    validator: LeaseRoomValidator,
    limit: int = 20,
) -> list[dict]:
    if not candidates:
        return []
    semantic_by_room_id = {c.room_id: c for c in candidates}
    payload = {
        "room_ids": [c.room_id for c in candidates],
        "limit": limit,
        "strategy": "rag_v2_vector_validated_search",
    }
    if hard_filters.get("district_id") is not None:
        payload["district_id"] = hard_filters["district_id"]
    if hard_filters.get("max_rent") is not None:
        payload["max_rent"] = hard_filters["max_rent"]
    if hard_filters.get("payment_type") is not None:
        payload["payment_type"] = hard_filters["payment_type"]

    result = validator.search_rooms(payload)
    rooms = result.get("rooms", []) if isinstance(result, dict) else []
    validated: list[dict] = []
    for room in rooms:
        room_id = room.get("room_id")
        if room_id not in semantic_by_room_id:
            continue
        candidate = semantic_by_room_id[room_id]
        merged = dict(room)
        merged["semantic_score"] = candidate.semantic_score
        merged["matched_query"] = candidate.matched_query
        merged["recall_source"] = candidate.recall_source
        validated.append(merged)
    return validated
```

- [ ] **Step 4: Run validation tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_validation.py -q
```

Expected: pass.

## 10. Task 6: Build RAG v2 Pipeline Without Changing Default `/chat`

**Files:**

- Create: `backend/src/aptguide2/rag/pipeline_v2.py`
- Modify: `backend/src/aptguide2/core/config.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Test: `backend/tests/e2e/test_api.py`

- [ ] **Step 1: Inspect current config and API branching**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
sed -n '1,220p' src/aptguide2/core/config.py
sed -n '1,220p' src/aptguide2/api/app.py
```

Expected:

- Existing `pipeline_version` controls MVP vs `harness_v1`.
- Add `rag_v2` as a new explicit value without altering MVP default.

- [ ] **Step 2: Add e2e test for default behavior preservation**

Append a test that sets no pipeline override and asserts the existing MVP path still returns a valid `ChatResponse` with task/message fields. Use the existing test style in `tests/e2e/test_api.py`.

Expected test shape:

```python
def test_chat_default_pipeline_still_returns_mvp_response(monkeypatch):
    monkeypatch.delenv("APTGUIDE_PIPELINE_VERSION", raising=False)
    # Reuse existing app test fakes from this file.
    # Assert response status 200 and JSON contains "task" and "message".
```

- [ ] **Step 3: Add RAG v2 branch test with fakes**

Add a test that sets:

```python
monkeypatch.setenv("APTGUIDE_PIPELINE_VERSION", "rag_v2")
```

Then monkeypatch dependencies so the route does not call real Milvus, lease, or LLM. Assert:

```python
assert body["task"] in {"room_search", "kb_qa", "fallback"}
assert "message" in body
```

- [ ] **Step 4: Implement `pipeline_v2.py` orchestration**

Implement the minimal orchestration:

```python
"""RAG v2 orchestration behind feature flag."""

from __future__ import annotations

from aptguide2.rag.pipeline import PipelineResult
from aptguide2.rag.planning import build_retrieval_plan
from aptguide2.rag.query_understanding import understand_query
from aptguide2.rag.room_retrieval import retrieve_rooms
from aptguide2.rag.validation import validate_room_candidates
from aptguide2.rag.ranking import rank_rooms
from aptguide2.rag.kb_retrieval import retrieve_kb
from aptguide2.rag.confidence import get_fallback_message


def run_pipeline_v2(message: str, vector_adapter, embed_fn, lease_validator=None, top_n_rooms: int = 5) -> PipelineResult:
    qr = understand_query(message)
    plan = build_retrieval_plan(qr)

    if plan.task == "fallback":
        return PipelineResult(
            task="fallback",
            message="抱歉，这个问题超出了我的服务范围。我是租房助手，可以帮您找房或回答租房相关问题。",
            fallback_reason="out_of_scope",
            query_understanding=qr,
        )

    if plan.task == "kb_qa":
        sources, is_confident = retrieve_kb(qr, vector_adapter, embed_fn)
        if not is_confident:
            return PipelineResult(
                task="kb_qa",
                message=get_fallback_message(qr.risk_level),
                kb_sources=sources,
                is_confident=False,
                fallback_reason="confidence_gate_blocked",
                query_understanding=qr,
            )
        return PipelineResult(
            task="kb_qa",
            kb_sources=sources,
            is_confident=True,
            query_understanding=qr,
        )

    candidates = retrieve_rooms(qr, vector_adapter, embed_fn)
    if lease_validator is None:
        return PipelineResult(
            task="room_search",
            message="房源需要经过业务系统校验后才能推荐，请稍后再试。",
            fallback_reason="lease_validator_missing",
            query_understanding=qr,
        )
    validated = validate_room_candidates(candidates, plan.hard_filters, lease_validator)
    if not validated:
        return PipelineResult(
            task="room_search",
            message="抱歉，经过业务系统校验后没有找到可靠可展示的房源。您可以尝试放宽预算或区域条件。",
            fallback_reason="lease_validation_empty",
            query_understanding=qr,
        )
    ranked = rank_rooms(validated, qr, top_n=top_n_rooms)
    return PipelineResult(task="room_search", rooms=ranked, query_understanding=qr)
```

- [ ] **Step 5: Wire `rag_v2` into `api/app.py`**

Add:

```python
from aptguide2.rag.pipeline_v2 import run_pipeline_v2
```

In `chat()` add a branch after `harness_v1` and before MVP:

```python
if settings.pipeline_version == "rag_v2":
    adapter = get_vector_adapter()
    embed_fn = get_embed_fn()
    result = run_pipeline_v2(
        message=req.message,
        vector_adapter=adapter,
        embed_fn=embed_fn,
        lease_validator=None,
    )
    return _build_response(result)
```

Note: this branch intentionally returns `lease_validator_missing` until Task 7 wires a governed validator. The branch must not call real lease from unit/e2e tests.

- [ ] **Step 6: Run API tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/e2e/test_api.py -q
```

Expected: pass.

## 11. Task 7: Connect RAG v2 Room Validation To Tool Runtime Safely

**Files:**

- Modify: `backend/src/aptguide2/api/deps.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Create: `backend/src/aptguide2/rag/tool_validation.py`
- Test: `backend/tests/unit/rag/test_validation.py`

- [ ] **Step 1: Add fake ToolRuntime validation test**

Extend `test_validation.py`:

```python
from aptguide2.rag.tool_validation import ToolRuntimeRoomValidator


class FakeToolRuntime:
    def execute(self, request):
        assert request.tool_name == "room.search"
        return type("Result", (), {
            "success": True,
            "data": {"rooms": [{"room_id": 101, "apartment_id": 1, "rent": 1500}]},
        })()


def test_tool_runtime_room_validator_calls_room_search():
    validator = ToolRuntimeRoomValidator(FakeToolRuntime())

    result = validator.search_rooms({"room_ids": [101]})

    assert result["rooms"][0]["room_id"] == 101
```

- [ ] **Step 2: Implement tool validation adapter**

Create `backend/src/aptguide2/rag/tool_validation.py`:

```python
"""RAG v2 validation adapters over governed ToolRuntime."""

from __future__ import annotations

from aptguide2.harness.tools.contracts import ToolCallRequest


class ToolRuntimeRoomValidator:
    def __init__(self, tool_runtime):
        self.tool_runtime = tool_runtime

    def search_rooms(self, payload: dict) -> dict:
        result = self.tool_runtime.execute(
            ToolCallRequest(
                tool_name="room.search",
                arguments=payload,
                metadata={"caller": "rag_v2", "purpose": "lease_validation"},
            )
        )
        if not result.success:
            return {"rooms": []}
        return result.data if isinstance(result.data, dict) else {"rooms": []}
```

- [ ] **Step 3: Wire validator dependency into API branch**

In `api/app.py`, import:

```python
from aptguide2.api.deps import get_tool_runtime
from aptguide2.rag.tool_validation import ToolRuntimeRoomValidator
```

Update `rag_v2` branch:

```python
lease_validator = ToolRuntimeRoomValidator(get_tool_runtime())
result = run_pipeline_v2(
    message=req.message,
    vector_adapter=adapter,
    embed_fn=embed_fn,
    lease_validator=lease_validator,
)
```

- [ ] **Step 4: Run validation and API tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_validation.py tests/e2e/test_api.py -q
```

Expected: pass with fakes and without real services.

## 12. Task 8: Add RAG v2 Eval Metrics And Runner

**Files:**

- Create: `backend/src/aptguide2/rag/eval_metrics.py`
- Create: `backend/evals/runners/run_rag_v2.py`
- Test: `backend/tests/unit/rag/test_eval_metrics.py`

- [ ] **Step 1: Write metric tests**

```python
from aptguide2.rag.eval_metrics import hit_at_k, mean_reciprocal_rank, ndcg_at_k


def test_hit_at_k_true_when_expected_item_in_top_k():
    assert hit_at_k(["a", "b", "c"], {"c"}, 3) is True
    assert hit_at_k(["a", "b", "c"], {"c"}, 2) is False


def test_mrr_uses_first_relevant_rank():
    assert mean_reciprocal_rank(["a", "b", "c"], {"c"}) == 1 / 3


def test_ndcg_at_k_is_one_for_perfect_first_result():
    assert ndcg_at_k(["a", "b"], {"a"}, 2) == 1.0
```

- [ ] **Step 2: Implement metrics**

Create `backend/src/aptguide2/rag/eval_metrics.py`:

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

- [ ] **Step 3: Create RAG v2 eval runner**

Create `backend/evals/runners/run_rag_v2.py` by adapting `run_rag_mvp.py` with these differences:

```python
from aptguide2.rag.pipeline_v2 import run_pipeline_v2
from aptguide2.rag.eval_metrics import hit_at_k, mean_reciprocal_rank, ndcg_at_k
```

Required behavior:

- For `kb_retrieval`, collect `source.doc_id` from `result.kb_sources`.
- For `room_retrieval`, collect `room.room_id` from `result.rooms`.
- Count `unvalidated_room_count` as 0 only when RAG v2 used lease validator.
- Write `reports/rag-v2-evaluation-report.md`.
- Set gates:

```python
gates = {
    "kb_source_hit_at_3_gate": metrics["kb_source_hit_at_3"] >= 0.90,
    "high_risk_fallback_gate": metrics["high_risk_fallback_rate"] >= 1.0,
    "room_hit_at_5_gate": metrics["room_hit_at_5"] >= 0.85,
    "unvalidated_room_count_gate": metrics["unvalidated_room_count"] == 0,
}
```

- [ ] **Step 4: Run metric tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_eval_metrics.py -q
```

Expected: pass.

## 13. Task 9: Add Trace Evidence For Retrieval Stages

**Files:**

- Modify: `backend/src/aptguide2/rag/pipeline_v2.py`
- Test: `backend/tests/unit/rag/test_pipeline_v2_trace.py`

- [ ] **Step 1: Write trace test**

```python
from aptguide2.rag.pipeline_v2 import run_pipeline_v2


class FakeTraceRecorder:
    def __init__(self):
        self.events = []

    def record(self, event, payload):
        self.events.append((event, payload))


def test_pipeline_v2_records_retrieval_finished_for_fallback():
    trace = FakeTraceRecorder()

    run_pipeline_v2("帮我查其他租户手机号", vector_adapter=None, embed_fn=lambda text: [], trace_recorder=trace)

    assert trace.events
    assert trace.events[-1][0] == "retrieval_finished"
    assert trace.events[-1][1]["task"] == "fallback"
```

- [ ] **Step 2: Add optional trace recorder parameter**

Update signature:

```python
def run_pipeline_v2(..., trace_recorder=None) -> PipelineResult:
```

Add helper:

```python
def _record_trace(trace_recorder, payload: dict) -> None:
    if trace_recorder is not None:
        trace_recorder.record("retrieval_finished", payload)
```

Record at every return path with:

```python
{
    "task": plan.task,
    "rewrite_count": len(plan.semantic_queries),
    "collections": ["apt_room_vector"] or ["apt_rental_kb"] or [],
    "filters": plan.hard_filters,
    "candidate_count": len(candidates) if available else 0,
    "validated_count": len(validated) if available else 0,
    "fallback_reason": "...",
}
```

- [ ] **Step 3: Run trace tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_pipeline_v2_trace.py -q
```

Expected: pass.

## 14. Task 10: Document Eval Gates

**Files:**

- Create: `docs/tests/rag-v2-evaluation-gates.md`
- Modify: `docs/tests/README.md`

- [ ] **Step 1: Create gate documentation**

```markdown
# RAG v2 Evaluation Gates

> 状态：active

## Purpose

RAG v2 quality is measured through retrieval, rerank, validation, and safety gates.

## Required Gates

| Gate | Threshold | Reason |
| --- | ---: | --- |
| KB source hit@3 | >= 90% | KB answers must retrieve reliable sources early. |
| High-risk fallback | 100% | High-risk policy questions must not be answered without sufficient source evidence. |
| Room hit@5 | >= 85% | Room retrieval must find expected candidates. |
| Unvalidated room count | 0 | No room can be shown without lease validation. |
| Default `/chat` unchanged | pass | RAG v2 must be feature-flagged until accepted. |

## Character-Match Governance

Character matching may extract hard filters and safety controls. It may not be the primary KB relevance or room semantic preference ranking mechanism.

## Evidence

Final evidence must be written to `reports/rag-v2-evaluation-report.md`.
```

- [ ] **Step 2: Add index row**

Add this row to `docs/tests/README.md`:

```markdown
| [rag-v2-evaluation-gates](./rag-v2-evaluation-gates.md) | RAG v2 hybrid retrieval、governed rerank、lease validation 和高风险 source gate 的验收门槛 | active |
```

## 15. Task 11: Final Regression And Report

**Files:**

- Create: `reports/rag-v2-evaluation-report.md`
- Modify: `progress/current-plan.md`

- [ ] **Step 1: Run full local regression**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/e2e -q
```

Expected: pass.

- [ ] **Step 2: Run offline eval if local services are available**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run python evals/runners/run_rag_v2.py \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-evaluation-report.md
```

Expected:

- If Milvus/embedding/lease are available, report contains metrics and gates.
- If services are unavailable, do not fake passing metrics. Write a report section named `Unavailable External Dependencies` with exact missing services and commands attempted.

- [ ] **Step 3: Update current plan**

Update `progress/current-plan.md`:

```markdown
## Active Objective

Enterprise RAG v2 hybrid retrieval, governed rerank, lease validation, and eval gates are the active objective.

## Active Plan

`docs/plans/2026-05-14-enterprise-rag-v2-hybrid-retrieval-governed-rerank-agent-plan.md`
```

Keep the existing completed-plan history.

- [ ] **Step 4: Final status check**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform"
git status --short
```

Expected:

- Only intended RAG v2 files, docs, reports, and tests changed.
- No unrelated user changes reverted.

## 16. Completion Criteria

The plan is complete only when all of these are true:

- Character-match audit exists and classifies keep/weaken/replace logic.
- RAG v2 has explicit `RetrievalPlan`.
- KB semantic relevance no longer depends primarily on character overlap.
- Room RAG v2 refuses to show unvalidated vector-only rooms.
- `rag_v2` is feature-flagged and default `/chat` remains MVP.
- Unit/e2e tests pass.
- Eval gates are documented.
- Final report records either passing eval evidence or explicit unavailable dependency blockers.

## 17. Execution Recommendation

Use subagent-driven execution with these ownership boundaries:

1. Planning and hybrid retrieval worker: Tasks 1-4.
2. Lease validation and pipeline worker: Tasks 5-7.
3. Eval, trace, and documentation worker: Tasks 8-11.

Workers are not alone in the codebase. They must not revert edits made by others, and they must adjust to concurrent changes instead of overwriting them.
