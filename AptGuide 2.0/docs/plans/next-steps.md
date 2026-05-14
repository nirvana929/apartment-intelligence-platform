# Next Steps

## Immediate

1. RAG retrieval quality optimization
   - Plan: `docs/plans/2026-05-14-aptguide2-rag-diagnostic-first-retrieval-optimization-plan.md`
   - First prove the eval runner injects `InteractionIntent` and measures the post-Semantic Interaction Routing path.
   - Re-run live RAG v2 eval after that measurement check.
   - Add per-case diagnostic trace for failed live eval cases before changing retrieval logic.
   - Improve KB hit@3 from 71.4% to >= 90%.
   - Improve Room hit@5 from 8.6% to >= 85%.
   - Improve high-risk fallback from 40% to 100%.
   - Preserve unvalidated room count at 0.

2. Staging deployment execution
   - Deploy Redis + MySQL schema (`persistence/schema.sql`) to staging.
   - Configure `AUTH_MODE=lease_token` for production auth.
   - Build frontend for production (`npm run build` + nginx).
   - End-to-end integration test with live lease backend.

## Later

3. Full platform integration
   - Integrate through `rentHouseH5`.
   - Align `lease /app/ai/chat` proxy path and schema.
   - Reuse platform login/token flow.

4. Production customer-service integration
   - Replace local operator console with a production service or workflow.

## Completed

- Harness Foundation - 17 Python files, 147 tests
- Tool Registry Governance - 8 Python files, 206 tests
- Enterprise RAG v2 - 8 new RAG files, 246 tests (19 new + 227 baseline)
- Procedure-Tool Runtime Integration
- Memory Module MVP
- Appointment List MVP
- Handoff User-Initiated MVP
- Appointment confirmation flow correction
- Tool failure automatic handoff
- System integration - live dependency readiness, RAG v2 live eval, API contract expansion
- System feature completion and mainline integration - harness is the only product runtime
- Standalone productization - auth, Redis+MySQL persistence, memory, handoff, operator API, Vue 3 frontend (365+2 tests)
- Risk-aware Query Understanding Guardrail - rule signals, semantic classifier, policy matrix, response-mode routing, 53-case eval (389 tests, risk eval 100%)
- RAG v2 Full Replacement - old RAG completely removed, v2-native kb_v2/room_v2 modules, 16 guard tests, source scan clean (376 tests)
- Standalone Hardening and Observability - deployment config, /ready endpoint, security hardening, structured events, frontend UX hardening (386+5 tests)
- Semantic Interaction Routing - unified intent layer replaces keyword-primary routing, entity resolution, heuristic+LLM classifier, 8-case eval 100% (402 tests)

## Live Dependency Status

- Milvus: OK (localhost:19530, 126 rooms, 70 KB vectors)
- Embedding: OK (`text-embedding-v3`, dim=1024)
- Lease: OK (localhost:8081)

## Guardrails

- Old RAG has been fully removed; old-path cleanup is already done. Guard tests and source scan prevent reintroduction.
- Harness is the product runtime.
- RAG v2 is the only active RAG implementation (`kb_v2.py` + `room_v2.py` + `pipeline_v2.py`).
- Semantic Interaction Routing is complete; keep keyword logic as fallback, safety, or hard-constraint extraction only.
- Do not mark feature `passes=true` without test evidence.
- `appointment.create` and `appointment.cancel` require two-turn confirmation with `confirmation_id`.
- In formal auth mode, derive `user_id` from lease token instead of trusting frontend input.
- Do not change RAG eval cases merely to improve metrics.
- Risk guardrail work should treat `risk_level` as routing metadata, not automatic blocking; use `response_mode` to avoid false block regressions.
