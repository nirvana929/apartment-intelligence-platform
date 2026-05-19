# AptGuide 3.0 System Flow: LLM and Rule Boundaries

This document shows the current AptGuide 3.0 request flow and marks where the system uses:

- LLM structured understanding
- deterministic string matching
- deterministic validation rules
- regular expressions

## Flow Diagram

```mermaid
flowchart TD
  U[User / rentHouseH5] --> L[lease web-app<br/>/app/ai/chat]
  L -->|Internal request<br/>X-Internal-Token + X-User-Id| A[AptGuide 3.0 FastAPI<br/>/chat]

  A --> AUTH[AuthResolver<br/>auth and user context]
  AUTH --> CS[ChatService.run]

  CS --> S[SafetyBoundary<br/>STRING MATCHING<br/>privacy hard block]
  S -->|privacy term matched| BLOCK[Reject directly<br/>no LLM call]
  S -->|not blocked| PERSIST1[Persist user message<br/>MySQL or memory]

  PERSIST1 --> LLM[LLMUnderstanding<br/>LLM STRUCTURED UNDERSTANDING<br/>route / task / filters / risk / confidence]
  LLM --> V[validate_or_clarify<br/>RULE VALIDATION<br/>confidence, route-task shape, filter whitelist]

  V -->|low confidence or invalid shape| CLARIFY[ClarifyProcedure<br/>ask follow-up question]
  V -->|valid UnderstandingResult| RUNTIME[ProcedureRuntime<br/>deterministic dispatch by route/task]

  RUNTIME --> ROOM[RoomSearchProcedure]
  RUNTIME --> KB[KbQaProcedure]
  RUNTIME --> APPT[AppointmentProcedure]
  RUNTIME --> LEASE[LeaseProcedure]
  RUNTIME --> MEM[MemoryProcedure]
  RUNTIME --> HAND[HandoffProcedure]

  ROOM --> LC1[LeaseClient<br/>lease room tools]
  LC1 --> FILTER[LeaseClient._matches_filters<br/>RULE FILTERING<br/>rent/payment checks]
  LC1 --> REGEX[LeaseClient._to_snake<br/>REGEX ONLY FOR FIELD NAME CONVERSION]

  APPT --> PA[PendingActionRepo<br/>confirmation TTL state]
  APPT --> LC2[LeaseClient<br/>create appointment]
  APPT --> AUD1[AuditRepo<br/>appointment audit]

  LEASE --> LC3[LeaseClient<br/>list user leases]
  LEASE --> AUD2[AuditRepo<br/>lease audit]

  KB --> EMB[Embedding API]
  EMB --> MILVUS[Milvus / VectorClient]

  MEM --> DB1[MemoryRepo<br/>MySQL or memory]
  HAND --> DB2[HandoffRepo<br/>MySQL or memory]
  HAND --> AUD3[AuditRepo<br/>handoff audit]

  BLOCK --> RESP[ResponseComposer]
  CLARIFY --> RESP
  FILTER --> RESP
  LC2 --> RESP
  LC3 --> RESP
  MILVUS --> RESP
  DB1 --> RESP
  DB2 --> RESP

  RESP --> PERSIST2[Persist assistant message<br/>session / trace / message repos]
  PERSIST2 --> OUT[ChatResponse]
  OUT --> L
  L --> U
```

## Boundary Notes

### LLM Usage

The LLM is used in `LLMUnderstanding` only. It converts the user's natural language message into a structured `UnderstandingResult`.

The expected output includes:

- `route`
- `task`
- `domain`
- `action`
- `hard_filters`
- `soft_preferences`
- `retrieval_queries`
- `risk`
- `confidence`

If the LLM is unavailable or the output is invalid, the system asks a clarification question. It does not fall back to keyword intent routing.

### String Matching

`SafetyBoundary` uses deterministic string matching before the LLM call. It checks hard privacy terms such as:

- `室友手机号`
- `别人手机号`
- `其他租户电话`
- `身份证`

If any term is present, the request is blocked before the LLM.

### Rule Validation

`validate_or_clarify` checks the LLM output shape. This is validation, not natural-language interpretation.

It checks:

- minimum confidence
- whether the model asked for clarification
- legal `route` and `task` combinations
- allowed `hard_filters` keys
- allowed enum values for payment type and room type

### Regular Expressions

The current regex usage is not for intent recognition. It is used in `LeaseClient._to_snake` to convert returned field names from `camelCase` to `snake_case`.

## Current Design Conclusion

AptGuide 3.0 is currently LLM-first for natural-language understanding. The code does not reuse AptGuide 2.0 style keyword routing or regex intent recognition. Deterministic code is used for safety blocking, schema validation, business dispatch, lease result filtering, persistence, and response composition.
