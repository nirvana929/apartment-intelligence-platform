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
  api/             FastAPI boundary and request/response schemas
  application/     chat orchestration and procedure runtime
  understanding/   LLM-first structured understanding
  domain/          pure domain contracts and decisions
  procedures/      business procedures
  retrieval/       KB and room retrieval abstractions
  integrations/    LLM, embedding, vector, lease, persistence adapters
  observability/   trace events and logging
```

## Current State

A runnable scaffold is complete:

- LLM-first backend foundation;
- `/health` and `/chat`;
- 7 typed procedures;
- lease/vector/embedding client skeletons;
- in-memory repository defaults;
- console trace sink;
- Vue3 validation frontend;
- 36 tests passed, 2 skipped;
- ruff clean.

The next milestone is the independent backend backbone: database schema, repository contracts, MySQL/Redis persistence, durable trace/procedure state, auth boundary, and readiness checks.

Start here:

- `docs/00-start-here.md`
- `docs/architecture.md`
- `docs/api-contract.md`
- `docs/understanding-contract.md`
- `docs/plans/2026-05-15-aptguide3-independent-backend-backbone-plan.md`
