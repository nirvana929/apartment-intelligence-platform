# AptGuide 3.0 Architecture

## Product Context

AptGuide 3.0 is an upgrade implementation of the AptGuide main-system C-side rental assistant.

It is developed as an independently runnable service first, then integrated through the established AptGuide production path:

```text
rentHouseH5
  -> lease web-app /app/ai/chat
      -> AptGuide 3.0 /api/chat
          -> lease internal tools
          -> Milvus
          -> AptGuide 3.0 Agent state DB / Redis
          -> LLM
```

The independent frontend is a validation surface. The final integrated frontend entry is developed in the AptGuide main system, with `lease` acting as the user-facing AI gateway.

## Dependency Direction

```text
api
  -> application
      -> domain
      -> understanding
      -> procedures
          -> retrieval
          -> integrations
      -> persistence
      -> observability
```

Domain contracts should not import FastAPI, OpenAI, Milvus, Redis, MySQL, or the lease backend.

## Request Flow

```text
POST /chat
  -> API schema validation
  -> auth context resolution
  -> ChatService
  -> hard safety boundary
  -> pending action repository boundary
  -> LLM Understanding
  -> contract validation
  -> ProcedureRuntime
      -> clarify
      -> room_search
      -> kb_qa
      -> appointment
      -> lease
      -> memory
      -> handoff
  -> ResponseComposer
  -> message/procedure/trace persistence
  -> ChatResponse
```

## Ownership Boundary

### AptGuide 3.0 Owns

- Agent sessions;
- chat messages;
- pending actions and confirmation TTL state;
- long-term assistant memory and memory candidates;
- handoff tickets and operator messages;
- trace events;
- procedure runs;
- audit events related to Agent state.

### lease Owns

- user identity and formal authentication;
- room and apartment facts;
- appointment creation/cancel/list facts;
- lease and contract facts;
- sensitive customer data;
- final business writes.

AptGuide 3.0 may persist Agent state, but business facts must be read and written through lease internal tools.

## Layer Responsibilities

### api

Owns FastAPI app construction, request/response schemas, auth header handling, dependency wiring, and HTTP error mapping.

### application

Owns the main orchestration use case. It coordinates safety, pending action handling, understanding, procedure dispatch, response composition, and message/procedure/trace persistence.

### understanding

Owns the LLM-first structured understanding call, prompt, JSON parsing, and contract validation. It never calls lease, vector search, or procedure code.

### domain

Owns pure business contracts: conversation frame, interaction intent, safety decision, procedure result, response objects, and permission decisions.

### procedures

Owns business workflows. Procedures consume validated intent and return typed procedure results.

### retrieval

Owns retrieval contracts and implementation-facing abstractions for room search and KB QA.

### integrations

Owns external service clients: LLM, embedding, lease, and vector store.

### persistence

Owns Agent state repository contracts and database implementations. MySQL is durable state. Redis is hot state and TTL support.

### observability

Owns trace events and log payloads. It records what happened without exposing hidden chain-of-thought. Durable trace events are written through persistence.

## Hard Rules

- No keyword fallback for natural-language understanding.
- LLM uncertainty becomes clarification.
- Tool writes require confirmation.
- User-owned data requires authenticated context.
- Room recommendations require lease-backed validation.
- AptGuide 3.0 does not trust frontend-provided `user_id` in integrated mode.
- `rentHouseH5` calls `lease`; `lease` calls AptGuide 3.0 with trusted internal headers.
