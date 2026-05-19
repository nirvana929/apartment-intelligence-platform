# AptGuide 3.0 Grounded Risk Answer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure medium/high-risk KB QA and room-related answers are grounded in concrete evidence and expose citations in both final text and metadata.

**Architecture:** Retrieval returns evidence; confidence gate decides whether evidence is enough; grounded answer generation writes the user-facing answer from evidence only. The model may summarize evidence but may not invent policy, availability, price validity, or operational commitments.

**Tech Stack:** Python, Pydantic, OpenAI-compatible client, LangSmith wrapper, pytest, existing KB QA and room search procedures.

---

## Files

- Create: `backend/src/aptguide3/rag/grounded_answer.py`
- Create: `backend/tests/unit/rag/test_grounded_answer.py`
- Modify: `backend/src/aptguide3/procedures/kb_qa.py`
- Modify: `backend/src/aptguide3/procedures/room_search.py`
- Modify: `backend/src/aptguide3/api/deps.py`
- Modify: `backend/tests/unit/procedures/test_kb_qa.py`
- Modify: `backend/tests/unit/procedures/test_room_search.py`
- Modify: `backend/evals/runners/run_rag_eval.py`
- Read: `docs/system/evidence-contract.md`

## Grounded Answer Contract

For medium/high-risk KB QA, final output must include:

```text
answer_text
citations: list[{chunk_id, doc_id, title}]
evidence_count
risk_level
grounded_answer=true
```

If evidence is insufficient:

```text
grounded_answer=false
fallback_reason=<reason>
message must avoid commitment language
```

## Tasks

### Task 1: Add Grounded Answer Data Types

- [ ] Create `backend/src/aptguide3/rag/grounded_answer.py`.
- [ ] Define a `GroundedAnswer` Pydantic model:

```python
from pydantic import BaseModel, Field


class Citation(BaseModel):
    chunk_id: str = ""
    doc_id: str = ""
    title: str = ""


class GroundedAnswer(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    grounded: bool = False
    fallback_reason: str = ""
```

### Task 2: Add Evidence-Only Prompt Builder

- [ ] Add a function that builds a prompt from user query and top sources.
- [ ] The prompt must say:

```text
Only answer using the provided sources.
For each factual or policy claim, cite doc_id/chunk_id.
If the sources do not support an answer, return a conservative fallback.
Do not promise refunds, availability, appointment success, contract changes, or operator actions.
```

### Task 3: Add Deterministic Fallback

- [ ] Add `build_conservative_grounded_fallback(query, risk_level, reason)` that returns a `GroundedAnswer`.
- [ ] For high risk, message must direct the user to verified channel or human follow-up when sources are insufficient.

### Task 4: Wire KB QA

- [ ] Update `KbQaProcedure` to accept optional `answer_client` and `answer_model`.
- [ ] After sources pass confidence gate, call grounded answer generation.
- [ ] Set `ProcedureResult.message` to grounded answer text.
- [ ] Keep `kb_source` cards.
- [ ] Put citations in metadata:

```text
grounded_answer
citations
evidence_count
fallback_reason
```

### Task 5: Wire Room Search Risk Language

- [ ] Update `RoomSearchProcedure` so room results with non-lease-validated evidence never claim confirmed availability.
- [ ] If risk level is medium/high and no lease-validated rooms exist, return a conservative message and diagnostic metadata.
- [ ] Room results with `evidence_level` of `vector_only` or `mapped_candidate` must NOT be presented as confirmed available, price-validated, or appointmentable in medium/high-risk responses.
- [ ] Only `mapped_verified` room results (verified via `RoomIdentityRepository`) may carry availability/price/appointment claims in medium/high-risk contexts.
- [ ] If all room results are `vector_only` or `mapped_candidate`, the response must include a disclaimer that room information has not been verified against the lease system.

### Task 6: Unit Tests

Add tests:

```python
def test_high_risk_kb_answer_contains_citations_when_sources_pass():
    answer = GroundedAnswer(
        answer="押金处理需以合同和平台规则为准。[KB-LS-011]",
        citations=[Citation(chunk_id="KB-LS-011", doc_id="KB-LS-011", title="签约后可以反悔吗")],
        grounded=True,
    )
    assert answer.grounded is True
    assert answer.citations[0].doc_id == "KB-LS-011"

def test_high_risk_kb_answer_falls_back_when_no_citations():
    answer = build_conservative_grounded_fallback("押金不退怎么办", "high", "no_citations")
    assert answer.grounded is False
    assert answer.fallback_reason == "no_citations"
    assert "无法基于现有资料确认" in answer.answer

def test_room_search_does_not_claim_availability_without_lease_validation():
    card = {"evidence_level": "vector_only", "lease_validation_status": "not_checked"}
    message = build_room_result_message([card], risk_level="medium")
    assert "确认可租" not in message
    assert "确认可预约" not in message
```

Run:

```bash
cd backend
uv run pytest tests/unit/rag/test_grounded_answer.py tests/unit/procedures/test_kb_qa.py tests/unit/procedures/test_room_search.py -q
```

Expected:

```text
grounded answer, KB QA, and room safety tests pass
```

### Task 7: Eval Runner Checks

- [ ] In `backend/evals/runners/run_rag_eval.py`, add checks for:

```text
must_have_citations_for_high_risk
must_have_grounded_answer_flag
must_not_make_unverified_commitment
```

- [ ] Update `backend/evals/datasets/rag_retrieval_cases.yaml` high-risk cases to require citations.
