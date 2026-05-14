# Main-System Integration Boundary

## Positioning

AptGuide 3.0 is an upgrade implementation of the AptGuide main-system C-side rental assistant.

It can run independently during development, evaluation, and demo validation. Final production integration follows the existing AptGuide path:

```text
rentHouseH5
  -> lease web-app /app/ai/chat
      -> AptGuide 3.0 /api/chat
          -> lease internal tools
          -> Milvus
          -> AptGuide 3.0 Agent state DB / Redis
          -> LLM
```

## Frontend Boundary

The independent AptGuide 3.0 frontend is a validation UI. It helps verify chat behavior, cards, actions, pending actions, traces, and operator flows before platform integration.

It is not the final integrated frontend. The final user-facing entry is developed or modified in the AptGuide main-system frontend, through `rentHouseH5` and `lease`.

## Data Ownership

AptGuide 3.0 owns Agent state:

- sessions;
- messages;
- pending actions;
- memory and memory candidates;
- handoff tickets and operator messages;
- trace events;
- procedure runs;
- audit events.

lease owns business facts:

- users and formal authentication;
- rooms and apartments;
- appointments;
- leases and contracts;
- sensitive customer data.

## Trust Boundary

In integrated mode:

- `rentHouseH5` calls `lease /app/ai/chat`.
- `lease` verifies JWT and resolves the user.
- `lease` calls AptGuide 3.0 with `X-Internal-Token`, `X-User-Id`, and `X-Request-Id`.
- AptGuide 3.0 ignores frontend/body-provided user identity.
- AptGuide 3.0 reads and writes business facts only through lease internal tools.

## Planning Implication

Before expanding procedures, AptGuide 3.0 must stabilize the independent backend backbone: schema, repositories, auth, readiness, trace persistence, and procedure-run persistence.
