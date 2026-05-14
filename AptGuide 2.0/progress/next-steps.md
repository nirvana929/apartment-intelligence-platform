# Next Steps

## Immediate

1. LLM-first interaction understanding replacement
   - Execute `docs/plans/2026-05-15-aptguide2-llm-first-interaction-understanding-plan.md`.
   - Make LLM structured output the default and only natural-language understanding path.
   - Convert LLM failure, invalid JSON, low confidence, and contradictory intent into `fallback.clarify`.
   - Remove keyword route helpers from `interaction/classifier.py`.
   - Remove keyword task/filter/preference extraction from the RAG runtime path in `rag/query_understanding.py`.
   - Add anti-regression source scans so keyword fallback cannot silently return.
   - Preserve deterministic safety, pending-action routing, write confirmation, ToolRuntime permissions, and lease validation.

2. RAG retrieval quality optimization after LLM-first understanding
   - Re-run live RAG v2 eval with LLM credentials configured.
   - Improve Room hit@5 from 10.0% to >= 85%.
   - Restore High-risk fallback from 40.0% to 100%.
   - Preserve KB source hit@3 >= 90% and unvalidated room count at 0.

3. Staging deployment execution
   - Deploy Redis + MySQL schema (`persistence/schema.sql`) to staging.
   - Configure `AUTH_MODE=lease_token` for production auth.
   - Build frontend for production (`npm run build` + nginx).
   - End-to-end integration test with live lease backend.

## Later

4. Full platform integration
   - Integrate through `rentHouseH5`.
   - Align `lease /app/ai/chat` proxy path and schema.
   - Reuse platform login/token flow.

5. Production customer-service integration
   - Replace local operator console with a production service or workflow.

## Completed

1. Harness Foundation — 17 Python files, 147 tests
2. Tool Registry Governance — 8 Python files, 206 tests
3. Enterprise RAG v2 — 8 new RAG files, 246 tests
4. Procedure-Tool Runtime Integration
5. Memory Module MVP
6. Appointment List MVP
7. Handoff User-Initiated MVP
8. Appointment confirmation flow correction
9. Tool failure automatic handoff
10. System integration — live dependency readiness, RAG v2 live eval, API contract expansion
11. System feature completion and mainline integration — harness is the only product runtime
12. Standalone productization — auth, Redis+MySQL persistence, memory, handoff, operator API, Vue 3 frontend
13. Risk-aware Query Understanding Guardrail — 53-case eval, 100% risk metrics
14. RAG v2 Full Replacement — old RAG removed, v2-native KB/room retrieval
15. Standalone Hardening and Observability — 386 backend + 5 frontend tests
16. Semantic Interaction Routing — unified intent layer, entity resolution, heuristic+LLM classifier, 8-case eval 100%, 402 backend tests
17. LLM-first Interaction Understanding Plan — architecture decision and implementation plan completed; code implementation not yet started

## Guardrails

- Old RAG has been fully removed; old-path cleanup is already done. Keep source scan as a regression guard.
- Semantic Interaction Routing is complete, but keyword fallback is no longer acceptable for natural-language understanding.
- Do not mark feature complete without test/eval evidence.
- Do not change RAG eval cases merely to improve metrics.
- `appointment.create` and `appointment.cancel` require two-turn confirmation with `confirmation_id`.
- In formal auth mode, derive `user_id` from lease token instead of trusting frontend input.
