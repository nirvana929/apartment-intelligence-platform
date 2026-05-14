# Next Steps

## Immediate

1. RAG retrieval quality improvement (live eval shows 48.6% KB hit@3, 40% Room hit@5)
   - Optimize query understanding for more kb_qa recognition
   - Adjust confidence gate threshold
   - Fix room retrieval filter precision

## Later

2. Redis or durable context store plan
3. Rolling summary generation (LLM-based summary of recent_messages)
4. Long-term profile extraction from conversation history

## Completed

- Harness Foundation — 17 Python files, 147 tests
- Tool Registry Governance — 8 Python files, 206 tests
- Enterprise RAG v2 — 8 new RAG files, 246 tests (19 new + 227 baseline)
- Procedure-Tool Runtime Integration
- Memory Module MVP
- Appointment List MVP
- Handoff User-Initiated MVP
- Appointment confirmation flow correction
- Tool failure automatic handoff
- System integration — live dependency readiness, RAG v2 live eval, API contract expansion
- System feature completion and mainline integration — harness is the only product runtime

## Live Dependency Status

- Milvus: OK (localhost:19530, 126 rooms, 70 KB vectors)
- Embedding: OK (`text-embedding-v3`, dim=1024)
- Lease: OK (localhost:8081)

## Guardrails

- Old RAG MVP code may remain in the repository, but no API, harness procedure, or system e2e path should call it.
- Harness is the product runtime.
- RAG v2 is an internal harness module, not a separate public `/chat` mode.
- Do not mark feature `passes=true` without test evidence.
- `appointment.create` and `appointment.cancel` require two-turn confirmation with `confirmation_id`.
