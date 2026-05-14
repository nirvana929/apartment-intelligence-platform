# Feature List

| Feature | Status | Notes |
| --- | --- | --- |
| Harness mainline `/chat` runtime | completed | `/chat` enters `AptGuideHarness`; legacy RAG disconnected. |
| RAG v2 harness module | completed | Internal module for room search and KB QA; quality tuning deferred. |
| Real lease backend tool access | completed | Lease adapter and governed tool runtime exist; readiness must remain green. |
| Appointment create confirmation | completed | Two-turn confirmation with `confirmation_id`. |
| Appointment cancel confirmation | completed | Two-turn confirmation with `confirmation_id`. |
| Appointment list | completed | User-scoped governed tool flow. |
| Lease list | completed | User-scoped governed tool flow. |
| Standalone frontend | completed | Vue 3 + Vant + Pinia + TypeScript SPA under `frontend/`. |
| Development auth | completed | Dev mode with configurable default user; test user selector in frontend. |
| Formal lease-token auth | completed | AuthResolver resolves `user_id` from lease token; ignores frontend `user_id`. |
| Redis + MySQL context store | completed | PersistentContextStore: Redis-first, MySQL fallback, new frame fallback. |
| Durable memory profile | completed | MemoryProcedure with profile CRUD; in-memory base, MySQL-ready. |
| Memory candidates | completed | Two-step confirmation flow for preference updates. |
| Durable pending actions | completed | RedisStateStore with TTL; rehydrated on context load. |
| Durable handoff tickets | completed | HandoffRepository with ticket CRUD; operator API for management. |
| Local operator console | completed | Operator API (list/detail/reply/close) + Vue 3 operator console UI. |
| Production platform integration | deferred | Later phase after standalone app works. |
| RAG retrieval-quality optimization | deferred | KB hit@3 and Room hit@5 gates remain known quality work. |
