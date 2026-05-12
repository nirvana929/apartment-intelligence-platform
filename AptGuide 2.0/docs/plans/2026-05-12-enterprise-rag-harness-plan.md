# Enterprise RAG Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an enterprise-grade RAG harness for AptGuide 2.0 that makes routing, query understanding, rewrite, retrieval, validation, rerank, confidence, response composition, trace, replay, and strategy switching explicit and replaceable.

**Architecture:** Add a new `aptguide2.rag_harness` package beside the current MVP `aptguide2.rag` package. The existing MVP remains runnable while the harness is built behind a version switch, then `/chat` can route to either the old pipeline or the new harness.

**Tech Stack:** FastAPI, Pydantic, OpenAI-compatible LLM and embedding APIs, Milvus, existing `LeaseAdapter`, pytest, YAML configuration.

---

## 1. Why This Plan Exists

The current RAG MVP proves the product direction, but it is not an enterprise-quality RAG harness yet.

Current problems:

- `query_understanding.py` relies on string matching for task routing, risk detection, preference extraction, and step-back query generation.
- `room_retrieval.py` uses Milvus as the main retrieval path, but room facts should be validated by `lease`.
- `ranking.py` uses hand-picked weights and does not separate hard constraint gates from soft ranking features.
- `kb_retrieval.py` uses vector-only retrieval plus lightweight string rerank.
- `confidence.py` uses three hand-picked thresholds without topic-specific calibration or grounding coverage checks.
- Trace schemas exist, but the main runtime does not yet produce a full stage-by-stage replayable trace.
- `session_id` exists in the API schema, but conversation state is not loaded into `run_pipeline()`.

The target is not just "better retrieval". The target is a harness:

```text
RagRequest
  -> ContextLoader
  -> SafetyGuard
  -> Router
  -> QueryUnderstanding
  -> QueryRewrite
  -> RetrievalPlanner
  -> MultiRetriever
  -> ResultMerger
  -> Validator
  -> Reranker
  -> ConfidenceGate
  -> ResponseComposer
  -> TraceRecorder
  -> RagResponse
```

Every stage must have:

- typed input and output;
- strategy name and version;
- latency and error capture;
- deterministic fallback behavior;
- enough trace data to replay one request offline.

## 2. Design Principles

1. **Do not break MVP while building harness.**
   Keep `aptguide2.rag` intact and add `aptguide2.rag_harness`.

2. **LLM understands language, code enforces contracts.**
   LLM can output structured intent and rewrite candidates, but Pydantic schemas validate every field.

3. **Tools own facts.**
   Milvus returns candidates. `lease` validates room state, price, and availability. KB sources validate policy answers.

4. **Rerank is a strategy, not a hardcoded function.**
   Start with deterministic baseline rankers behind interfaces, then plug in semantic rerankers.

5. **Trace first.**
   Each stage emits input summary, output summary, strategy version, latency, and recoverable errors.

6. **Replay before large eval.**
   The user explicitly wants architecture first. Replay harness comes before a full eval platform because it makes failures diagnosable.

## 3. Target File Structure

Create:

```text
backend/src/aptguide2/rag_harness/
├── __init__.py
├── config.py
├── contracts.py
├── orchestrator.py
├── registry.py
├── errors.py
├── context.py
├── safety.py
├── router.py
├── understanding.py
├── rewrite.py
├── planning.py
├── merge.py
├── confidence.py
├── composer.py
├── trace.py
├── replay.py
├── retrievers/
│   ├── __init__.py
│   ├── base.py
│   ├── room_lease.py
│   ├── room_vector.py
│   ├── kb_vector.py
│   └── kb_keyword.py
├── validators/
│   ├── __init__.py
│   ├── room.py
│   └── kb.py
└── rerankers/
    ├── __init__.py
    ├── base.py
    ├── room_rule.py
    ├── kb_rule.py
    └── semantic_stub.py
```

Create tests:

```text
backend/tests/unit/rag_harness/
├── test_contracts.py
├── test_registry.py
├── test_router.py
├── test_rewrite.py
├── test_planning.py
├── test_merge.py
├── test_confidence.py
├── test_composer.py
├── test_trace.py
├── test_replay.py
├── test_room_harness.py
└── test_kb_harness.py
```

Modify later:

```text
backend/src/aptguide2/core/config.py
backend/src/aptguide2/api/app.py
backend/src/aptguide2/api/deps.py
backend/tests/e2e/test_api.py
```

## 4. Core Contracts

The harness should introduce these stable contracts in `contracts.py`.

```python
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


Task = Literal["room_search", "kb_qa", "fallback"]
RiskLevel = Literal["low", "medium", "high"]


class RagRequest(BaseModel):
    message: str
    session_id: str | None = None
    user_id: str | None = None
    rag_version: str = "harness_v1"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationContext(BaseModel):
    session_id: str | None = None
    previous_hard_filters: dict[str, Any] = Field(default_factory=dict)
    previous_soft_preferences: list[str] = Field(default_factory=list)
    last_room_ids: list[int] = Field(default_factory=list)
    active_task: Task | None = None


class RouterDecision(BaseModel):
    task: Task
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel = "low"
    topic: str = ""
    reason: str = ""
    safety_flags: list[str] = Field(default_factory=list)


class StructuredQuery(BaseModel):
    raw_message: str
    task: Task
    confidence: float = Field(ge=0.0, le=1.0)
    hard_filters: dict[str, Any] = Field(default_factory=dict)
    soft_preferences: list[str] = Field(default_factory=list)
    negative_preferences: list[str] = Field(default_factory=list)
    missing_slots: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = "low"
    topic: str = ""
    needs_clarification: bool = False
    clarification_question: str = ""


class RewriteQuery(BaseModel):
    text: str
    kind: Literal["original", "normalized", "expanded", "step_back", "hyde", "lifestyle"]
    weight: float = Field(default=1.0, ge=0.0, le=2.0)
    source: str = ""


class RetrievalChannelPlan(BaseModel):
    name: str
    kind: Literal["structured", "vector", "keyword"]
    top_k: int = 20
    filters: dict[str, Any] = Field(default_factory=dict)
    query_kinds: list[str] = Field(default_factory=list)
    required: bool = False


class RetrievalPlan(BaseModel):
    task: Task
    channels: list[RetrievalChannelPlan]
    rewrites: list[RewriteQuery]
    fallback_policy: str = "none"


class Candidate(BaseModel):
    candidate_id: str
    kind: Literal["room", "kb_source"]
    score: float = 0.0
    payload: dict[str, Any] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    matched_queries: list[str] = Field(default_factory=list)


class StageTrace(BaseModel):
    stage: str
    strategy: str
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
    errors: list[str] = Field(default_factory=list)


class RagTrace(BaseModel):
    trace_id: str
    stages: list[StageTrace] = Field(default_factory=list)


class RagResponse(BaseModel):
    task: Task
    message: str
    rooms: list[dict[str, Any]] = Field(default_factory=list)
    kb_sources: list[dict[str, Any]] = Field(default_factory=list)
    is_confident: bool = False
    fallback_reason: str = ""
    trace: RagTrace | None = None
```

These contracts are the backbone. Later tasks may add fields, but they should not return free-form dicts between harness stages.

## 5. Implementation Tasks

### Task 1: Add Harness Package and Core Contracts

**Files:**

- Create: `backend/src/aptguide2/rag_harness/__init__.py`
- Create: `backend/src/aptguide2/rag_harness/contracts.py`
- Create: `backend/src/aptguide2/rag_harness/errors.py`
- Test: `backend/tests/unit/rag_harness/test_contracts.py`

- [ ] **Step 1: Write contract tests**

```python
from aptguide2.rag_harness.contracts import (
    Candidate,
    RagRequest,
    RetrievalPlan,
    RetrievalChannelPlan,
    RouterDecision,
    StructuredQuery,
)


def test_router_decision_bounds_confidence():
    decision = RouterDecision(task="room_search", confidence=0.8)
    assert decision.task == "room_search"
    assert decision.risk_level == "low"


def test_structured_query_defaults_are_isolated():
    q1 = StructuredQuery(raw_message="番禺1500以内", task="room_search", confidence=0.9)
    q2 = StructuredQuery(raw_message="押金怎么退", task="kb_qa", confidence=0.9)
    q1.soft_preferences.append("安静")
    assert q2.soft_preferences == []


def test_retrieval_plan_contains_channels():
    plan = RetrievalPlan(
        task="room_search",
        rewrites=[],
        channels=[
            RetrievalChannelPlan(
                name="room_vector",
                kind="vector",
                top_k=30,
                query_kinds=["original", "expanded"],
            )
        ],
    )
    assert plan.channels[0].name == "room_vector"
    assert plan.channels[0].top_k == 30


def test_candidate_merges_traceable_sources():
    c = Candidate(
        candidate_id="room:1001",
        kind="room",
        score=0.7,
        sources=["room_vector"],
        matched_queries=["番禺 安静 房源"],
    )
    assert c.candidate_id == "room:1001"
    assert c.sources == ["room_vector"]
```

- [ ] **Step 2: Run contract tests and confirm they fail**

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness/test_contracts.py -q
```

Expected: fail because `aptguide2.rag_harness` does not exist.

- [ ] **Step 3: Implement contracts and errors**

Create `errors.py`:

```python
from __future__ import annotations


class RagHarnessError(Exception):
    """Base error for the RAG harness."""


class StrategyNotFoundError(RagHarnessError):
    """Raised when a requested harness strategy is not registered."""


class HarnessStageError(RagHarnessError):
    """Raised when a harness stage fails without a recoverable fallback."""
```

Create `contracts.py` using the code from section 4.

Create `__init__.py`:

```python
"""Enterprise RAG harness for AptGuide 2.0."""
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness/test_contracts.py -q
```

Expected: pass.

- [ ] **Step 5: Suggested commit**

```bash
git add backend/src/aptguide2/rag_harness backend/tests/unit/rag_harness/test_contracts.py
git commit -m "feat(rag): add harness core contracts"
```

### Task 2: Add Strategy Registry and Harness Config

**Files:**

- Create: `backend/src/aptguide2/rag_harness/config.py`
- Create: `backend/src/aptguide2/rag_harness/registry.py`
- Modify: `backend/src/aptguide2/core/config.py`
- Test: `backend/tests/unit/rag_harness/test_registry.py`

- [ ] **Step 1: Write registry tests**

```python
import pytest

from aptguide2.rag_harness.errors import StrategyNotFoundError
from aptguide2.rag_harness.registry import StrategyRegistry


def test_registry_returns_registered_strategy():
    registry = StrategyRegistry()
    obj = object()
    registry.register("router", "rule_v1", obj)
    assert registry.get("router", "rule_v1") is obj


def test_registry_raises_for_missing_strategy():
    registry = StrategyRegistry()
    with pytest.raises(StrategyNotFoundError):
        registry.get("router", "missing")
```

- [ ] **Step 2: Implement registry**

```python
from __future__ import annotations

from typing import Any

from aptguide2.rag_harness.errors import StrategyNotFoundError


class StrategyRegistry:
    """Small runtime registry for pluggable harness strategies."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Any] = {}

    def register(self, category: str, name: str, strategy: Any) -> None:
        self._items[(category, name)] = strategy

    def get(self, category: str, name: str) -> Any:
        key = (category, name)
        if key not in self._items:
            raise StrategyNotFoundError(f"Strategy not found: {category}.{name}")
        return self._items[key]
```

- [ ] **Step 3: Add harness config model**

Create `config.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class RagHarnessConfig(BaseModel):
    enabled: bool = False
    router_strategy: str = "rule_structured_v1"
    understanding_strategy: str = "rule_structured_v1"
    rewrite_strategy: str = "rule_rewrite_v1"
    room_retrieval_channels: list[str] = Field(default_factory=lambda: ["room_vector"])
    kb_retrieval_channels: list[str] = Field(default_factory=lambda: ["kb_vector"])
    room_reranker: str = "room_rule_v1"
    kb_reranker: str = "kb_rule_v1"
    include_trace_in_response: bool = False
```

Modify `core/config.py` to include:

```python
rag_harness_enabled: bool = False
rag_harness_include_trace: bool = False
```

- [ ] **Step 4: Run registry tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness/test_registry.py -q
```

Expected: pass.

### Task 3: Add Safety Router and Structured Rule Router

**Files:**

- Create: `backend/src/aptguide2/rag_harness/safety.py`
- Create: `backend/src/aptguide2/rag_harness/router.py`
- Test: `backend/tests/unit/rag_harness/test_router.py`

- [ ] **Step 1: Write router tests**

```python
from aptguide2.rag_harness.contracts import ConversationContext, RagRequest
from aptguide2.rag_harness.router import RuleStructuredRouter


def route(message: str):
    router = RuleStructuredRouter()
    return router.route(RagRequest(message=message), ConversationContext())


def test_room_search_route():
    decision = route("番禺1500以内安静的房子")
    assert decision.task == "room_search"
    assert decision.confidence >= 0.6


def test_kb_route_for_deposit():
    decision = route("押金多久到账")
    assert decision.task == "kb_qa"
    assert decision.risk_level == "high"
    assert decision.topic == "deposit"


def test_safety_fallback_route():
    decision = route("你能保证邻居不会吵吗")
    assert decision.task == "fallback"
    assert "guarantee" in decision.safety_flags
```

- [ ] **Step 2: Implement safety guard**

```python
from __future__ import annotations


GUARANTEE_PATTERNS = ("保证", "担保", "一定", "肯定")
PRIVACY_PATTERNS = ("别人手机号", "其他租户", "身份证", "查别人")
OUT_OF_DOMAIN_PATTERNS = ("股票", "航班", "电影", "酒店", "黑客", "黑进")


def detect_safety_flags(message: str) -> list[str]:
    flags: list[str] = []
    if any(p in message for p in GUARANTEE_PATTERNS):
        flags.append("guarantee")
    if any(p in message for p in PRIVACY_PATTERNS):
        flags.append("privacy")
    if any(p in message for p in OUT_OF_DOMAIN_PATTERNS):
        flags.append("out_of_domain")
    return flags
```

- [ ] **Step 3: Implement rule structured router**

```python
from __future__ import annotations

from aptguide2.rag_harness.contracts import ConversationContext, RagRequest, RouterDecision
from aptguide2.rag_harness.safety import detect_safety_flags


KB_TOPICS = {
    "deposit": ("押金", "扣钱", "扣多少"),
    "lease": ("合同", "租约", "签约", "续租", "退租", "违约"),
    "appointment": ("预约", "看房", "取消预约", "改期"),
    "repair": ("报修", "维修"),
    "account": ("隐私", "注销", "实名", "账号", "密码"),
}

ROOM_TERMS = ("找房", "房子", "房源", "租房", "公寓", "以内", "附近", "安静", "近地铁", "推荐")
HIGH_RISK_TERMS = ("押金", "违约金", "退租", "合同", "赔偿", "扣钱", "扣多少")
MEDIUM_RISK_TERMS = ("投诉", "纠纷", "法律", "维权")


class RuleStructuredRouter:
    """Deterministic baseline router behind the harness router contract."""

    name = "rule_structured_v1"

    def route(self, request: RagRequest, context: ConversationContext) -> RouterDecision:
        message = request.message
        flags = detect_safety_flags(message)
        if flags:
            return RouterDecision(
                task="fallback",
                confidence=0.95,
                risk_level="medium" if "privacy" in flags else "low",
                topic="safety",
                reason="safety flag matched",
                safety_flags=flags,
            )

        risk_level = "low"
        if any(term in message for term in HIGH_RISK_TERMS):
            risk_level = "high"
        elif any(term in message for term in MEDIUM_RISK_TERMS):
            risk_level = "medium"

        for topic, terms in KB_TOPICS.items():
            if any(term in message for term in terms):
                return RouterDecision(
                    task="kb_qa",
                    confidence=0.85,
                    risk_level=risk_level,
                    topic=topic,
                    reason=f"matched kb topic {topic}",
                )

        if any(term in message for term in ROOM_TERMS):
            return RouterDecision(
                task="room_search",
                confidence=0.75,
                risk_level="low",
                topic="room_search",
                reason="matched room search terms",
            )

        return RouterDecision(
            task="fallback",
            confidence=0.55,
            risk_level="low",
            topic="unknown",
            reason="no supported task matched",
        )
```

- [ ] **Step 4: Run router tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness/test_router.py -q
```

Expected: pass.

### Task 4: Add Structured Query Understanding

**Files:**

- Create: `backend/src/aptguide2/rag_harness/understanding.py`
- Test: `backend/tests/unit/rag_harness/test_understanding.py`

- [ ] **Step 1: Write understanding tests**

```python
from aptguide2.rag_harness.contracts import ConversationContext, RagRequest, RouterDecision
from aptguide2.rag_harness.understanding import RuleStructuredUnderstanding


def understand(message: str):
    strategy = RuleStructuredUnderstanding()
    request = RagRequest(message=message)
    decision = RouterDecision(task="room_search", confidence=0.8)
    return strategy.understand(request, ConversationContext(), decision)


def test_extracts_room_filters_and_preferences():
    query = understand("番禺1500以内安静点，适合考研")
    assert query.task == "room_search"
    assert query.hard_filters["max_rent"] == 1500
    assert query.hard_filters["area_text"] == "番禺"
    assert "安静" in query.soft_preferences
    assert "适合考研" in query.soft_preferences


def test_inherits_previous_budget():
    strategy = RuleStructuredUnderstanding()
    request = RagRequest(message="那番禺呢")
    context = ConversationContext(previous_hard_filters={"max_rent": 1500})
    decision = RouterDecision(task="room_search", confidence=0.8)
    query = strategy.understand(request, context, decision)
    assert query.hard_filters["max_rent"] == 1500
```

- [ ] **Step 2: Implement deterministic baseline by reusing current parser**

```python
from __future__ import annotations

from aptguide2.rag.query_understanding import understand_query
from aptguide2.rag_harness.contracts import (
    ConversationContext,
    RagRequest,
    RouterDecision,
    StructuredQuery,
)


class RuleStructuredUnderstanding:
    """Baseline understanding strategy that adapts the MVP parser into harness contracts."""

    name = "rule_structured_v1"

    def understand(
        self,
        request: RagRequest,
        context: ConversationContext,
        decision: RouterDecision,
    ) -> StructuredQuery:
        previous_state = dict(context.previous_hard_filters)
        qr = understand_query(request.message, previous_state=previous_state)
        return StructuredQuery(
            raw_message=request.message,
            task=decision.task,
            confidence=min(decision.confidence, 0.95),
            hard_filters=qr.hard_filters,
            soft_preferences=qr.soft_preferences,
            negative_preferences=[],
            missing_slots=[],
            risk_level=decision.risk_level,
            topic=decision.topic,
            needs_clarification=False,
        )
```

- [ ] **Step 3: Run understanding tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness/test_understanding.py -q
```

Expected: pass.

### Task 5: Add Task-Specific Query Rewrite

**Files:**

- Create: `backend/src/aptguide2/rag_harness/rewrite.py`
- Test: `backend/tests/unit/rag_harness/test_rewrite.py`

- [ ] **Step 1: Write rewrite tests**

```python
from aptguide2.rag_harness.contracts import StructuredQuery
from aptguide2.rag_harness.rewrite import RuleQueryRewrite


def test_room_rewrite_generates_multiple_query_kinds():
    strategy = RuleQueryRewrite()
    query = StructuredQuery(
        raw_message="番禺1500以内安静点",
        task="room_search",
        confidence=0.9,
        hard_filters={"area_text": "番禺", "max_rent": 1500},
        soft_preferences=["安静", "低噪音"],
    )
    rewrites = strategy.rewrite(query)
    kinds = {r.kind for r in rewrites}
    assert {"original", "expanded", "lifestyle"} <= kinds


def test_kb_rewrite_generates_step_back_for_high_risk():
    strategy = RuleQueryRewrite()
    query = StructuredQuery(
        raw_message="押金多久到账",
        task="kb_qa",
        confidence=0.9,
        risk_level="high",
        topic="deposit",
    )
    rewrites = strategy.rewrite(query)
    assert any(r.kind == "step_back" and "押金退还规则" in r.text for r in rewrites)
```

- [ ] **Step 2: Implement rewrite strategy**

```python
from __future__ import annotations

from aptguide2.rag_harness.contracts import RewriteQuery, StructuredQuery


STEP_BACK_BY_TOPIC = {
    "deposit": "租房押金退还规则 流程 扣费",
    "lease": "租赁合同 签约 退租 续租 违约 规则",
    "appointment": "看房预约 取消预约 改期 规则 流程",
    "repair": "报修维修 流程 责任 费用",
    "account": "账号实名 隐私保护 注销 规则",
}


class RuleQueryRewrite:
    """Baseline query rewrite strategy for room and KB tasks."""

    name = "rule_rewrite_v1"

    def rewrite(self, query: StructuredQuery) -> list[RewriteQuery]:
        rewrites = [
            RewriteQuery(
                text=query.raw_message,
                kind="original",
                weight=1.0,
                source=self.name,
            )
        ]
        if query.task == "room_search":
            rewrites.extend(self._rewrite_room(query))
        elif query.task == "kb_qa":
            rewrites.extend(self._rewrite_kb(query))
        return self._dedupe(rewrites)

    def _rewrite_room(self, query: StructuredQuery) -> list[RewriteQuery]:
        area = query.hard_filters.get("area_text", "")
        budget = query.hard_filters.get("max_rent")
        prefs = query.soft_preferences[:4]
        out: list[RewriteQuery] = []

        parts = []
        if area:
            parts.append(f"{area}附近")
        if budget:
            parts.append(f"{budget}以内")
        parts.extend(prefs)
        parts.append("房源")
        if parts:
            out.append(RewriteQuery(text=" ".join(parts), kind="expanded", weight=1.1, source=self.name))

        lifestyle = ["适合"]
        if "适合考研" in query.soft_preferences or "适合学习" in query.soft_preferences:
            lifestyle = ["适合考研学生"]
        elif "通勤方便" in query.soft_preferences or "近地铁" in query.soft_preferences:
            lifestyle = ["适合白领通勤"]
        lifestyle.extend(prefs[:2])
        lifestyle.append("公寓")
        out.append(RewriteQuery(text=" ".join(lifestyle), kind="lifestyle", weight=0.9, source=self.name))
        return out

    def _rewrite_kb(self, query: StructuredQuery) -> list[RewriteQuery]:
        out: list[RewriteQuery] = []
        if query.soft_preferences:
            out.append(
                RewriteQuery(
                    text=" ".join(query.soft_preferences),
                    kind="normalized",
                    weight=0.8,
                    source=self.name,
                )
            )
        if query.risk_level in ("medium", "high"):
            step_back = STEP_BACK_BY_TOPIC.get(query.topic)
            if step_back:
                out.append(RewriteQuery(text=step_back, kind="step_back", weight=1.15, source=self.name))
        return out

    def _dedupe(self, rewrites: list[RewriteQuery]) -> list[RewriteQuery]:
        seen: set[str] = set()
        out: list[RewriteQuery] = []
        for item in rewrites:
            if item.text and item.text not in seen:
                seen.add(item.text)
                out.append(item)
        return out
```

- [ ] **Step 3: Run rewrite tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness/test_rewrite.py -q
```

Expected: pass.

### Task 6: Add Retrieval Planner

**Files:**

- Create: `backend/src/aptguide2/rag_harness/planning.py`
- Test: `backend/tests/unit/rag_harness/test_planning.py`

- [ ] **Step 1: Write planner tests**

```python
from aptguide2.rag_harness.contracts import RewriteQuery, StructuredQuery
from aptguide2.rag_harness.planning import DefaultRetrievalPlanner


def test_room_plan_uses_lease_and_vector_channels():
    planner = DefaultRetrievalPlanner()
    query = StructuredQuery(raw_message="番禺1500以内", task="room_search", confidence=0.9)
    rewrites = [RewriteQuery(text="番禺1500以内", kind="original")]
    plan = planner.plan(query, rewrites)
    assert [c.name for c in plan.channels] == ["room_lease", "room_vector"]


def test_kb_plan_uses_keyword_and_vector_channels():
    planner = DefaultRetrievalPlanner()
    query = StructuredQuery(raw_message="押金多久到账", task="kb_qa", confidence=0.9, topic="deposit")
    rewrites = [RewriteQuery(text="押金多久到账", kind="original")]
    plan = planner.plan(query, rewrites)
    assert [c.name for c in plan.channels] == ["kb_keyword", "kb_vector"]
```

- [ ] **Step 2: Implement planner**

```python
from __future__ import annotations

from aptguide2.rag_harness.contracts import RetrievalChannelPlan, RetrievalPlan, RewriteQuery, StructuredQuery


class DefaultRetrievalPlanner:
    """Builds retrieval plans from task-specific structured queries."""

    name = "default_planner_v1"

    def plan(self, query: StructuredQuery, rewrites: list[RewriteQuery]) -> RetrievalPlan:
        if query.task == "room_search":
            return RetrievalPlan(
                task=query.task,
                rewrites=rewrites,
                channels=[
                    RetrievalChannelPlan(name="room_lease", kind="structured", top_k=30, required=False),
                    RetrievalChannelPlan(
                        name="room_vector",
                        kind="vector",
                        top_k=50,
                        filters=query.hard_filters,
                        query_kinds=["original", "expanded", "lifestyle"],
                    ),
                ],
                fallback_policy="relax_soft_preferences",
            )
        if query.task == "kb_qa":
            return RetrievalPlan(
                task=query.task,
                rewrites=rewrites,
                channels=[
                    RetrievalChannelPlan(name="kb_keyword", kind="keyword", top_k=20, required=False),
                    RetrievalChannelPlan(
                        name="kb_vector",
                        kind="vector",
                        top_k=20,
                        filters={"topic": query.topic, "risk_level": query.risk_level},
                        query_kinds=["original", "normalized", "step_back"],
                    ),
                ],
                fallback_policy="low_confidence_fallback",
            )
        return RetrievalPlan(task=query.task, rewrites=rewrites, channels=[], fallback_policy="fallback")
```

- [ ] **Step 3: Run planner tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness/test_planning.py -q
```

Expected: pass.

### Task 7: Add Retriever Interfaces and Baseline Retrievers

**Files:**

- Create: `backend/src/aptguide2/rag_harness/retrievers/base.py`
- Create: `backend/src/aptguide2/rag_harness/retrievers/room_vector.py`
- Create: `backend/src/aptguide2/rag_harness/retrievers/room_lease.py`
- Create: `backend/src/aptguide2/rag_harness/retrievers/kb_vector.py`
- Create: `backend/src/aptguide2/rag_harness/retrievers/kb_keyword.py`
- Create: `backend/src/aptguide2/rag_harness/retrievers/__init__.py`
- Test: `backend/tests/unit/rag_harness/test_retrievers.py`

- [ ] **Step 1: Implement retriever protocol**

```python
from __future__ import annotations

from typing import Protocol

from aptguide2.rag_harness.contracts import Candidate, RetrievalChannelPlan, RetrievalPlan, StructuredQuery


class Retriever(Protocol):
    name: str

    def retrieve(
        self,
        query: StructuredQuery,
        plan: RetrievalPlan,
        channel: RetrievalChannelPlan,
    ) -> list[Candidate]:
        ...
```

- [ ] **Step 2: Add vector room retriever by adapting current `VectorAdapter.search_rooms()`**

Key behavior:

- Use only rewrites matching channel `query_kinds`.
- Call `embed_fn(text)`.
- Call `vector_adapter.search_rooms(vector, filters=channel.filters, top_k=channel.top_k)`.
- Return `Candidate(candidate_id=f"room:{room_id}", kind="room", payload=r)`.

- [ ] **Step 3: Add lease room retriever baseline**

Initial baseline can return `[]` if no synchronous lease search helper is available. This is intentional because room validation is added in Task 9. The file must still exist behind the retriever interface so the harness shape is correct.

```python
from __future__ import annotations

from aptguide2.rag_harness.contracts import Candidate, RetrievalChannelPlan, RetrievalPlan, StructuredQuery


class RoomLeaseRetriever:
    name = "room_lease"

    def retrieve(
        self,
        query: StructuredQuery,
        plan: RetrievalPlan,
        channel: RetrievalChannelPlan,
    ) -> list[Candidate]:
        return []
```

- [ ] **Step 4: Add KB vector retriever by adapting `VectorAdapter.search_kb()`**

Key behavior:

- Use `chunk_id` as candidate id: `kb:{chunk_id}`.
- Preserve `doc_id`, `module`, `title`, `content`, `risk_level` in payload.

- [ ] **Step 5: Add KB keyword retriever baseline**

Use simple lexical matching over KB payload only if a local in-memory source is supplied. If no source is supplied, return `[]`. The interface exists so BM25 can replace this baseline later.

- [ ] **Step 6: Test retrievers with fake adapters**

Write fake adapter tests that assert:

- room vector retriever passes filters;
- KB vector retriever maps `chunk_id` into `Candidate`;
- lease and keyword baselines return empty lists without failing.

- [ ] **Step 7: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness/test_retrievers.py -q
```

Expected: pass.

### Task 8: Add Result Merger

**Files:**

- Create: `backend/src/aptguide2/rag_harness/merge.py`
- Test: `backend/tests/unit/rag_harness/test_merge.py`

- [ ] **Step 1: Write merger tests**

```python
from aptguide2.rag_harness.contracts import Candidate
from aptguide2.rag_harness.merge import merge_candidates


def test_merge_keeps_best_score_and_combines_sources():
    items = [
        Candidate(candidate_id="room:1", kind="room", score=0.6, sources=["room_vector"]),
        Candidate(candidate_id="room:1", kind="room", score=0.8, sources=["room_lease"]),
    ]
    merged = merge_candidates(items)
    assert len(merged) == 1
    assert merged[0].score == 0.8
    assert set(merged[0].sources) == {"room_vector", "room_lease"}
```

- [ ] **Step 2: Implement merger**

```python
from __future__ import annotations

from aptguide2.rag_harness.contracts import Candidate


def merge_candidates(candidates: list[Candidate]) -> list[Candidate]:
    merged: dict[str, Candidate] = {}
    for candidate in candidates:
        existing = merged.get(candidate.candidate_id)
        if existing is None:
            merged[candidate.candidate_id] = candidate.model_copy(deep=True)
            continue
        if candidate.score > existing.score:
            existing.score = candidate.score
            existing.payload.update(candidate.payload)
        existing.sources = sorted(set(existing.sources + candidate.sources))
        existing.matched_queries = sorted(set(existing.matched_queries + candidate.matched_queries))
    return sorted(merged.values(), key=lambda c: c.score, reverse=True)
```

- [ ] **Step 3: Run merger tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness/test_merge.py -q
```

Expected: pass.

### Task 9: Add Validation Gates

**Files:**

- Create: `backend/src/aptguide2/rag_harness/validators/room.py`
- Create: `backend/src/aptguide2/rag_harness/validators/kb.py`
- Create: `backend/src/aptguide2/rag_harness/validators/__init__.py`
- Test: `backend/tests/unit/rag_harness/test_validators.py`

- [ ] **Step 1: Implement room validation baseline**

Purpose:

- For now, trust vector payload fields only if `status` is absent or active.
- Keep this behind a `RoomValidationGate` so a lease-backed validator can replace it next.
- Mark payload with `validated_by="vector_payload_baseline"`.

- [ ] **Step 2: Implement KB grounding validation**

Purpose:

- Drop KB candidates without `doc_id`, `title`, or `content`.
- For high-risk queries, keep only sources with `risk_level="high"` or module in `lease/payment`.

- [ ] **Step 3: Write tests**

Tests should assert:

- inactive room candidates are removed;
- KB candidates without content are removed;
- high-risk KB validation removes low-risk unrelated module candidates.

### Task 10: Add Reranker Interfaces and Baseline Rerankers

**Files:**

- Create: `backend/src/aptguide2/rag_harness/rerankers/base.py`
- Create: `backend/src/aptguide2/rag_harness/rerankers/room_rule.py`
- Create: `backend/src/aptguide2/rag_harness/rerankers/kb_rule.py`
- Create: `backend/src/aptguide2/rag_harness/rerankers/semantic_stub.py`
- Create: `backend/src/aptguide2/rag_harness/rerankers/__init__.py`
- Test: `backend/tests/unit/rag_harness/test_rerankers.py`

- [ ] **Step 1: Add reranker protocol**

```python
from __future__ import annotations

from typing import Protocol

from aptguide2.rag_harness.contracts import Candidate, StructuredQuery


class Reranker(Protocol):
    name: str

    def rerank(self, query: StructuredQuery, candidates: list[Candidate], top_n: int) -> list[Candidate]:
        ...
```

- [ ] **Step 2: Add room rule reranker**

Business rules:

- hard filter mismatch gets a strong penalty;
- exact area match gets a boost;
- budget fit gets a boost;
- soft preference overlap with tags/facilities gets a boost;
- source `room_lease` gets a boost over vector-only candidates.

- [ ] **Step 3: Add KB rule reranker**

Business rules:

- start from candidate score;
- boost matching module/topic;
- boost exact title phrase overlap;
- penalize high-risk query with low-risk source;
- keep code behind interface so semantic reranker can replace it.

- [ ] **Step 4: Add semantic stub**

`SemanticRerankerStub` should return candidates unchanged. This lets config reference a semantic reranker in development without failing before an external provider is added.

### Task 11: Add Confidence Gate V2

**Files:**

- Create: `backend/src/aptguide2/rag_harness/confidence.py`
- Test: `backend/tests/unit/rag_harness/test_confidence.py`

- [ ] **Step 1: Write tests**

Test cases:

- room candidates with at least one validated room are confident;
- KB high-risk needs a high score and grounded source;
- KB low-risk can pass with lower score;
- empty candidates fail with `retrieval_empty`.

- [ ] **Step 2: Implement confidence result**

Add model if needed:

```python
class ConfidenceDecision(BaseModel):
    is_confident: bool
    reason: str = ""
    score: float = 0.0
```

Rules:

```text
room_search:
  confident if validated candidate count > 0

kb_qa low:
  top score >= 0.45 and source has content

kb_qa medium:
  top score >= 0.55 and top 3 include lease/payment/policy/appointment/life/account depending topic

kb_qa high:
  top score >= 0.65 and top 3 include high-risk lease/payment source
```

### Task 12: Add Response Composer

**Files:**

- Create: `backend/src/aptguide2/rag_harness/composer.py`
- Test: `backend/tests/unit/rag_harness/test_composer.py`

- [ ] **Step 1: Implement fallback composition**

Reasons:

```text
safety_blocked
router_uncertain
retrieval_empty
validation_empty
low_confidence
unsupported_task
```

- [ ] **Step 2: Implement room response composition**

Compose message from top rooms without inventing facts:

```text
为您找到以下房源推荐：
1. {apartment_name}，月租{rent}元（{reason}）
```

- [ ] **Step 3: Implement KB source-bound composition baseline**

Initial version can use extractive answer snippets from top source content. LLM grounded generation can be wired later by provider strategy.

### Task 13: Add Trace Recorder and Replay Case Writer

**Files:**

- Create: `backend/src/aptguide2/rag_harness/trace.py`
- Create: `backend/src/aptguide2/rag_harness/replay.py`
- Test: `backend/tests/unit/rag_harness/test_trace.py`
- Test: `backend/tests/unit/rag_harness/test_replay.py`

- [ ] **Step 1: Implement trace recorder**

Requirements:

- Add `start_stage(stage, strategy, input_summary)`.
- Add `finish_stage(stage_id, output_summary, errors)`.
- Store latency in milliseconds.
- Return `RagTrace`.

- [ ] **Step 2: Implement replay case writer**

Output JSONL shape:

```json
{
  "request": {"message": "...", "session_id": "..."},
  "response": {"task": "...", "message": "..."},
  "trace": {"trace_id": "...", "stages": []}
}
```

- [ ] **Step 3: Add PII guard**

Reuse `trace.retrieval_events.validate_no_pii()` before writing replay case.

### Task 14: Add Orchestrator

**Files:**

- Create: `backend/src/aptguide2/rag_harness/orchestrator.py`
- Test: `backend/tests/unit/rag_harness/test_room_harness.py`
- Test: `backend/tests/unit/rag_harness/test_kb_harness.py`

- [ ] **Step 1: Implement orchestrator dependency shape**

Constructor inputs:

```python
RagHarness(
    router,
    understanding,
    rewrite,
    planner,
    retrievers,
    validators,
    rerankers,
    confidence_gate,
    composer,
)
```

- [ ] **Step 2: Implement room flow**

```text
request
  -> context
  -> router
  -> understanding
  -> rewrite
  -> plan
  -> retrievers
  -> merge
  -> room validator
  -> room reranker
  -> confidence
  -> composer
```

- [ ] **Step 3: Implement KB flow**

Same flow, but use KB validator and KB reranker.

- [ ] **Step 4: Implement fallback flow**

If router returns fallback, skip retrieval and compose fallback with `fallback_reason`.

- [ ] **Step 5: Tests with fake retrievers**

Use fake retrievers to avoid Milvus and lease:

- room fake returns two room candidates;
- KB fake returns two KB candidates;
- assert final `RagResponse.task`, `rooms`, `kb_sources`, and trace stages.

### Task 15: Wire Harness Behind API Version Switch

**Files:**

- Modify: `backend/src/aptguide2/api/deps.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Modify: `backend/src/aptguide2/core/config.py`
- Test: `backend/tests/e2e/test_api.py`

- [ ] **Step 1: Add settings**

In `Settings`:

```python
rag_pipeline_version: str = "v1"
rag_harness_include_trace: bool = False
```

Environment examples:

```text
APTGUIDE_RAG_PIPELINE_VERSION=v1
APTGUIDE_RAG_PIPELINE_VERSION=harness_v1
APTGUIDE_RAG_HARNESS_INCLUDE_TRACE=false
```

- [ ] **Step 2: Add `get_rag_harness()` factory**

Create dependencies using existing `get_vector_adapter()` and `get_embed_fn()`.

- [ ] **Step 3: Branch in `/chat`**

Pseudo-code:

```python
settings = get_settings()
if settings.rag_pipeline_version == "harness_v1":
    harness = get_rag_harness()
    result = harness.run(RagRequest(message=req.message, session_id=req.session_id))
    return _build_harness_response(result)
```

Keep current `run_pipeline()` as v1 default.

- [ ] **Step 4: Add E2E test for default compatibility**

Assert current v1 behavior still works when default config is unchanged.

- [ ] **Step 5: Add E2E test for harness branch**

Use monkeypatch or dependency override to run fake harness and assert `/chat` can serialize harness response.

### Task 16: Add Lease-Backed Room Validation

**Files:**

- Modify: `backend/src/aptguide2/rag_harness/validators/room.py`
- Modify: `backend/src/aptguide2/tools/lease_adapter.py` only if an internal batch validation helper is missing
- Test: `backend/tests/unit/rag_harness/test_validators.py`

- [ ] **Step 1: Define validation payload**

Input:

```json
{
  "room_ids": [1001, 1002],
  "hard_filters": {"district_id": 4, "max_rent": 1500},
  "limit": 20,
  "strategy": "harness_room_validation_v1"
}
```

- [ ] **Step 2: Implement adapter method or local fallback**

If lease already exposes a compatible endpoint, use it. If not, keep vector payload validation as fallback and name the strategy `vector_payload_baseline`.

- [ ] **Step 3: Enforce fact ownership**

After this task, response composer must use validated room payloads, not raw Milvus payloads, for price, availability, and display fields.

### Task 17: Add Semantic Reranker Provider Interface

**Files:**

- Modify: `backend/src/aptguide2/rag_harness/rerankers/semantic_stub.py`
- Create: `backend/src/aptguide2/rag_harness/rerankers/provider.py`
- Test: `backend/tests/unit/rag_harness/test_rerankers.py`

- [ ] **Step 1: Define provider request**

```python
class RerankRequest(BaseModel):
    query: str
    documents: list[str]
    top_n: int
```

- [ ] **Step 2: Define provider response**

```python
class RerankScore(BaseModel):
    index: int
    score: float
```

- [ ] **Step 3: Keep provider optional**

If no provider is configured, the harness must fall back to rule reranker and add trace error `semantic_reranker_unconfigured`.

### Task 18: Add Developer Documentation

**Files:**

- Create: `docs/system/rag-harness-architecture.md`
- Modify: `docs/system/README.md`
- Modify: `docs/plans/README.md`

- [ ] **Step 1: Document harness runtime flow**

Include:

```text
RagRequest -> RagResponse
stage contracts
strategy registry
trace and replay
v1/harness_v1 switch
```

- [ ] **Step 2: Document extension points**

Explain how to add:

- router strategy;
- retriever channel;
- validator;
- reranker;
- composer.

- [ ] **Step 3: Update indexes**

Add links to the architecture doc and this plan.

## 6. Execution Order

Recommended sequence:

```text
1. Contracts
2. Registry and config
3. Router and understanding
4. Rewrite and planning
5. Retrievers and merger
6. Validators and rerankers
7. Confidence and composer
8. Trace and replay
9. Orchestrator
10. API switch
11. Lease-backed validation
12. Semantic reranker provider
13. Documentation
```

This order gives a working harness shell before expensive provider integrations.

## 7. Verification Commands

After each task:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness -q
```

Before enabling the harness branch:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag_harness tests/unit/rag tests/e2e -q
```

Manual smoke test after API switch:

```bash
cd "AptGuide 2.0/backend"
APTGUIDE_RAG_PIPELINE_VERSION=harness_v1 uv run uvicorn aptguide2.api.app:app --reload
```

Then:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"番禺1500以内安静点的房子","session_id":"dev-session"}'
```

Expected:

- response `task` is `room_search`;
- response contains room results or a clear `fallback_reason`;
- no traceback;
- trace is included only when `APTGUIDE_RAG_HARNESS_INCLUDE_TRACE=true`.

## 8. Acceptance Criteria

The enterprise harness foundation is complete when:

- `aptguide2.rag_harness` exists and is covered by unit tests.
- All stage outputs are Pydantic models, not uncontrolled dict chains.
- `/chat` can run either `v1` or `harness_v1` by configuration.
- Room and KB flows both pass through orchestrator, rewrite, retrieval plan, merger, validation, rerank, confidence, composer, and trace.
- Missing retriever or reranker providers degrade cleanly instead of crashing.
- Replay cases can be written without PII.
- Current MVP tests still pass with `APTGUIDE_RAG_PIPELINE_VERSION=v1`.

## 9. What This Plan Intentionally Defers

This plan does not start with a full eval platform because the current goal is to fix the RAG system architecture first.

Deferred until harness foundation is stable:

- large-scale RAG eval suite redesign;
- online A/B testing;
- Learning to Rank training;
- long-term user preference profile;
- MCP tool exposure;
- front-end interaction cards;
- production observability integration beyond local trace and replay.

These are easier and safer once the harness has stable contracts, strategy registry, trace, and replay.
