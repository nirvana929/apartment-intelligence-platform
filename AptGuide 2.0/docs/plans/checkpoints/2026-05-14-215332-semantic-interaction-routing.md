# Checkpoint: semantic-interaction-routing

## Metadata

- Created at: 2026-05-14T21:53:32+08:00
- Task: semantic-interaction-routing
- Status: completed
- Test status: passed

## Goal

Replace keyword-primary Harness/RAG dual-layer task classification with a unified Semantic Interaction Routing layer. The new layer uses structured LLM classification when enabled, deterministic safety and business guardrails where required, and a heuristic fallback for tests/offline development.

## Context

Plan: `docs/plans/2026-05-14-aptguide2-semantic-interaction-routing-agent-plan.md`
Previous state: 386 backend tests + 5 frontend tests (standalone hardening complete)

## Completed Work

- Task 1: Interaction contracts — InteractionIntent, EntityMention, RouteName, DomainName, ActionName literals
- Task 2: Entity resolution — area alias normalization (7 aliases), budget regex, payment alias extraction, hard/soft filter policy
- Task 3: Heuristic + LLM classifier — HeuristicInteractionClassifier, LLMInteractionClassifier, apply_policy_corrections, config flags
- Task 4: Harness routing rewrite — HybridRouter uses InteractionClassifier, SafetyBoundary + pending_action preserved
- Task 5: RAG intent passthrough — understand_query accepts interaction_intent, pipeline_v2 passes it, RagV2Procedure extracts from decision.metadata
- Task 6: Appointment semantic entities — _get_intent/_extract_room_id_from_intent, tries intent entities before regex, confirmation still required
- Task 7: Eval dataset + runner — 8 cases, run_interaction_intent_eval.py, 100% exact match
- Task 8: Docs sync — verification-log.md, next-steps.md updated

## Files Changed

**Created:**
- `backend/src/aptguide2/interaction/__init__.py`
- `backend/src/aptguide2/interaction/contracts.py`
- `backend/src/aptguide2/interaction/entity_resolution.py`
- `backend/src/aptguide2/interaction/classifier.py`
- `backend/src/aptguide2/interaction/prompts.py`
- `backend/tests/unit/interaction/__init__.py`
- `backend/tests/unit/interaction/test_contracts.py`
- `backend/tests/unit/interaction/test_entity_resolution.py`
- `backend/tests/unit/interaction/test_classifier.py`
- `backend/evals/datasets/interaction_intent_cases.yaml`
- `backend/evals/runners/run_interaction_intent_eval.py`
- `backend/tests/unit/evals/test_run_interaction_intent_eval.py`

**Modified:**
- `backend/src/aptguide2/core/config.py` — added intent_classifier_mode, intent_classifier_timeout_seconds, intent_classifier_min_confidence
- `backend/src/aptguide2/harness/contracts.py` — RouteDecision gains metadata field
- `backend/src/aptguide2/harness/routing.py` — HybridRouter rewritten to use InteractionClassifier
- `backend/src/aptguide2/api/deps.py` — get_interaction_classifier(), memory.workflow registration
- `backend/src/aptguide2/rag/query_understanding.py` — accepts interaction_intent, merges hard_filters/soft_preferences
- `backend/src/aptguide2/rag/pipeline_v2.py` — accepts interaction_intent, passes to understand_query
- `backend/src/aptguide2/harness/modules/rag/v2.py` — extracts InteractionIntent from decision.metadata
- `backend/src/aptguide2/harness/modules/appointment.py` — _get_intent/_extract_room_id_from_intent, intent-first entity extraction
- `backend/tests/unit/harness/test_routing.py` — added StubClassifier + 2 semantic routing tests
- `backend/tests/unit/rag/test_query_understanding.py` — added interaction_intent passthrough test
- `backend/tests/unit/harness/modules/test_appointment.py` — added semantic appointment test
- `docs/tests/verification-log.md` — Semantic Interaction Routing entry
- `docs/plans/next-steps.md` — updated completed list

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| — | test_unknown_area_stays_soft_preference_not_hard_filter: "彩虹桥附近找房" added full message as soft pref | entity_resolution.py added full message instead of area+附近 | Fixed to extract `message[:near_idx]` | resolved |
| — | SyntaxError: invalid character '"' (U+201C) in query_understanding.py | Smart quotes (U+201C/U+201D) replaced triple-quote docstring delimiters | Replaced all smart quotes with ASCII equivalents | resolved |
| — | intent-kb-002 eval case failed: "房间空调坏了找谁修" → room_search | "房间" keyword triggered room search before kb policy check | Moved kb policy check before room search in classifier | resolved |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `uv run pytest tests/unit/interaction -q` | 9 passed | All interaction unit tests green |
| `uv run pytest tests/unit/harness/test_routing.py tests/unit/rag/test_query_understanding.py tests/unit/harness/modules/test_rag_v2.py -q` | 40 passed | Routing/RAG focused tests green |
| `uv run pytest tests/unit/harness/modules/test_appointment.py -q` | 22 passed | Appointment tests green |
| `uv run pytest tests/unit/evals/test_run_interaction_intent_eval.py -q` | 3 passed | Eval tests green |
| `uv run python -m evals.runners.run_interaction_intent_eval --cases evals/datasets/interaction_intent_cases.yaml` | total=8, exact=8, exact_rate=1.0 | 100% exact match |
| `uv run pytest tests/ -q` | 402 passed, 3 warnings | Full backend tests green |
| `rg -n "legacy RAG patterns" src tests evals` | No matches | Legacy source scan clean |

## Known Issues

- 3 pre-existing RuntimeWarning about unawaited coroutines in lease_tools.py (not introduced by this work)
- 15 pre-existing E402 lint issues (not introduced by this work)
- Pylance type warning: `_detect_task()` returns `str` but `QueryUnderstandingResult.task` expects Literal (pre-existing, not a runtime issue)

## Next Steps

- RAG retrieval quality improvement: KB hit@3 target >= 90% (current 48.6%), Room hit@5 target >= 85% (current 40%)
- Staging deployment execution

## Outcome Notes

- 8 tasks completed in sequence (TDD approach)
- New interaction package: 5 source files, 3 test files
- Unified intent layer replaces dual keyword routing (harness/routing.py + rag/query_understanding.py)
- SafetyBoundary, pending_action, lease validation, and appointment confirmation all preserved
- Heuristic fallback ensures tests run without live LLM
- Total test count: 402 backend (was 386, +16 new tests)
