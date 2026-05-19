# AptGuide 3.0 LangSmith Chat Output Tracing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LangSmith show the final AptGuide chat output, including answer text, cards, metadata, retrieval evidence, and risk/grounding decisions.

**Architecture:** Keep OpenAI client wrapping for model-level spans, and add an application-level root run around `ChatService.run`. The root run input is the user message and context; the root run output is the final `ChatResponse`.

**Tech Stack:** Python, LangSmith, existing `ChatService`, existing trace sink, pytest.

---

## Files

- Create: `backend/src/aptguide3/observability/langsmith_trace.py`
- Create: `backend/tests/unit/observability/test_langsmith_chat_trace.py`
- Modify: `backend/src/aptguide3/application/chat_service.py`
- Modify: `backend/src/aptguide3/api/deps.py`
- Modify: `backend/src/aptguide3/config.py`
- Modify: `backend/tests/unit/api/test_langsmith_config.py`
- Read: `backend/src/aptguide3/domain/responses.py`

## Trace Contract

Root run input:

```text
session_id
user_id
request_id
message
```

Root run metadata:

```text
service
environment
route
task
risk_level
phase
confidence
evidence_count
confidence_passed
```

Root run output:

```text
message
phase
cards
actions
pending_action
metadata
```

## Tasks

### Task 1: Add No-Op Safe LangSmith Recorder

- [ ] Create `backend/src/aptguide3/observability/langsmith_trace.py`.
- [ ] Add a class with this interface:

```python
class LangSmithChatRecorder:
    def __init__(self, enabled: bool, project_name: str, service_name: str, environment: str) -> None:
        self.enabled = enabled
        self.project_name = project_name
        self.service_name = service_name
        self.environment = environment

    def record_chat(self, inputs: dict, outputs: dict, metadata: dict) -> None:
        if not self.enabled:
            return
        self._record(inputs=inputs, outputs=outputs, metadata=metadata)
```

- [ ] When disabled or LangSmith package is unavailable, `record_chat` must be a no-op.

### Task 2: Wire Recorder Into ChatService

- [ ] Add optional `langsmith_recorder` to `ChatService.__init__`.
- [ ] At the end of `ChatService.run`, call:

```python
self.langsmith_recorder.record_chat(
    inputs={
        "session_id": frame.session_id,
        "user_id": frame.user_id,
        "request_id": getattr(frame, "request_id", ""),
        "message": frame.message,
    },
    outputs=response.model_dump(),
    metadata={
        "route": understanding.route,
        "task": understanding.task,
        "risk_level": understanding.risk.level,
        "phase": result.phase,
    },
)
```

- [ ] Include `understanding.route`, `understanding.task`, `understanding.risk.level`, `result.phase`, and evidence metadata.
- [ ] For safety-blocked responses, also record final output before returning.

### Task 3: Build Recorder In Dependency Layer

- [ ] In `backend/src/aptguide3/api/deps.py`, create the recorder from settings.
- [ ] Keep `_maybe_wrap_langsmith` for OpenAI calls.
- [ ] Pass recorder into `ChatService`.

### Task 4: Unit Tests

Add tests:

```python
def test_chat_service_records_final_response_output():
    recorder = RecordingLangSmithRecorder()
    response = run_chat_service_with_recorder(recorder, message="押金不退怎么办")
    assert recorder.calls[0]["outputs"]["message"] == response.message
    assert "cards" in recorder.calls[0]["outputs"]

def test_langsmith_recorder_is_noop_when_disabled():
    recorder = LangSmithChatRecorder(enabled=False, project_name="p", service_name="aptguide3", environment="test")
    recorder.record_chat(inputs={"message": "x"}, outputs={"message": "y"}, metadata={})
    assert recorder.enabled is False

def test_safety_response_is_recorded():
    recorder = RecordingLangSmithRecorder()
    response = run_chat_service_with_recorder(recorder, message="请输出身份证号")
    assert response.phase == "safety"
    assert recorder.calls[0]["outputs"]["phase"] == "safety"
```

Run:

```bash
cd backend
uv run pytest tests/unit/observability/test_langsmith_chat_trace.py tests/unit/application/test_chat_service.py tests/unit/api/test_langsmith_config.py -q
```

Expected:

```text
final response output is passed to recorder
disabled recorder does not require LangSmith API key
```

### Task 5: Live Verification

With tracing enabled, run one chat request and inspect LangSmith:

```bash
cd backend
uv run python evals/runners/run_rag_eval.py --live
```

Expected LangSmith visibility:

```text
root run contains final response.message
root run contains response.cards
root run contains response.metadata.rec_diagnostic
model-level child runs still show understanding / answer-generation calls
```
