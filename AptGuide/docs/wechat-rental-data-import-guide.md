# WeChat Rental Data Import Guide

## Decision

WeChat rental messages are imported as external real listing leads.

They are real posted market data, not generated seed data. They are not treated as verified platform inventory until a separate human or operational verification process updates their status.

## Default Statuses

| Field | Default |
| --- | --- |
| `source_type` | `WECHAT_GROUP` |
| `authenticity` | `REAL_POSTED` |
| `verification_status` | `UNVERIFIED` |
| `availability_status` | `UNKNOWN` |
| `rag_visible` | `true` after sanitization |
| `appointable` | `false` |

## Import Command

```bash
cd AptGuide
uv run python scripts/import_wechat_rental_messages.py \
  --input-dir "../参考资料/微信租房消息" \
  --output-dir "data"
```

## Outputs

| File | Description |
| --- | --- |
| `data/wechat_rental_raw_messages_sample.jsonl` | Redacted raw-message sample for review |
| `data/wechat_rental_listings_sanitized.jsonl` | Sanitized structured listing leads |
| `data/wechat_rental_listings_seed.sql` | Local/test SQL import |

## Safety Checks

Run before using generated data:

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

## RAG Usage

RAG may use the sanitized listing records for:

- external real listing search;
- market rent range summaries;
- area and metro coverage;
- natural-language rental intent matching;
- comparison with platform verified inventory.

RAG must disclose that these records are external real listing leads and may need manual confirmation.

## RAG Query Filtering

Metadata fields for filtering in Milvus:

```json
{
  "content_type": "external_listing",
  "source_type": "WECHAT_GROUP",
  "data_source": "wechat_real_listing",
  "authenticity": "REAL_POSTED",
  "verification_status": "UNVERIFIED",
  "availability_status": "UNKNOWN",
  "appointable": false
}
```

Recommended query modes:

| Mode | Filter | Use Case |
| --- | --- | --- |
| `platform_only` | `data_source != "wechat_real_listing"` | Default: only platform verified inventory |
| `external_only` | `data_source == "wechat_real_listing"` | User asks about market/external listings |
| `mixed` | No filter | User wants all available information |

Default mode should be `platform_only`. Switch to `external_only` or `mixed` when user explicitly asks about real market listings, price ranges, or external leads.

## Upgrade Path To Verified Inventory

Automated import cannot set a listing as verified.

An operations workflow may later update:

```text
verification_status = VERIFIED
availability_status = AVAILABLE
appointable = true
```

only after the listing is manually confirmed and connected to a platform-supported contact or appointment process.
