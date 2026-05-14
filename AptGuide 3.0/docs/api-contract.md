# API Contract

## Integration Modes

AptGuide 3.0 supports two API modes:

```text
independent-dev:
  validation frontend -> AptGuide 3.0 /api/chat

integrated:
  rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat
```

In integrated mode, AptGuide 3.0 trusts only the user identity injected by `lease` headers.

## Trusted Headers

| Header | Mode | Purpose |
| --- | --- | --- |
| `X-Internal-Token` | integrated | Shared service token from lease to AptGuide 3.0 |
| `X-User-Id` | integrated | User ID resolved by lease after JWT verification |
| `X-Request-Id` | integrated/dev | Cross-service trace ID |

Frontend-provided `user_id` must not override trusted headers.

## `POST /api/chat`

Request:

```json
{
  "message": "珠江新城3000以内有阳台的房间",
  "session_id": "s-001",
  "action": null,
  "client_context": {}
}
```

Response:

```json
{
  "message": "我找到了一些符合条件的房源。",
  "phase": "room_search",
  "cards": [],
  "actions": [],
  "pending_action": null,
  "metadata": {
    "trace_id": "trace-001",
    "route": "rag",
    "task": "room_search"
  }
}
```

## Development Compatibility

During independent development, the validation frontend may send a development user selector through `client_context`. That selector is allowed only when `APTGUIDE3_AUTH_MODE=dev`.

In `lease_token` or `internal_header` mode, AptGuide 3.0 must ignore body-provided identity data and use the authenticated context.

## Response Identity

Responses must include enough identity for frontend rendering and support diagnosis:

- `session_id`;
- `request_id`;
- `trace_id` in metadata;
- `phase`;
- `cards`;
- `actions`;
- `pending_action`.

## Final Main-System Boundary

The final AptGuide main-system frontend should call `lease /app/ai/chat`, not AptGuide 3.0 directly. The lease gateway handles JWT verification and response wrapping before calling AptGuide 3.0 internally.
