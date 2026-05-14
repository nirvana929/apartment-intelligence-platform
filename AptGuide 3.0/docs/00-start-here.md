# Start Here

## What This Project Is

AptGuide 3.0 is the next upgrade of the AptGuide C-side rental assistant in `apartment-intelligence-platform`.

It keeps useful product and integration lessons from AptGuide and AptGuide 2.0, but it does not reuse the AptGuide 2.0 keyword-based understanding runtime.

## Delivery Model

```text
Stage 1: independent AptGuide 3.0 service for development, demo, and evaluation.
Stage 2: integration into the AptGuide main-system chain through lease web-app.
```

Final C-side integration:

```text
rentHouseH5
  -> lease web-app /app/ai/chat
      -> AptGuide 3.0 /api/chat
          -> lease internal tools
          -> Milvus
          -> AptGuide 3.0 Agent state DB / Redis
          -> LLM
```

The independent validation frontend is useful for Stage 1, but the final production entry is still the AptGuide main-system frontend through `rentHouseH5` and `lease`.

## Completed Milestone

Milestone 0 is complete: runnable scaffold.

- Backend foundation: 36 tests, ruff clean.
- LLM-first structured understanding.
- Typed procedure runtime.
- Procedures: clarify, room_search, kb_qa, appointment, lease, memory, handoff.
- Integrations: LeaseClient, VectorClient, EmbeddingClient.
- Persistence: in-memory session/memory/handoff repos.
- Observability: trace events with console sink.
- Frontend: Vue3 validation UI.

## Current Engineering Objective

Build the AptGuide 3.0 independent backend backbone:

1. database schema and migration script;
2. repository contracts for Agent state;
3. MySQL durable state for sessions, messages, memories, handoff, traces, procedure runs, and audit;
4. Redis hot state for active sessions and pending-action TTL;
5. `ChatService` wired to durable persistence;
6. auth boundary matching final AptGuide integration;
7. readiness checks for MySQL, Redis, lease, Milvus, embeddings, and LLM config.

## Non-Goals For The First Milestone

- Do not copy AptGuide 2.0 runtime modules.
- No keyword fallback for route, task, domain, filters, preferences, risk posture, or retrieval queries.
- No live room availability claims without lease validation.
- Do not make AptGuide 3.0 the source of truth for rooms, appointments, leases, contracts, or sensitive user data.
- Do not make frontend call lease, Milvus, Redis, MySQL, or LLM directly.

## Current Entry Points

- Architecture: `docs/architecture.md`
- Understanding contract: `docs/understanding-contract.md`
- API contract: `docs/api-contract.md`
- Current plan: `docs/plans/current-plan.md`
- Next implementation plan: `docs/plans/2026-05-15-aptguide3-independent-backend-backbone-plan.md`
