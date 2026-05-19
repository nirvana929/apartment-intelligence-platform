# Redis Keys -- AptGuide 3.0

## Key Pattern

All keys follow the format:

```
{redis_key_prefix}:{namespace}:{id}
```

Default prefix: `aptguide3`

## Namespaces

| Namespace | Example Key | Data Type | TTL | Purpose |
|---|---|---|---|---|
| `session` | `aptguide3:session:{session_id}` | STRING (JSON) | `session_ttl_seconds` (default 86400 s / 24 h) | Cached session state for fast retrieval |
| `pending` | `aptguide3:pending:{pending_action_id}` | STRING (JSON) | `pending_action_ttl_seconds` (default 300 s / 5 min) | Pending action awaiting user confirmation |

## TTL Behavior

- Session cache: expires after 24 hours by default. Refreshed on write (`save_session`).
- Pending actions: expires after 5 minutes by default. Short-lived by design to auto-cancel stale confirmations.
- Both TTLs are configurable via environment variables (`APTGUIDE3_SESSION_TTL_SECONDS`, `APTGUIDE3_PENDING_ACTION_TTL_SECONDS`).

## Allowed Inventory Operations

When inspecting Redis for inventory purposes, use ONLY these read-only operations:

| Command | Purpose |
|---|---|
| `SCAN` | Enumerate key patterns (use `MATCH` with prefix) |
| `TYPE` | Check data type of a key |
| `TTL` | Check remaining time-to-live |
| `DBSIZE` | Total key count |

## Prohibited Operations

- Do NOT use `GET`, `HGETALL`, `SMEMBERS`, or any command that returns stored values.
- Do NOT export, snapshot, or dump key contents. Values contain session state and action payloads.
- Do NOT use `KEYS *` in production. Use `SCAN` with a cursor.

## Key Count Estimation

To estimate the number of cached sessions without reading values:

```
SCAN 0 MATCH aptguide3:session:* COUNT 1000
```

To estimate pending actions:

```
SCAN 0 MATCH aptguide3:pending:* COUNT 1000
```
