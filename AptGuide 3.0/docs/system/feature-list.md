# Feature List

| Feature | Status | Notes |
| --- | --- | --- |
| LLM-first structured understanding | completed | No keyword fallback for natural-language interpretation. |
| Typed procedure runtime | completed | clarify, room_search, kb_qa, appointment, lease, memory, handoff are registered. |
| Lease/vector/embedding integrations | scaffolded | Clients exist; live service verification remains pending. |
| In-memory persistence defaults | scaffolded | Useful for local tests, not production-ready. |
| Vue3 validation frontend | scaffolded | Independent validation UI, not final main-system entry. |
| Independent backend backbone | planned | Active Milestone 1: schema, repositories, MySQL/Redis, auth, readiness. |
| Main-system integration | deferred | Final path is `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`. |
