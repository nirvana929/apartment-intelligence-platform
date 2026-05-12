# Room Data Audit Report

Date: 2026-05-11

## Summary

- Active public rooms: **31**
- Cities covered: **2**（北京市辖区、广州市）
- Districts covered: **2**（昌平区、番禺区）
- Min rent: **600 元/月**
- Max rent: **6000 元/月**
- Missing public fields: area, layout（存储在 EAV 表中，当前 RoomVo 未返回）

## Coverage By District

| City | District | Active Rooms | Rent Range | Gap |
| --- | --- | ---: | --- | --- |
| 北京市辖区 | 昌平区 | 12 | 2000 - 6000 | 需补充至 10（已满足） |
| 广州市 | 番禺区 | 19 | 600 - 1800 | 需补充至 38（差 19 个） |

## Target District Distribution（需补充）

| District | Target Count | Current Count | Need to Add |
| --- | ---: | ---: | ---: |
| 天河区 | 30 | 0 | 30 |
| 越秀区 | 22 | 0 | 22 |
| 海珠区 | 26 | 0 | 26 |
| 番禺区 | 38 | 19 | 19 |
| 白云区 | 24 | 0 | 24 |
| 北京昌平区 | 10 | 12 | 0（已满足） |
| **总计** | **150** | **31** | **119** |

## Target Rent Distribution

| Rent Band | Target Count |
| --- | ---: |
| 800-1500 | 24 |
| 1500-2200 | 34 |
| 2200-3200 | 42 |
| 3200-4500 | 32 |
| 4500+ | 18 |

## Target Tag Coverage

| Tag | Minimum Count |
| --- | ---: |
| 安静 | 45 |
| 近地铁 | 55 |
| 独卫 | 60 |
| 朝南 | 45 |
| 可月付 | 80 |
| 适合考研 | 35 |
| 适合通勤 | 55 |
| 采光好 | 45 |
| 家电齐全 | 70 |
| 可短租 | 25 |

## Sensitive Fields Excluded

- phone（公寓前台电话）
- exact address detail（精确地址）
- latitude / longitude（经纬度）
- user data（用户数据）
- contract data（合同数据）
- payment data（支付记录）

## Decision

Current data is **NOT** enough for RAG MVP.

Seed rooms required: **119**

- 广州市需要补充 4 个区（天河、越秀、海珠、白云）的房间，共 102 个
- 番禺区需要补充 19 个房间
- 北京昌平区已满足要求（12 个 >= 10 个目标）

## Next Steps

1. 创建种子 SQL 脚本 `aptguide_rag_room_seed.sql`
2. 插入测试公寓和房间数据
3. 确保种子房间通过 `/internal/ai/tools/sync/rooms` 可见
4. 确保种子房间通过 `/internal/ai/tools/room/search` 可查询
