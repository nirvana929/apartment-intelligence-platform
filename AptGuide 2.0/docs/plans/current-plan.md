# Current Plan

## Status: COMPLETED — LLM-First Interaction Understanding (2026-05-15)

## Last Completed Plan

LLM-First Interaction Understanding — `docs/plans/2026-05-15-aptguide2-llm-first-interaction-understanding-plan.md`

## Completion Evidence

- Checkpoint: `docs/plans/checkpoints/2026-05-15-003107-llm-first-interaction-understanding.md`
- Backend full verification: `uv run pytest tests/ -q` → 394 passed, 3 warnings
- Anti-regression scan: no keyword helpers in classifier.py or query_understanding.py
- Live RAG v2 eval: completed — all gates FAIL but significant improvement (100/120 → 15/120 clarification)

## Completed Outcome

The keyword-driven intent classification and query understanding has been completely replaced by an LLM-first structured understanding layer:

- `ClarifyingInteractionClassifier` replaces `HeuristicInteractionClassifier` — no keyword fallback
- `LLMInteractionClassifier` returns clarification on failure, not keyword guessing
- `understand_query()` is intent-only — no interaction_intent = clarification fallback
- `build_retrieval_plan()` uses LLM-provided domain, not keyword inference
- All keyword helpers removed from runtime
- Anti-regression scan tests guard against reintroduction

## Next Steps

1. Investigate room retrieval quality (seed IDs vs Milvus content) — biggest gap: hit@5 = 8.6%
2. Fix KB routing for appointment/lease/account queries (currently going to fallback)
3. Improve high-risk fallback detection (40% → 100%)
4. Provide Langfuse secret key
5. Staging deployment execution

## Guardrails

- Old RAG path cleanup is already complete; keep the source scan as a regression guard.
- Do not change eval cases merely to improve metrics.
- Keep deterministic safety, auth, write confirmation, and lease validation.
- Clarification-on-failure is the new pattern — never fall back to keyword guessing.
