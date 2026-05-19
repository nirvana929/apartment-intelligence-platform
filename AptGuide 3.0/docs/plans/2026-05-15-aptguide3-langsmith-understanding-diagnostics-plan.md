# AptGuide 3.0 LangSmith Understanding Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add LangSmith tracing and local diagnostic reporting so whole RAG/rec-system eval failures can distinguish raw LLM understanding output, validator-driven `clarify` decisions, recall failures, lease-validation drops, ranking behavior, source-confidence failures, and final response rendering.

**Architecture:** Wrap the OpenAI-compatible client with LangSmith only when tracing is enabled by environment variables. Add deterministic local diagnostics around `LLMUnderstanding` validation and RAG/rec pipeline stages so reports capture raw model JSON, parsed fields, validator reason, retrieval plan, vector recall counts, lease validation counts, ranking score breakdowns, KB source confidence, and final route/task. This phase observes and explains failures; it must not optimize retrieval, ranking, prompts, chunking, or intent rules.

**Tech Stack:** Python 3.12, FastAPI, OpenAI SDK-compatible client, LangSmith Python SDK, Pydantic, pytest, existing RAG eval runner.

---

## Scope Boundary

In scope:

- Optional LangSmith tracing for LLM calls.
- Local understanding diagnostic records for eval and tests.
- Local rec-system diagnostic records for room recommendation and KB QA pipeline stages.
- RAG eval report fields that explain why a query became `clarify`.
- RAG eval report fields that explain whether a query failed before retrieval, during vector recall, during lease validation, during ranking, during confidence gating, or during response rendering.
- Documentation and harness progress updates.

Out of scope:

- Changing RAG retrieval/ranking/chunking.
- Tuning prompts to improve routing.
- Adding keyword/rule-based intent classification.
- Fixing the 35 full-suite asyncio runner failures unless they block this diagnostic work.
- Production LangSmith rollout with real user data.

## Safety Requirements

- LangSmith tracing must be opt-in.
- Default local behavior must remain unchanged when tracing variables are absent.
- Do not send production user data or secrets to LangSmith during development verification.
- Do not log API keys, internal tokens, JWTs, database DSNs with passwords, or lease customer PII.

## Files and Responsibilities

- `backend/pyproject.toml`: Add `langsmith` dependency.
- `backend/.env.example`: Document LangSmith and diagnostic env vars.
- `backend/src/aptguide3/config.py`: Add opt-in LangSmith/diagnostic settings.
- `backend/src/aptguide3/api/deps.py`: Wrap OpenAI clients when tracing is enabled.
- `backend/src/aptguide3/understanding/diagnostics.py`: New focused module for diagnostic data structures and sanitization.
- `backend/src/aptguide3/rag/diagnostics.py`: New focused module for recommendation/RAG stage diagnostics.
- `backend/src/aptguide3/understanding/validation.py`: Return validator decision details without changing routing semantics.
- `backend/src/aptguide3/understanding/llm_understanding.py`: Capture raw LLM JSON, parsed fields, validation reason, final result; expose last diagnostic.
- `backend/src/aptguide3/rag/room_retrieval.py`: Capture room vector recall, dedupe, validation, preference scoring, and ranking diagnostics without changing behavior.
- `backend/src/aptguide3/rag/kb_retrieval.py`: Capture KB vector recall, dedupe, rerank, and confidence-input diagnostics without changing behavior.
- `backend/src/aptguide3/procedures/room_search.py`: Attach room rec diagnostics to response metadata/eval context when enabled.
- `backend/src/aptguide3/procedures/kb_qa.py`: Attach KB diagnostics and confidence-gate details to response metadata/eval context when enabled.
- `backend/evals/runners/run_rag_eval.py`: Include understanding diagnostic details in live reports.
- `backend/tests/unit/understanding/test_diagnostics.py`: Unit tests for diagnostic sanitization and validator reason capture.
- `backend/tests/unit/understanding/test_llm_understanding.py`: Tests that low confidence, model-requested clarification, and invalid filters report distinct reasons.
- `backend/tests/unit/rag/test_rec_diagnostics.py`: Unit tests for room and KB diagnostic summaries.
- `backend/tests/unit/api/test_langsmith_config.py`: Test client wrapping is opt-in and does not require LangSmith by default.
- `docs/tests/verification-log.md`: Append commands and results.
- `docs/tests/evaluation-report.md`: Summarize diagnostic capability.
- `progress/current-plan.md`, `progress/next-steps.md`, `reports/evaluation-report.md`: Harness state.

## Task 1: Add Opt-In LangSmith Settings

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/.env.example`
- Modify: `backend/src/aptguide3/config.py`
- Test: `backend/tests/unit/test_config.py`

- [ ] **Step 1: Add dependency**

Modify `backend/pyproject.toml`:

```toml
dependencies = [
    "fastapi>=0.111.0",
    "openai>=1.0.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",
    "pymilvus>=2.4.0",
    "uvicorn>=0.30.0",
    "httpx>=0.27.0",
    "asyncmy>=0.2.10",
    "redis>=5.0.0",
    "sqlalchemy>=2.0.0",
    "pyyaml>=6.0",
    "langsmith>=0.2.0",
]
```

- [ ] **Step 2: Add config fields**

Modify `backend/src/aptguide3/config.py` inside `Settings`:

```python
    langsmith_tracing: bool = False
    langsmith_project: str = "aptguide3-local"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    understanding_diagnostics_enabled: bool = False
```

- [ ] **Step 3: Document environment variables**

Append to `backend/.env.example`:

```bash
# --- LangSmith tracing (optional, development only) ---
# When true, OpenAI-compatible LLM/embedding calls may be traced to LangSmith.
# Do not enable with production user data or secrets.
APTGUIDE3_LANGSMITH_TRACING=false
APTGUIDE3_LANGSMITH_PROJECT=aptguide3-local
APTGUIDE3_LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=

# --- Understanding diagnostics (local report fields) ---
APTGUIDE3_UNDERSTANDING_DIAGNOSTICS_ENABLED=false
```

- [ ] **Step 4: Add config test**

Append to `backend/tests/unit/test_config.py`:

```python
def test_langsmith_settings_default_off(monkeypatch):
    from aptguide3.config import get_settings

    get_settings.cache_clear()
    monkeypatch.delenv("APTGUIDE3_LANGSMITH_TRACING", raising=False)
    settings = get_settings()

    assert settings.langsmith_tracing is False
    assert settings.langsmith_project == "aptguide3-local"
    assert settings.understanding_diagnostics_enabled is False
    get_settings.cache_clear()


def test_langsmith_settings_can_be_enabled(monkeypatch):
    from aptguide3.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("APTGUIDE3_LANGSMITH_TRACING", "true")
    monkeypatch.setenv("APTGUIDE3_LANGSMITH_PROJECT", "aptguide3-rag-debug")
    monkeypatch.setenv("APTGUIDE3_UNDERSTANDING_DIAGNOSTICS_ENABLED", "true")
    settings = get_settings()

    assert settings.langsmith_tracing is True
    assert settings.langsmith_project == "aptguide3-rag-debug"
    assert settings.understanding_diagnostics_enabled is True
    get_settings.cache_clear()
```

- [ ] **Step 5: Run focused config tests**

Run from `AptGuide 3.0/backend`:

```bash
uv run pytest tests/unit/test_config.py -q
```

Expected: config tests pass.

## Task 2: Wrap OpenAI Clients Only When LangSmith Is Enabled

**Files:**
- Modify: `backend/src/aptguide3/api/deps.py`
- Create: `backend/tests/unit/api/test_langsmith_config.py`

- [ ] **Step 1: Locate OpenAI client creation**

Open `backend/src/aptguide3/api/deps.py` and identify the helper that creates the LLM and embedding clients. Do not change behavior yet.

- [ ] **Step 2: Add wrapper helper**

Add near the OpenAI client creation code:

```python
def _maybe_wrap_langsmith(client, settings):
    if not settings.langsmith_tracing:
        return client
    try:
        from langsmith.wrappers import wrap_openai
    except ImportError:
        return client
    return wrap_openai(
        client,
        tracing_extra={
            "project_name": settings.langsmith_project,
            "metadata": {
                "service": settings.service_name,
                "environment": settings.environment,
            },
            "tags": ["aptguide3", "understanding"],
        },
    )
```

Then apply it to the OpenAI-compatible clients:

```python
client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key.get_secret_value())
client = _maybe_wrap_langsmith(client, settings)
```

Use the same helper for embedding client creation if it also uses OpenAI SDK.

- [ ] **Step 3: Add opt-in tests**

Create `backend/tests/unit/api/test_langsmith_config.py`:

```python
from types import SimpleNamespace

from aptguide3.api.deps import _maybe_wrap_langsmith


class DummyClient:
    pass


def test_langsmith_wrapper_is_noop_when_disabled():
    client = DummyClient()
    settings = SimpleNamespace(
        langsmith_tracing=False,
        langsmith_project="aptguide3-local",
        service_name="aptguide3",
        environment="test",
    )

    assert _maybe_wrap_langsmith(client, settings) is client


def test_langsmith_wrapper_does_not_require_api_key_when_disabled():
    client = DummyClient()
    settings = SimpleNamespace(
        langsmith_tracing=False,
        langsmith_project="aptguide3-local",
        service_name="aptguide3",
        environment="test",
    )

    wrapped = _maybe_wrap_langsmith(client, settings)

    assert wrapped is client
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
uv run pytest tests/unit/api/test_langsmith_config.py tests/unit/test_config.py -q
```

Expected: tests pass.

## Task 3: Add Understanding Diagnostic Data Structures

**Files:**
- Create: `backend/src/aptguide3/understanding/diagnostics.py`
- Create: `backend/tests/unit/understanding/test_diagnostics.py`

- [ ] **Step 1: Create diagnostics module**

Create `backend/src/aptguide3/understanding/diagnostics.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "token",
    "internal_token",
    "password",
    "mysql_dsn",
}


@dataclass
class UnderstandingDiagnostic:
    raw_message: str
    raw_llm_json: str = ""
    parse_error: str = ""
    parsed_route: str = ""
    parsed_task: str = ""
    parsed_confidence: float | None = None
    parsed_clarification_needed: bool | None = None
    parsed_clarification_question: str = ""
    parsed_risk_response_mode: str = ""
    parsed_hard_filters: dict[str, Any] = field(default_factory=dict)
    validator_reason: str = ""
    final_route: str = ""
    final_task: str = ""
    final_confidence: float | None = None

    def to_report_dict(self) -> dict[str, Any]:
        return sanitize_for_report(asdict(self))


def sanitize_for_report(value: Any) -> Any:
    if isinstance(value, dict):
        clean = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_KEYS:
                clean[key] = "<redacted>"
            else:
                clean[key] = sanitize_for_report(item)
        return clean
    if isinstance(value, list):
        return [sanitize_for_report(item) for item in value]
    return value
```

- [ ] **Step 2: Add diagnostic tests**

Create `backend/tests/unit/understanding/test_diagnostics.py`:

```python
from aptguide3.understanding.diagnostics import UnderstandingDiagnostic, sanitize_for_report


def test_sanitize_for_report_redacts_sensitive_keys():
    payload = {
        "api_key": "secret",
        "nested": {"token": "secret-token", "safe": "ok"},
        "items": [{"password": "pw", "value": 1}],
    }

    assert sanitize_for_report(payload) == {
        "api_key": "<redacted>",
        "nested": {"token": "<redacted>", "safe": "ok"},
        "items": [{"password": "<redacted>", "value": 1}],
    }


def test_understanding_diagnostic_report_dict_is_sanitized():
    diagnostic = UnderstandingDiagnostic(
        raw_message="找番禺1500以内安静一点的房子",
        raw_llm_json='{"api_key":"secret"}',
        parsed_route="rag",
        parsed_task="room_search",
        parsed_confidence=0.9,
        parsed_clarification_needed=False,
        final_route="rag",
        final_task="room_search",
        final_confidence=0.9,
    )

    report = diagnostic.to_report_dict()

    assert report["parsed_route"] == "rag"
    assert report["parsed_task"] == "room_search"
```

- [ ] **Step 3: Run diagnostic tests**

Run:

```bash
uv run pytest tests/unit/understanding/test_diagnostics.py -q
```

Expected: tests pass.

## Task 4: Preserve Validator Reasons Without Changing Semantics

**Files:**
- Modify: `backend/src/aptguide3/understanding/validation.py`
- Test: `backend/tests/unit/understanding/test_llm_understanding.py`

- [ ] **Step 1: Add validation decision helper**

In `backend/src/aptguide3/understanding/validation.py`, add:

```python
def validation_failure_reason(result: UnderstandingResult, min_confidence: float) -> str:
    if result.confidence < min_confidence:
        return "low_confidence"
    if result.clarification.needed or result.risk.response_mode == "ask_clarification":
        return result.reason or "model_requested_clarification"
    if not _shape_is_valid(result):
        return "invalid_route_task_shape"
    if not _hard_filters_are_valid(result.hard_filters):
        return "invalid_hard_filters"
    return ""
```

Then modify `validate_or_clarify` to use it:

```python
def validate_or_clarify(result: UnderstandingResult, min_confidence: float) -> UnderstandingResult:
    reason = validation_failure_reason(result, min_confidence)
    if not reason:
        return result
    if reason == (result.reason or "model_requested_clarification"):
        return clarification_result(result.raw_message, reason, result.clarification.question)
    return clarification_result(result.raw_message, reason)
```

Keep returned behavior equivalent to current behavior.

- [ ] **Step 2: Add validator reason tests**

Append to `backend/tests/unit/understanding/test_llm_understanding.py` or create `test_validation.py`:

```python
from aptguide3.domain.understanding import Clarification, RiskDecision, UnderstandingResult
from aptguide3.understanding.validation import validation_failure_reason


def test_validation_failure_reason_low_confidence():
    result = UnderstandingResult(
        raw_message="找番禺1500以内安静一点的房子",
        route="rag",
        task="room_search",
        confidence=0.5,
    )

    assert validation_failure_reason(result, 0.65) == "low_confidence"


def test_validation_failure_reason_model_requested_clarification():
    result = UnderstandingResult(
        raw_message="我想租房",
        route="clarify",
        task="clarify",
        action="ask_clarification",
        confidence=0.8,
        risk=RiskDecision(response_mode="ask_clarification"),
        clarification=Clarification(needed=True, question="预算是多少？"),
        reason="missing_budget",
    )

    assert validation_failure_reason(result, 0.65) == "missing_budget"


def test_validation_failure_reason_invalid_hard_filters():
    result = UnderstandingResult(
        raw_message="找番禺1500以内安静一点的房子",
        route="rag",
        task="room_search",
        confidence=0.9,
        hard_filters={"max_rent": "1500"},
    )

    assert validation_failure_reason(result, 0.65) == "invalid_hard_filters"
```

- [ ] **Step 3: Run validation tests**

Run:

```bash
uv run pytest tests/unit/understanding -q
```

Expected: understanding tests pass.

## Task 5: Capture Raw LLM Output and Final Validator Decision

**Files:**
- Modify: `backend/src/aptguide3/understanding/llm_understanding.py`
- Test: `backend/tests/unit/understanding/test_llm_understanding.py`

- [ ] **Step 1: Add diagnostic storage**

Modify `LLMUnderstanding.__init__`:

```python
from aptguide3.understanding.diagnostics import UnderstandingDiagnostic
from aptguide3.understanding.validation import clarification_result, validate_or_clarify, validation_failure_reason


class LLMUnderstanding:
    def __init__(self, client, model: str, min_confidence: float = 0.65, diagnostics_enabled: bool = False) -> None:
        self.client = client
        self.model = model
        self.min_confidence = min_confidence
        self.diagnostics_enabled = diagnostics_enabled
        self.last_diagnostic: UnderstandingDiagnostic | None = None
```

- [ ] **Step 2: Capture parsed and final fields**

Modify `understand` so it records diagnostic data:

```python
    def understand(self, message: str) -> UnderstandingResult:
        diagnostic = UnderstandingDiagnostic(raw_message=message)
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
            diagnostic.raw_llm_json = content
            result = UnderstandingResult.model_validate_json(content)
            diagnostic.parsed_route = result.route
            diagnostic.parsed_task = result.task
            diagnostic.parsed_confidence = result.confidence
            diagnostic.parsed_clarification_needed = result.clarification.needed
            diagnostic.parsed_clarification_question = result.clarification.question
            diagnostic.parsed_risk_response_mode = result.risk.response_mode
            diagnostic.parsed_hard_filters = dict(result.hard_filters)
        except (ValidationError, Exception) as exc:
            diagnostic.parse_error = exc.__class__.__name__
            final = clarification_result(message, f"llm_understanding_failed:{exc.__class__.__name__}")
            diagnostic.validator_reason = final.reason
            diagnostic.final_route = final.route
            diagnostic.final_task = final.task
            diagnostic.final_confidence = final.confidence
            self.last_diagnostic = diagnostic
            return final

        if not result.raw_message:
            result = result.model_copy(update={"raw_message": message})

        diagnostic.validator_reason = validation_failure_reason(result, self.min_confidence)
        final = validate_or_clarify(result, self.min_confidence)
        diagnostic.final_route = final.route
        diagnostic.final_task = final.task
        diagnostic.final_confidence = final.confidence
        self.last_diagnostic = diagnostic
        return final
```

Do not gate `last_diagnostic` behind `diagnostics_enabled`; keep it in memory only. Gate report rendering elsewhere.

- [ ] **Step 3: Add fake-client tests**

Append tests:

```python
def test_llm_understanding_records_low_confidence_diagnostic():
    content = """{
      "raw_message": "找番禺1500以内安静一点的房子",
      "route": "rag",
      "task": "room_search",
      "domain": "room",
      "action": "search",
      "confidence": 0.5,
      "hard_filters": {"district_name": "番禺", "max_rent": 1500},
      "soft_preferences": ["安静"],
      "retrieval_queries": ["番禺 1500以内 安静 房子"],
      "risk": {"level": "low", "response_mode": "normal_answer", "reason": ""},
      "clarification": {"needed": false, "question": ""},
      "reason": ""
    }"""
    understanding = LLMUnderstanding(FakeClient(content=content), model="fake-model", min_confidence=0.65)

    result = understanding.understand("找番禺1500以内安静一点的房子")

    assert result.route == "clarify"
    assert understanding.last_diagnostic is not None
    assert understanding.last_diagnostic.parsed_route == "rag"
    assert understanding.last_diagnostic.parsed_task == "room_search"
    assert understanding.last_diagnostic.parsed_confidence == 0.5
    assert understanding.last_diagnostic.validator_reason == "low_confidence"
    assert understanding.last_diagnostic.final_route == "clarify"
```

Also add a test where `clarification.needed=true` with confidence `0.9` and assert `validator_reason` is the model reason.

- [ ] **Step 4: Run focused tests**

Run:

```bash
uv run pytest tests/unit/understanding -q
```

Expected: understanding tests pass.

## Task 6: Wire Diagnostics Setting into Dependency Construction

**Files:**
- Modify: `backend/src/aptguide3/api/deps.py`
- Test: existing focused tests

- [ ] **Step 1: Pass diagnostics setting to LLMUnderstanding**

Find the existing construction:

```python
LLMUnderstanding(client, settings.llm_model, settings.understanding_min_confidence)
```

Change to:

```python
LLMUnderstanding(
    client,
    settings.llm_model,
    settings.understanding_min_confidence,
    diagnostics_enabled=settings.understanding_diagnostics_enabled,
)
```

- [ ] **Step 2: Run dependency-related tests**

Run:

```bash
uv run pytest tests/unit/api tests/unit/test_config.py tests/unit/understanding -q
```

Expected: focused tests pass.

## Task 7: Add Rec-System Stage Diagnostics

**Files:**
- Create: `backend/src/aptguide3/rag/diagnostics.py`
- Modify: `backend/src/aptguide3/rag/room_retrieval.py`
- Modify: `backend/src/aptguide3/rag/kb_retrieval.py`
- Modify: `backend/src/aptguide3/procedures/room_search.py`
- Modify: `backend/src/aptguide3/procedures/kb_qa.py`
- Create: `backend/tests/unit/rag/test_rec_diagnostics.py`

- [ ] **Step 1: Create rec diagnostics module**

Create `backend/src/aptguide3/rag/diagnostics.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RoomRecDiagnostic:
    task: str = "room_search"
    raw_message: str = ""
    semantic_queries: list[str] = field(default_factory=list)
    hard_filters: dict[str, Any] = field(default_factory=dict)
    soft_preferences: list[str] = field(default_factory=list)
    embedding_queries_attempted: int = 0
    embedding_empty_count: int = 0
    vector_hits_total: int = 0
    vector_unique_room_count: int = 0
    vector_top_room_ids: list[int] = field(default_factory=list)
    lease_validation_requested_count: int = 0
    lease_validated_count: int = 0
    lease_dropped_room_ids: list[int] = field(default_factory=list)
    preference_scored_count: int = 0
    ranked_count: int = 0
    final_room_ids: list[int] = field(default_factory=list)
    score_breakdown: list[dict[str, Any]] = field(default_factory=list)
    failure_stage: str = ""

    def to_report_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KbRecDiagnostic:
    task: str = "kb_qa"
    raw_message: str = ""
    semantic_queries: list[str] = field(default_factory=list)
    module_intent: str | None = None
    risk_level: str = "low"
    embedding_queries_attempted: int = 0
    embedding_empty_count: int = 0
    vector_hits_total: int = 0
    unique_chunk_count: int = 0
    returned_doc_ids: list[str] = field(default_factory=list)
    returned_chunk_ids: list[str] = field(default_factory=list)
    top_sources: list[dict[str, Any]] = field(default_factory=list)
    confidence_passed: bool | None = None
    confidence_failure_reason: str = ""
    failure_stage: str = ""

    def to_report_dict(self) -> dict[str, Any]:
        return asdict(self)
```

- [ ] **Step 2: Instrument room retrieval without behavior changes**

Modify `retrieve_ranked_rooms` in `backend/src/aptguide3/rag/room_retrieval.py` to accept:

```python
diagnostic: RoomRecDiagnostic | None = None
```

Populate these fields during the existing flow:

```text
semantic_queries
hard_filters
soft_preferences
embedding_queries_attempted
embedding_empty_count
vector_hits_total
vector_unique_room_count
vector_top_room_ids
lease_validation_requested_count
lease_validated_count
lease_dropped_room_ids
preference_scored_count
ranked_count
final_room_ids
score_breakdown
failure_stage
```

Required stage labels:

```text
vector_recall_empty
lease_validation_empty
ranking_empty
```

- [ ] **Step 3: Instrument KB retrieval without behavior changes**

Modify `retrieve_kb_sources` in `backend/src/aptguide3/rag/kb_retrieval.py` to accept:

```python
diagnostic: KbRecDiagnostic | None = None
```

Populate these fields during the existing flow:

```text
semantic_queries
module_intent
risk_level
embedding_queries_attempted
embedding_empty_count
vector_hits_total
unique_chunk_count
returned_doc_ids
returned_chunk_ids
top_sources
failure_stage
```

Required stage labels:

```text
kb_vector_recall_empty
kb_rerank_empty
```

- [ ] **Step 4: Attach diagnostics in procedures**

In `backend/src/aptguide3/procedures/room_search.py`, create `RoomRecDiagnostic`, pass it into `retrieve_ranked_rooms`, and include:

```python
"rec_diagnostic": diagnostic.to_report_dict()
```

in `ProcedureResult.metadata` for both success and fallback paths.

In `backend/src/aptguide3/procedures/kb_qa.py`, create `KbRecDiagnostic`, pass it into `retrieve_kb_sources`, set:

```python
diagnostic.confidence_passed = confidence_passed
diagnostic.confidence_failure_reason = f"source_count={len(sources)}, risk_level={plan.risk_level}"
```

when confidence fails, and include:

```python
"rec_diagnostic": diagnostic.to_report_dict()
```

in `ProcedureResult.metadata` for both success and fallback paths.

- [ ] **Step 5: Add diagnostic unit tests**

Create `backend/tests/unit/rag/test_rec_diagnostics.py`:

```python
from aptguide3.rag.diagnostics import KbRecDiagnostic, RoomRecDiagnostic


def test_room_rec_diagnostic_report_contains_stage_counts():
    diagnostic = RoomRecDiagnostic(
        raw_message="找番禺1500以内安静一点的房子",
        semantic_queries=["番禺 1500以内 安静 房子"],
        vector_hits_total=10,
        vector_unique_room_count=4,
        lease_validation_requested_count=4,
        lease_validated_count=2,
        lease_dropped_room_ids=[3, 4],
        final_room_ids=[1, 2],
    )

    report = diagnostic.to_report_dict()

    assert report["vector_hits_total"] == 10
    assert report["lease_dropped_room_ids"] == [3, 4]
    assert report["final_room_ids"] == [1, 2]


def test_kb_rec_diagnostic_report_contains_source_counts():
    diagnostic = KbRecDiagnostic(
        raw_message="押金不退怎么办",
        semantic_queries=["押金不退 处理"],
        vector_hits_total=8,
        unique_chunk_count=5,
        returned_doc_ids=["KB-LEASE-005"],
        returned_chunk_ids=["chunk-1"],
        confidence_passed=True,
    )

    report = diagnostic.to_report_dict()

    assert report["vector_hits_total"] == 8
    assert report["returned_doc_ids"] == ["KB-LEASE-005"]
    assert report["confidence_passed"] is True
```

- [ ] **Step 6: Run focused rec diagnostic tests**

Run:

```bash
uv run pytest tests/unit/rag/test_rec_diagnostics.py tests/unit/procedures/test_room_search.py tests/unit/procedures/test_kb_qa.py -q
```

Expected: focused tests pass.

## Task 8: Include Understanding and Rec Diagnostics in Live RAG Eval Report

**Files:**
- Modify: `backend/evals/runners/run_rag_eval.py`
- Test: `backend/tests/unit/rag/` or create focused eval runner unit tests if existing structure allows

- [ ] **Step 1: Capture diagnostic after each live call**

In `run_live_eval`, after `_send_live(chat_service, query, session_id)`, inspect:

```python
diagnostic = getattr(chat_service.understanding, "last_diagnostic", None)
diagnostic_report = diagnostic.to_report_dict() if diagnostic else {}
```

Add to each `live_results.append` item:

```python
"understanding_diagnostic": diagnostic_report,
"rec_diagnostic": response.metadata.get("rec_diagnostic", {}),
```

- [ ] **Step 2: Render understanding diagnostic fields per case**

In live case rendering, include:

```text
understanding:
  parsed_route=<...>, parsed_task=<...>, parsed_confidence=<...>
  clarification_needed=<...>, risk_response_mode=<...>
  validator_reason=<...>
  final_route=<...>, final_task=<...>, final_confidence=<...>
```

Do not print raw JSON by default. Add raw JSON only when an env flag is enabled:

```python
include_raw = os.environ.get("APTGUIDE3_EVAL_INCLUDE_RAW_LLM_JSON") == "1"
```

If raw JSON is included, use sanitized diagnostic output.

- [ ] **Step 3: Render rec-system diagnostic fields per case**

For `room_search` cases, render:

```text
rec:
  semantic_queries=<...>
  vector_hits_total=<...>, vector_unique_room_count=<...>
  lease_validation_requested_count=<...>, lease_validated_count=<...>
  lease_dropped_room_ids=<...>
  final_room_ids=<...>
  failure_stage=<...>
  score_breakdown=<top ranked score details>
```

For `kb_qa` cases, render:

```text
rec:
  semantic_queries=<...>, module_intent=<...>, risk_level=<...>
  vector_hits_total=<...>, unique_chunk_count=<...>
  returned_doc_ids=<...>, returned_chunk_ids=<...>
  confidence_passed=<...>, confidence_failure_reason=<...>
  failure_stage=<...>
  top_sources=<top source score details>
```

- [ ] **Step 4: Add report note**

Add a report note:

```text
- Understanding diagnostics show raw parsed model intent separately from validator final route. This distinguishes low confidence, model-requested clarification, schema/shape failures, and invalid hard filters.
- Rec diagnostics show whether the query reached vector recall, lease validation, ranking, KB rerank, confidence gating, and final response rendering.
```

- [ ] **Step 5: Run smoke eval**

Run:

```bash
uv run python evals/runners/run_rag_eval.py
```

Expected: smoke report still works without live services.

- [ ] **Step 6: Run live eval with diagnostics enabled**

Run with live env:

```bash
APTGUIDE3_UNDERSTANDING_DIAGNOSTICS_ENABLED=true \
APTGUIDE3_LIVE_TESTS=1 \
APTGUIDE3_LLM_API_KEY="$APTGUIDE3_LLM_API_KEY" \
APTGUIDE3_EMBEDDING_API_KEY="$APTGUIDE3_EMBEDDING_API_KEY" \
APTGUIDE3_VECTOR_URI=http://127.0.0.1:19530 \
APTGUIDE3_LEASE_BASE_URL=http://127.0.0.1:8081 \
uv run python evals/runners/run_rag_eval.py --live
```

Expected: report shows per-case parsed route/task/confidence and validator reason. If a case reaches retrieval, report also shows vector recall counts, validation counts, ranked IDs/source IDs, and stage-level failure reason.

## Task 9: Verify LangSmith Trace Visibility

**Files:**
- No code changes unless Task 2 tests reveal wrapper issues.
- Update: `docs/tests/verification-log.md`
- Update: `docs/tests/evaluation-report.md`

- [ ] **Step 1: Export LangSmith variables**

Run from `AptGuide 3.0/backend`:

```bash
export LANGSMITH_API_KEY="<your-dev-langsmith-key>"
export LANGSMITH_TRACING=true
export LANGSMITH_PROJECT=aptguide3-rag-debug
export APTGUIDE3_LANGSMITH_TRACING=true
export APTGUIDE3_LANGSMITH_PROJECT=aptguide3-rag-debug
export APTGUIDE3_UNDERSTANDING_DIAGNOSTICS_ENABLED=true
```

- [ ] **Step 2: Run one direct understanding/RAG eval call**

Run:

```bash
APTGUIDE3_LIVE_TESTS=1 \
uv run python evals/runners/run_rag_eval.py --live
```

Expected locally: report generated. Expected in LangSmith: OpenAI-compatible LLM calls appear under project `aptguide3-rag-debug`.

- [ ] **Step 3: Record what is visible**

Append to `docs/tests/verification-log.md`:

```markdown
## 2026-05-15 - langsmith-understanding-diagnostics

- LangSmith project: `aptguide3-rag-debug`
- Command: `APTGUIDE3_UNDERSTANDING_DIAGNOSTICS_ENABLED=true uv run python evals/runners/run_rag_eval.py --live`
- Result: <fill exact pass/fail>
- LangSmith trace visibility: <LLM calls visible / not visible>
- Local diagnostic report: `backend/evals/reports/rag-evaluation-report.md`
```

Do not paste secrets or API keys.

## Task 10: Update Harness State

**Files:**
- Modify: `progress/current-plan.md`
- Modify: `progress/next-steps.md`
- Modify: `reports/evaluation-report.md`
- Modify: `docs/plans/current-plan.md`
- Modify: `docs/plans/next-steps.md`
- Modify: `docs/plans/README.md`

- [ ] **Step 1: Add this plan to docs index**

Add to `docs/plans/README.md`:

```markdown
| [2026-05-15-aptguide3-langsmith-understanding-diagnostics-plan.md](2026-05-15-aptguide3-langsmith-understanding-diagnostics-plan.md) | LangSmith tracing and local understanding diagnostics for RAG eval routing failures | active |
```

- [ ] **Step 2: Update current plan**

Set current objective to:

```text
AptGuide 3.0 Milestone 6: LangSmith tracing and understanding diagnostics for RAG eval routing failures.
```

Record:

```text
This phase is diagnostic only. It identifies whether clarify comes from low confidence, model-requested clarification, invalid route/task shape, invalid hard filters, or parse errors.
```

- [ ] **Step 3: Update next steps**

Next steps should be:

```text
1. Run diagnostic live eval on the 4 seed cases.
2. Read per-case validator reason and rec-stage diagnostics.
3. Decide whether each failure belongs to understanding, vector recall, lease validation, ranking, confidence gating, response rendering, or dataset labels.
4. Only then plan RAG routing/rec optimization.
```

- [ ] **Step 4: Run project harness snapshot**

Run from `AptGuide 3.0`:

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Expected: snapshot lists this plan and the updated harness docs.

## Exit Criteria

- LangSmith tracing is opt-in and disabled by default.
- OpenAI-compatible LLM calls can be visible in LangSmith when configured.
- RAG eval report shows parsed LLM understanding fields and validator reason per live case.
- RAG eval report shows rec-system stage diagnostics for cases that reach retrieval.
- Existing behavior is unchanged when tracing/diagnostics are disabled.
- No secrets are written to reports.
- Focused tests pass.
- Harness docs point to the diagnostics plan and next decision point.
