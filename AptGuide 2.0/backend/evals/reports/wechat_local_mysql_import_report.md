# WeChat Local MySQL Import Report

Date: 2026-05-12

## Summary

- Source directory: `参考资料/微信租房消息`
- Target table: `external_wechat_rental_listing`
- Storage target: local MySQL
- Includes phone numbers: yes
- Includes WeChat IDs: yes, when extractable
- Inserts into platform inventory tables: no

## Generated Artifacts

| Artifact | Purpose |
| --- | --- |
| `data/wechat_local_mysql_listings.jsonl` | Reviewable structured listing output |
| `data/wechat_local_mysql_raw_messages_sample.jsonl` | Raw message sample for review |
| `data/wechat_local_mysql_seed.sql` | Idempotent local MySQL import SQL |

## Coverage

- Imported listings: 44
- District distribution: 天河区 28, 荔湾区 9, 海珠区 4, 番禺区 3
- Listings with phone numbers: 40
- Listings with WeChat IDs: 14
- Min rent: 300
- Max rent: 2500

## Defaults

- `source_type = WECHAT_GROUP`
- `authenticity = REAL_POSTED`
- `verification_status = UNVERIFIED`
- `availability_status = UNKNOWN`
- `is_active = 1`
- `appointable = 0`

## Verification Commands

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/data_import/test_wechat_local_mysql_parser.py -v
uv run ruff check scripts/import_wechat_local_mysql.py src/aptguide2/data_import tests/unit/data_import
rg -n "external_wechat_rental_listing|phone_numbers|wechat_ids|contact_text|raw_text|ON DUPLICATE KEY UPDATE" data/wechat_local_mysql_seed.sql
```
