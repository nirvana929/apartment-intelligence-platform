# LLM-First Interaction Understanding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace keyword-driven intent classification and query understanding with an LLM-first structured understanding layer; if the LLM is uncertain or invalid, ask the user to clarify instead of falling back to keyword matching.

**Architecture:** The LLM becomes the only natural-language understanding entrypoint for route, RAG task, domain, action, filters, preferences, risk posture, and retrieval queries. Python code keeps deterministic hard boundaries only: safety refusal, pending-action routing, schema/contract validation, permission checks, tool confirmation, and lease validation. Keyword-based `in` matching must not decide route, task, filters, preferences, or KB module intent.

**Tech Stack:** Python 3.12, Pydantic, OpenAI-compatible chat completions, pytest, uv, AptGuide 2.0 harness/RAG v2.

---

## Current Problem

The current `HeuristicInteractionClassifier` and `understand_query()` contain broad keyword lists. Those lists decide whether a message is `kb_qa`, `room_search`, `appointment`, `lease`, `memory`, or `fallback`. This creates biased misrouting: `吗` pushes room queries into KB, `房间/空调/宠物` oscillate between room and policy, and eval-driven keyword expansion makes the system memorize cases instead of understanding user intent.

The replacement rule is:

```text
LLM success + confidence >= threshold + contract valid -> execute route
LLM failure / invalid JSON / low confidence / contradictory intent -> fallback.clarify
No keyword classifier fallback.
No keyword query extraction fallback.
```

## Files And Responsibilities

- Modify `backend/src/aptguide2/interaction/contracts.py`
  - Extend `InteractionIntent` with `retrieval_queries` and `clarification_needed`.
  - Keep Pydantic enum validation as the contract boundary.

- Create `backend/src/aptguide2/interaction/validation.py`
  - Validate LLM output contract without reading the user message.
  - Enforce allowed hard filter keys, basic value types, confidence threshold, and route/task coherence.
  - Convert invalid or low-confidence output into a clarification intent.

- Modify `backend/src/aptguide2/interaction/prompts.py`
  - Replace the short prompt with a stricter schema-oriented prompt.
  - Instruct the model to do intent classification, extraction, normalization, risk posture, and retrieval query generation.
  - Instruct the model to return `fallback` + `clarify` when uncertain.
  - Explicitly forbid inventing business facts or room availability.

- Modify `backend/src/aptguide2/interaction/classifier.py`
  - Remove keyword route/query helpers from the production path.
  - Make `LLMInteractionClassifier` return clarification on exceptions, invalid JSON, low confidence, or validation failure.
  - Replace `HeuristicInteractionClassifier` with a no-keyword `ClarifyingInteractionClassifier` or keep the name as a compatibility alias that only returns clarification.

- Modify `backend/src/aptguide2/core/config.py`
  - Change default `intent_classifier_mode` to `llm`.
  - Keep `intent_classifier_min_confidence` as the validation threshold.

- Modify `backend/src/aptguide2/api/deps.py`
  - Build the default classifier as `LLMInteractionClassifier(..., min_confidence=settings.intent_classifier_min_confidence)`.
  - Do not pass a heuristic keyword fallback.

- Modify `backend/src/aptguide2/rag/query_understanding.py`
  - Require `interaction_intent` for RAG v2.
  - Build `QueryUnderstandingResult` from the LLM intent only.
  - Remove or bypass `_detect_task`, `_extract_budget`, `_extract_district`, `_extract_payment`, `_extract_preferences`, `_extract_reference`, and `_generate_retrieval_queries` for runtime.

- Modify `backend/src/aptguide2/rag/planning.py`
  - Stop inferring KB module intent from raw message keywords.
  - Use `qr.domain` after adding it to `QueryUnderstandingResult`, or map from `InteractionIntent.domain`.

- Modify `backend/src/aptguide2/rag/schemas.py`
  - Add `domain` to `QueryUnderstandingResult` so retrieval planning can use LLM-provided domain without keyword inference.

- Modify tests under `backend/tests/unit/interaction/`, `backend/tests/unit/rag/`, `backend/tests/unit/harness/`, and `backend/tests/unit/evals/`
  - Replace heuristic keyword expectations with fake LLM client outputs.
  - Add regression tests proving failure and low confidence produce clarification, not keyword fallback.

---

## Task 1: Extend The Interaction Contract

**Files:**
- Modify: `backend/src/aptguide2/interaction/contracts.py`
- Test: `backend/tests/unit/interaction/test_contracts.py`

- [ ] **Step 1: Add failing contract tests**

Append these tests to `backend/tests/unit/interaction/test_contracts.py`:

```python
from pydantic import ValidationError

from aptguide2.interaction.contracts import InteractionIntent


def test_interaction_intent_supports_llm_retrieval_queries_and_clarification_flag():
    intent = InteractionIntent(
        raw_message="越秀区3000以内有阳台的房间",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        confidence=0.91,
        hard_filters={"district_id": 2, "area_text": "越秀", "max_rent": 3000},
        soft_preferences=["有阳台"],
        retrieval_queries=["越秀 3000以内 有阳台 房源"],
        clarification_needed=False,
    )

    assert intent.retrieval_queries == ["越秀 3000以内 有阳台 房源"]
    assert intent.clarification_needed is False


def test_interaction_intent_rejects_invalid_confidence():
    try:
        InteractionIntent(raw_message="x", confidence=1.2)
    except ValidationError:
        return

    raise AssertionError("confidence above 1.0 must fail Pydantic validation")
```

- [ ] **Step 2: Run the focused test and confirm failure**

Run:

```bash
cd backend
uv run pytest tests/unit/interaction/test_contracts.py -q
```

Expected: failure because `retrieval_queries` and `clarification_needed` do not exist yet.

- [ ] **Step 3: Extend `InteractionIntent`**

In `backend/src/aptguide2/interaction/contracts.py`, add these fields to `InteractionIntent`:

```python
    retrieval_queries: list[str] = Field(default_factory=list)
    clarification_needed: bool = False
```

- [ ] **Step 4: Re-run the focused test**

Run:

```bash
cd backend
uv run pytest tests/unit/interaction/test_contracts.py -q
```

Expected: pass.

---

## Task 2: Add Contract Validation With Clarification Instead Of Keyword Fallback

**Files:**
- Create: `backend/src/aptguide2/interaction/validation.py`
- Test: `backend/tests/unit/interaction/test_validation.py`

- [ ] **Step 1: Write failing validation tests**

Create `backend/tests/unit/interaction/test_validation.py`:

```python
from aptguide2.interaction.contracts import InteractionIntent
from aptguide2.interaction.validation import validate_or_clarify_intent


def test_low_confidence_intent_becomes_clarification():
    intent = InteractionIntent(
        raw_message="这个可以吗",
        route="rag",
        rag_task="kb_qa",
        domain="policy",
        action="ask_policy",
        confidence=0.31,
    )

    result = validate_or_clarify_intent(intent, min_confidence=0.65)

    assert result.route == "fallback"
    assert result.action == "clarify"
    assert result.response_mode == "ask_clarification"
    assert result.clarification_needed is True
    assert "请补充" in result.clarification_question


def test_contradictory_rag_intent_becomes_clarification():
    intent = InteractionIntent(
        raw_message="有阳台的房间吗",
        route="rag",
        rag_task="none",
        domain="room",
        action="search",
        confidence=0.9,
    )

    result = validate_or_clarify_intent(intent, min_confidence=0.65)

    assert result.route == "fallback"
    assert result.action == "clarify"
    assert result.response_mode == "ask_clarification"


def test_valid_room_intent_passes_through_without_keyword_inference():
    intent = InteractionIntent(
        raw_message="有阳台的房间吗",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        confidence=0.92,
        needs_room_search=True,
        hard_filters={"max_rent": 3000, "district_id": 1, "area_text": "珠江新城"},
        soft_preferences=["有阳台"],
        retrieval_queries=["珠江新城 3000以内 有阳台 房源"],
    )

    result = validate_or_clarify_intent(intent, min_confidence=0.65)

    assert result.route == "rag"
    assert result.rag_task == "room_search"
    assert result.hard_filters["max_rent"] == 3000
    assert result.retrieval_queries == ["珠江新城 3000以内 有阳台 房源"]


def test_invalid_filter_type_becomes_clarification():
    intent = InteractionIntent(
        raw_message="珠江新城3000以内",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
        hard_filters={"max_rent": "三千以内"},
    )

    result = validate_or_clarify_intent(intent, min_confidence=0.65)

    assert result.route == "fallback"
    assert result.action == "clarify"
```

- [ ] **Step 2: Run the focused test and confirm failure**

Run:

```bash
cd backend
uv run pytest tests/unit/interaction/test_validation.py -q
```

Expected: import failure because `interaction.validation` does not exist.

- [ ] **Step 3: Implement validation**

Create `backend/src/aptguide2/interaction/validation.py`:

```python
from __future__ import annotations

from typing import Any

from aptguide2.interaction.contracts import InteractionIntent


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


def validate_or_clarify_intent(intent: InteractionIntent, min_confidence: float) -> InteractionIntent:
    if intent.confidence < min_confidence:
        return build_clarification_intent(intent.raw_message, "low_confidence")

    if intent.clarification_needed or intent.response_mode == "ask_clarification" or intent.action == "clarify":
        return build_clarification_intent(
            intent.raw_message,
            intent.reason or "model_requested_clarification",
            question=intent.clarification_question,
        )

    if not _route_shape_is_valid(intent):
        return build_clarification_intent(intent.raw_message, "invalid_route_shape")

    if not _hard_filters_are_valid(intent.hard_filters):
        return build_clarification_intent(intent.raw_message, "invalid_hard_filters")

    return intent


def build_clarification_intent(raw_message: str, reason: str, question: str = "") -> InteractionIntent:
    return InteractionIntent(
        raw_message=raw_message,
        route="fallback",
        rag_task="none",
        domain="unknown",
        action="clarify",
        confidence=0.0,
        response_mode="ask_clarification",
        clarification_needed=True,
        clarification_question=question or "请补充一下：您是想找房、咨询租房规则，还是处理预约/租约相关事项？",
        reason=reason,
    )


def _route_shape_is_valid(intent: InteractionIntent) -> bool:
    if intent.route == "rag":
        return intent.rag_task in {"kb_qa", "room_search"}
    if intent.route != "rag":
        return intent.rag_task == "none"
    return True


def _hard_filters_are_valid(filters: dict[str, Any]) -> bool:
    for key, value in filters.items():
        if key not in ALLOWED_HARD_FILTER_KEYS:
            return False
        if key in {"max_rent", "min_rent", "district_id", "apartment_id"}:
            if value is not None and not isinstance(value, int):
                return False
        if key == "payment_type" and value is not None and value not in ALLOWED_PAYMENT_TYPES:
            return False
        if key == "room_type" and value is not None and value not in ALLOWED_ROOM_TYPES:
            return False
        if key in {"district_name", "area_text"} and value is not None and not isinstance(value, str):
            return False
    return True
```

- [ ] **Step 4: Run validation tests**

Run:

```bash
cd backend
uv run pytest tests/unit/interaction/test_validation.py -q
```

Expected: pass.

---

## Task 3: Replace Keyword Fallback In The LLM Classifier

**Files:**
- Modify: `backend/src/aptguide2/interaction/classifier.py`
- Test: `backend/tests/unit/interaction/test_classifier.py`

- [ ] **Step 1: Replace classifier tests with LLM-first behavior**

Rewrite `backend/tests/unit/interaction/test_classifier.py`:

```python
from aptguide2.interaction.classifier import ClarifyingInteractionClassifier, LLMInteractionClassifier, apply_policy_corrections


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


def test_llm_classifier_uses_model_output_for_room_search():
    content = """
    {
      "raw_message": "有阳台的房间吗",
      "route": "rag",
      "rag_task": "room_search",
      "domain": "room",
      "action": "search",
      "needs_room_search": true,
      "hard_filters": {},
      "soft_preferences": ["有阳台"],
      "retrieval_queries": ["有阳台 房源"],
      "risk_level": "low",
      "response_mode": "normal_answer",
      "confidence": 0.92
    }
    """
    classifier = LLMInteractionClassifier(FakeClient(content=content), "fake-model", min_confidence=0.65)

    intent = classifier.classify("有阳台的房间吗")

    assert intent.route == "rag"
    assert intent.rag_task == "room_search"
    assert intent.soft_preferences == ["有阳台"]
    assert intent.retrieval_queries == ["有阳台 房源"]


def test_llm_classifier_failure_returns_clarification_not_keyword_guess():
    classifier = LLMInteractionClassifier(FakeClient(error=RuntimeError("timeout")), "fake-model", min_confidence=0.65)

    intent = classifier.classify("有阳台的房间吗")

    assert intent.route == "fallback"
    assert intent.action == "clarify"
    assert intent.response_mode == "ask_clarification"
    assert intent.clarification_needed is True


def test_llm_classifier_low_confidence_returns_clarification():
    content = """
    {
      "raw_message": "这个可以吗",
      "route": "rag",
      "rag_task": "kb_qa",
      "domain": "policy",
      "action": "ask_policy",
      "confidence": 0.3
    }
    """
    classifier = LLMInteractionClassifier(FakeClient(content=content), "fake-model", min_confidence=0.65)

    intent = classifier.classify("这个可以吗")

    assert intent.route == "fallback"
    assert intent.action == "clarify"


def test_clarifying_classifier_never_uses_keywords():
    intent = ClarifyingInteractionClassifier().classify("大学城附近1500以内安静房源")

    assert intent.route == "fallback"
    assert intent.action == "clarify"
    assert intent.response_mode == "ask_clarification"


def test_privacy_correction_still_refuses():
    intent = apply_policy_corrections(ClarifyingInteractionClassifier().classify("查一下室友手机号"))

    assert intent.route == "fallback"
    assert intent.risk_level == "high"
    assert intent.response_mode == "refuse"
```

- [ ] **Step 2: Run the focused test and confirm failure**

Run:

```bash
cd backend
uv run pytest tests/unit/interaction/test_classifier.py -q
```

Expected: import or assertion failures because the current classifier still uses keyword fallback.

- [ ] **Step 3: Refactor `classifier.py`**

Update imports:

```python
from aptguide2.interaction.validation import build_clarification_intent, validate_or_clarify_intent
```

Replace `HeuristicInteractionClassifier` with:

```python
class ClarifyingInteractionClassifier:
    def classify(self, message: str) -> InteractionIntent:
        return build_clarification_intent(message, "no_llm_available")


HeuristicInteractionClassifier = ClarifyingInteractionClassifier
```

Change `LLMInteractionClassifier.__init__`:

```python
class LLMInteractionClassifier:
    def __init__(self, client, model: str, min_confidence: float = 0.65) -> None:
        self.client = client
        self.model = model
        self.min_confidence = min_confidence
```

Change exception handling in `classify()`:

```python
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
        except Exception as exc:
            return apply_policy_corrections(build_clarification_intent(message, f"llm_intent_failed:{exc.__class__.__name__}"))

        if not intent.raw_message:
            intent = intent.model_copy(update={"raw_message": message})

        validated = validate_or_clarify_intent(normalize_entities(intent), self.min_confidence)
        return apply_policy_corrections(validated)
```

Delete these helpers from `classifier.py` after all tests are updated:

```python
_looks_like_room_search
_looks_like_kb_policy
_looks_like_policy_question
_infer_kb_domain
```

- [ ] **Step 4: Run classifier tests**

Run:

```bash
cd backend
uv run pytest tests/unit/interaction/test_classifier.py tests/unit/interaction/test_validation.py -q
```

Expected: pass.

---

## Task 4: Make LLM Mode The Default Dependency

**Files:**
- Modify: `backend/src/aptguide2/core/config.py`
- Modify: `backend/src/aptguide2/api/deps.py`
- Test: `backend/tests/unit/api/test_mainline_wiring.py`

- [ ] **Step 1: Add dependency wiring tests**

Append to `backend/tests/unit/api/test_mainline_wiring.py`:

```python
from aptguide2.interaction.classifier import LLMInteractionClassifier


def test_default_interaction_classifier_is_llm(monkeypatch):
    from aptguide2.api import deps
    from aptguide2.core.config import Settings

    deps.get_settings.cache_clear()

    monkeypatch.setattr(deps, "get_settings", lambda: Settings(llm_api_key="test-key"))
    classifier = deps.get_interaction_classifier()

    assert isinstance(classifier, LLMInteractionClassifier)
```

- [ ] **Step 2: Run the focused test and confirm failure**

Run:

```bash
cd backend
uv run pytest tests/unit/api/test_mainline_wiring.py::test_default_interaction_classifier_is_llm -q
```

Expected: failure if default remains heuristic.

- [ ] **Step 3: Update config default**

In `backend/src/aptguide2/core/config.py`, change:

```python
    intent_classifier_mode: str = "heuristic"  # heuristic | llm
```

to:

```python
    intent_classifier_mode: str = "llm"  # llm | clarify_only
```

- [ ] **Step 4: Update dependency construction**

In `backend/src/aptguide2/api/deps.py`, replace `get_interaction_classifier()` with:

```python
def get_interaction_classifier():
    settings = get_settings()
    if settings.intent_classifier_mode == "clarify_only":
        return HeuristicInteractionClassifier()
    return LLMInteractionClassifier(
        get_llm_client(),
        settings.llm_model,
        min_confidence=settings.intent_classifier_min_confidence,
    )
```

The `HeuristicInteractionClassifier` name is now a compatibility alias for the no-keyword clarifying classifier.

- [ ] **Step 5: Run focused wiring test**

Run:

```bash
cd backend
uv run pytest tests/unit/api/test_mainline_wiring.py::test_default_interaction_classifier_is_llm -q
```

Expected: pass.

---

## Task 5: Replace Query Understanding With Intent-Only Construction

**Files:**
- Modify: `backend/src/aptguide2/rag/schemas.py`
- Modify: `backend/src/aptguide2/rag/query_understanding.py`
- Test: `backend/tests/unit/rag/test_query_understanding.py`

- [ ] **Step 1: Add intent-only query understanding tests**

Append to `backend/tests/unit/rag/test_query_understanding.py`:

```python
from aptguide2.interaction.contracts import InteractionIntent
from aptguide2.rag.query_understanding import understand_query


def test_understand_query_requires_interaction_intent():
    result = understand_query("有阳台的房间吗", interaction_intent=None)

    assert result.task == "fallback"
    assert result.response_mode == "ask_clarification"


def test_understand_query_uses_llm_intent_filters_preferences_and_queries():
    intent = InteractionIntent(
        raw_message="珠江新城3000以内有阳台的房间",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        confidence=0.92,
        hard_filters={"district_id": 1, "area_text": "珠江新城", "max_rent": 3000},
        soft_preferences=["有阳台"],
        retrieval_queries=["珠江新城 3000以内 有阳台 房源"],
    )

    result = understand_query("珠江新城3000以内有阳台的房间", interaction_intent=intent)

    assert result.task == "room_search"
    assert result.domain == "room"
    assert result.hard_filters == {"district_id": 1, "area_text": "珠江新城", "max_rent": 3000}
    assert result.soft_preferences == ["有阳台"]
    assert result.retrieval_queries == ["珠江新城 3000以内 有阳台 房源"]


def test_understand_query_clarifies_non_rag_intent():
    intent = InteractionIntent(
        raw_message="查看我的合同",
        route="lease",
        rag_task="none",
        domain="lease",
        action="list",
        confidence=0.9,
    )

    result = understand_query("查看我的合同", interaction_intent=intent)

    assert result.task == "fallback"
    assert result.response_mode == "ask_clarification"
```

- [ ] **Step 2: Add `domain` to `QueryUnderstandingResult`**

In `backend/src/aptguide2/rag/schemas.py`, add:

```python
    domain: str = "unknown"
```

to `QueryUnderstandingResult`.

- [ ] **Step 3: Replace `understand_query()` runtime logic**

In `backend/src/aptguide2/rag/query_understanding.py`, make `understand_query()` intent-only:

```python
def understand_query(
    message: str,
    previous_state: dict[str, Any] | None = None,
    interaction_intent: InteractionIntent | None = None,
) -> QueryUnderstandingResult:
    if interaction_intent is None:
        return QueryUnderstandingResult(
            raw_message=message,
            task="fallback",
            domain="unknown",
            response_mode="ask_clarification",
        )

    if interaction_intent.route != "rag" or interaction_intent.rag_task == "none":
        return QueryUnderstandingResult(
            raw_message=message,
            task="fallback",
            domain=interaction_intent.domain,
            response_mode="ask_clarification",
        )

    return QueryUnderstandingResult(
        raw_message=message,
        task=interaction_intent.rag_task,
        domain=interaction_intent.domain,
        reference_resolution=interaction_intent.reference,
        hard_filters=dict(interaction_intent.hard_filters),
        soft_preferences=list(interaction_intent.soft_preferences),
        retrieval_queries=list(interaction_intent.retrieval_queries),
        risk_level=interaction_intent.risk_level,
        response_mode=interaction_intent.response_mode,
    )
```

After this change, remove runtime use of these keyword helpers:

```python
_detect_task
_extract_budget
_is_budget_clearing
_extract_district
_extract_payment
_extract_preferences
_extract_reference
_generate_retrieval_queries
```

They can be deleted in this task once tests that reference them are updated.

- [ ] **Step 4: Run focused query tests**

Run:

```bash
cd backend
uv run pytest tests/unit/rag/test_query_understanding.py -q
```

Expected: pass after updating older tests that expected keyword extraction.

---

## Task 6: Stop Retrieval Planning From Inferring KB Module By Keywords

**Files:**
- Modify: `backend/src/aptguide2/rag/planning.py`
- Test: `backend/tests/unit/rag/test_planning.py`

- [ ] **Step 1: Add planning test for LLM-provided domain**

Append to `backend/tests/unit/rag/test_planning.py`:

```python
from aptguide2.rag.planning import build_retrieval_plan
from aptguide2.rag.schemas import QueryUnderstandingResult


def test_kb_module_intent_uses_query_understanding_domain_not_message_keywords():
    qr = QueryUnderstandingResult(
        raw_message="这个可以吗",
        task="kb_qa",
        domain="payment",
        retrieval_queries=["支付规则 支持方式"],
    )

    plan = build_retrieval_plan(qr)

    assert plan.task == "kb_qa"
    assert plan.module_intent == "payment"
    assert "支付规则 支持方式" in plan.semantic_queries
```

- [ ] **Step 2: Run the focused test and confirm failure**

Run:

```bash
cd backend
uv run pytest tests/unit/rag/test_planning.py::test_kb_module_intent_uses_query_understanding_domain_not_message_keywords -q
```

Expected: failure because planning currently uses raw-message keyword inference.

- [ ] **Step 3: Replace module inference**

In `backend/src/aptguide2/rag/planning.py`, replace:

```python
    module_intent = _infer_kb_module_intent(qr.raw_message)
```

with:

```python
    module_intent = qr.domain if qr.domain in {"payment", "lease", "life", "appointment", "account", "policy"} else None
```

Remove `_infer_kb_module_intent()` and change `_build_kb_rewrite_queries()` to use only `qr.retrieval_queries` plus optional step-back:

```python
def _build_kb_rewrite_queries(qr: QueryUnderstandingResult, module_intent: str | None) -> list[str]:
    queries = list(qr.retrieval_queries)
    if qr.risk_level in ("medium", "high"):
        queries.append(_step_back_query(qr.raw_message, module_intent))
    return [q for q in queries if q]
```

Keep `_step_back_query()` for now because it is template generation based on an already-validated domain, not user-message keyword routing.

- [ ] **Step 4: Run planning tests**

Run:

```bash
cd backend
uv run pytest tests/unit/rag/test_planning.py -q
```

Expected: pass after updating any old tests that asserted keyword-based module inference.

---

## Task 7: Strengthen The LLM Prompt

**Files:**
- Modify: `backend/src/aptguide2/interaction/prompts.py`
- Test: `backend/tests/unit/interaction/test_classifier.py`

- [ ] **Step 1: Replace the prompt**

Update `INTERACTION_INTENT_SYSTEM_PROMPT`:

```python
INTERACTION_INTENT_SYSTEM_PROMPT = """You are the only natural-language understanding layer for AptGuide.

Return only one JSON object that matches the InteractionIntent schema.
Do not answer the user.
Do not use markdown.
Do not invent room availability, prices, lease records, appointment records, or business decisions.

Classify and extract in one pass:
- route: rag | appointment | lease | handoff | memory | capability | fallback
- rag_task: kb_qa | room_search | none
- domain: room | payment | lease | life | appointment | account | policy | memory | handoff | capability | unknown
- action: search | ask_policy | query_status | create | cancel | list | confirm | deny | update_preference | delete_preference | request_handoff | ask_capability | clarify | unknown
- confidence: 0.0 to 1.0
- hard_filters: normalized filters such as max_rent, min_rent, district_id, district_name, area_text, payment_type, room_type, apartment_id
- soft_preferences: user preferences as normalized Chinese phrases
- retrieval_queries: 1 to 4 short Chinese search queries for retrieval when route=rag
- risk_level: low | medium | high
- response_mode: normal_answer | kb_grounded_answer | authenticated_tool_query | template_answer | handoff_to_human | refuse | ask_clarification
- clarification_needed: true when intent is ambiguous or information is insufficient
- clarification_question: a short Chinese question when clarification_needed=true

Rules:
- If the user wants to find/list/recommend available rooms, use route=rag, rag_task=room_search, domain=room, action=search.
- If the user asks rental rules, fees, policies, procedures, photos, search rules, appointment rules, repair rules, account rules, or contract rules, use route=rag, rag_task=kb_qa.
- If the user requests a concrete appointment create/cancel/list flow, use route=appointment and rag_task=none.
- If the user asks for their own lease or contract records, use route=lease and rag_task=none.
- If the user asks for human service, use route=handoff and rag_task=none.
- If the user asks what the assistant can do, use route=capability and rag_task=none.
- If the message is ambiguous, do not guess. Use route=fallback, action=clarify, response_mode=ask_clarification, confidence below 0.65.
- If route is not rag, rag_task must be none.
- Use payment_type enum values MONTHLY, QUARTERLY, SEMI_ANNUAL, ANNUAL.
- Use room_type enum values STUDIO, ONE_BEDROOM, TWO_BEDROOM, SHARED, WHOLE_RENT, UNKNOWN.
"""
```

- [ ] **Step 2: Add prompt coverage assertion**

Append to `backend/tests/unit/interaction/test_classifier.py`:

```python
def test_prompt_forbids_guessing_when_ambiguous():
    from aptguide2.interaction.prompts import INTERACTION_INTENT_SYSTEM_PROMPT

    assert "do not guess" in INTERACTION_INTENT_SYSTEM_PROMPT.lower()
    assert "clarification_needed" in INTERACTION_INTENT_SYSTEM_PROMPT
    assert "retrieval_queries" in INTERACTION_INTENT_SYSTEM_PROMPT
```

- [ ] **Step 3: Run prompt-related test**

Run:

```bash
cd backend
uv run pytest tests/unit/interaction/test_classifier.py::test_prompt_forbids_guessing_when_ambiguous -q
```

Expected: pass.

---

## Task 8: Update Router And RAG Tests To Use Stub LLM Intents

**Files:**
- Modify: `backend/tests/unit/harness/test_routing.py`
- Modify: `backend/tests/unit/harness/modules/test_appointment.py`
- Modify: `backend/tests/unit/evals/test_run_interaction_intent_eval.py`
- Modify: `backend/tests/unit/evals/test_run_rag_v2.py`

- [ ] **Step 1: Update routing tests away from heuristic keyword assumptions**

Where tests currently instantiate `HybridRouter()` and rely on message keywords, change them to pass a stub classifier:

```python
class StubClassifier:
    def __init__(self, intent):
        self.intent = intent

    def classify(self, message: str):
        return self.intent.model_copy(update={"raw_message": message})
```

Example route test:

```python
router = HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
    raw_message="",
    route="rag",
    rag_task="room_search",
    domain="room",
    action="search",
    confidence=0.9,
)))
decision = router.route(ConversationFrame(session_id="s", user_id="u", message="有阳台的房间吗"))
assert decision.task == "room_search"
```

- [ ] **Step 2: Keep pending-action tests deterministic**

Pending-action tests should continue to use real `HybridRouter()` if they assert priority before classifier. If the classifier could be called, inject a `StubClassifier` returning clarification:

```python
StubClassifier(InteractionIntent(raw_message="", route="fallback", action="clarify", response_mode="ask_clarification"))
```

- [ ] **Step 3: Update eval runner tests**

In `backend/tests/unit/evals/test_run_rag_v2.py`, keep fake classifiers but ensure they return fully populated `InteractionIntent` including `retrieval_queries` for RAG cases:

```python
InteractionIntent(
    raw_message=query,
    route="rag",
    rag_task="room_search",
    domain="room",
    action="search",
    confidence=0.9,
    hard_filters={"max_rent": 1500},
    soft_preferences=["安静"],
    retrieval_queries=["1500以内 安静 房源"],
)
```

- [ ] **Step 4: Run affected tests**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/test_routing.py tests/unit/harness/modules/test_appointment.py tests/unit/evals/test_run_interaction_intent_eval.py tests/unit/evals/test_run_rag_v2.py -q
```

Expected: pass after replacing keyword-dependent expectations with explicit LLM intent fixtures.

---

## Task 9: Add Anti-Regression Scan For Keyword Runtime Helpers

**Files:**
- Create: `backend/tests/unit/interaction/test_no_keyword_fallback.py`

- [ ] **Step 1: Add source scan tests**

Create `backend/tests/unit/interaction/test_no_keyword_fallback.py`:

```python
from pathlib import Path


PROJECT_SRC = Path(__file__).resolve().parents[3] / "src" / "aptguide2"


def test_classifier_has_no_keyword_route_helpers():
    text = (PROJECT_SRC / "interaction" / "classifier.py").read_text(encoding="utf-8")

    forbidden = [
        "_looks_like_room_search",
        "_looks_like_kb_policy",
        "_looks_like_policy_question",
        "_infer_kb_domain",
        "any(term in message",
    ]
    for pattern in forbidden:
        assert pattern not in text


def test_query_understanding_has_no_message_keyword_extractors():
    text = (PROJECT_SRC / "rag" / "query_understanding.py").read_text(encoding="utf-8")

    forbidden = [
        "AREA_KEYWORDS",
        "PREFERENCE_SYNONYMS",
        "PAYMENT_PATTERNS",
        "_detect_task",
        "_extract_budget",
        "_extract_district",
        "_extract_payment",
        "_extract_preferences",
        " in message",
    ]
    for pattern in forbidden:
        assert pattern not in text
```

- [ ] **Step 2: Run scan test**

Run:

```bash
cd backend
uv run pytest tests/unit/interaction/test_no_keyword_fallback.py -q
```

Expected: fail until keyword helpers are removed from runtime files.

- [ ] **Step 3: Remove or move legacy helper code**

Delete the forbidden runtime helpers from:

```text
backend/src/aptguide2/interaction/classifier.py
backend/src/aptguide2/rag/query_understanding.py
```

If historical helper logic is still needed for reference, move it into a non-runtime document under `docs/plans/archive/` rather than keeping it importable.

- [ ] **Step 4: Re-run scan test**

Run:

```bash
cd backend
uv run pytest tests/unit/interaction/test_no_keyword_fallback.py -q
```

Expected: pass.

---

## Task 10: Run Full Verification And Live Eval

**Files:**
- Modify after successful run: `docs/tests/verification-log.md`
- Modify after successful run: `reports/rag-v2-live-evaluation-report.md`

- [ ] **Step 1: Run interaction and RAG focused tests**

Run:

```bash
cd backend
uv run pytest tests/unit/interaction tests/unit/rag/test_query_understanding.py tests/unit/rag/test_planning.py -q
```

Expected: pass.

- [ ] **Step 2: Run harness and eval focused tests**

Run:

```bash
cd backend
uv run pytest tests/unit/harness tests/unit/evals -q
```

Expected: pass.

- [ ] **Step 3: Run full backend tests**

Run:

```bash
cd backend
uv run pytest tests/ -q
```

Expected: all tests pass. Record the exact pass count and warnings.

- [ ] **Step 4: Run ruff**

Run:

```bash
cd backend
uv run ruff check src tests
```

Expected: clean.

- [ ] **Step 5: Run live RAG v2 eval only when LLM credentials are configured**

Run:

```bash
cd backend
uv run python evals/runners/run_rag_v2.py \
  --cases evals/datasets/rag_mvp_retrieval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected: report generated. If LLM credentials are missing, record this as skipped with reason `LLM credentials unavailable`; do not mark live eval passed.

- [ ] **Step 6: Update verification log**

Append to `docs/tests/verification-log.md`:

```markdown
## 2026-05-15 - LLM-First Interaction Understanding

- Focused interaction/RAG tests: <exact result>
- Harness/eval focused tests: <exact result>
- Full backend tests: <exact result>
- Ruff: <exact result>
- Live RAG v2 eval: <exact result or skipped with reason>
- Keyword fallback source scan: passed
```

---

## Task 11: Project Harness Checkpoint

**Files:**
- Modify: `progress/current-plan.md`
- Modify: `progress/next-steps.md`
- Modify: `progress/completed.md`
- Modify: `reports/evaluation-report.md`
- Create: `docs/plans/checkpoints/2026-05-15-llm-first-interaction-understanding.md`

- [ ] **Step 1: Snapshot state**

Run:

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Expected: JSON output with project path, git status, and state file previews.

- [ ] **Step 2: Record factual checkpoint**

Create `docs/plans/checkpoints/2026-05-15-llm-first-interaction-understanding.md`:

```markdown
# Checkpoint: LLM-First Interaction Understanding

## Metadata

- Created at: 2026-05-15
- Task: LLM-first interaction understanding
- Status: complete | partial
- Test status: <exact command results>

## Completed Work

- <facts only>

## Verification

- <commands and exact results>

## Known Issues

- <remaining failures or skipped verification>

## Next Steps

- <next concrete step>
```

- [ ] **Step 3: Update project state files**

Update:

```text
progress/current-plan.md
progress/next-steps.md
progress/completed.md
reports/evaluation-report.md
```

Only mark the feature complete if tests and eval evidence support it. If live eval was skipped because credentials were unavailable, write that explicitly.

---

## Self-Review

- Spec coverage: The plan replaces keyword classifier fallback, removes keyword query extraction from RAG runtime, defaults to LLM, adds contract validation, and converts uncertainty into clarification.
- Placeholder scan: No implementation step uses placeholder markers or vague error-handling instructions without concrete code or command.
- Type consistency: `InteractionIntent.retrieval_queries`, `InteractionIntent.clarification_needed`, and `QueryUnderstandingResult.domain` are introduced before later tasks use them.
- Risk boundary: Deterministic safety, pending action, tool confirmation, and lease validation remain outside the LLM understanding layer.
