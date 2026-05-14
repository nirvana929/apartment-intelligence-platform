# Current Plan

## Active Objective

LLM-first interaction understanding replacement.

Targets:

- LLM is the only natural-language understanding entrypoint for route, RAG task, domain, filters, preferences, risk posture, and retrieval queries.
- LLM failure, invalid JSON, low confidence, or contradictory output routes to `fallback.clarify`.
- Keyword classifiers and keyword query extractors are removed from the production runtime path.
- Deterministic safety, pending-action routing, schema validation, permission checks, write confirmation, ToolRuntime governance, and lease validation remain intact.

## Active Plan

`docs/plans/2026-05-15-aptguide2-llm-first-interaction-understanding-plan.md`

## Last Completed Plan

`docs/plans/2026-05-14-aptguide2-rag-diagnostic-first-retrieval-optimization-plan.md` — partial: KB gate passed, room and high-risk gates not met.

## Completion Evidence

- Checkpoint: `docs/plans/checkpoints/2026-05-14-215332-semantic-interaction-routing.md`
- Backend full verification: 402 passed, 3 warnings
- Interaction intent eval: total=8, exact=8, exact_rate=1.0
- Legacy RAG source scan: no legacy runtime matches

## Current State

- `/chat` enters `AptGuideHarness` by default.
- Latest RAG v2 diagnostic eval: KB source hit@3=94.3% PASS, Room hit@5=10.0% FAIL, High-risk fallback=40.0% FAIL, Unvalidated rooms=0 PASS.
- The previous keyword-based classifier changes are now considered an architectural liability, not the path forward.
- The agreed design is LLM-first structured understanding with clarification on uncertainty and no keyword fallback.
- Implementation plan is complete; production code has not yet been changed for this new LLM-first architecture.

## Current Guardrails

- Do not reintroduce old RAG runtime paths; scan for them during final verification.
- Do not change eval cases merely to improve metrics.
- Keep deterministic safety, auth, write confirmation, and lease validation.
- Do not use keyword matching as fallback for natural-language route/task/filter/preference inference.
- Treat LLM output as structured intent, not business fact authority.
