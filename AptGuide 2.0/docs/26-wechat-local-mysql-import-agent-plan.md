# WeChat Local MySQL Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import real WeChat rental messages from local txt files into local MySQL as structured external rental listings, including phone and WeChat contact fields.

**Architecture:** This plan only covers local database import. The parser reads `参考资料/微信租房消息/*.txt`, extracts rental listing fields and contact fields, deduplicates repeated posts, and generates idempotent SQL for a standalone local MySQL table. It does not implement search behavior, appointment behavior, or other downstream features.

**Tech Stack:** Python 3.12, pytest, ruff, JSONL, MySQL SQL seed files, existing AptGuide 2.0 backend script layout.

---

## 0. Scope

This document is for the agent that will implement local WeChat rental data import.

You are responsible for:

- parsing local WeChat txt exports under `参考资料/微信租房消息`;
- extracting structured listing data;
- extracting phone numbers and WeChat IDs when present;
- preserving source traceability with `source_file`, `source_group`, `message_time`, and `source_message_hash`;
- deduplicating repeated group posts;
- generating reviewable JSONL output;
- generating idempotent local MySQL SQL;
- writing tests and a short import report.

You are not responsible for:

- running SQL against production;
- implementing non-database downstream features;
- implementing search filters;
- implementing appointment or contact workflow;
- building an admin UI;
- changing existing `room_info` platform inventory tables.

## 1. Required Reading

Read these before editing:

1. `AptGuide 2.0/backend/pyproject.toml`
2. `参考资料/微信租房消息/广州租房群A134_全部消息.txt`
3. `参考资料/微信租房消息/广州租房群A134_消息.txt`
4. Existing scripts in `AptGuide 2.0/backend/scripts/`
5. Existing tests under `AptGuide 2.0/backend/tests/unit/`

## 2. Data Positioning

These WeChat messages are real posted rental data. They should be imported as **external rental listings**, not as platform verified inventory.

Default status fields:

| Field | Default |
| --- | --- |
| `source_type` | `WECHAT_GROUP` |
| `authenticity` | `REAL_POSTED` |
| `verification_status` | `UNVERIFIED` |
| `availability_status` | `UNKNOWN` |
| `is_active` | `1` |
| `appointable` | `0` |

Local import path:

```text
WeChat txt
  -> parser
  -> JSONL review artifact
  -> local MySQL external_wechat_rental_listing
```

## 3. Contact Policy For This Local Import

Phone numbers and WeChat IDs may be stored because this dataset is intended for local use.

Store contacts in explicit contact fields, not mixed into derived fields:

- `phone_numbers` JSON
- `wechat_ids` JSON
- `contact_text` TEXT

The structured description field may still include a concise version of the post, but contacts should be separately extracted for easier filtering and review.

## 4. Deliverables

Create these files:

```text
AptGuide 2.0/backend/src/aptguide2/data_import/__init__.py
AptGuide 2.0/backend/src/aptguide2/data_import/wechat_local_mysql_parser.py
AptGuide 2.0/backend/scripts/import_wechat_local_mysql.py
AptGuide 2.0/backend/tests/unit/data_import/__init__.py
AptGuide 2.0/backend/tests/unit/data_import/test_wechat_local_mysql_parser.py
AptGuide 2.0/backend/data/wechat_local_mysql_listings.jsonl
AptGuide 2.0/backend/data/wechat_local_mysql_seed.sql
AptGuide 2.0/backend/evals/reports/wechat_local_mysql_import_report.md
```

If `AptGuide 2.0/backend/data/` does not exist, create it.

## 5. MySQL Table

Generate SQL for this standalone local table:

```sql
CREATE TABLE IF NOT EXISTS external_wechat_rental_listing (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  source_type VARCHAR(32) NOT NULL DEFAULT 'WECHAT_GROUP',
  authenticity VARCHAR(32) NOT NULL DEFAULT 'REAL_POSTED',
  verification_status VARCHAR(32) NOT NULL DEFAULT 'UNVERIFIED',
  availability_status VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
  source_file VARCHAR(255) NOT NULL,
  source_group VARCHAR(128) NOT NULL,
  source_message_hash VARCHAR(80) NOT NULL,
  message_time DATETIME NULL,
  sender_alias VARCHAR(128) NULL,
  message_type VARCHAR(32) NOT NULL,
  city_name VARCHAR(64) NULL,
  district_name VARCHAR(64) NULL,
  area_label VARCHAR(128) NULL,
  metro_lines JSON NULL,
  metro_stations JSON NULL,
  layouts JSON NULL,
  rent_min INT NULL,
  rent_max INT NULL,
  payment_tags JSON NULL,
  facility_tags JSON NULL,
  rental_tags JSON NULL,
  phone_numbers JSON NULL,
  wechat_ids JSON NULL,
  contact_text TEXT NULL,
  description_text TEXT NOT NULL,
  raw_text MEDIUMTEXT NOT NULL,
  is_active TINYINT NOT NULL DEFAULT 1,
  appointable TINYINT NOT NULL DEFAULT 0,
  dedupe_key VARCHAR(80) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_external_wechat_rental_source_hash (source_message_hash),
  KEY idx_external_wechat_rental_city_district (city_name, district_name),
  KEY idx_external_wechat_rental_rent (rent_min, rent_max),
  KEY idx_external_wechat_rental_dedupe (dedupe_key)
);
```

Use `INSERT INTO ... ON DUPLICATE KEY UPDATE` for every listing row.

Do not insert into `room_info`, `apartment_info`, or other platform verified inventory tables in this task.

## 6. JSONL Output Schema

File: `AptGuide 2.0/backend/data/wechat_local_mysql_listings.jsonl`

Each line:

```json
{
  "source_type": "WECHAT_GROUP",
  "authenticity": "REAL_POSTED",
  "verification_status": "UNVERIFIED",
  "availability_status": "UNKNOWN",
  "source_file": "参考资料/微信租房消息/广州租房群A134_全部消息.txt",
  "source_group": "广州租房群A134-禁中介",
  "source_message_hash": "sha256:...",
  "message_time": "2026-04-30 06:34",
  "sender_alias": "爱杰的可可",
  "message_type": "text",
  "city_name": "广州市",
  "district_name": "天河区",
  "area_label": "黄村/珠村",
  "metro_lines": ["4号线", "21号线", "13号线"],
  "metro_stations": ["黄村", "珠村"],
  "layouts": [
    {"layout": "单间", "rent_min": 599, "rent_max": null},
    {"layout": "一房一厅", "rent_min": 699, "rent_max": null}
  ],
  "rent_min": 599,
  "rent_max": 699,
  "payment_tags": ["押一付一"],
  "facility_tags": ["密码锁"],
  "rental_tags": ["房东直租", "无中介费", "民水民电", "宠物友好", "近地铁"],
  "phone_numbers": ["15202955805"],
  "wechat_ids": [],
  "contact_text": "联系方式：15202955805（微信同步）",
  "description_text": "天河黄村、珠村附近房东直租，步行约6分钟到地铁，民水民电，押一付一，单间599起，一房一厅699起。",
  "raw_text": "天河黄村4/21珠村13号线三地铁线房东直租...",
  "is_active": true,
  "appointable": false,
  "dedupe_key": "sha256:..."
}
```

## 7. Parser Rules

### 7.1 Message Blocks

Parse blocks split by `---`.

Header regex:

```python
r"^\[(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s+(?P<sender>.*?)\s+\((?P<type>[^)]+)\):\s*(?P<body>.*)$"
```

Only `text` messages become listing rows. Ignore `image`, `video`, and `share` rows for this import.

### 7.2 Contact Extraction

Extract phone numbers:

```python
r"1[3-9]\d{9}"
```

Extract likely WeChat IDs from phrases such as:

- `微信：abc123`
- `微信/电话同号：abc123`
- `加V abc123`
- `微信请添加电话号码`

If the post says WeChat is phone-synced and has phone numbers, keep phone numbers in `phone_numbers`; `wechat_ids` may be empty.

Store the original contact sentence in `contact_text`.

### 7.3 District and Area Mapping

Use conservative keyword mapping:

```python
DISTRICT_KEYWORDS = {
    "天河区": ["天河", "黄村", "珠村", "棠下", "棠东", "上社", "车陂", "科韵路", "员村", "体育西", "珠江新城"],
    "番禺区": ["番禺", "大石", "市桥", "南村万博", "汉溪长隆", "大学城", "广州南站"],
    "白云区": ["白云", "鹤边", "马务", "嘉禾", "嘉禾望岗", "新市", "沙贝", "横沙"],
    "荔湾区": ["荔湾", "菊树", "西塱", "坑口", "芳村", "黄沙", "上下九"],
    "海珠区": ["海珠", "客村", "琶洲", "昌岗", "沙园", "凤凰新村", "中大", "鹭江", "赤岗"],
    "越秀区": ["越秀", "北京路", "公园前", "淘金", "小北", "东山口"]
}
```

### 7.4 Layout and Rent

Normalize layouts to:

- `单间`
- `一房一厅`
- `两房一厅`

Support examples:

```text
单间680-950
一房980-1580
两房1380-2400
精装带阳台单间 599起
一房一厅：799-1199
精品单间 450～
```

Reject a text message as non-listing if:

- no rent is found;
- rent is below 300 or above 20000;
- no district/area/metro/layout signal is found.

### 7.5 Tags

Map these tags:

```python
TAG_KEYWORDS = {
    "房东直租": ["房东直租", "房东", "自家新房"],
    "无中介费": ["无中介费", "0中介费"],
    "近地铁": ["地铁", "分钟到地铁"],
    "民水民电": ["民水民电", "民水电"],
    "押一付一": ["押一付一"],
    "可短租": ["可短租", "短租"],
    "不短租": ["不短租"],
    "宠物友好": ["可养猫", "宠物友好", "养猫"],
    "采光好": ["采光好", "阳光", "光线好", "光线充足"],
    "家电齐全": ["家电齐全", "家具齐全", "拎包入住", "领包入住"],
    "独卫": ["独卫", "独立卫生间", "独立洗手间", "洗手间"],
    "阳台": ["阳台", "独立阳台"]
}
```

Conflict rule:

- If text contains `不短租`, include `不短租` and do not include `可短租`.

## 8. Task L1: Parser Tests

**Files:**

- Create: `AptGuide 2.0/backend/tests/unit/data_import/__init__.py`
- Create: `AptGuide 2.0/backend/tests/unit/data_import/test_wechat_local_mysql_parser.py`

- [ ] **Step 1: Create the test package**

Create empty file:

```text
AptGuide 2.0/backend/tests/unit/data_import/__init__.py
```

- [ ] **Step 2: Write parser tests**

Create `AptGuide 2.0/backend/tests/unit/data_import/test_wechat_local_mysql_parser.py`:

```python
from aptguide2.data_import.wechat_local_mysql_parser import (
    extract_contacts,
    extract_listing,
    parse_message_blocks,
)


def test_parse_message_blocks_keeps_sender_and_text_body():
    text = """Ⱥ��: 广州租房群A134-禁中介

[2026-05-06 15:43] 广州房东直租 (text): 🏠 天河棠下-上社房东自建屋
单间680-950
电话同步18620724159
---"""

    blocks = parse_message_blocks(text, "sample.txt")

    assert len(blocks) == 1
    assert blocks[0].message_time == "2026-05-06 15:43"
    assert blocks[0].sender_alias == "广州房东直租"
    assert blocks[0].message_type == "text"
    assert "电话同步18620724159" in blocks[0].body


def test_extract_contacts_keeps_phone_numbers():
    contacts = extract_contacts("请加微信 18998438337微信，电话同步18620724159")

    assert contacts["phone_numbers"] == ["18998438337", "18620724159"]
    assert "18998438337" in contacts["contact_text"]


def test_extract_listing_keeps_contact_fields():
    body = """天河黄村4/21珠村13号线三地铁线房东直租
✅ 步行6分钟到地铁
✅ 房东直租 无中介费
✅ 民水民电
✅ 押一付一
599起拿下阳光大单间
699起住一房一厅
联系方式：15202955805（微信同步）"""

    listing = extract_listing(
        source_file="sample.txt",
        source_group="广州租房群A134-禁中介",
        message_time="2026-04-30 06:34",
        sender_alias="爱杰的可可",
        message_type="text",
        body=body,
    )

    assert listing is not None
    assert listing["source_type"] == "WECHAT_GROUP"
    assert listing["authenticity"] == "REAL_POSTED"
    assert listing["verification_status"] == "UNVERIFIED"
    assert listing["availability_status"] == "UNKNOWN"
    assert listing["district_name"] == "天河区"
    assert listing["rent_min"] == 599
    assert listing["rent_max"] == 699
    assert listing["phone_numbers"] == ["15202955805"]
    assert "15202955805" in listing["contact_text"]
    assert "15202955805" in listing["raw_text"]
    assert listing["is_active"] is True
    assert listing["appointable"] is False


def test_extract_listing_rejects_text_without_rent():
    listing = extract_listing(
        source_file="sample.txt",
        source_group="广州租房群A134-禁中介",
        message_time="2026-05-06 16:12",
        sender_alias="小师妹",
        message_type="text",
        body="看到自己附近的房东，直接加房东微信，地铁30分钟左右可以到达的地方，都是优选！",
    )

    assert listing is None
```

- [ ] **Step 3: Run failing tests**

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/data_import/test_wechat_local_mysql_parser.py -v
```

Expected: fail because parser module does not exist yet.

## 9. Task L2: Parser Implementation

**Files:**

- Create: `AptGuide 2.0/backend/src/aptguide2/data_import/__init__.py`
- Create: `AptGuide 2.0/backend/src/aptguide2/data_import/wechat_local_mysql_parser.py`

- [ ] **Step 1: Implement parser module**

Implement functions:

```python
parse_message_blocks(text: str, source_file: str) -> list[WechatMessageBlock]
extract_contacts(text: str) -> dict[str, list[str] | str | None]
extract_listing(...) -> dict | None
```

Required behavior:

- preserve `sender_alias`;
- preserve `raw_text`;
- extract `phone_numbers`;
- extract likely `wechat_ids`;
- compute `source_message_hash`;
- compute `dedupe_key`;
- return `None` for non-listing text messages.

- [ ] **Step 2: Run parser tests**

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/data_import/test_wechat_local_mysql_parser.py -v
```

Expected: pass.

- [ ] **Step 3: Run ruff**

Run:

```bash
cd "AptGuide 2.0/backend"
uv run ruff check src/aptguide2/data_import tests/unit/data_import
```

Expected: pass.

## 10. Task L3: Import Script

**Files:**

- Create: `AptGuide 2.0/backend/scripts/import_wechat_local_mysql.py`
- Generate: `AptGuide 2.0/backend/data/wechat_local_mysql_listings.jsonl`
- Generate: `AptGuide 2.0/backend/data/wechat_local_mysql_seed.sql`

- [ ] **Step 1: Implement script**

The script must:

- accept `--input-dir`;
- accept `--output-dir`;
- read all `*.txt`;
- parse all blocks;
- extract text listings;
- deduplicate by `dedupe_key`;
- write JSONL;
- write SQL with `CREATE TABLE IF NOT EXISTS external_wechat_rental_listing`;
- write `INSERT INTO ... ON DUPLICATE KEY UPDATE`;
- print counts for total blocks, accepted listings, rejected text messages, and deduped listings.

- [ ] **Step 2: Run script**

Run:

```bash
cd "AptGuide 2.0/backend"
uv run python scripts/import_wechat_local_mysql.py \
  --input-dir "../../参考资料/微信租房消息" \
  --output-dir "data"
```

Expected:

- command exits 0;
- `data/wechat_local_mysql_listings.jsonl` exists;
- `data/wechat_local_mysql_seed.sql` exists;
- generated listing count is greater than 0.

- [ ] **Step 3: Verify contacts are retained**

Run:

```bash
cd "AptGuide 2.0/backend"
rg -n "phone_numbers|wechat_ids|contact_text|1[3-9][0-9]{9}" data/wechat_local_mysql_listings.jsonl data/wechat_local_mysql_seed.sql
```

Expected: matches exist.

- [ ] **Step 4: Verify SQL table semantics**

Run:

```bash
cd "AptGuide 2.0/backend"
rg -n "external_wechat_rental_listing|phone_numbers|wechat_ids|contact_text|raw_text|ON DUPLICATE KEY UPDATE" data/wechat_local_mysql_seed.sql
```

Expected: all terms appear.

## 11. Task L4: Import Report

**Files:**

- Create: `AptGuide 2.0/backend/evals/reports/wechat_local_mysql_import_report.md`

- [ ] **Step 1: Generate metrics**

Run:

```bash
cd "AptGuide 2.0/backend"
python - <<'PY'
import json
from collections import Counter
from pathlib import Path

records = [json.loads(line) for line in Path("data/wechat_local_mysql_listings.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
print("total", len(records))
print("districts", Counter(record.get("district_name") for record in records))
print("with_phone", sum(1 for record in records if record.get("phone_numbers")))
print("with_wechat", sum(1 for record in records if record.get("wechat_ids")))
print("rent_min", min(record["rent_min"] for record in records if record.get("rent_min") is not None))
print("rent_max", max(record["rent_max"] for record in records if record.get("rent_max") is not None))
PY
```

- [ ] **Step 2: Write report**

Create `AptGuide 2.0/backend/evals/reports/wechat_local_mysql_import_report.md`:

```markdown
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
| `AptGuide 2.0/backend/data/wechat_local_mysql_listings.jsonl` | Reviewable structured listing output |
| `AptGuide 2.0/backend/data/wechat_local_mysql_seed.sql` | Idempotent local MySQL import SQL |

## Coverage

- Imported listings:
- District distribution:
- Listings with phone numbers:
- Listings with WeChat IDs:
- Min rent:
- Max rent:

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
```

Fill the Coverage section with metrics from Step 1.

## 12. Final Verification

- [ ] **Step 1: Run tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/data_import/test_wechat_local_mysql_parser.py -v
```

- [ ] **Step 2: Run lint**

```bash
cd "AptGuide 2.0/backend"
uv run ruff check scripts/import_wechat_local_mysql.py src/aptguide2/data_import tests/unit/data_import
```

- [ ] **Step 3: Regenerate artifacts**

```bash
cd "AptGuide 2.0/backend"
uv run python scripts/import_wechat_local_mysql.py \
  --input-dir "../../参考资料/微信租房消息" \
  --output-dir "data"
```

- [ ] **Step 4: Verify SQL**

```bash
cd "AptGuide 2.0/backend"
rg -n "CREATE TABLE IF NOT EXISTS external_wechat_rental_listing|ON DUPLICATE KEY UPDATE|phone_numbers|wechat_ids|raw_text" data/wechat_local_mysql_seed.sql
```

## 13. Acceptance Criteria

Implementation is complete only when:

- parser tests pass;
- ruff passes;
- JSONL output exists;
- SQL output exists;
- SQL creates `external_wechat_rental_listing`;
- SQL uses `ON DUPLICATE KEY UPDATE`;
- phone numbers are extracted when present;
- WeChat IDs are extracted when present;
- source traceability fields exist;
- imported records default to `REAL_POSTED`, `UNVERIFIED`, `UNKNOWN`, `is_active=1`, `appointable=0`;
- no existing platform inventory table is modified.
