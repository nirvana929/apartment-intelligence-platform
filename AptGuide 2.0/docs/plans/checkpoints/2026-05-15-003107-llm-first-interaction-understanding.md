# Checkpoint: LLM-First Interaction Understanding

## Metadata

- Created at: 2026-05-15T00:31:07+08:00
- Task: LLM-first interaction understanding
- Status: complete
- Test status: 394 passed, 3 warnings

## Goal

Replace keyword-driven intent classification and query understanding with an LLM-first structured understanding layer. If the LLM is uncertain or invalid, ask the user to clarify instead of falling back to keyword matching.

## Context

The previous `HeuristicInteractionClassifier` and `understand_query()` used broad keyword lists that decided route/task/filters. This caused biased misrouting: `吗` pushed room queries into KB, room attributes oscillated between room and policy. The replacement makes the LLM the only NL understanding entrypoint.

## Completed Work

1. Extended `InteractionIntent` with `retrieval_queries` and `clarification_needed` fields
2. Created `interaction/validation.py` with `validate_or_clarify_intent()` — validates LLM output contract, converts invalid/low-confidence to clarification
3. Replaced `HeuristicInteractionClassifier` with `ClarifyingInteractionClassifier` (no-keyword fallback that always returns clarification)
4. `LLMInteractionClassifier` now returns clarification on exceptions, invalid JSON, low confidence, or validation failure — no keyword fallback
5. Changed default `intent_classifier_mode` from `"heuristic"` to `"llm"`
6. Updated `deps.py` to build `LLMInteractionClassifier` by default with `min_confidence` threshold
7. Replaced `understand_query()` with intent-only construction — no interaction_intent = clarification fallback
8. Added `domain` field to `QueryUnderstandingResult`
9. Updated `planning.py` to use `qr.domain` instead of `_infer_kb_module_intent()` keyword inference
10. Replaced LLM prompt with stricter schema-oriented prompt (forbids guessing, requires retrieval_queries)
11. Removed all keyword helpers from runtime: `_looks_like_room_search`, `_looks_like_kb_policy`, `_looks_like_policy_question`, `_infer_kb_domain`, `_detect_task`, `_extract_budget`, `_extract_district`, `_extract_payment`, `_extract_preferences`, `_extract_reference`, `_generate_retrieval_queries`
12. Added anti-regression source scan tests
13. Updated all tests (routing, orchestrator, appointment, handoff, e2e) to use StubClassifier

## Files Changed

- `backend/src/aptguide2/interaction/contracts.py` — added `retrieval_queries`, `clarification_needed`
- `backend/src/aptguide2/interaction/validation.py` — new: contract validation with clarification
- `backend/src/aptguide2/interaction/classifier.py` — replaced keyword classifier with ClarifyingInteractionClassifier + LLM-first; injects `raw_message` into LLM JSON before validation
- `backend/src/aptguide2/interaction/prompts.py` — stricter schema-oriented prompt
- `backend/src/aptguide2/core/config.py` — default `intent_classifier_mode = "llm"`
- `backend/src/aptguide2/api/deps.py` — LLM classifier by default
- `backend/src/aptguide2/rag/schemas.py` — added `domain` to `QueryUnderstandingResult`
- `backend/src/aptguide2/rag/query_understanding.py` — intent-only, no keyword extraction
- `backend/src/aptguide2/rag/planning.py` — uses `qr.domain` instead of keyword inference
- `backend/tests/unit/interaction/test_contracts.py` — new retrieval_queries/clarification tests
- `backend/tests/unit/interaction/test_validation.py` — new validation tests
- `backend/tests/unit/interaction/test_classifier.py` — rewritten for LLM-first behavior
- `backend/tests/unit/interaction/test_no_keyword_fallback.py` — new anti-regression scan
- `backend/tests/unit/rag/test_query_understanding.py` — rewritten for intent-only
- `backend/tests/unit/rag/test_planning.py` — rewritten for domain-based planning
- `backend/tests/unit/api/test_mainline_wiring.py` — added LLM classifier test
- `backend/tests/unit/harness/test_routing.py` — StubClassifier for all tests
- `backend/tests/unit/harness/test_orchestrator.py` — StubClassifier for all tests
- `backend/tests/unit/harness/modules/test_handoff.py` — StubClassifier for routing test
- `backend/tests/e2e/test_api.py` — StubClassifier for e2e tests
- `backend/tests/e2e/test_system_mainline.py` — clarify_only mode + StubClassifier

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
|---|---|---|---|---|
| 00:15 | `test_llm_classifier_failure_returns_clarification` failed: response_mode was `normal_answer` | `apply_policy_corrections` overwrites response_mode for clarification intents | Skip response_mode overwrite when action=clarify, but always apply refuse | resolved |
| 00:35 | Live eval: 100/120 cases returned clarification (route=fallback, action=clarify) | LLM JSON output lacks `raw_message` field, causing Pydantic `ValidationError` | Inject `raw_message` into parsed JSON before validation | resolved |

## Verification

| Command | Result | Evidence |
|---|---|---|
| `uv run pytest tests/unit/interaction -q` | 19 passed | 0.08s |
| `uv run pytest tests/unit/rag/test_query_understanding.py tests/unit/rag/test_planning.py -q` | 10 passed | 0.10s |
| `uv run pytest tests/unit/harness/test_routing.py tests/unit/harness/test_orchestrator.py tests/unit/harness/modules/test_handoff.py -q` | 24 passed | 0.21s |
| `uv run pytest tests/unit/api/test_mainline_wiring.py -q` | 9 passed, 1 warning | 3.64s |
| `uv run pytest tests/ -q` | 394 passed, 3 warnings | 3.28s |
| `uv run ruff check src/aptguide2/interaction/ src/aptguide2/rag/query_understanding.py src/aptguide2/rag/planning.py` | clean | no new errors |
| Live RAG v2 eval (post raw_message fix) | all gates FAIL | `../reports/rag-v2-llm-first-evaluation-report.md` |

### Live RAG v2 Eval Results (post raw_message fix)

| Metric | Value | Gate | Pass |
|---|---:|---:|---|
| KB source hit@3 | 71.4% | >= 90% | FAIL |
| KB source hit@5 | 74.3% | - | PASS |
| KB MRR | 0.626 | - | PASS |
| Room hit@5 | 8.6% | >= 85% | FAIL |
| Room MRR | 0.003 | - | PASS |
| High-risk fallback | 40.0% | >= 100% | FAIL |
| Unvalidated rooms | 0 | = 0 | PASS |

Improvement vs first run: 100/120 clarification → now only 15/120 clarification (route=fallback). The raw_message injection fix resolved the mass-clarification bug.

Remaining issues: room retrieval quality (seed IDs vs Milvus content mismatch), KB routing for appointment/lease/account queries, high-risk fallback coverage.

## Known Issues

- Ruff has 57 pre-existing errors (E402 import ordering in deps.py, I001 in tests) — not introduced by this work
- Langfuse public key provided; secret key still needed
- Room retrieval hit@5 = 8.6% — seed IDs vs Milvus content mismatch (known from before this task)
- KB hit@3 = 71.4% — appointment/lease/account queries routed to non-RAG routes, missing KB sources
- High-risk fallback = 40% — some high-risk queries not detected as fallback

## Next Steps

1. Investigate room retrieval quality (seed IDs vs Milvus content mismatch) — biggest gap
2. Fix KB routing: appointment/lease/account queries should reach KB retrieval instead of going to fallback
3. Improve high-risk fallback detection
4. Provide real Langfuse secret key to enable tracing
5. Staging deployment execution

## Outcome Notes

- All keyword-based runtime helpers removed from classifier and query understanding — the LLM is now the sole NL understanding layer
- Clarification-on-failure pattern: LLM errors, low confidence, invalid JSON, and validation failures all produce a clarification intent instead of guessing
- `apply_policy_corrections` preserves clarification response_mode while still applying refuse for safety
- Anti-regression scan tests guard against keyword helpers being reintroduced
