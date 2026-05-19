# Checkpoint: RAG evidence trace eval roadmap complete

## Metadata

- Created at: 2026-05-16T00:14:45+08:00
- Task: RAG evidence trace eval roadmap complete
- Status: complete
- Test status: 347 passed, 1 pre-existing failure, ruff clean

## Goal

Complete the 6-plan RAG evidence/trace/evaluation roadmap for AptGuide 3.0: establish data evidence contracts, preserve room identity mapping, align wechat-to-lease IDs, implement grounded risk answers, add LangSmith final-output tracing, and build comprehensive RAG evaluation.

## Context

Starting from Milestone 6 (LangSmith tracing + understanding diagnostics), the roadmap addressed production blockers: synthetic hash IDs replacing real wechat_room_id, no lease validation path, no grounded answer generation, and no comprehensive eval gate.

## Completed Work

1. **Data Evidence Contract** (Plan 1) — evidence levels defined, 32 tests, key finding: wechat-to-lease ID path missing
2. **LangSmith Chat Output Tracing** (Plan 4) — LangSmithChatRecorder wired into ChatService, 3 tests
3. **Room Identity Map Prerequisite** — RoomIdentity model, repository, 7 source identity fields preserved in vector_client, 11 tests
4. **Room Lease ID Alignment** (Plan 2) — lease validation for verified identities, evidence fields in room cards, 180 RAG+procedure tests
5. **Grounded Risk Answer** (Plan 3) — grounded_answer.py with citations, risk language disclaimers, 174 RAG+procedure tests
6. **Comprehensive RAG Evaluation** (Plan 5) — schema validation, strengthened criteria, 12 failure owner categories, 44 tests

## Files Changed

**New files (15+):**
- `docs/system/evidence-contract.md`
- `docs/system/data-inventory/room-id-alignment.md`
- `backend/src/aptguide3/rag/room_identity.py`
- `backend/src/aptguide3/rag/grounded_answer.py`
- `backend/src/aptguide3/persistence/room_identity_repo.py`
- `backend/src/aptguide3/observability/langsmith_trace.py`
- `backend/scripts/inspect_room_identity_sources.py`
- `backend/tests/unit/rag/test_evidence_contract.py`
- `backend/tests/unit/rag/test_room_identity.py`
- `backend/tests/unit/rag/test_grounded_answer.py`
- `backend/tests/unit/persistence/test_room_identity_repo.py`
- `backend/tests/unit/observability/test_langsmith_chat_trace.py`
- `backend/tests/unit/evals/test_rag_eval_runner.py`

**Modified files (10+):**
- `backend/src/aptguide3/integrations/vector_client.py` — preserves 7 identity fields
- `backend/src/aptguide3/rag/room_retrieval.py` — identity-aware lease validation
- `backend/src/aptguide3/rag/room_ranking.py` — evidence field passthrough
- `backend/src/aptguide3/rag/diagnostics.py` — identity + lease diagnostic counters
- `backend/src/aptguide3/procedures/room_search.py` — evidence fields, risk language
- `backend/src/aptguide3/procedures/kb_qa.py` — grounded answer wiring
- `backend/src/aptguide3/application/chat_service.py` — LangSmith recorder
- `backend/src/aptguide3/api/deps.py` — recorder + identity repo wiring
- `backend/evals/runners/run_rag_eval.py` — schema validation, criteria, failure owners

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| 2026-05-16 | 7 ruff errors | Import sorting + unused imports from agent changes | `ruff --fix` + noqa for E402 (sys.path insert pattern) | fixed |
| 2026-05-16 | test_persistence_mode_default_is_memory failure | Pre-existing env var override | Not related to this roadmap | deferred |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `uv run pytest tests/unit/ -q --ignore=tests/unit/scripts/` | 347 passed, 1 failed (pre-existing) | 12.63s |
| `uv run ruff check src tests` | All checks passed | Clean |

## Known Issues

- `test_persistence_mode_default_is_memory` pre-existing failure (env var override)
- `tests/unit/scripts/test_generate_data_inventory.py` collection error (ModuleNotFoundError: scripts)
- No live Milvus/MySQL/lease verification of the new identity mapping pipeline

## Next Steps

1. Run live RAG evaluation with `uv run python evals/runners/run_rag_eval.py --live`
2. Populate RoomIdentityRepository with actual wechat-to-lease mappings
3. Wire `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat` integration
4. Production hardening: retry, idempotency, rate limiting, metrics

## Outcome Notes

The roadmap transformed AptGuide 3.0 from "demo works but evidence is unverifiable" to a system with:
- Formal evidence contracts (5 evidence levels)
- Preserved source identity through the full pipeline
- Lease validation gated on verified business IDs
- Grounded answers with citations for medium/high-risk queries
- LangSmith final-output tracing
- Comprehensive eval with 12 failure owner categories
- 347 unit tests covering all new modules
