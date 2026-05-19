# Feature List

| Feature | Status | Notes |
| --- | --- | --- |
| LLM-first structured understanding | completed | No keyword fallback. LLM structured output only; uncertainty becomes clarification. |
| Typed procedure runtime | completed | 7 procedures: clarify, room_search, kb_qa, appointment, lease, memory, handoff. |
| Independent backend backbone | completed | M1: 11-table MySQL schema, repository contracts, MySQL/Redis persistence, auth, readiness. |
| Live integration readiness | completed | M2: docker-compose, skip-safe integration tests for all external services. |
| Procedure integration | completed | M3: all procedures wired with RepoBundle, audit writes, async /ready probes. |
| LLM-first RAG pipeline | completed | M4: multi-query vector recall, 5-dimension ranking, KB reranking, confidence gates. |
| Frontend E2E + live RAG eval | completed | M5: Playwright E2E, live dependency verification, live RAG integration, eval runner. |
| LangSmith tracing + diagnostics | completed | M6: opt-in LangSmith, understanding diagnostics, rec-stage diagnostics. |
| Lease/vector/embedding integrations | completed | LeaseClient (HTTP), VectorClient (Milvus), EmbeddingClient (OpenAI-compatible). All live-verified. |
| MySQL + Redis persistence | completed | 11 MySQL tables, RedisStateStore with TTL, RepoBundle for all 8 repo types. |
| Auth boundary | completed | dev mode + internal_header mode for lease gateway integration. |
| Vue3 validation frontend | completed | Chat UI with card rendering (room cards, KB source cards). |
| Main-system integration | deferred | Final path: `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`. |
