# Next Steps

## Completed

1. Harness Foundation — 17 Python files, 147 tests
2. Tool Registry Governance — 8 Python files, 206 tests
3. Enterprise RAG v2 — 8 new RAG files, 246 tests (19 new + 227 baseline)
4. Procedure-Tool Runtime Integration — tool_runtime parameter threading, backward compatible
5. Memory Module MVP — MemoryManager + orchestrator integration exists
6. Appointment List MVP — appointment.list_mine path exists
7. Handoff User-Initiated MVP — handoff.user_initiated path exists
8. Appointment confirmation flow correction — two-turn pending-action workflow
9. Tool failure automatic handoff — orchestrator triggers handoff.tool_failure after 2 consecutive failures
10. System integration — live dependency readiness, RAG v2 live eval, API contract expansion
11. System feature completion and mainline integration — harness is the only product runtime, legacy RAG disconnected
   - 323 tests all passing (308 unit + 15 e2e)
   - ruff clean
   - `/chat` only enters harness mainline
   - RAG v2 mounted as internal harness module
   - `appointment.cancel` uses two-turn confirmation
   - `ChatResponse.cards` is first-class
   - readiness includes pipeline version check

## Immediate

12. RAG retrieval quality improvement (live eval shows 48.6% KB hit@3, 40% Room hit@5)
   - Create a focused RAG retrieval quality tuning plan
   - Add per-case diagnostic trace for failed live eval cases
   - Fix KB no-source cases in PAY, LIFE, APPT, and LEASE categories
   - Improve KB hybrid retrieval / rerank so expected docs enter top-3/top-5
   - Fix room retrieval filter precision and room ranking failures
   - Preserve high-risk fallback at 100% and unvalidated room count at 0

## Live Dependency Status

- Milvus: OK (localhost:19530, 126 rooms, 70 KB vectors)
- Embedding: OK (`text-embedding-v3`, dim=1024)
- Lease: OK (localhost:8081)

## Later

13. Redis or durable context store plan
14. Rolling summary generation (LLM-based summary of recent_messages)
15. Long-term profile extraction from conversation history

## Current Guardrails

- Old RAG MVP code may remain in the repository, but no API, harness procedure, or system e2e path should call it.
- Harness is the product runtime.
- RAG v2 is an internal harness module, not a separate public `/chat` mode.
- Do not mark feature `passes=true` without test evidence.
- `appointment.create` and `appointment.cancel` require two-turn confirmation with `confirmation_id`.
