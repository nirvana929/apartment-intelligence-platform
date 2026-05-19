# AptGuide 3.0 Comprehensive RAG Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full evaluation gate for AptGuide 3.0 RAG covering retrieval quality, business validation, grounded answer quality, risk safety, trace completeness, and latency.

**Architecture:** Extend the existing eval runner instead of introducing a new framework. Keep smoke mode for local checks and live mode for full-system validation. Reports must separate data gaps from model/retrieval/product defects.

**Tech Stack:** Python, YAML eval datasets, pytest, existing eval metrics, LangSmith, Milvus, lease API.

---

## Files

- Modify: `backend/evals/datasets/rag_retrieval_cases.yaml`
- Modify: `backend/evals/runners/run_rag_eval.py`
- Modify: `backend/evals/reports/rag-evaluation-report.md`
- Modify: `backend/src/aptguide3/rag/eval_metrics.py`
- Create: `backend/tests/unit/evals/test_rag_eval_runner.py`
- Modify: `docs/eval-plan.md`
- Modify: `docs/tests/evaluation-report.md`

## Prerequisites

This plan is blocked until the Room Identity Map prerequisite plan is complete and `RoomIdentityRepository` is available. Comprehensive room evaluation cannot score `lease_validation_pass_rate`, `invalid_room_rate`, or production-grade room correctness without verified identity mapping. When `RoomIdentityRepository` is available, room eval cases must check that returned room cards carry `mapped_verified` evidence level before counting them as valid lease-validated results.

## Required Metrics

Understanding:

```text
route_accuracy
task_accuracy
hard_filter_extraction_accuracy
risk_classification_accuracy
clarification_overtrigger_rate
```

Room retrieval:

```text
Hit@K
Recall@K
MRR
nDCG@K
hard_filter_pass_rate
lease_validation_pass_rate
invalid_room_rate
room_id_alignment_gap_count
```

KB QA:

```text
Source Hit@K
citation_rate
grounded_answer_rate
faithfulness_review_status
high_risk_caution_pass_rate
unverified_commitment_rate
```

System:

```text
success_rate
error_rate
timeout_rate
p50_latency_ms
p95_latency_ms
empty_recall_rate
fallback_rate
trace_output_visibility_rate
```

## Dataset Expansion

Minimum live dataset before full evaluation:

```text
room_search: 30 cases
kb_qa: 30 cases
appointment: 10 cases
lease: 10 cases
memory: 10 cases
handoff: 10 cases
```

Room cases must include expected conditions:

```text
expected.district_name
expected.max_rent
expected.min_rent when relevant
expected.must_validate_with_lease=true
expected.must_not_return_unvalidated_vector_room=true
expected.allowed_room_ids when available
```

KB cases must include:

```text
expected_doc_ids
risk_level
expected.must_cite_source
expected.must_have_grounded_answer
expected.must_not_make_unverified_commitment
```

## Tasks

### Task 1: Add Eval Schema Validation

- [ ] Add a schema validation function in `run_rag_eval.py`.
- [ ] Reject cases missing `id`, `task`, `query`.
- [ ] For high-risk KB cases, reject missing `expected_doc_ids`.
- [ ] For production room eval, reject missing lease validation expectation.

### Task 2: Strengthen Room Criteria

- [ ] Update `_check_criteria` so `must_validate_with_lease` checks card metadata:

```text
lease_validation_status == passed
evidence_level in {lease_validated, lease_validated_with_freshness, mapped_verified}
lease_room_id exists
identity_mapping_status == verified (from RoomIdentityRepository)
```

- [ ] Count cards that lack these fields as unvalidated.
- [ ] If room results have only synthetic IDs and no verified identity mapping, classify the failure as `identity_mapping` (not `lease_validation`).

### Task 3: Strengthen KB Criteria

- [ ] Add checks:

```text
must_have_citations_for_high_risk
must_have_grounded_answer
must_have_source_cards
must_not_make_unverified_commitment
```

- [ ] Validate citations against returned source cards.

### Task 4: Add Trace Completeness Check

- [ ] If LangSmith tracing is enabled, record whether the response metadata includes a trace/run identifier.
- [ ] Add `trace_output_visibility_rate` to the report.
- [ ] If direct LangSmith API inspection is unavailable, mark this metric as `local-output-recorded` based on recorder invocation tests, not as remotely verified.

### Task 5: Add Failure Owner Classification

Classify each failed case into exactly one primary owner:

```text
understanding
entity_resolution
data_alignment
vector_recall
identity_mapping
lease_validation
ranking
confidence_gate
grounded_answer
trace_visibility
dataset_gap
runtime_error
```

`identity_mapping` is used when room results carry only synthetic IDs with no verified business identity. This is distinct from `lease_validation` (which assumes a valid business ID was provided but the lease API rejected it) and `data_alignment` (which is for broader data pipeline issues).

### Task 6: Unit Tests

Add tests in `backend/tests/unit/evals/test_rag_eval_runner.py`:

```python
def test_high_risk_kb_case_requires_expected_doc_ids():
    case = {"id": "kb-risk-1", "task": "kb_qa", "query": "押金不退怎么办", "risk_level": "high"}
    errors = validate_eval_case(case)
    assert "expected_doc_ids" in errors

def test_room_validation_criteria_rejects_vector_only_card():
    response = SimpleNamespace(
        cards=[{"type": "room_card", "room_id": 1, "evidence_level": "vector_only"}],
        metadata={},
        message="",
    )
    case = {"expected": {"must_validate_with_lease": True}}
    result = _check_criteria(response, case)
    assert result["must_validate_with_lease"]["pass"] is False

def test_citations_must_match_source_cards():
    cards = [{"type": "kb_source", "doc_id": "KB-LS-011", "chunk_id": "KB-LS-011"}]
    citations = [{"doc_id": "KB-LS-011", "chunk_id": "KB-LS-011"}]
    assert citations_match_source_cards(citations, cards) is True

def test_failure_owner_is_single_value():
    result = classify_failure_owner({"failure_stage": "lease_validation_empty"})
    assert result == "lease_validation"
```

Run:

```bash
cd backend
uv run pytest tests/unit/evals/test_rag_eval_runner.py tests/unit/rag/test_eval_metrics.py -q
```

Expected:

```text
eval schema, criteria, and metric tests pass
```

### Task 7: Full Eval Run

Run:

```bash
cd backend
uv run python evals/runners/run_rag_eval.py --live
```

Minimum acceptance for full RAG gate:

```text
success_rate >= 95%
high_risk_citation_rate = 100%
high_risk_unverified_commitment_rate = 0%
room invalid_room_rate = 0%
room lease_validation_pass_rate = 100% for returned production room cards
trace_output_visibility_rate = 100% in local recorder tests
p95_latency_ms recorded and reviewed
```
