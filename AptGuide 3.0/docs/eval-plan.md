# Evaluation Plan

## Completed Gates

### Gate 1: Understanding Contract Tests — PASSED (M0)

- Valid room search output passes.
- Valid KB QA output passes.
- Ambiguous output becomes clarification.
- Invalid JSON becomes clarification.
- Low confidence becomes clarification.
- Keyword fallback source scan passes (anti-regression guardrail).

### Gate 2: Procedure Routing Tests — PASSED (M0/M3)

- Each route dispatches to the expected procedure.
- Non-RAG routes keep retrieval off.
- Pending action has priority over new LLM interpretation.
- All 7 procedures wired and tested (129 tests at M3).

### Gate 3: API Smoke Tests — PASSED (M0/M3)

- `/health` returns service status.
- `/chat` returns a typed response for clarification.
- `/chat` returns a typed response for stubbed room search.
- `/ready` returns readiness checks (config-based + live probes with `?live=true`).

### Gate 4: Live Dependency Verification — PASSED (M2/M5)

- Live MySQL: schema applied, repos tested (6 passed).
- Live Redis: state store tested (4 passed).
- Live LLM: understanding call tested (1 passed).
- Live embedding: vectorization tested (1 passed).
- Live Milvus: vector search tested (1 passed).
- Live internal-header auth: 6 passed.
- Live chat persistence: 8 passed.

### Gate 5: RAG Pipeline — PASSED (M4/M5)

- Room retrieval: multi-query vector recall + lease validation (207 tests at M4).
- Room ranking: 5-dimension weighted scoring tested.
- KB retrieval: multi-query recall + dedup tested.
- KB reranking: module-weighted reranking tested.
- Confidence gates: risk-level thresholds tested.
- Eval metrics: hit@k, MRR, nDCG (21 tests).
- Live RAG integration: 5/5 passed.

### Gate 6: Frontend E2E — PASSED (M5)

- Playwright: page load, chat render, network assertion (3 passed).
- Business scenario routing: greeting, room search, KB QA route correctly.

### Gate 7: Diagnostics — PASSED (M6)

- Understanding diagnostics: raw LLM JSON, parsed fields, validator reason.
- Rec diagnostics: vector recall, lease validation, ranking, confidence gate counts.
- Eval report integration: per-case diagnostic fields rendered.
- 22 diagnostic tests passed.

## Active Gate

### Gate 8: Live RAG Evaluation with Vectors — IN PROGRESS

- 4 seed eval cases correctly route through RAG pipeline.
- Room search: failure_stage=vector_recall_empty (Milvus data missing).
- KB QA: failure_stage=kb_vector_recall_empty (chunk_id metadata missing).
- Requires: sync room/KB vectors to Milvus, re-run eval.

## Later Gates

- RAG quality optimization after diagnostic baseline review.
- Full `rentHouseH5 -> lease -> AptGuide 3.0` chain testing.
- Production hardening: retry, idempotency, rate limiting, metrics, alerting.
