# WeChat Rental Import Report

Date: 2026-05-12

## Summary

- Source directory: `参考资料/微信租房消息`
- Source files:
  - `广州租房群A134_全部消息.txt`
  - `广州租房群A134_消息.txt`
- Data classification: external real listing leads
- Authenticity default: `REAL_POSTED`
- Verification default: `UNVERIFIED`
- Availability default: `UNKNOWN`
- RAG visibility: sanitized records only
- Appointable default: `false`

## Generated Artifacts

| Artifact | Purpose |
| --- | --- |
| `data/wechat_rental_raw_messages_sample.jsonl` | Redacted raw-message review sample |
| `data/wechat_rental_listings_sanitized.jsonl` | RAG-visible sanitized external listing leads |
| `data/wechat_rental_listings_seed.sql` | Local/test SQL import for `external_rental_listing` |

## Coverage

- Sanitized listings: 44
- District distribution: 天河区 28, 荔湾区 9, 海珠区 4, 番禺区 3
- Min rent: 300
- Max rent: 2500
- Common tags: 近地铁 43, 房东直租 22, 押一付一 22, 家电齐全 19, 民水民电 18, 阳台 15, 无中介费 13, 采光好 9, 可短租 4, 宠物友好 4

## Sensitive Fields Excluded

- phone numbers
- WeChat IDs
- sender aliases
- local image URLs
- local video URLs
- exact contact instructions
- user identity data
- contract/payment private data

## Product Semantics

These records are real posted rental leads from WeChat group messages. They are not generated mock data.

The automated import does not prove current availability or platform verification. Therefore imported records must remain:

- `verification_status = UNVERIFIED`
- `availability_status = UNKNOWN`
- `appointable = false`

## RAG Answer Policy

The assistant may use these records to answer market and external-listing questions. It must state that these are external real listing leads and may require manual confirmation.

The assistant must not expose contacts or promise appointment availability for these records.

## Verification Commands

```bash
uv run pytest tests/unit/data_import/test_wechat_rental_parser.py -v
uv run ruff check scripts/import_wechat_rental_messages.py src/aptguide/data_import tests/unit/data_import
python3 -c "
import json, re
from pathlib import Path
phone_re = re.compile(r'1[3-9]\d{9}')
for line in Path('data/wechat_rental_listings_sanitized.jsonl').read_text().splitlines():
    rec = json.loads(line)
    for m in phone_re.finditer(rec.get('description_sanitized', '')):
        print('LEAK:', m.group())
print('Check complete.')
"
```
