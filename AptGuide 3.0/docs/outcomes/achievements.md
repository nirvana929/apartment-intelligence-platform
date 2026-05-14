# Achievements

## 2026-05-15 - AptGuide 3.0 Full-Stack System

Built a runnable LLM-first rental assistant scaffold in a single session:

- **Architecture**: Clean separation — understanding (LLM only), domain contracts, application orchestration, procedure dispatch, integrations, persistence, observability
- **Procedures**: 7 typed procedures (clarify, room_search, kb_qa, appointment, lease, memory, handoff)
- **Integrations**: LeaseClient (HTTP), VectorClient (Milvus), EmbeddingClient (OpenAI-compatible)
- **Persistence**: Protocol-based repos (session, memory, handoff) with in-memory defaults, swappable to Redis/MySQL
- **Observability**: TraceEvent system with ConsoleTraceSink
- **Frontend**: Vue3 chat UI with card rendering
- **LLM**: qwen-turbo-latest via DashScope, with ClarifyOnlyUnderstanding fallback
- **Quality**: 36 tests, ruff clean, anti-regression source scan for no keyword fallback
- **Parallel execution**: 8 agents across 2 batches, 4 concurrent workstreams

## 2026-05-15 - Main-System Boundary Clarified

Clarified that AptGuide 3.0 is an AptGuide main-system upgrade:

- independent validation first;
- final integration through `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`;
- AptGuide 3.0 owns Agent state;
- lease remains source of truth for users, rooms, appointments, leases, contracts, and sensitive customer data.
