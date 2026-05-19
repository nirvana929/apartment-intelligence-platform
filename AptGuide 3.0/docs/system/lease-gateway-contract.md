# Lease-to-AptGuide Gateway Contract

## Overview

This document defines the minimum HTTP contract between the lease platform
gateway and AptGuide 3.0.  The lease gateway acts as a trusted proxy: it
 authenticates end users (rentHouseH5) via JWT, then forwards chat requests to
AptGuide 3.0 with internal headers that assert the caller's identity.

```text
rentHouseH5  -->  lease /app/ai/chat  -->  AptGuide 3.0 /api/chat
                  (JWT auth)               (internal-header auth)
```

## Endpoint

| Field  | Value                |
|--------|----------------------|
| Method | `POST`               |
| Path   | `/api/chat`          |
| Content-Type | `application/json` |

## Required Headers

| Header             | Required | Description                                       |
|--------------------|----------|---------------------------------------------------|
| `X-Internal-Token` | Yes      | Shared secret configured in both lease and AptGuide 3.0.  Must match `APTGUIDE3_INTERNAL_TOKEN`. |
| `X-User-Id`        | Yes      | The lease platform user id of the authenticated caller.  AptGuide 3.0 trusts this value; it does **not** verify JWT. |
| `X-Request-Id`     | Recommended | Trace / correlation id propagated from the original client request.  Returned unchanged in the response header for end-to-end tracing. |

## Request Body

```json
{
  "message": "我想租一个两居室",
  "session_id": "sess-abc-123"
}
```

| Field       | Type   | Required | Description                              |
|-------------|--------|----------|------------------------------------------|
| `message`   | string | Yes      | The user's chat message.                 |
| `session_id`| string | Yes      | Client-generated session identifier.     |

Optional fields (`action`, `client_context`) are accepted but not required for
the lease gateway integration path.

## Response Body

AptGuide 3.0 returns a `ChatResponse` object:

```json
{
  "message": "为您找到以下房源……",
  "phase": "room_search",
  "cards": [ ... ],
  "actions": [ ... ],
  "pending_action": null,
  "metadata": { ... }
}
```

| Field           | Type   | Description                                           |
|-----------------|--------|-------------------------------------------------------|
| `message`       | string | The assistant's reply text.                           |
| `phase`         | string | Procedure phase that produced the response.           |
| `cards`         | array  | Structured card payloads (room listings, etc.).       |
| `actions`       | array  | Available follow-up actions for the user.             |
| `pending_action`| object | If set, the client must confirm or cancel this action.|
| `metadata`      | object | Diagnostic / tracing metadata.                        |

## Response Headers

| Header          | Condition              | Description                        |
|-----------------|------------------------|------------------------------------|
| `X-Request-Id`  | If present on request  | Echoed back for trace propagation. |

## Error Responses

| Status | Cause                                       | Body example                                      |
|--------|---------------------------------------------|---------------------------------------------------|
| `401`  | Missing or invalid `X-Internal-Token`       | `{"detail": "invalid internal token"}`            |
| `401`  | Missing `X-User-Id` when required           | `{"detail": "missing X-User-Id"}`                 |
| `422`  | Request body validation failure             | FastAPI validation error detail                   |
| `500`  | Internal server error                       | `{"detail": "Internal Server Error"}`             |

## Auth Modes

AptGuide 3.0 supports two auth modes controlled by `APTGUIDE3_AUTH_MODE`:

- **`dev`** (default) -- No header validation.  Returns a fixed dev user id.
  Used for local development and standalone demos.
- **`internal_header`** -- Validates `X-Internal-Token` against
  `APTGUIDE3_INTERNAL_TOKEN` and requires `X-User-Id`.  Used in the lease
  gateway integration path.

When `APTGUIDE3_INTERNAL_TOKEN_REQUIRED` is `false` (default), the token check
is skipped even in `internal_header` mode.  Set it to `true` in production.

## Security Notes

- AptGuide 3.0 **never** trusts `user_id` from the request body in
  `internal_header` mode.  The user identity comes exclusively from the
  `X-User-Id` header set by the lease gateway.
- The `X-Internal-Token` shared secret must be rotated out-of-band.
- AptGuide 3.0 does not verify JWT; that responsibility belongs to the lease
  gateway.
