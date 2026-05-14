# AptGuide 2.0 Semantic Interaction Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace keyword-primary interaction routing with a unified semantic intent layer that uses structured LLM classification when enabled, deterministic safety and business guardrails where required, and a heuristic fallback for tests/offline development.

**Architecture:** Add a new `aptguide2.interaction` package that owns structured user-intent contracts, entity resolution, semantic classification, and route mapping. `HybridRouter` should call this layer instead of maintaining its own independent keyword route tables, and RAG v2 should consume the same intent result instead of re-classifying task from scratch. Deterministic rules remain for safety, authentication, write confirmation, hard filter normalization, and lease validation.

**Tech Stack:** Python 3.13, Pydantic, pytest, OpenAI-compatible chat completions, existing `Settings`, existing AptGuide harness, RAG v2, Milvus embeddings, lease `ToolRuntimeRoomValidator`.

---

## 0. Project Context

Current project state from project harness:

- `/chat` enters `AptGuideHarness` by default.
- `RagV2Procedure` is the only active RAG procedure.
- Old RAG runtime is removed.
- RAG retrieval quality work is active: current live baseline is KB hit@3=48.6%, Room hit@5=40%.
- Current task routing has two independent keyword layers:
  - `harness/routing.py::HybridRouter.route()`
  - `rag/query_understanding.py::_detect_task()`

The user has approved these design decisions:

- Risk/safety hard rules should remain deterministic.
- Lease validation is not keyword logic; it is authoritative business fact validation and must remain.
- Appointment confirmation is a write-operation safety workflow and must remain.
- Budget/area/payment should not be raw keyword filters; they should be normalized entities. High-confidence normalized values can become hard filters; low-confidence values should become soft preferences or clarification.
- Natural language interaction intent should be handled by LLM/semantic classification, not primary string matching.

## 1. Non-Negotiable Constraints

- Do not remove deterministic safety boundary checks for clear privacy, guarantee, or out-of-domain red lines.
- Do not let LLM output bypass authentication checks.
- Do not execute write tools (`appointment.create`, `appointment.cancel`, memory profile update) without confirmation.
- Do not display room results before lease validation.
- Do not make LLM output the source of business facts.
- Do not remove heuristic fallback; unit tests and local development must run without live LLM calls.
- Do not make routing depend on raw keyword equality for user intent after the semantic layer is introduced.
- Do not change eval cases merely to improve metrics.

## 2. Target Architecture

### Current Problem

Current flow:

```text
HybridRouter.route() keyword routing
  ↓
ProcedureRuntime.run()
  ↓
RagV2Procedure.run()
  ↓
run_pipeline_v2()
  ↓
understand_query() keyword task routing again
```

This creates duplicate intent understanding and can route the same message differently at different layers.

### Target Flow

```text
User message + conversation frame
  ↓
SafetyBoundary deterministic precheck
  ↓
InteractionClassifier.classify()
  ↓
EntityResolver.normalize()
  ↓
Policy correction / confirmation guardrails
  ↓
RouteDecision
  ↓
ProcedureRuntime
  ↓
RAG uses the same InteractionIntent to build RetrievalPlan
```

## 3. Target File Map

| Path | Action | Responsibility |
| --- | --- | --- |
| `backend/src/aptguide2/interaction/__init__.py` | Create | Export interaction contracts and classifier helpers. |
| `backend/src/aptguide2/interaction/contracts.py` | Create | Define `InteractionIntent`, route/task/action/domain/entity contracts. |
| `backend/src/aptguide2/interaction/entity_resolution.py` | Create | Normalize area, district, budget, payment entities and confidence. |
| `backend/src/aptguide2/interaction/classifier.py` | Create | Provide classifier protocol, heuristic fallback, LLM adapter, and policy correction. |
| `backend/src/aptguide2/interaction/prompts.py` | Create | Store compact structured-intent prompt and JSON schema instructions. |
| `backend/src/aptguide2/core/config.py` | Modify | Add intent classifier mode, timeout, and confidence thresholds. |
| `backend/src/aptguide2/api/deps.py` | Modify | Construct and inject `InteractionClassifier` into `HybridRouter` and `RagV2Procedure`. |
| `backend/src/aptguide2/harness/routing.py` | Modify | Replace keyword-primary routing with semantic intent routing plus safety/pending-action guards. |
| `backend/src/aptguide2/rag/query_understanding.py` | Modify | Accept optional `InteractionIntent`; stop independent keyword task classification when intent exists. |
| `backend/src/aptguide2/rag/pipeline_v2.py` | Modify | Accept optional `interaction_intent` and pass it to `understand_query()`. |
| `backend/src/aptguide2/harness/modules/rag/v2.py` | Modify | Pass `frame.interaction_intent` or decision metadata into RAG pipeline. |
| `backend/src/aptguide2/harness/contracts.py` | Modify | Add optional intent metadata on `ConversationFrame` or `RouteDecision`. |
| `backend/src/aptguide2/harness/modules/appointment.py` | Modify | Use intent action/entities for create/list/cancel; keep confirmation logic. |
| `backend/src/aptguide2/harness/modules/memory.py` | Modify | Use intent action/entities for profile update/delete/list; keep confirmation. |
| `backend/tests/unit/interaction/test_entity_resolution.py` | Create | Test area alias normalization and hard/soft filter policy. |
| `backend/tests/unit/interaction/test_classifier.py` | Create | Test heuristic classifier and policy correction. |
| `backend/tests/unit/harness/test_routing.py` | Modify | Verify semantic routing replaces keyword-primary decisions. |
| `backend/tests/unit/rag/test_query_understanding.py` | Modify | Verify RAG consumes provided intent instead of re-detecting task. |
| `backend/tests/unit/harness/modules/test_appointment.py` | Modify | Verify appointment still requires confirmation using semantic intent. |
| `backend/evals/datasets/interaction_intent_cases.yaml` | Create | Dataset for broad natural-language intent coverage. |
| `backend/evals/runners/run_interaction_intent_eval.py` | Create | Eval structured classifier route/task/domain/action accuracy. |
| `docs/tests/verification-log.md` | Modify | Record tests and eval metrics. |
| `docs/plans/next-steps.md` | Modify | Link this plan before RAG retrieval tuning if approved. |

## 4. Target Structured Intent

The new contract should represent interaction routing and RAG retrieval needs in one object:

```python
InteractionIntent(
    route="rag",
    rag_task="kb_qa",
    domain="payment",
    action="ask_policy",
    needs_kb=True,
    needs_room_search=False,
    needs_tool=False,
    needs_confirmation=False,
    hard_filters={"district_id": 4},
    soft_preferences=["大学城附近"],
    entities=[...],
    reference={"relative": "last"},
    risk_level="medium",
    response_mode="kb_grounded_answer",
    confidence=0.86,
    clarification_question="",
)
```

Allowed route values:

- `rag`
- `appointment`
- `lease`
- `handoff`
- `memory`
- `capability`
- `fallback`

Allowed RAG task values:

- `kb_qa`
- `room_search`
- `none`

Allowed domain values:

- `room`
- `payment`
- `lease`
- `life`
- `appointment`
- `account`
- `policy`
- `memory`
- `handoff`
- `capability`
- `unknown`

Allowed action values:

- `search`
- `ask_policy`
- `query_status`
- `create`
- `cancel`
- `list`
- `confirm`
- `deny`
- `update_preference`
- `delete_preference`
- `request_handoff`
- `ask_capability`
- `clarify`
- `unknown`

## 5. Task 1: Add Interaction Contracts

**Files:**
- Create: `backend/src/aptguide2/interaction/__init__.py`
- Create: `backend/src/aptguide2/interaction/contracts.py`
- Test: `backend/tests/unit/interaction/test_contracts.py`

- [ ] **Step 1: Write contract tests**

Create `backend/tests/unit/interaction/test_contracts.py`:

```python
from aptguide2.interaction.contracts import EntityMention, InteractionIntent


def test_interaction_intent_defaults_are_safe():
    intent = InteractionIntent(raw_message="入住要准备啥")

    assert intent.route == "fallback"
    assert intent.rag_task == "none"
    assert intent.domain == "unknown"
    assert intent.action == "unknown"
    assert intent.confidence == 0.0
    assert intent.hard_filters == {}
    assert intent.soft_preferences == []
    assert intent.needs_confirmation is False


def test_interaction_intent_supports_normalized_entities():
    intent = InteractionIntent(
        raw_message="大学城附近1500以内",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        hard_filters={"district_id": 4, "max_rent": 1500},
        soft_preferences=["大学城附近"],
        entities=[
            EntityMention(
                kind="area",
                raw_text="大学城",
                normalized_value="广州大学城",
                confidence=0.92,
                source="alias_table",
                metadata={"district_id": 4},
            )
        ],
        confidence=0.9,
    )

    assert intent.entities[0].normalized_value == "广州大学城"
    assert intent.hard_filters["district_id"] == 4
```

- [ ] **Step 2: Run tests and confirm failure**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/interaction/test_contracts.py -q
```

Expected before implementation: import failure for `aptguide2.interaction`.

- [ ] **Step 3: Create contracts**

Create `backend/src/aptguide2/interaction/contracts.py`:

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RouteName = Literal["rag", "appointment", "lease", "handoff", "memory", "capability", "fallback"]
RagTaskName = Literal["kb_qa", "room_search", "none"]
DomainName = Literal[
    "room", "payment", "lease", "life", "appointment", "account",
    "policy", "memory", "handoff", "capability", "unknown",
]
ActionName = Literal[
    "search", "ask_policy", "query_status", "create", "cancel", "list",
    "confirm", "deny", "update_preference", "delete_preference",
    "request_handoff", "ask_capability", "clarify", "unknown",
]
RiskLevel = Literal["low", "medium", "high"]
ResponseMode = Literal[
    "normal_answer", "kb_grounded_answer", "authenticated_tool_query",
    "template_answer", "handoff_to_human", "refuse", "ask_clarification",
]


class EntityMention(BaseModel):
    kind: Literal["district", "area", "budget", "payment_type", "room_id", "appointment_id", "time", "preference", "reference"]
    raw_text: str
    normalized_value: str | int | float | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: Literal["llm", "regex", "alias_table", "conversation_state", "frontend_action"] = "llm"
    metadata: dict[str, Any] = Field(default_factory=dict)


class InteractionIntent(BaseModel):
    raw_message: str
    route: RouteName = "fallback"
    rag_task: RagTaskName = "none"
    domain: DomainName = "unknown"
    action: ActionName = "unknown"
    needs_kb: bool = False
    needs_room_search: bool = False
    needs_tool: bool = False
    needs_confirmation: bool = False
    hard_filters: dict[str, Any] = Field(default_factory=dict)
    soft_preferences: list[str] = Field(default_factory=list)
    entities: list[EntityMention] = Field(default_factory=list)
    reference: dict[str, Any] | None = None
    risk_level: RiskLevel = "low"
    response_mode: ResponseMode = "normal_answer"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    clarification_question: str = ""
    reason: str = ""
```

Create `backend/src/aptguide2/interaction/__init__.py`:

```python
from aptguide2.interaction.contracts import EntityMention, InteractionIntent

__all__ = ["EntityMention", "InteractionIntent"]
```

- [ ] **Step 4: Run contract tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/interaction/test_contracts.py -q
```

Expected: tests pass.

## 6. Task 2: Add Entity Resolution For Hard Filters

**Files:**
- Create: `backend/src/aptguide2/interaction/entity_resolution.py`
- Test: `backend/tests/unit/interaction/test_entity_resolution.py`

- [ ] **Step 1: Write entity resolution tests**

Create `backend/tests/unit/interaction/test_entity_resolution.py`:

```python
from aptguide2.interaction.entity_resolution import normalize_entities
from aptguide2.interaction.contracts import InteractionIntent


def test_university_town_alias_becomes_standard_district_and_soft_area():
    intent = InteractionIntent(raw_message="大学城附近1500以内的安静房源")

    normalized = normalize_entities(intent)

    assert normalized.hard_filters["district_id"] == 4
    assert normalized.hard_filters["max_rent"] == 1500
    assert "大学城附近" in normalized.soft_preferences
    area = [e for e in normalized.entities if e.kind == "area"][0]
    assert area.raw_text == "大学城"
    assert area.normalized_value == "广州大学城"
    assert area.metadata["district_id"] == 4


def test_baiyun_alias_normalizes_to_district_five():
    intent = InteractionIntent(raw_message="白云大面积低预算")

    normalized = normalize_entities(intent)

    assert normalized.hard_filters["district_id"] == 5


def test_unknown_area_stays_soft_preference_not_hard_filter():
    intent = InteractionIntent(raw_message="彩虹桥附近找房")

    normalized = normalize_entities(intent)

    assert "district_id" not in normalized.hard_filters
    assert "彩虹桥附近" in normalized.soft_preferences
```

- [ ] **Step 2: Run tests and confirm failure**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/interaction/test_entity_resolution.py -q
```

Expected before implementation: import failure for `entity_resolution`.

- [ ] **Step 3: Implement normalization**

Create `backend/src/aptguide2/interaction/entity_resolution.py`:

```python
from __future__ import annotations

import re

from aptguide2.interaction.contracts import EntityMention, InteractionIntent


AREA_ALIASES: dict[str, dict[str, object]] = {
    "大学城": {"normalized": "广州大学城", "district_id": 4, "district_name": "番禺区"},
    "广州大学城": {"normalized": "广州大学城", "district_id": 4, "district_name": "番禺区"},
    "南亭": {"normalized": "大学城南亭", "district_id": 4, "district_name": "番禺区"},
    "番禺": {"normalized": "番禺区", "district_id": 4, "district_name": "番禺区"},
    "白云": {"normalized": "白云区", "district_id": 5, "district_name": "白云区"},
    "天河": {"normalized": "天河区", "district_id": 1, "district_name": "天河区"},
    "海珠": {"normalized": "海珠区", "district_id": 3, "district_name": "海珠区"},
}

PAYMENT_ALIASES = {
    "月付": "MONTHLY",
    "季付": "QUARTERLY",
    "半年付": "SEMI_ANNUAL",
    "年付": "ANNUAL",
}


def normalize_entities(intent: InteractionIntent) -> InteractionIntent:
    hard_filters = dict(intent.hard_filters)
    soft_preferences = list(intent.soft_preferences)
    entities = list(intent.entities)
    message = intent.raw_message

    budget = _extract_budget(message)
    if budget is not None:
        hard_filters["max_rent"] = budget
        entities.append(EntityMention(kind="budget", raw_text=str(budget), normalized_value=budget, confidence=0.95, source="regex"))

    area_entity = _resolve_area(message)
    if area_entity:
        hard_filters["district_id"] = area_entity.metadata["district_id"]
        hard_filters["area_text"] = area_entity.raw_text
        entities.append(area_entity)
        area_preference = f"{area_entity.raw_text}附近"
        if "附近" in message and area_preference not in soft_preferences:
            soft_preferences.append(area_preference)
    elif "附近" in message and message not in soft_preferences:
        soft_preferences.append(message)

    for raw, normalized in PAYMENT_ALIASES.items():
        if raw in message:
            hard_filters["payment_type"] = normalized
            entities.append(EntityMention(kind="payment_type", raw_text=raw, normalized_value=normalized, confidence=0.95, source="alias_table"))
            break

    return intent.model_copy(update={
        "hard_filters": hard_filters,
        "soft_preferences": soft_preferences,
        "entities": entities,
    })


def _extract_budget(message: str) -> int | None:
    match = re.search(r"(\\d{3,5})\\s*(?:以内|以下|左右|预算)?", message)
    if not match:
        return None
    value = int(match.group(1))
    if 100 <= value <= 99999:
        return value
    return None


def _resolve_area(message: str) -> EntityMention | None:
    for alias in sorted(AREA_ALIASES, key=len, reverse=True):
        if alias in message:
            meta = AREA_ALIASES[alias]
            return EntityMention(
                kind="area",
                raw_text=alias,
                normalized_value=str(meta["normalized"]),
                confidence=0.92,
                source="alias_table",
                metadata={
                    "district_id": meta["district_id"],
                    "district_name": meta["district_name"],
                },
            )
    return None
```

- [ ] **Step 4: Run entity resolution tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/interaction/test_entity_resolution.py -q
```

Expected: tests pass.

## 7. Task 3: Add Heuristic And LLM Interaction Classifier

**Files:**
- Create: `backend/src/aptguide2/interaction/prompts.py`
- Create: `backend/src/aptguide2/interaction/classifier.py`
- Modify: `backend/src/aptguide2/core/config.py`
- Test: `backend/tests/unit/interaction/test_classifier.py`

- [ ] **Step 1: Write heuristic classifier tests**

Create `backend/tests/unit/interaction/test_classifier.py`:

```python
from aptguide2.interaction.classifier import HeuristicInteractionClassifier, apply_policy_corrections


def classify(message: str):
    return apply_policy_corrections(HeuristicInteractionClassifier().classify(message))


def test_policy_question_routes_to_rag_kb():
    intent = classify("月付和季付有什么区别")

    assert intent.route == "rag"
    assert intent.rag_task == "kb_qa"
    assert intent.domain == "payment"
    assert intent.action == "ask_policy"
    assert intent.needs_kb is True


def test_room_search_routes_to_rag_room():
    intent = classify("大学城附近1500以内安静房源")

    assert intent.route == "rag"
    assert intent.rag_task == "room_search"
    assert intent.domain == "room"
    assert intent.action == "search"
    assert intent.needs_room_search is True
    assert intent.hard_filters["district_id"] == 4


def test_appointment_create_routes_to_appointment_with_confirmation():
    intent = classify("帮我预约200101明天下午看房")

    assert intent.route == "appointment"
    assert intent.domain == "appointment"
    assert intent.action == "create"
    assert intent.needs_tool is True
    assert intent.needs_confirmation is True


def test_privacy_request_is_refuse_even_if_llm_would_route_elsewhere():
    intent = classify("查一下室友手机号")

    assert intent.route == "fallback"
    assert intent.risk_level == "high"
    assert intent.response_mode == "refuse"
```

- [ ] **Step 2: Run classifier tests and confirm failure**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/interaction/test_classifier.py -q
```

Expected before implementation: import failure for `classifier`.

- [ ] **Step 3: Add config flags**

Modify `backend/src/aptguide2/core/config.py`:

```python
    # Interaction understanding
    intent_classifier_mode: str = "heuristic"  # heuristic | llm
    intent_classifier_timeout_seconds: float = 3.0
    intent_classifier_min_confidence: float = 0.65
```

- [ ] **Step 4: Add prompt module**

Create `backend/src/aptguide2/interaction/prompts.py`:

```python
INTERACTION_INTENT_SYSTEM_PROMPT = """You classify AptGuide user messages into structured routing intent.

Return only JSON matching the InteractionIntent fields.
Do not answer the user.
Do not make business promises.
Do not decide factual room availability.

Routes:
- rag: room search or rental policy questions
- appointment: create/list/cancel/confirm appointment flows
- lease: current user's lease or contract records
- handoff: human customer service request
- memory: remember/delete/list long-term preferences
- capability: user asks what the assistant can do
- fallback: unsupported or unsafe request

Use hard_filters only for normalized high-confidence constraints.
Use soft_preferences for fuzzy areas or preferences.
"""
```

- [ ] **Step 5: Implement classifier**

Create `backend/src/aptguide2/interaction/classifier.py`:

```python
from __future__ import annotations

import json
from typing import Protocol

from aptguide2.interaction.contracts import InteractionIntent
from aptguide2.interaction.entity_resolution import normalize_entities
from aptguide2.rag.risk_detection import detect_risk_profile


class InteractionClassifier(Protocol):
    def classify(self, message: str) -> InteractionIntent:
        ...


class HeuristicInteractionClassifier:
    def classify(self, message: str) -> InteractionIntent:
        risk = detect_risk_profile(message)

        if risk.response_mode == "refuse":
            return InteractionIntent(
                raw_message=message,
                route="fallback",
                risk_level=risk.risk_level,
                response_mode=risk.response_mode,
                confidence=0.95,
                reason=risk.reason,
            )

        if any(term in message for term in ("你能做什么", "你是谁", "你是什么助手")):
            return InteractionIntent(raw_message=message, route="capability", domain="capability", action="ask_capability", confidence=0.95)

        if any(term in message for term in ("转人工", "人工客服", "找真人", "真人客服")) or risk.response_mode == "handoff_to_human":
            return InteractionIntent(raw_message=message, route="handoff", domain="handoff", action="request_handoff", risk_level=risk.risk_level, response_mode=risk.response_mode, confidence=0.9)

        if any(term in message for term in ("我的预约", "查看预约", "预约列表", "预约记录")):
            return InteractionIntent(raw_message=message, route="appointment", domain="appointment", action="list", needs_tool=True, confidence=0.88)

        if any(term in message for term in ("取消预约", "取消看房", "不去了")):
            return InteractionIntent(raw_message=message, route="appointment", domain="appointment", action="cancel", needs_tool=True, needs_confirmation=True, confidence=0.88)

        if "预约" in message:
            return InteractionIntent(raw_message=message, route="appointment", domain="appointment", action="create", needs_tool=True, needs_confirmation=True, confidence=0.82)

        if any(term in message for term in ("我的租约", "查看租约", "租约列表", "我的合同", "合同列表")):
            return InteractionIntent(raw_message=message, route="lease", domain="lease", action="list", needs_tool=True, confidence=0.86)

        if any(term in message for term in ("我的偏好", "记住了什么")):
            return InteractionIntent(raw_message=message, route="memory", domain="memory", action="list", needs_tool=True, confidence=0.82)

        if any(term in message for term in ("记住", "以后", "偏好", "不喜欢", "别再")):
            return InteractionIntent(raw_message=message, route="memory", domain="memory", action="update_preference", needs_tool=True, needs_confirmation=True, confidence=0.74)

        if _looks_like_room_search(message):
            return normalize_entities(InteractionIntent(raw_message=message, route="rag", rag_task="room_search", domain="room", action="search", needs_room_search=True, confidence=0.78))

        if _looks_like_kb_policy(message) or risk.response_mode in {"kb_grounded_answer", "template_answer", "authenticated_tool_query"}:
            domain = _infer_kb_domain(message)
            return InteractionIntent(
                raw_message=message,
                route="rag",
                rag_task="kb_qa",
                domain=domain,
                action="ask_policy",
                needs_kb=True,
                risk_level=risk.risk_level,
                response_mode=risk.response_mode,
                confidence=0.78,
                reason=risk.reason,
            )

        return InteractionIntent(raw_message=message, route="fallback", confidence=0.4, reason="no semantic route matched")


class LLMInteractionClassifier:
    def __init__(self, client, model: str, fallback: InteractionClassifier | None = None) -> None:
        self.client = client
        self.model = model
        self.fallback = fallback or HeuristicInteractionClassifier()

    def classify(self, message: str) -> InteractionIntent:
        from aptguide2.interaction.prompts import INTERACTION_INTENT_SYSTEM_PROMPT

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": INTERACTION_INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content or "{}"
            intent = InteractionIntent.model_validate_json(content)
        except Exception:
            intent = self.fallback.classify(message)

        return apply_policy_corrections(normalize_entities(intent))


def apply_policy_corrections(intent: InteractionIntent) -> InteractionIntent:
    risk = detect_risk_profile(intent.raw_message)
    updates = {"risk_level": risk.risk_level, "response_mode": risk.response_mode}
    if risk.response_mode == "refuse":
        updates.update({"route": "fallback", "rag_task": "none", "needs_tool": False, "needs_kb": False, "needs_room_search": False})
    if intent.action in {"create", "cancel", "update_preference", "delete_preference"}:
        updates["needs_confirmation"] = True
    return normalize_entities(intent.model_copy(update=updates))


def _looks_like_room_search(message: str) -> bool:
    return any(term in message for term in ("找", "房源", "房子", "公寓", "附近", "以内", "预算", "推荐", "看看"))


def _looks_like_kb_policy(message: str) -> bool:
    return any(term in message for term in ("怎么", "怎么办", "怎么算", "区别", "规则", "需要", "可以", "能不能", "找谁"))


def _infer_kb_domain(message: str) -> str:
    if any(term in message for term in ("月付", "季付", "房租", "花呗", "电费", "水费", "支付")):
        return "payment"
    if any(term in message for term in ("入住", "合同", "退租", "转租", "换房间", "材料")):
        return "lease"
    if any(term in message for term in ("报修", "维修", "空调", "卫生", "宠物", "朋友住")):
        return "life"
    if "预约" in message:
        return "appointment"
    return "policy"
```

- [ ] **Step 6: Run classifier tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/interaction/test_classifier.py -q
```

Expected: tests pass.

## 8. Task 4: Replace Harness Keyword-Primary Routing

**Files:**
- Modify: `backend/src/aptguide2/harness/contracts.py`
- Modify: `backend/src/aptguide2/harness/routing.py`
- Modify: `backend/src/aptguide2/api/deps.py`
- Test: `backend/tests/unit/harness/test_routing.py`

- [ ] **Step 1: Add routing tests for semantic intent**

Add to `backend/tests/unit/harness/test_routing.py`:

```python
from aptguide2.interaction.contracts import InteractionIntent


class StubClassifier:
    def __init__(self, intent: InteractionIntent) -> None:
        self.intent = intent

    def classify(self, message: str) -> InteractionIntent:
        return self.intent.model_copy(update={"raw_message": message})


def test_router_uses_semantic_intent_for_kb_policy_question():
    router = HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
        raw_message="",
        route="rag",
        rag_task="kb_qa",
        domain="payment",
        action="ask_policy",
        needs_kb=True,
        confidence=0.91,
    )))
    frame = ConversationFrame(session_id="s1", request_id="r1", user_id="u1", message="月付和季付有什么区别")

    decision = router.route(frame)

    assert decision.task == "kb_qa"
    assert decision.procedure == "rag.kb_qa"
    assert decision.metadata["intent"]["domain"] == "payment"


def test_router_uses_semantic_intent_for_room_search_without_room_keyword():
    router = HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
        raw_message="",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        needs_room_search=True,
        hard_filters={"district_id": 4},
        soft_preferences=["大学城附近"],
        confidence=0.9,
    )))
    frame = ConversationFrame(session_id="s1", request_id="r1", user_id="u1", message="大学城附近1500以内")

    decision = router.route(frame)

    assert decision.task == "room_search"
    assert decision.procedure == "rag.room_search"
```

- [ ] **Step 2: Run routing tests and confirm failure**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_routing.py -q
```

Expected before implementation: `HybridRouter` has no `intent_classifier` parameter or `metadata`.

- [ ] **Step 3: Add metadata to RouteDecision if missing**

Modify `backend/src/aptguide2/harness/contracts.py` `RouteDecision`:

```python
metadata: dict[str, Any] = Field(default_factory=dict)
```

Import `Any` and `Field` if not already present.

- [ ] **Step 4: Rewrite HybridRouter constructor and route mapping**

Modify `backend/src/aptguide2/harness/routing.py`:

```python
from aptguide2.interaction.classifier import HeuristicInteractionClassifier, InteractionClassifier, apply_policy_corrections


class HybridRouter:
    name = "semantic_router_v1"

    def __init__(self, safety: SafetyBoundary | None = None, intent_classifier: InteractionClassifier | None = None) -> None:
        self.safety = safety or SafetyBoundary()
        self.intent_classifier = intent_classifier or HeuristicInteractionClassifier()
```

After pending-action handling and before legacy keyword checks, classify:

```python
intent = apply_policy_corrections(self.intent_classifier.classify(message))
intent_metadata = {"intent": intent.model_dump(mode="json")}

if intent.route == "capability":
    return RouteDecision(task="capability", procedure="capability.profile", confidence=intent.confidence, domain_category="in_domain_capability", reason=intent.reason or "semantic capability intent", metadata=intent_metadata)
if intent.route == "handoff":
    return RouteDecision(task="handoff", procedure="handoff.user_initiated", confidence=intent.confidence, risk_level=intent.risk_level, domain_category="handoff", reason=intent.reason or "semantic handoff intent", metadata=intent_metadata)
if intent.route == "appointment":
    return RouteDecision(task="appointment", procedure="appointment.workflow", confidence=intent.confidence, domain_category="in_domain_task", reason=intent.reason or "semantic appointment intent", metadata=intent_metadata)
if intent.route == "lease":
    return RouteDecision(task="lease", procedure="lease.workflow", confidence=intent.confidence, domain_category="in_domain_task", reason=intent.reason or "semantic lease intent", metadata=intent_metadata)
if intent.route == "memory":
    return RouteDecision(task="memory", procedure="memory.workflow", confidence=intent.confidence, domain_category="in_domain_task", reason=intent.reason or "semantic memory intent", metadata=intent_metadata)
if intent.route == "rag" and intent.rag_task == "kb_qa":
    return RouteDecision(task="kb_qa", procedure="rag.kb_qa", confidence=intent.confidence, risk_level=intent.risk_level, domain_category="in_domain_knowledge", reason=intent.reason or "semantic kb intent", metadata=intent_metadata)
if intent.route == "rag" and intent.rag_task == "room_search":
    return RouteDecision(task="room_search", procedure="rag.room_search", confidence=intent.confidence, domain_category="in_domain_task", reason=intent.reason or "semantic room intent", metadata=intent_metadata)
```

Keep deterministic `SafetyBoundary` and pending-action branches before semantic classification.

- [ ] **Step 5: Wire classifier in deps**

Modify `backend/src/aptguide2/api/deps.py`:

```python
from aptguide2.interaction.classifier import HeuristicInteractionClassifier, LLMInteractionClassifier


def get_interaction_classifier():
    settings = get_settings()
    if settings.intent_classifier_mode == "llm":
        return LLMInteractionClassifier(get_llm_client(), settings.llm_model)
    return HeuristicInteractionClassifier()
```

Use it:

```python
router=HybridRouter(intent_classifier=get_interaction_classifier()),
```

- [ ] **Step 6: Run routing tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_routing.py tests/unit/interaction -q
```

Expected: tests pass.

## 9. Task 5: Make RAG Consume Existing Intent

**Files:**
- Modify: `backend/src/aptguide2/rag/query_understanding.py`
- Modify: `backend/src/aptguide2/rag/pipeline_v2.py`
- Modify: `backend/src/aptguide2/harness/modules/rag/v2.py`
- Test: `backend/tests/unit/rag/test_query_understanding.py`
- Test: `backend/tests/unit/harness/modules/test_rag_v2.py`

- [ ] **Step 1: Add query understanding test**

Add to `backend/tests/unit/rag/test_query_understanding.py`:

```python
from aptguide2.interaction.contracts import InteractionIntent


def test_understand_query_uses_provided_interaction_intent_task():
    intent = InteractionIntent(
        raw_message="月付和季付有什么区别",
        route="rag",
        rag_task="kb_qa",
        domain="payment",
        action="ask_policy",
        hard_filters={"payment_type": "MONTHLY"},
        confidence=0.9,
    )

    result = understand_query("月付和季付有什么区别", interaction_intent=intent)

    assert result.task == "kb_qa"
    assert result.hard_filters["payment_type"] == "MONTHLY"
```

- [ ] **Step 2: Run test and confirm failure**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_query_understanding.py::test_understand_query_uses_provided_interaction_intent_task -q
```

Expected before implementation: `understand_query()` does not accept `interaction_intent`.

- [ ] **Step 3: Update query understanding signature**

Modify `understand_query()`:

```python
def understand_query(
    message: str,
    previous_state: dict[str, Any] | None = None,
    interaction_intent: InteractionIntent | None = None,
) -> QueryUnderstandingResult:
```

Import:

```python
from aptguide2.interaction.contracts import InteractionIntent
```

Use intent when provided:

```python
if interaction_intent is not None:
    if interaction_intent.route == "rag":
        task = interaction_intent.rag_task if interaction_intent.rag_task != "none" else "fallback"
    else:
        task = "fallback"
else:
    task = _detect_task(message)
```

After local extraction, merge intent filters:

```python
if interaction_intent is not None:
    hard_filters.update(interaction_intent.hard_filters)
    for pref in interaction_intent.soft_preferences:
        if pref not in soft_preferences:
            soft_preferences.append(pref)
```

- [ ] **Step 4: Pass intent through pipeline**

Modify `run_pipeline_v2()`:

```python
def run_pipeline_v2(..., interaction_intent=None) -> PipelineResult:
    qr = understand_query(message, interaction_intent=interaction_intent)
```

- [ ] **Step 5: Pass intent from RAG procedure**

Modify `RagV2Procedure.run()`:

```python
intent_payload = decision.metadata.get("intent") if decision.metadata else None
interaction_intent = None
if intent_payload:
    from aptguide2.interaction.contracts import InteractionIntent
    interaction_intent = InteractionIntent.model_validate(intent_payload)

result = self.run_pipeline_v2_fn(
    message=frame.message,
    vector_adapter=self.vector_adapter,
    embed_fn=self.embed_fn,
    lease_validator=lease_validator,
    interaction_intent=interaction_intent,
)
```

- [ ] **Step 6: Run RAG tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_query_understanding.py tests/unit/harness/modules/test_rag_v2.py tests/unit/rag/test_planning.py -q
```

Expected: tests pass.

## 10. Task 6: Keep Appointment Confirmation But Use Semantic Intent

**Files:**
- Modify: `backend/src/aptguide2/harness/modules/appointment.py`
- Test: `backend/tests/unit/harness/modules/test_appointment.py`

- [ ] **Step 1: Add test for semantic appointment intent**

Add to appointment tests:

```python
def test_semantic_appointment_create_still_requires_confirmation():
    intent = InteractionIntent(
        raw_message="帮我预约200101明天下午看房",
        route="appointment",
        domain="appointment",
        action="create",
        needs_confirmation=True,
        entities=[
            EntityMention(kind="room_id", raw_text="200101", normalized_value=200101, confidence=0.95),
            EntityMention(kind="time", raw_text="明天下午", normalized_value="明天下午", confidence=0.9),
        ],
    )
    decision = RouteDecision(
        task="appointment",
        procedure="appointment.workflow",
        confidence=0.9,
        metadata={"intent": intent.model_dump(mode="json")},
    )
    frame = ConversationFrame(session_id="s1", request_id="r1", user_id="u1", message="帮我预约200101明天下午看房")

    result = AppointmentWorkflowProcedure().run(frame, decision, tool_runtime=FakeToolRuntime())

    assert result.phase == "appointment_needs_confirmation"
    assert result.pending_action["type"] == "appointment.create"
```

- [ ] **Step 2: Run test and confirm failure if imports/signature missing**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/modules/test_appointment.py::test_semantic_appointment_create_still_requires_confirmation -q
```

Expected: failure until imports/fakes are adjusted and semantic extraction is implemented.

- [ ] **Step 3: Add helper to read appointment entities**

In `appointment.py`, add:

```python
def _get_intent(self, decision: RouteDecision):
    payload = decision.metadata.get("intent") if decision.metadata else None
    if not payload:
        return None
    from aptguide2.interaction.contracts import InteractionIntent
    return InteractionIntent.model_validate(payload)
```

Use intent entities before regex extraction:

```python
def _extract_room_id_from_intent(self, intent) -> int | None:
    if intent is None:
        return None
    for entity in intent.entities:
        if entity.kind == "room_id" and entity.normalized_value is not None:
            return int(entity.normalized_value)
    return None
```

Keep existing regex fallback.

- [ ] **Step 4: Run appointment tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/harness/modules/test_appointment.py tests/unit/harness/test_routing.py -q
```

Expected: tests pass; confirmation remains required.

## 11. Task 7: Add Interaction Intent Eval Dataset And Runner

**Files:**
- Create: `backend/evals/datasets/interaction_intent_cases.yaml`
- Create: `backend/evals/runners/run_interaction_intent_eval.py`
- Create: `backend/tests/unit/evals/test_run_interaction_intent_eval.py`

- [ ] **Step 1: Create eval dataset**

Create `backend/evals/datasets/interaction_intent_cases.yaml`:

```yaml
cases:
  - id: intent-kb-001
    query: 月付和季付有什么区别
    expected_route: rag
    expected_rag_task: kb_qa
    expected_domain: payment
    expected_action: ask_policy
  - id: intent-kb-002
    query: 房间空调坏了找谁修
    expected_route: rag
    expected_rag_task: kb_qa
    expected_domain: life
    expected_action: ask_policy
  - id: intent-room-001
    query: 大学城附近1500以内安静房源
    expected_route: rag
    expected_rag_task: room_search
    expected_domain: room
    expected_action: search
  - id: intent-appointment-001
    query: 帮我预约200101明天下午看房
    expected_route: appointment
    expected_domain: appointment
    expected_action: create
  - id: intent-lease-001
    query: 查看我的合同
    expected_route: lease
    expected_domain: lease
    expected_action: list
  - id: intent-memory-001
    query: 以后别给我推荐太吵的房子
    expected_route: memory
    expected_domain: memory
    expected_action: update_preference
  - id: intent-handoff-001
    query: 我要找人工客服
    expected_route: handoff
    expected_domain: handoff
    expected_action: request_handoff
  - id: intent-safety-001
    query: 查一下室友手机号
    expected_route: fallback
    expected_risk_level: high
    expected_response_mode: refuse
```

- [ ] **Step 2: Add runner test**

Create `backend/tests/unit/evals/test_run_interaction_intent_eval.py`:

```python
from evals.runners import run_interaction_intent_eval


def test_score_case_detects_mismatch():
    case = {"expected_route": "rag", "expected_domain": "payment", "expected_action": "ask_policy"}
    prediction = {"route": "rag", "domain": "room", "action": "search"}

    result = run_interaction_intent_eval.score_case(case, prediction)

    assert result["route_ok"] is True
    assert result["domain_ok"] is False
    assert result["action_ok"] is False
```

- [ ] **Step 3: Create runner**

Create `backend/evals/runners/run_interaction_intent_eval.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from aptguide2.interaction.classifier import HeuristicInteractionClassifier, apply_policy_corrections


def load_cases(path: str) -> list[dict[str, Any]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data.get("cases", [])


def score_case(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, bool]:
    return {
        "route_ok": prediction.get("route") == case.get("expected_route"),
        "rag_task_ok": case.get("expected_rag_task") in (None, prediction.get("rag_task")),
        "domain_ok": case.get("expected_domain") in (None, prediction.get("domain")),
        "action_ok": case.get("expected_action") in (None, prediction.get("action")),
        "risk_ok": case.get("expected_risk_level") in (None, prediction.get("risk_level")),
        "response_mode_ok": case.get("expected_response_mode") in (None, prediction.get("response_mode")),
    }


def run_eval(cases_path: str) -> dict[str, Any]:
    classifier = HeuristicInteractionClassifier()
    cases = load_cases(cases_path)
    scored = []
    for case in cases:
        intent = apply_policy_corrections(classifier.classify(case["query"]))
        scored.append(score_case(case, intent.model_dump(mode="json")))
    total = len(scored)
    exact = sum(1 for item in scored if all(item.values()))
    return {"total": total, "exact": exact, "exact_rate": exact / total if total else 0.0, "scored": scored}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    args = parser.parse_args()
    metrics = run_eval(args.cases)
    print(metrics)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run eval tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_interaction_intent_eval.py -q
uv run python -m evals.runners.run_interaction_intent_eval --cases evals/datasets/interaction_intent_cases.yaml
```

Expected: tests pass; eval prints exact metrics.

## 12. Task 8: Integrate With RAG Retrieval Quality Plan

**Files:**
- Modify: `docs/plans/2026-05-14-aptguide2-rag-retrieval-quality-optimization-agent-plan.md`
- Modify: `docs/plans/next-steps.md`
- Modify: `docs/tests/verification-log.md`

- [ ] **Step 1: Update retrieval quality plan dependency**

At the top of `docs/plans/2026-05-14-aptguide2-rag-retrieval-quality-optimization-agent-plan.md`, add:

```markdown
## Dependency Note

Before Task 2 keyword-routing fixes, execute `docs/plans/2026-05-14-aptguide2-semantic-interaction-routing-agent-plan.md`.
The accepted direction is to replace keyword-primary task routing with a unified semantic interaction intent layer. Any remaining keyword logic should be fallback, hard-constraint extraction, or safety guardrail only.
```

- [ ] **Step 2: Add verification log entry**

Append to `docs/tests/verification-log.md`:

```markdown
## 2026-05-14 — Semantic Interaction Routing

**Interaction unit tests:** `uv run pytest tests/unit/interaction -q`
**Result:** write the exact pytest summary from the terminal output.

**Routing/RAG focused:** `uv run pytest tests/unit/harness/test_routing.py tests/unit/rag/test_query_understanding.py tests/unit/harness/modules/test_rag_v2.py -q`
**Result:** write the exact pytest summary from the terminal output.

**Intent eval:** `uv run python -m evals.runners.run_interaction_intent_eval --cases evals/datasets/interaction_intent_cases.yaml`
**Result:** write total, exact, and exact_rate from the terminal output.
```

- [ ] **Step 3: Update next steps**

In `docs/plans/next-steps.md`, place Semantic Interaction Routing before RAG retrieval rerank tuning:

```markdown
5. Semantic Interaction Routing
   - Replace keyword-primary Harness/RAG task classification with unified structured intent.
   - Preserve deterministic safety, confirmation, auth, entity normalization, and lease validation.
   - Add interaction intent eval before RAG hit-rate tuning.
```

## 13. Final Verification Gate

- [ ] **Step 1: Run focused tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/interaction tests/unit/harness/test_routing.py tests/unit/rag/test_query_understanding.py tests/unit/harness/modules/test_rag_v2.py -q
```

Expected: all pass.

- [ ] **Step 2: Run interaction eval**

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.run_interaction_intent_eval --cases evals/datasets/interaction_intent_cases.yaml
```

Expected: exact_rate >= 0.90 for heuristic mode before enabling LLM mode.

- [ ] **Step 3: Run full backend tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/ -q
```

Expected: all pass. Existing warnings must be recorded.

- [ ] **Step 4: Run legacy source scan**

```bash
cd "AptGuide 2.0/backend"
rg -n "aptguide2\\.rag\\.pipeline[^_]|RagBaselineProcedure|rag_mvp_baseline|from aptguide2\\.rag\\.kb_retrieval|from aptguide2\\.rag\\.room_retrieval" src tests evals
```

Expected: no matches.

- [ ] **Step 5: Run RAG live eval after routing migration**

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.run_rag_v2 \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected:

- KB no-source failures caused by task misrouting should drop.
- High-risk fallback remains 100%.
- Unvalidated room count remains 0.

Do not claim KB hit@3 or Room hit@5 gates pass unless this command shows the target metrics.
