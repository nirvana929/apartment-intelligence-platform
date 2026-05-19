# Source Responsibilities -- AptGuide 3.0

## 1. MySQL (aptguide3 database)

Durable agent state. Stores all persistent records that survive restarts.

- Sessions and their rolling summaries
- Message history per session
- Pending actions awaiting confirmation
- Memory candidates and persisted memories
- Handoff tickets and operator messages
- Trace events for request-level observability
- Procedure run logs
- Audit log for security-relevant events

Persistence mode is controlled by `persistence_mode` (`memory`, `mysql`, `hybrid`). Only `mysql` and `hybrid` modes write to the database.

## 2. Redis

Hot state with TTL-based expiry. Used in `hybrid` persistence mode as a fast cache layer.

- **Session cache** -- serialized session JSON, TTL = `session_ttl_seconds` (default 86400 s / 24 h)
- **Pending actions** -- serialized action JSON, TTL = `pending_action_ttl_seconds` (default 300 s / 5 min)

Key prefix: configurable via `redis_key_prefix` (default `aptguide3`). All keys follow the pattern `{prefix}:{namespace}:{id}`.

## 3. Milvus (Vector Database)

Semantic search over two collections:

| Collection | Purpose |
|---|---|
| `apt_room_vector` | Room listings vectorized for natural-language search |
| `apt_rental_kb` | Knowledge-base chunks (rules, policies, FAQs) |

Connected via `pymilvus.MilvusClient` at `vector_uri` (default `http://localhost:19530`).

## 4. Lease API (External Business System)

Source of truth for all business data that AptGuide does not own:

- Room details and availability
- Apartment metadata
- Appointments (create, list)
- Leases and contracts
- User identity (via `X-User-Id` header)

Base URL: `lease_base_url` (default `http://localhost:8081`). All endpoints are under `/internal/ai/tools/`.

## 5. LLM / Embedding (DashScope)

| Service | Model | Base URL |
|---|---|---|
| Chat / Understanding | `qwen-turbo-latest` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| Embeddings | `text-embedding-3-small` | `https://api.openai.com/v1` |

Used for intent understanding, preference scoring, and vector embedding generation. Connected through the OpenAI-compatible SDK.

## 6. LangSmith (Observability)

Optional tracing layer. Enabled via `langsmith_tracing=true`.

- Project: `langsmith_project` (default `aptguide3-local`)
- Endpoint: `https://api.smith.langchain.com`

LangSmith receives trace spans only. It does not store business data independently.
