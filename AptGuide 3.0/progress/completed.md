# Completed

## 2026-05-15

- Created AptGuide 3.0 project skeleton.
- Created architecture and contract documentation.
- Implemented clean LLM-first backend foundation (36 tests, ruff clean).
- Domain contracts: UnderstandingResult, ConversationFrame, ProcedureResult, ChatResponse.
- Understanding layer: LLM adapter, validation, clarification-on-uncertainty.
- Application layer: safety boundary, procedure runtime, chat service.
- Procedures: clarify, room_search, kb_qa, appointment, lease, memory, handoff.
- Integrations: LeaseClient, VectorClient (Milvus), EmbeddingClient.
- Persistence: InMemorySessionRepo, MemoryRepo, HandoffRepo.
- Observability: TraceEvent, ChatTrace, ConsoleTraceSink, Tracer.
- Frontend: Vue3 chat UI with CORS and static file serving.
- LLM: qwen-turbo-latest via DashScope OpenAI-compatible API.
- FastAPI API: /health, /chat, static frontend mount.
- Anti-regression source scan: no keyword fallback in understanding runtime.
- Clarified AptGuide 3.0 product boundary: independent validation first, final integration through `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`.
- Created independent backend backbone plan for database schema, repository contracts, MySQL/Redis persistence, auth boundary, readiness, trace persistence, and procedure-run persistence.
