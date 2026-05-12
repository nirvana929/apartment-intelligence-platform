from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from aptguide2.data_import.wechat_local_mysql_parser import (
    extract_listing,
    parse_message_blocks,
)

CREATE_TABLE_SQL = """\
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
);"""


def sql_quote(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def listing_to_insert_sql(listing: dict) -> str:
    columns = [
        "source_type",
        "authenticity",
        "verification_status",
        "availability_status",
        "source_file",
        "source_group",
        "source_message_hash",
        "message_time",
        "sender_alias",
        "message_type",
        "city_name",
        "district_name",
        "area_label",
        "metro_lines",
        "metro_stations",
        "layouts",
        "rent_min",
        "rent_max",
        "payment_tags",
        "facility_tags",
        "rental_tags",
        "phone_numbers",
        "wechat_ids",
        "contact_text",
        "description_text",
        "raw_text",
        "is_active",
        "appointable",
        "dedupe_key",
    ]
    values = ", ".join(sql_quote(listing.get(column)) for column in columns)
    updates = ", ".join(
        f"{column}=VALUES({column})"
        for column in columns
        if column not in {"source_message_hash"}
    )
    return (
        f"INSERT INTO external_wechat_rental_listing ({', '.join(columns)}) VALUES ({values}) "
        f"ON DUPLICATE KEY UPDATE {updates};"
    )


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--raw-sample-limit", type=int, default=50)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    files = sorted(input_dir.glob("*.txt"))
    listings_by_dedupe: dict[str, dict] = {}
    raw_samples: list[dict] = []
    stats = Counter()

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        blocks = parse_message_blocks(text, str(path))
        stats["message_blocks"] += len(blocks)
        for block in blocks:
            if len(raw_samples) < args.raw_sample_limit:
                raw_samples.append(
                    {
                        "source_file": block.source_file,
                        "source_group": block.source_group,
                        "message_time": block.message_time,
                        "sender_alias": block.sender_alias,
                        "message_type": block.message_type,
                        "raw_content": block.body[:500],
                        "content_hash": block.content_hash,
                    }
                )
            if block.message_type != "text":
                stats[f"ignored_{block.message_type}"] += 1
                continue
            listing = extract_listing(
                source_file=block.source_file,
                source_group=block.source_group,
                message_time=block.message_time,
                sender_alias=block.sender_alias,
                message_type=block.message_type,
                body=block.body,
            )
            if listing is None:
                stats["rejected_text"] += 1
                continue
            stats["accepted_text"] += 1
            listings_by_dedupe.setdefault(listing["dedupe_key"], listing)

    listings = sorted(
        listings_by_dedupe.values(),
        key=lambda item: (
            item.get("district_name") or "",
            item.get("rent_min") or 0,
            item["source_message_hash"],
        ),
    )

    # Strip extraction_warnings from output
    for listing in listings:
        listing.pop("extraction_warnings", None)

    write_jsonl(output_dir / "wechat_local_mysql_listings.jsonl", listings)
    write_jsonl(output_dir / "wechat_local_mysql_raw_messages_sample.jsonl", raw_samples)

    with (output_dir / "wechat_local_mysql_seed.sql").open("w", encoding="utf-8") as file:
        file.write("-- WeChat real rental listing import. Local/test only.\n")
        file.write("-- Includes phone numbers and WeChat IDs for local use.\n")
        file.write("-- Do not run against production.\n\n")
        file.write(CREATE_TABLE_SQL)
        file.write("\n\n")
        for listing in listings:
            file.write(listing_to_insert_sql(listing))
            file.write("\n")

    print(json.dumps({"stats": dict(stats), "deduped_listings": len(listings)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
