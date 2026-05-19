# Data Inventory (Auto-Generated)

Generated: 2026-05-15T11:03:21.979856+00:00
Mode: metadata-only

## Configuration

- `environment`: local
- `service_name`: aptguide3
- `llm_base_url`: https://dashscope.aliyuncs.com/compatible-mode/v1
- `llm_model`: qwen-turbo-latest
- `embedding_base_url`: https://dashscope.aliyuncs.com/compatible-mode/v1
- `embedding_model`: text-embedding-v3
- `lease_base_url`: http://127.0.0.1:8081
- `vector_uri`: http://127.0.0.1:19530
- `auth_mode`: <redacted>
- `persistence_mode`: hybrid
- `redis_url`: <set>
- `langsmith_tracing`: False
- `langsmith_project`: aptguide3-local
- `understanding_diagnostics_enabled`: False

## MySQL

- Status: error — 'cryptography' package is required for sha256_password or caching_sha2_password auth methods

## Redis

- Total keys: 0

## Milvus

- `apt_rental_kb`: 70 entities
  - id: 21
  - content: 21
  - vector: 101
  - category: 21
  - title: 21
- `room_index`: 150 entities
  - id: 5
  - title: 21
  - description: 21
  - vector: 101
  - rent: 5
  - district: 21
  - tags: 21
  - payment_type: 21
  - status: 21
