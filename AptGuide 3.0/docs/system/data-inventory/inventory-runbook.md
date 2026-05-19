# Inventory Runbook -- AptGuide 3.0

Safe procedures for generating data inventory reports without exposing sensitive information.

---

## Pre-Checks

1. Confirm you are in a **non-production** environment or have read-only database access.
2. Verify no `.env` file or credentials are staged for commit.
3. Ensure the output directory exists: `docs/system/data-inventory/`.

---

## Step 1: MySQL Table Inventory

Count rows and list indexes. Do NOT dump row contents.

```sql
-- Row counts (run against aptguide3 database)
SELECT 'aptguide3_users' AS tbl, COUNT(*) AS rows FROM aptguide3_users
UNION ALL SELECT 'aptguide3_sessions', COUNT(*) FROM aptguide3_sessions
UNION ALL SELECT 'aptguide3_messages', COUNT(*) FROM aptguide3_messages
UNION ALL SELECT 'aptguide3_pending_actions', COUNT(*) FROM aptguide3_pending_actions
UNION ALL SELECT 'aptguide3_memories', COUNT(*) FROM aptguide3_memories
UNION ALL SELECT 'aptguide3_memory_candidates', COUNT(*) FROM aptguide3_memory_candidates
UNION ALL SELECT 'aptguide3_handoff_tickets', COUNT(*) FROM aptguide3_handoff_tickets
UNION ALL SELECT 'aptguide3_operator_messages', COUNT(*) FROM aptguide3_operator_messages
UNION ALL SELECT 'aptguide3_trace_events', COUNT(*) FROM aptguide3_trace_events
UNION ALL SELECT 'aptguide3_procedure_runs', COUNT(*) FROM aptguide3_procedure_runs
UNION ALL SELECT 'aptguide3_audit_log', COUNT(*) FROM aptguide3_audit_log;
```

Safe to include in reports: table names, column names, column types, index names, row counts.

---

## Step 2: Redis Key Inventory

Use `SCAN` only. Never retrieve values.

```bash
# Count session keys
redis-cli --scan --pattern "aptguide3:session:*" | wc -l

# Count pending action keys
redis-cli --scan --pattern "aptguide3:pending:*" | wc -l

# Check TTL of a specific key (does not return value)
redis-cli TTL "aptguide3:session:{sample_id}"
```

Safe to include in reports: key patterns, counts, TTL ranges.

---

## Step 3: Milvus Collection Inventory

List collections and their schema. Do NOT export vectors or content.

```python
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530")

# List collections
collections = client.list_collections()

# Get collection stats (row count, index info)
for name in collections:
    stats = client.get_collection_stats(name)
    print(name, stats)
```

Safe to include in reports: collection names, field names, field types, index types, row counts.

---

## Step 4: Lease API Connectivity

Verify the Lease API is reachable. Do NOT log response payloads.

```bash
# Check connectivity (adjust URL as needed)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/internal/ai/tools/room/1
```

Safe to include in reports: endpoint availability (up/down), response time.

---

## Step 5: External AI Service Connectivity

Verify LLM and embedding endpoints are reachable. Do NOT log API keys.

```bash
# DashScope LLM (will return 401 if no key, which confirms reachability)
curl -s -o /dev/null -w "%{http_code}" https://dashscope.aliyuncs.com/compatible-mode/v1/models

# Embedding endpoint
curl -s -o /dev/null -w "%{http_code}" https://api.openai.com/v1/models
```

Safe to include in reports: service status (reachable/unreachable), model names.

---

## What NOT to Dump

The following must NEVER appear in inventory reports, exports, logs, or commits:

| Category | Examples |
|---|---|
| Environment files | `.env`, `.env.local`, `.env.production` |
| API keys / tokens | `llm_api_key`, `embedding_api_key`, `internal_token` |
| Passwords | MySQL passwords, Redis passwords |
| User messages | `aptguide3_messages.content`, `aptguide3_operator_messages.content` |
| Session state | `aptguide3_sessions.context`, `aptguide3_sessions.rolling_summary` |
| Lease PII | User names, phone numbers, ID card numbers, addresses |
| KB content | `apt_rental_kb.content` field values |
| Embeddings | Vector arrays from any Milvus collection |
| Payloads | `aptguide3_pending_actions.payload`, `aptguide3_trace_events.payload`, `aptguide3_audit_log.payload` |
| Memory values | `aptguide3_memories.value_json`, `aptguide3_memory_candidates.payload` |

---

## Output Format

Inventory reports should be Markdown files containing:

- Table/collection/column names and types
- Row counts and index metadata
- TTL configurations
- Endpoint availability status

Reports must NOT contain:

- Actual data values
- Sample rows
- Query results with user content
- API key references (even masked)
