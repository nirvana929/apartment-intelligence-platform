# KB Vector Sync Report

**Sync ID:** kb-sync-1778568206
**Release ID:** kb-v1
**Date:** 2026-05-12

## Summary

| Metric | Value |
| --- | ---: |
| Total KB chunks | 70 |
| Added | 0 |
| Updated | 0 |
| Inactive | 0 |
| Embedded | 0 |
| Failed | 0 |

## Notes

- "No changes detected" means all 70 chunks were already synced and content hashes match
- Duplicate doc_id issue fixed: `load_rules()` now deduplicates by doc_id
- The `knowledge/rules/` directory has `_rules.yaml` and `.yaml` pairs with same doc_ids; dedup keeps the first occurrence

## KB Module Distribution

| Module | Chunks | Description |
|--------|-------:|-------------|
| lease | 12 | 租赁合同规则 |
| appointment | 10 | 预约看房规则 |
| life | 10 | 生活服务规则 |
| payment | 10 | 支付费用规则 |
| policy | 10 | 公寓政策规则 |
| room_search | 10 | 搜索找房规则 |
| account | 8 | 账号安全规则 |

## Search Quality

| Query | Top Match | Score |
|-------|-----------|-------|
| "押金退还规则" | KB-LEASE-005 押金退还规则 | 0.84 |
| "怎么预约看房" | KB-APPT-001 预约看房流程 | 0.81 |
| "退租要提前多久" | KB-LEASE-011 退租验房标准 | 0.72 |
