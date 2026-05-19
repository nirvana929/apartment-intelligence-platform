# AptGuide 3.0

LLM-first rental assistant rebuilt as the next upgrade of the AptGuide main system.

## Purpose

AptGuide 3.0 is a new implementation of the AptGuide C-side rental assistant. It is not an in-place refactor of AptGuide 2.0 and it is not a disconnected demo product.

The intended delivery model follows the original AptGuide two-stage path:

```text
Stage 1: AptGuide 3.0 can run independently for development, evaluation, and demo validation.
Stage 2: AptGuide 3.0 is integrated back into the AptGuide main-system chain through the lease AI gateway.
```

Final platform integration should look like:

```text
rentHouseH5
  -> lease web-app POST /app/ai/chat
      -> AptGuide 3.0 POST /api/chat
          -> AptGuide 3.0 Agent state DB / Redis
          -> lease internal tools
          -> Milvus
          -> LLM
```

AptGuide 3.0 may have its own independent validation frontend during development. That frontend is not the final `rentHouseH5` entry.

## Core Rule

Natural-language understanding is model-first:

```text
LLM structured output valid and confident -> execute the selected procedure
LLM unavailable, invalid, low confidence, or contradictory -> ask the user to clarify
```

Keyword matching must not decide:

- route
- task
- domain
- filters
- preferences
- risk posture
- retrieval queries

Deterministic code still owns:

- safety hard boundaries
- pending action handling
- schema and contract validation
- permissions
- write confirmation
- ToolRuntime governance
- lease-backed room and user-data validation

## System Boundary

AptGuide 3.0 owns Agent runtime state:

- sessions;
- messages;
- pending actions;
- memory and memory candidates;
- handoff tickets and operator messages;
- trace events;
- procedure runs;
- audit events.

The lease system remains the business source of truth for:

- users and authentication;
- rooms and apartments;
- appointments;
- leases and contracts;
- sensitive customer data.

AptGuide 3.0 must call lease internal tools for business facts and writes. It must not let the frontend directly access lease, Milvus, Redis, MySQL, or the LLM provider.

## Backend Shape

```text
backend/src/aptguide3/
  api/             FastAPI boundary, auth, readiness, dependency wiring
  application/     chat orchestration, procedure runtime, response composition, safety
  understanding/   LLM-first structured understanding, validation, diagnostics
  domain/          pure domain contracts and decisions
  procedures/      7 typed business procedures
  rag/             RAG pipeline: planning, retrieval, ranking, confidence, eval metrics
  integrations/    LLM, embedding, vector (Milvus), lease HTTP clients
  persistence/     repository contracts, in-memory + MySQL + Redis implementations
  database/        SQLAlchemy models, schema.sql, engine factory
  observability/   trace events, sinks (console, MySQL repository)
```

## Current State

All 6 milestones are complete (2026-05-15):

| Milestone | Description | Tests |
|-----------|-------------|-------|
| 0 | Runnable scaffold | 36 passed |
| 1 | Independent backend backbone (schema, repos, MySQL/Redis, auth, readiness) | 55 passed |
| 2 | Live integration readiness (docker-compose, skip-safe integration tests) | 68 passed, 23 skipped |
| 3 | Procedure integration (all 7 procedures wired, audit writes, RepoBundle) | 129 passed, 28 skipped |
| 4 | LLM-first RAG upgrade (room retrieval, ranking, KB retrieval, confidence) | 207 passed, 28 skipped |
| 5 | Frontend E2E + live RAG evaluation (Playwright, live dependency verification) | 175 passed, 33 skipped, 35 failed |
| 6 | LangSmith tracing + understanding/rec diagnostics | 22 diagnostic tests passed |

Key capabilities:
- LLM-first structured understanding with no keyword fallback;
- 7 typed procedures: clarify, room_search, kb_qa, appointment, lease, memory, handoff;
- Full RAG pipeline: multi-query vector recall, 5-dimension ranking, confidence gates;
- MySQL durable persistence (11 tables) + Redis TTL hot state;
- Auth boundary: dev mode + internal_header mode for lease gateway integration;
- LangSmith opt-in tracing + understanding/rec-stage diagnostics;
- Playwright frontend E2E + live RAG evaluation runner;
- `/health`, `/ready` (with `?live=true` probes), `/chat`;
- Vue3 validation frontend with card rendering.

Next phase: sync room/KB vectors to Milvus, re-run live RAG eval, then plan RAG optimization.

Start here:

- `docs/00-start-here.md`
- `docs/architecture.md`
- `docs/api-contract.md`
- `docs/understanding-contract.md`
- `docs/system/deployment-readiness.md`
