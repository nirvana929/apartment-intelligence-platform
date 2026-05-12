# Room Vector Sync Report

**Sync ID:** room-sync-1778568582
**Date:** 2026-05-12

## Summary

| Metric | Value |
| --- | ---: |
| Total fetched | 126 |
| Added | 76 |
| Updated | 0 |
| Inactive | 0 |
| Embedded | 76 |
| Failed | 0 |

## Room Distribution by District

| District | Count |
|----------|------:|
| 天河区 | 30 |
| 海珠区 | 26 |
| 番禺区 | 23 |
| 越秀区 | 22 |
| 白云区 | 22 |
| 昌平区 | 3 |

## Sample Rooms

| Room ID | Apartment | District | Rent |
|---------|-----------|----------|-----:|
| 200001 | 天河智慧城公寓 | 天河区 | 2800 |
| 200002 | 天河智慧城公寓 | 天河区 | 3000 |
| 200092 | 市桥老城温馨居 | 番禺区 | 1200 |
| 200097 | 市桥老城温馨居 | 番禺区 | 2200 |

## Search Quality

| Query | Top Match | Score |
|-------|-----------|-------|
| "番禺区安静的房子" | 市桥老城温馨居 ¥1200 | 0.67 |
| "天河区3000以内" | 天河智慧城公寓 ¥2800 | 0.72 |

## Notes

- Synced from lease backend via `/internal/ai/tools/sync/rooms`
- 50 rooms were previously synced; 76 new rooms added in this run
- Total active rooms in Milvus: 126
- Lease backend timeout observed when requesting 500 rooms; 200 limit works reliably
