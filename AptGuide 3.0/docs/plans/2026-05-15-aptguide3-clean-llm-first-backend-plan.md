# AptGuide 3.0 Clean LLM-First Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable AptGuide 3.0 backend foundation with LLM-first understanding, clarification on uncertainty, typed procedure dispatch, and no keyword fallback.

**Architecture:** AptGuide 3.0 is a clean backend project. `api` handles HTTP, `application` orchestrates chat, `understanding` calls and validates the LLM, `domain` owns pure contracts, `procedures` own business workflows, `retrieval` and `integrations` isolate external systems, and `observability` records trace events. Natural-language route/task/filter/preference/risk inference must come only from LLM structured output; code validates contracts and deterministic business boundaries.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, pydantic-settings, OpenAI-compatible client, pytest, ruff, uv.

---

## Scope

This plan builds the backend foundation only. It does not build frontend UI, live Milvus retrieval, live lease write flows, Redis/MySQL persistence, or production observability sinks. Those are later layers.

The first runnable backend must support:

- `GET /health`
- `POST /chat`
- LLM-first understanding contract
- clarification when LLM output is invalid or uncertain
- procedure dispatch for `clarify`, `room_search`, and `kb_qa` with placeholder procedure responses
- deterministic safety hard boundary
- anti-regression source scan proving there is no keyword fallback in the understanding runtime

## File Structure

- `backend/src/aptguide3/config.py`
  - Settings and environment parsing.

- `backend/src/aptguide3/domain/`
  - `conversation.py`: request-time conversation frame and user context.
  - `understanding.py`: typed understanding result and enums.
  - `safety.py`: safety decision.
  - `procedures.py`: procedure result and procedure protocol.
  - `responses.py`: response cards/actions/pending action/chat response.

- `backend/src/aptguide3/understanding/`
  - `prompts.py`: strict LLM system prompt.
  - `llm_understanding.py`: OpenAI-compatible structured understanding adapter.
  - `validation.py`: contract validation and clarification conversion.

- `backend/src/aptguide3/application/`
  - `safety_boundary.py`: deterministic safety checks for hard red lines only.
  - `procedure_runtime.py`: registry and dispatch.
  - `response_composer.py`: procedure result to API response.
  - `chat_service.py`: main `/chat` use case.

- `backend/src/aptguide3/procedures/`
  - `clarify.py`: clarification procedure.
  - `room_search.py`: placeholder room-search procedure.
  - `kb_qa.py`: placeholder KB QA procedure.

- `backend/src/aptguide3/api/`
  - `schemas.py`: HTTP schemas.
  - `deps.py`: dependency wiring.
  - `app.py`: FastAPI app.

- `backend/src/aptguide3/observability/`
  - `events.py`: simple trace event contracts.

- `backend/tests/`
  - Unit, e2e, and source-scan tests.

---

## Task 1: Domain Understanding Contract

**Files:**
- Create: `backend/src/aptguide3/domain/understanding.py`
- Test: `backend/tests/unit/domain/test_understanding_contract.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/domain/test_understanding_contract.py`:

```python
import pytest
from pydantic import ValidationError

from aptguide3.domain.understanding import (
    Clarification,
    RiskDecision,
    UnderstandingResult,
)


def test_valid_room_search_understanding_contract():
    result = UnderstandingResult(
        raw_message="珠江新城3000以内有阳台的房间",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.91,
        hard_filters={"max_rent": 3000, "district_id": 1, "area_text": "珠江新城"},
        soft_preferences=["有阳台"],
        retrieval_queries=["珠江新城 3000以内 有阳台 房源"],
        risk=RiskDecision(level="low", response_mode="normal_answer"),
        clarification=Clarification(needed=False, question=""),
    )

    assert result.route == "rag"
    assert result.task == "room_search"
    assert result.hard_filters["max_rent"] == 3000
    assert result.retrieval_queries == ["珠江新城 3000以内 有阳台 房源"]


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        UnderstandingResult(
            raw_message="x",
            route="rag",
            task="kb_qa",
            domain="policy",
            action="ask_policy",
            confidence=1.2,
        )
```

- [ ] **Step 2: Run the test and confirm failure**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/domain/test_understanding_contract.py -q
```

Expected: fails because `aptguide3.domain.understanding` does not exist.

- [ ] **Step 3: Implement the contract**

Create `backend/src/aptguide3/domain/understanding.py`:

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RouteName = Literal["rag", "appointment", "lease", "handoff", "memory", "capability", "clarify", "fallback"]
TaskName = Literal["room_search", "kb_qa", "appointment", "lease", "handoff", "memory", "capability", "clarify", "fallback"]
DomainName = Literal["room", "payment", "lease", "life", "appointment", "account", "policy", "memory", "handoff", "capability", "unknown"]
ActionName = Literal[
    "search",
    "ask_policy",
    "query_status",
    "create",
    "cancel",
    "list",
    "confirm",
    "deny",
    "update_preference",
    "delete_preference",
    "request_handoff",
    "ask_capability",
    "ask_clarification",
    "unknown",
]
RiskLevel = Literal["low", "medium", "high"]
ResponseMode = Literal[
    "normal_answer",
    "kb_grounded_answer",
    "authenticated_tool_query",
    "template_answer",
    "handoff_to_human",
    "refuse",
    "ask_clarification",
]


class RiskDecision(BaseModel):
    level: RiskLevel = "low"
    response_mode: ResponseMode = "normal_answer"
    reason: str = ""


class Clarification(BaseModel):
    needed: bool = False
    question: str = ""


class UnderstandingResult(BaseModel):
    raw_message: str
    route: RouteName
    task: TaskName
    domain: DomainName = "unknown"
    action: ActionName = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    hard_filters: dict[str, Any] = Field(default_factory=dict)
    soft_preferences: list[str] = Field(default_factory=list)
    retrieval_queries: list[str] = Field(default_factory=list)
    risk: RiskDecision = Field(default_factory=RiskDecision)
    clarification: Clarification = Field(default_factory=Clarification)
    reason: str = ""
```

- [ ] **Step 4: Run the test**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/domain/test_understanding_contract.py -q
```

Expected: passes.

---

## Task 2: Contract Validation And Clarification Conversion

**Files:**
- Create: `backend/src/aptguide3/understanding/validation.py`
- Test: `backend/tests/unit/understanding/test_validation.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/understanding/test_validation.py`:

```python
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.understanding.validation import validate_or_clarify


def test_low_confidence_becomes_clarification():
    result = UnderstandingResult(
        raw_message="这个可以吗",
        route="rag",
        task="kb_qa",
        domain="policy",
        action="ask_policy",
        confidence=0.2,
    )

    validated = validate_or_clarify(result, min_confidence=0.65)

    assert validated.route == "clarify"
    assert validated.task == "clarify"
    assert validated.action == "ask_clarification"
    assert validated.clarification.needed is True


def test_invalid_rag_task_shape_becomes_clarification():
    result = UnderstandingResult(
        raw_message="有阳台的房间吗",
        route="rag",
        task="fallback",
        domain="room",
        action="search",
        confidence=0.9,
    )

    validated = validate_or_clarify(result, min_confidence=0.65)

    assert validated.route == "clarify"
    assert validated.task == "clarify"


def test_invalid_hard_filter_type_becomes_clarification():
    result = UnderstandingResult(
        raw_message="3000以内",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
        hard_filters={"max_rent": "三千"},
    )

    validated = validate_or_clarify(result, min_confidence=0.65)

    assert validated.route == "clarify"
    assert validated.clarification.needed is True


def test_valid_understanding_passes_through():
    result = UnderstandingResult(
        raw_message="3000以内有阳台的房间",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
        hard_filters={"max_rent": 3000},
        soft_preferences=["有阳台"],
        retrieval_queries=["3000以内 有阳台 房源"],
    )

    validated = validate_or_clarify(result, min_confidence=0.65)

    assert validated.route == "rag"
    assert validated.task == "room_search"
```

- [ ] **Step 2: Run the test and confirm failure**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/understanding/test_validation.py -q
```

Expected: fails because validation module does not exist.

- [ ] **Step 3: Implement validation**

Create `backend/src/aptguide3/understanding/validation.py`:

```python
from __future__ import annotations

from typing import Any

from aptguide3.domain.understanding import Clarification, RiskDecision, UnderstandingResult


ALLOWED_HARD_FILTER_KEYS = {
    "max_rent",
    "min_rent",
    "district_id",
    "district_name",
    "area_text",
    "payment_type",
    "room_type",
    "apartment_id",
}
ALLOWED_PAYMENT_TYPES = {"MONTHLY", "QUARTERLY", "SEMI_ANNUAL", "ANNUAL"}
ALLOWED_ROOM_TYPES = {"STUDIO", "ONE_BEDROOM", "TWO_BEDROOM", "SHARED", "WHOLE_RENT", "UNKNOWN"}


def validate_or_clarify(result: UnderstandingResult, min_confidence: float) -> UnderstandingResult:
    if result.confidence < min_confidence:
        return clarification_result(result.raw_message, "low_confidence")
    if result.clarification.needed or result.risk.response_mode == "ask_clarification":
        return clarification_result(result.raw_message, result.reason or "model_requested_clarification", result.clarification.question)
    if not _shape_is_valid(result):
        return clarification_result(result.raw_message, "invalid_route_task_shape")
    if not _hard_filters_are_valid(result.hard_filters):
        return clarification_result(result.raw_message, "invalid_hard_filters")
    return result


def clarification_result(raw_message: str, reason: str, question: str = "") -> UnderstandingResult:
    return UnderstandingResult(
        raw_message=raw_message,
        route="clarify",
        task="clarify",
        domain="unknown",
        action="ask_clarification",
        confidence=0.0,
        risk=RiskDecision(level="low", response_mode="ask_clarification"),
        clarification=Clarification(
            needed=True,
            question=question or "请补充一下：您是想找房、咨询租房规则，还是处理预约/租约相关事项？",
        ),
        reason=reason,
    )


def _shape_is_valid(result: UnderstandingResult) -> bool:
    if result.route == "rag":
        return result.task in {"room_search", "kb_qa"}
    if result.route == "clarify":
        return result.task == "clarify" and result.action == "ask_clarification"
    if result.route == "fallback":
        return result.task == "fallback"
    return result.task == result.route


def _hard_filters_are_valid(filters: dict[str, Any]) -> bool:
    for key, value in filters.items():
        if key not in ALLOWED_HARD_FILTER_KEYS:
            return False
        if key in {"max_rent", "min_rent", "district_id", "apartment_id"}:
            if value is not None and not isinstance(value, int):
                return False
        if key in {"district_name", "area_text"}:
            if value is not None and not isinstance(value, str):
                return False
        if key == "payment_type" and value is not None and value not in ALLOWED_PAYMENT_TYPES:
            return False
        if key == "room_type" and value is not None and value not in ALLOWED_ROOM_TYPES:
            return False
    return True
```

- [ ] **Step 4: Run validation tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/understanding/test_validation.py -q
```

Expected: passes.

---

## Task 3: LLM Understanding Adapter

**Files:**
- Create: `backend/src/aptguide3/understanding/prompts.py`
- Create: `backend/src/aptguide3/understanding/llm_understanding.py`
- Test: `backend/tests/unit/understanding/test_llm_understanding.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/understanding/test_llm_understanding.py`:

```python
from aptguide3.understanding.llm_understanding import LLMUnderstanding


class FakeMessage:
    def __init__(self, content: str):
        self.content = content


class FakeChoice:
    def __init__(self, content: str):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content: str):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, content: str | None = None, error: Exception | None = None):
        self.content = content
        self.error = error

    def create(self, **kwargs):
        if self.error is not None:
            raise self.error
        return FakeResponse(self.content or "{}")


class FakeChat:
    def __init__(self, completions: FakeCompletions):
        self.completions = completions


class FakeClient:
    def __init__(self, content: str | None = None, error: Exception | None = None):
        self.chat = FakeChat(FakeCompletions(content=content, error=error))


def test_llm_understanding_returns_valid_model_output():
    content = """
    {
      "raw_message": "有阳台的房间吗",
      "route": "rag",
      "task": "room_search",
      "domain": "room",
      "action": "search",
      "confidence": 0.92,
      "hard_filters": {},
      "soft_preferences": ["有阳台"],
      "retrieval_queries": ["有阳台 房源"],
      "risk": {"level": "low", "response_mode": "normal_answer"},
      "clarification": {"needed": false, "question": ""},
      "reason": "User wants room search."
    }
    """

    understanding = LLMUnderstanding(FakeClient(content=content), model="fake-model", min_confidence=0.65)

    result = understanding.understand("有阳台的房间吗")

    assert result.route == "rag"
    assert result.task == "room_search"
    assert result.soft_preferences == ["有阳台"]


def test_llm_understanding_error_returns_clarification():
    understanding = LLMUnderstanding(FakeClient(error=RuntimeError("timeout")), model="fake-model", min_confidence=0.65)

    result = understanding.understand("有阳台的房间吗")

    assert result.route == "clarify"
    assert result.task == "clarify"
    assert result.clarification.needed is True


def test_llm_understanding_invalid_json_returns_clarification():
    understanding = LLMUnderstanding(FakeClient(content="not json"), model="fake-model", min_confidence=0.65)

    result = understanding.understand("有阳台的房间吗")

    assert result.route == "clarify"
```

- [ ] **Step 2: Run the test and confirm failure**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/understanding/test_llm_understanding.py -q
```

Expected: fails because adapter does not exist.

- [ ] **Step 3: Create the prompt**

Create `backend/src/aptguide3/understanding/prompts.py`:

```python
UNDERSTANDING_SYSTEM_PROMPT = """You are AptGuide 3.0's only natural-language understanding layer.

Return only one JSON object matching the UnderstandingResult schema.
Do not answer the user.
Do not use markdown.
Do not invent room availability, prices, lease records, appointment records, or business decisions.

Fields:
- raw_message: the original user message
- route: rag | appointment | lease | handoff | memory | capability | clarify | fallback
- task: room_search | kb_qa | appointment | lease | handoff | memory | capability | clarify | fallback
- domain: room | payment | lease | life | appointment | account | policy | memory | handoff | capability | unknown
- action: search | ask_policy | query_status | create | cancel | list | confirm | deny | update_preference | delete_preference | request_handoff | ask_capability | ask_clarification | unknown
- confidence: 0.0 to 1.0
- hard_filters: normalized filters such as max_rent, min_rent, district_id, district_name, area_text, payment_type, room_type, apartment_id
- soft_preferences: normalized Chinese preference phrases
- retrieval_queries: 1 to 4 short Chinese retrieval queries when route=rag
- risk: {level, response_mode, reason}
- clarification: {needed, question}
- reason: short explanation

Rules:
- Room search uses route=rag and task=room_search.
- Rental policy or process questions use route=rag and task=kb_qa.
- Appointment, lease, memory, handoff, and capability intents use their matching route and task.
- If ambiguous, do not guess. Use route=clarify, task=clarify, action=ask_clarification, confidence below 0.65.
- If route is rag, task must be room_search or kb_qa.
- If route is not rag, task must match the route except clarify/fallback.
- payment_type values: MONTHLY, QUARTERLY, SEMI_ANNUAL, ANNUAL.
- room_type values: STUDIO, ONE_BEDROOM, TWO_BEDROOM, SHARED, WHOLE_RENT, UNKNOWN.
"""
```

- [ ] **Step 4: Implement the adapter**

Create `backend/src/aptguide3/understanding/llm_understanding.py`:

```python
from __future__ import annotations

from pydantic import ValidationError

from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.understanding.prompts import UNDERSTANDING_SYSTEM_PROMPT
from aptguide3.understanding.validation import clarification_result, validate_or_clarify


class LLMUnderstanding:
    def __init__(self, client, model: str, min_confidence: float = 0.65) -> None:
        self.client = client
        self.model = model
        self.min_confidence = min_confidence

    def understand(self, message: str) -> UnderstandingResult:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": UNDERSTANDING_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content or "{}"
            result = UnderstandingResult.model_validate_json(content)
        except (ValidationError, Exception) as exc:
            return clarification_result(message, f"llm_understanding_failed:{exc.__class__.__name__}")

        if not result.raw_message:
            result = result.model_copy(update={"raw_message": message})
        return validate_or_clarify(result, self.min_confidence)
```

- [ ] **Step 5: Run adapter tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/understanding/test_llm_understanding.py -q
```

Expected: passes.

---

## Task 4: Domain Runtime Contracts

**Files:**
- Create: `backend/src/aptguide3/domain/conversation.py`
- Create: `backend/src/aptguide3/domain/procedures.py`
- Create: `backend/src/aptguide3/domain/responses.py`
- Test: `backend/tests/unit/domain/test_runtime_contracts.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/domain/test_runtime_contracts.py`:

```python
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.responses import ChatResponse


def test_conversation_frame_defaults():
    frame = ConversationFrame(message="你好", session_id="s-1")

    assert frame.message == "你好"
    assert frame.session_id == "s-1"
    assert frame.user_id is None
    assert frame.pending_action is None


def test_procedure_result_composes_chat_response_shape():
    result = ProcedureResult(
        message="请补充一下您的需求。",
        phase="clarify",
        metadata={"route": "clarify"},
    )
    response = ChatResponse.from_procedure_result(result)

    assert response.message == "请补充一下您的需求。"
    assert response.phase == "clarify"
    assert response.metadata["route"] == "clarify"
```

- [ ] **Step 2: Implement contracts**

Create `backend/src/aptguide3/domain/conversation.py`:

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ConversationFrame(BaseModel):
    message: str
    session_id: str
    user_id: str | None = None
    action: dict[str, Any] | None = None
    client_context: dict[str, Any] = Field(default_factory=dict)
    pending_action: dict[str, Any] | None = None
```

Create `backend/src/aptguide3/domain/procedures.py`:

```python
from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult


class ProcedureResult(BaseModel):
    message: str
    phase: str
    cards: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Procedure(Protocol):
    name: str

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        ...
```

Create `backend/src/aptguide3/domain/responses.py`:

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from aptguide3.domain.procedures import ProcedureResult


class ChatResponse(BaseModel):
    message: str
    phase: str
    cards: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_procedure_result(cls, result: ProcedureResult) -> "ChatResponse":
        return cls(
            message=result.message,
            phase=result.phase,
            cards=result.cards,
            actions=result.actions,
            pending_action=result.pending_action,
            metadata=result.metadata,
        )
```

- [ ] **Step 3: Run tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/domain/test_runtime_contracts.py -q
```

Expected: passes.

---

## Task 5: Safety Boundary

**Files:**
- Create: `backend/src/aptguide3/domain/safety.py`
- Create: `backend/src/aptguide3/application/safety_boundary.py`
- Test: `backend/tests/unit/application/test_safety_boundary.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/application/test_safety_boundary.py`:

```python
from aptguide3.application.safety_boundary import SafetyBoundary


def test_privacy_request_is_blocked_before_llm():
    decision = SafetyBoundary().check("查一下室友手机号")

    assert decision.blocked is True
    assert decision.reason == "privacy"


def test_normal_room_search_is_not_blocked():
    decision = SafetyBoundary().check("有阳台的房间吗")

    assert decision.blocked is False
```

- [ ] **Step 2: Implement safety contracts**

Create `backend/src/aptguide3/domain/safety.py`:

```python
from pydantic import BaseModel


class SafetyDecision(BaseModel):
    blocked: bool = False
    reason: str = ""
    message: str = ""
```

Create `backend/src/aptguide3/application/safety_boundary.py`:

```python
from __future__ import annotations

from aptguide3.domain.safety import SafetyDecision


class SafetyBoundary:
    def check(self, message: str) -> SafetyDecision:
        privacy_terms = ("室友手机号", "别人手机号", "其他租户电话", "身份证")
        if any(term in message for term in privacy_terms):
            return SafetyDecision(
                blocked=True,
                reason="privacy",
                message="抱歉，我不能查询或透露他人隐私信息。",
            )
        return SafetyDecision()
```

This is allowed because safety hard boundaries are deterministic red lines, not natural-language route/task/filter inference.

- [ ] **Step 3: Run tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/application/test_safety_boundary.py -q
```

Expected: passes.

---

## Task 6: Procedures And Runtime

**Files:**
- Create: `backend/src/aptguide3/application/procedure_runtime.py`
- Create: `backend/src/aptguide3/procedures/clarify.py`
- Create: `backend/src/aptguide3/procedures/room_search.py`
- Create: `backend/src/aptguide3/procedures/kb_qa.py`
- Test: `backend/tests/unit/application/test_procedure_runtime.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/application/test_procedure_runtime.py`:

```python
import pytest

from aptguide3.application.procedure_runtime import ProcedureNotFoundError, ProcedureRuntime
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.procedures.clarify import ClarifyProcedure
from aptguide3.procedures.kb_qa import KbQaProcedure
from aptguide3.procedures.room_search import RoomSearchProcedure


def test_runtime_dispatches_clarify():
    runtime = ProcedureRuntime()
    runtime.register(ClarifyProcedure())
    frame = ConversationFrame(message="这个可以吗", session_id="s-1")
    understanding = UnderstandingResult(
        raw_message="这个可以吗",
        route="clarify",
        task="clarify",
        action="ask_clarification",
        confidence=0.0,
    )

    result = runtime.run(frame, understanding)

    assert result.phase == "clarify"


def test_runtime_dispatches_room_search_placeholder():
    runtime = ProcedureRuntime()
    runtime.register(RoomSearchProcedure())
    frame = ConversationFrame(message="有阳台的房间吗", session_id="s-1")
    understanding = UnderstandingResult(
        raw_message="有阳台的房间吗",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
    )

    result = runtime.run(frame, understanding)

    assert result.phase == "room_search"


def test_runtime_dispatches_kb_qa_placeholder():
    runtime = ProcedureRuntime()
    runtime.register(KbQaProcedure())
    frame = ConversationFrame(message="照片是真的吗", session_id="s-1")
    understanding = UnderstandingResult(
        raw_message="照片是真的吗",
        route="rag",
        task="kb_qa",
        domain="policy",
        action="ask_policy",
        confidence=0.9,
    )

    result = runtime.run(frame, understanding)

    assert result.phase == "kb_qa"


def test_missing_procedure_raises():
    runtime = ProcedureRuntime()
    frame = ConversationFrame(message="x", session_id="s")
    understanding = UnderstandingResult(raw_message="x", route="rag", task="room_search", confidence=0.9)

    with pytest.raises(ProcedureNotFoundError):
        runtime.run(frame, understanding)
```

- [ ] **Step 2: Implement runtime and procedures**

Create `backend/src/aptguide3/application/procedure_runtime.py`:

```python
from __future__ import annotations

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import Procedure, ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class ProcedureNotFoundError(Exception):
    pass


class ProcedureRuntime:
    def __init__(self) -> None:
        self._procedures: dict[str, Procedure] = {}

    def register(self, procedure: Procedure) -> None:
        self._procedures[procedure.name] = procedure

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        name = self._procedure_name(understanding)
        procedure = self._procedures.get(name)
        if procedure is None:
            raise ProcedureNotFoundError(name)
        return procedure.run(frame, understanding)

    def _procedure_name(self, understanding: UnderstandingResult) -> str:
        if understanding.route == "clarify":
            return "clarify"
        if understanding.route == "rag":
            return understanding.task
        return understanding.route
```

Create `backend/src/aptguide3/procedures/clarify.py`:

```python
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class ClarifyProcedure:
    name = "clarify"

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        question = understanding.clarification.question or "请补充一下您的需求。"
        return ProcedureResult(
            message=question,
            phase="clarify",
            metadata={"route": understanding.route, "task": understanding.task, "reason": understanding.reason},
        )
```

Create `backend/src/aptguide3/procedures/room_search.py`:

```python
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class RoomSearchProcedure:
    name = "room_search"

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        return ProcedureResult(
            message="已理解您的找房需求。房源检索将在接入 lease 和 vector 后返回可验证结果。",
            phase="room_search",
            metadata={
                "route": understanding.route,
                "task": understanding.task,
                "hard_filters": understanding.hard_filters,
                "soft_preferences": understanding.soft_preferences,
            },
        )
```

Create `backend/src/aptguide3/procedures/kb_qa.py`:

```python
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class KbQaProcedure:
    name = "kb_qa"

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        return ProcedureResult(
            message="已理解您的租房规则问题。知识库检索将在接入 retrieval 后返回带来源的回答。",
            phase="kb_qa",
            metadata={"route": understanding.route, "task": understanding.task, "domain": understanding.domain},
        )
```

- [ ] **Step 3: Run runtime tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/application/test_procedure_runtime.py -q
```

Expected: passes.

---

## Task 7: Chat Service Orchestration

**Files:**
- Create: `backend/src/aptguide3/application/response_composer.py`
- Create: `backend/src/aptguide3/application/chat_service.py`
- Test: `backend/tests/unit/application/test_chat_service.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/application/test_chat_service.py`:

```python
from aptguide3.application.chat_service import ChatService
from aptguide3.application.procedure_runtime import ProcedureRuntime
from aptguide3.application.safety_boundary import SafetyBoundary
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import Clarification, UnderstandingResult
from aptguide3.procedures.clarify import ClarifyProcedure
from aptguide3.procedures.room_search import RoomSearchProcedure


class StubUnderstanding:
    def __init__(self, result: UnderstandingResult):
        self.result = result
        self.calls = 0

    def understand(self, message: str) -> UnderstandingResult:
        self.calls += 1
        return self.result


def build_runtime() -> ProcedureRuntime:
    runtime = ProcedureRuntime()
    runtime.register(ClarifyProcedure())
    runtime.register(RoomSearchProcedure())
    return runtime


def test_chat_service_blocks_privacy_before_llm():
    understanding = StubUnderstanding(
        UnderstandingResult(raw_message="", route="clarify", task="clarify", action="ask_clarification", confidence=0.0)
    )
    service = ChatService(SafetyBoundary(), understanding, build_runtime())

    response = service.run(ConversationFrame(message="查一下室友手机号", session_id="s-1"))

    assert response.phase == "safety"
    assert understanding.calls == 0


def test_chat_service_routes_llm_room_search():
    understanding = StubUnderstanding(
        UnderstandingResult(
            raw_message="有阳台的房间吗",
            route="rag",
            task="room_search",
            domain="room",
            action="search",
            confidence=0.9,
            soft_preferences=["有阳台"],
        )
    )
    service = ChatService(SafetyBoundary(), understanding, build_runtime())

    response = service.run(ConversationFrame(message="有阳台的房间吗", session_id="s-1"))

    assert response.phase == "room_search"
    assert response.metadata["task"] == "room_search"


def test_chat_service_returns_clarification():
    understanding = StubUnderstanding(
        UnderstandingResult(
            raw_message="这个可以吗",
            route="clarify",
            task="clarify",
            action="ask_clarification",
            confidence=0.0,
            clarification=Clarification(needed=True, question="您是想找房还是咨询规则？"),
        )
    )
    service = ChatService(SafetyBoundary(), understanding, build_runtime())

    response = service.run(ConversationFrame(message="这个可以吗", session_id="s-1"))

    assert response.phase == "clarify"
    assert response.message == "您是想找房还是咨询规则？"
```

- [ ] **Step 2: Implement composer and service**

Create `backend/src/aptguide3/application/response_composer.py`:

```python
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.responses import ChatResponse


class ResponseComposer:
    def compose(self, result: ProcedureResult) -> ChatResponse:
        return ChatResponse.from_procedure_result(result)
```

Create `backend/src/aptguide3/application/chat_service.py`:

```python
from __future__ import annotations

from aptguide3.application.procedure_runtime import ProcedureRuntime
from aptguide3.application.response_composer import ResponseComposer
from aptguide3.application.safety_boundary import SafetyBoundary
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.responses import ChatResponse


class ChatService:
    def __init__(self, safety: SafetyBoundary, understanding, runtime: ProcedureRuntime) -> None:
        self.safety = safety
        self.understanding = understanding
        self.runtime = runtime
        self.composer = ResponseComposer()

    def run(self, frame: ConversationFrame) -> ChatResponse:
        safety_decision = self.safety.check(frame.message)
        if safety_decision.blocked:
            return self.composer.compose(
                ProcedureResult(
                    message=safety_decision.message,
                    phase="safety",
                    metadata={"reason": safety_decision.reason},
                )
            )

        understanding = self.understanding.understand(frame.message)
        result = self.runtime.run(frame, understanding)
        return self.composer.compose(result)
```

- [ ] **Step 3: Run service tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/application/test_chat_service.py -q
```

Expected: passes.

---

## Task 8: FastAPI API

**Files:**
- Create: `backend/src/aptguide3/config.py`
- Create: `backend/src/aptguide3/api/schemas.py`
- Create: `backend/src/aptguide3/api/deps.py`
- Create: `backend/src/aptguide3/api/app.py`
- Test: `backend/tests/e2e/test_api.py`

- [ ] **Step 1: Write failing API tests**

Create `backend/tests/e2e/test_api.py`:

```python
from fastapi.testclient import TestClient

from aptguide3.api.app import create_app


def test_health():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "aptguide3"


def test_chat_returns_typed_response():
    client = TestClient(create_app())

    response = client.post("/chat", json={"message": "这个可以吗", "session_id": "s-1"})

    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert "phase" in body
    assert "metadata" in body
```

- [ ] **Step 2: Implement config**

Create `backend/src/aptguide3/config.py`:

```python
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "local"
    service_name: str = "aptguide3"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = "gpt-4o-mini"
    understanding_min_confidence: float = 0.65

    model_config = {"env_prefix": "APTGUIDE3_", "env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 3: Implement API schemas**

Create `backend/src/aptguide3/api/schemas.py`:

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str | None = None
    action: dict[str, Any] | None = None
    client_context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    message: str
    phase: str
    cards: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

- [ ] **Step 4: Implement dependency wiring**

Create `backend/src/aptguide3/api/deps.py`:

```python
from functools import lru_cache

from openai import OpenAI

from aptguide3.application.chat_service import ChatService
from aptguide3.application.procedure_runtime import ProcedureRuntime
from aptguide3.application.safety_boundary import SafetyBoundary
from aptguide3.config import Settings, get_settings
from aptguide3.procedures.clarify import ClarifyProcedure
from aptguide3.procedures.kb_qa import KbQaProcedure
from aptguide3.procedures.room_search import RoomSearchProcedure
from aptguide3.understanding.llm_understanding import LLMUnderstanding
from aptguide3.understanding.validation import clarification_result


class ClarifyOnlyUnderstanding:
    def understand(self, message: str):
        return clarification_result(message, "llm_not_configured")


def get_llm_client(settings: Settings):
    if not settings.llm_api_key.get_secret_value():
        return None
    return OpenAI(api_key=settings.llm_api_key.get_secret_value(), base_url=settings.llm_base_url)


def build_runtime() -> ProcedureRuntime:
    runtime = ProcedureRuntime()
    runtime.register(ClarifyProcedure())
    runtime.register(RoomSearchProcedure())
    runtime.register(KbQaProcedure())
    return runtime


@lru_cache
def get_chat_service() -> ChatService:
    settings = get_settings()
    client = get_llm_client(settings)
    understanding = (
        LLMUnderstanding(client, settings.llm_model, settings.understanding_min_confidence)
        if client is not None
        else ClarifyOnlyUnderstanding()
    )
    return ChatService(SafetyBoundary(), understanding, build_runtime())
```

- [ ] **Step 5: Implement FastAPI app**

Create `backend/src/aptguide3/api/app.py`:

```python
from fastapi import FastAPI

from aptguide3.api.deps import get_chat_service
from aptguide3.api.schemas import ChatRequest, ChatResponse
from aptguide3.config import get_settings
from aptguide3.domain.conversation import ConversationFrame


def create_app() -> FastAPI:
    app = FastAPI(title="AptGuide 3.0")

    @app.get("/health")
    def health():
        settings = get_settings()
        return {"service": settings.service_name, "status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest):
        frame = ConversationFrame(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id,
            action=request.action,
            client_context=request.client_context,
        )
        return get_chat_service().run(frame)

    return app


app = create_app()
```

- [ ] **Step 6: Run API tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/e2e/test_api.py -q
```

Expected: passes.

---

## Task 9: No Keyword Fallback Source Scan

**Files:**
- Create: `backend/tests/unit/test_no_keyword_fallback.py`

- [ ] **Step 1: Add the source scan**

Create `backend/tests/unit/test_no_keyword_fallback.py`:

```python
from pathlib import Path


SRC = Path(__file__).resolve().parents[2] / "src" / "aptguide3"


def test_understanding_runtime_has_no_keyword_fallback_patterns():
    files = [
        SRC / "understanding" / "llm_understanding.py",
        SRC / "understanding" / "validation.py",
        SRC / "application" / "chat_service.py",
    ]
    forbidden = [
        "any(term in message",
        " if \"",
        "_looks_like",
        "_detect_task",
        "_extract_budget",
        "_extract_district",
        "_extract_preferences",
        "regex",
    ]

    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            assert pattern not in text, f"{pattern} found in {path}"
```

- [ ] **Step 2: Run scan**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest tests/unit/test_no_keyword_fallback.py -q
```

Expected: passes. If it fails because a deterministic safety check is scanned, narrow the scan to understanding runtime files only; safety hard boundaries are allowed but must stay out of natural-language route/task/filter inference.

---

## Task 10: Full Verification

**Files:**
- Modify: `reports/evaluation-report.md`
- Modify: `progress/completed.md`
- Modify: `progress/current-plan.md`
- Modify: `progress/next-steps.md`

- [ ] **Step 1: Run all tests**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run ruff**

Run:

```bash
cd "AptGuide 3.0/backend"
uv run ruff check src tests
```

Expected: clean.

- [ ] **Step 3: Update evaluation report**

Update `reports/evaluation-report.md`:

```markdown
## 2026-05-15 - Clean Backend Foundation

- Unit/e2e tests: <exact result>
- Ruff: <exact result>
- No keyword fallback source scan: <exact result>
- Live LLM eval: not run
```

- [ ] **Step 4: Update progress files**

Update:

```text
progress/completed.md
progress/current-plan.md
progress/next-steps.md
```

Only mark runtime foundation complete if tests and ruff passed.

---

## Self-Review

- Spec coverage: The plan creates clean AptGuide 3.0 backend contracts, LLM-first understanding, clarification-on-uncertainty behavior, procedure runtime, API endpoints, and anti-regression source scan.
- Placeholder scan: No task uses placeholder implementation instructions; every code-writing step includes concrete code.
- Type consistency: `UnderstandingResult`, `ConversationFrame`, `ProcedureResult`, and `ChatResponse` are introduced before later tasks consume them.
- Boundary check: Deterministic safety is allowed only as hard red-line handling; it does not route room/KB/appointment intent or extract filters/preferences.
