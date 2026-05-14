# Checkpoint: RAG v2 Diagnostic-First Retrieval Optimization - Final

## Metadata

- Created at: 2026-05-14T23:27:48+08:00
- Task: RAG v2 diagnostic-first retrieval optimization
- Status: partial — KB gate passed, Room and High-risk gates not met
- Test status: 407 passed, 3 warnings

## Goal

Raise live RAG v2 quality to: KB hit@3 >= 90%, Room hit@5 >= 85%, High-risk fallback = 100%, Unvalidated rooms = 0.

## Context

Eval cases expanded from 50 to 120, exposing classifier keyword gaps. Diagnostic metadata was threaded through the entire pipeline for failure attribution. Langfuse observability was integrated mid-sprint.

## Completed Work

1. Diagnostic metadata threading: eval → pipeline → kb_v2/room_v2 (diagnostics dict at each layer)
2. Interaction intent eval: 8/8 = 100%
3. Unit tests: 407 passed
4. Langfuse integration: drop-in OpenAI SDK replacement in deps.py
5. Classifier improvements: expanded question_words, room keywords, district names, domain topics
6. KB hit@3 improved from 57.1% → 94.3% (PASS)

## Final Eval Results (120 cases)

| Metric | Value | Gate | Pass |
|---|---:|---:|---|
| KB source hit@3 | 94.3% | >= 90% | PASS |
| KB source hit@5 | 94.3% | - | PASS |
| KB MRR | 0.848 | - | PASS |
| KB NDCG@5 | 0.872 | - | PASS |
| Room hit@5 | 10.0% | >= 85% | FAIL |
| Room MRR | 0.010 | - | PASS |
| Room NDCG@5 | 0.007 | - | PASS |
| High-risk fallback | 40.0% | >= 100% | FAIL |
| Unvalidated rooms | 0 | = 0 | PASS |

## Files Changed

- `backend/src/aptguide2/interaction/classifier.py` — expanded keywords
- `backend/src/aptguide2/rag/kb_v2.py` — diagnostics parameter
- `backend/src/aptguide2/rag/room_v2.py` — diagnostics parameter
- `backend/src/aptguide2/rag/pipeline_v2.py` — diagnostics threading
- `backend/src/aptguide2/core/config.py` — Langfuse config fields
- `backend/src/aptguide2/api/deps.py` — Langfuse OpenAI integration
- `backend/evals/runners/run_rag_v2.py` — intent injection, diagnostic metadata
- `backend/tests/` — new eval and diagnostic tests
- `backend/.env` / `.env.example` — Langfuse env vars

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
|---|---|---|---|---|
| 23:02 | Room queries → fallback (out_of_scope) | Missing room attribute keywords (采光/阳台/独卫/etc) | Added keywords to _looks_like_room_search | partial |
| 23:12 | Room queries → kb_qa | "吗" in question_markers catches room queries | Trade-off: keep "吗" for KB gain, accept room regression | accepted |
| 23:19 | KB hit@3 dropped to 71.4% | Removed "吗" broke KB classification | Re-added "吗" | resolved |

## Verification

| Command | Result | Evidence |
|---|---|---|
| `uv run pytest tests/ -q` | 407 passed, 3 warnings | 2.87s |
| `run_interaction_intent_eval` | 8/8 = 100% | exact_rate=1.0 |
| `run_rag_v2 --cases ... --report ...` | KB hit@3=94.3%, Room hit@5=10.0% | report at reports/rag-v2-live-evaluation-report.md |

## Known Issues

- Room hit@5 = 10.0% (gate 85%): 63/70 room cases fail. Mix of classifier misroutes and retrieval quality.
- High-risk fallback = 40.0% (gate 100%): risk detection patterns incomplete.
- Langfuse keys are placeholders (pk-lf-.../sk-lf-...) — 401 errors on export, does not affect eval.

## Next Steps

1. Replace keyword classifier with LLM-based classifier (LLMInteractionClassifier already scaffolded)
2. Investigate room retrieval quality: seed room IDs vs Milvus content mismatch
3. Expand high-risk detection patterns
4. Provide real Langfuse keys to enable tracing

## Outcome Notes

- KB retrieval achieved 94.3% hit@3, exceeding the 90% gate — diagnostic-first approach proved effective for debugging intent misroutes.
- Keyword-based classifier is the primary bottleneck for room and fallback metrics. LLM classifier is the recommended next step.
- Diagnostic metadata threading enables rapid failure attribution: each failed case shows exact route, task, domain, action, and retrieval queries.
