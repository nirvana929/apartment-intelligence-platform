# AptGuide RAG Room Seed

This seed is for local/test RAG evaluation only.

Rules:

- Do not run against production.
- Seed rooms are demo/test inventory.
- Public fields may be indexed into Milvus after they are exposed by lease sync tools.
- Phone, exact door number, latitude, longitude, user data, contract data, and payment data must not be indexed.
- Rooms inserted by this seed must be returned by `/internal/ai/tools/room/search`.

## Seed Details

- **Total rooms**: 119 (to reach 150 target)
- **Target districts**: 天河区, 越秀区, 海珠区, 番禺区, 白云区
- **ID range**: 200001 - 200119 (seed rooms)
- **Apartment ID range**: 10001 - 10020 (seed apartments)

## Usage

```bash
# Apply seed to test database
mysql -h <host> -u <user> -p <database> < aptguide_rag_room_seed.sql

# Verify seed
mysql -h <host> -u <user> -p <database> -e "
SELECT COUNT(*) FROM room_info r
JOIN apartment_info a ON a.id = r.apartment_id
WHERE r.is_deleted = 0 AND a.is_deleted = 0
  AND r.is_release = 1 AND a.is_release = 1;
"
```

Expected result: >= 150
