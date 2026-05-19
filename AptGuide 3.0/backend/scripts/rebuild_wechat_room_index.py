"""Rebuild wechat_room_index Milvus collection with lease_room_id field.

Reads the original JSONL data source, generates embeddings, applies identity
mappings from CSV, and inserts into a fresh collection with lease_room_id.

Usage:
    uv run python scripts/rebuild_wechat_room_index.py

Requires: APTGUIDE3_VECTOR_URI, APTGUIDE3_EMBEDDING_BASE_URL, APTGUIDE3_EMBEDDING_API_KEY, APTGUIDE3_EMBEDDING_MODEL
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient
from pymilvus.milvus_client.index import IndexParams

from aptguide3.config import get_settings
from aptguide3.integrations.embedding_client import EmbeddingClient

COLLECTION_NAME = "wechat_room_index"
JSONL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "AptGuide" / "data" / "wechat_rental_listings_sanitized.jsonl"
IDENTITY_CSV = Path(__file__).resolve().parent.parent / "evals" / "datasets" / "local_room_identity_mappings.csv"
VECTOR_DIM = 1024


def load_identity_mappings(csv_path: Path) -> dict[str, int]:
    """Read identity CSV and return {source_record_id: business_room_id}."""
    mappings: dict[str, int] = {}
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            rid = row["business_room_id"].strip()
            if rid:
                mappings[row["source_record_id"]] = int(rid)
    return mappings


def build_text_content(record: dict) -> str:
    """Build embedding text from a wechat rental listing record."""
    district = record.get("district_name", "")
    area = record.get("area_label", "")
    rent_min = record.get("rent_min", 0)
    rent_max = record.get("rent_max", 0)
    tags = record.get("rental_tags", [])
    facilities = record.get("facility_tags", [])
    metro = record.get("metro_stations", [])
    payment = record.get("payment_tags", [])
    desc = record.get("description_sanitized", "")

    parts = [
        f"[room][广州市][{district}][{area}]",
        f"月租 {rent_min}-{rent_max} 元",
    ]
    if tags:
        parts.append(f"标签：{'、'.join(tags)}")
    if facilities:
        parts.append(f"设施：{'、'.join(facilities)}")
    if metro:
        parts.append(f"地铁：{'、'.join(metro)}")
    if payment:
        parts.append(f"付款：{'、'.join(payment)}")
    if desc:
        parts.append(desc)
    return "\n".join(parts)


def build_schema() -> CollectionSchema:
    """Create schema with lease_room_id field."""
    fields = [
        FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),
        FieldSchema("content", DataType.VARCHAR, max_length=4096),
        FieldSchema("district", DataType.VARCHAR, max_length=64),
        FieldSchema("area_label", DataType.VARCHAR, max_length=128),
        FieldSchema("rent_min", DataType.INT64),
        FieldSchema("rent_max", DataType.INT64),
        FieldSchema("tags", DataType.JSON),
        FieldSchema("metro_stations", DataType.JSON),
        FieldSchema("facility_tags", DataType.JSON),
        FieldSchema("payment_tags", DataType.JSON),
        FieldSchema("lease_room_id", DataType.INT64, nullable=True),
        FieldSchema("vector", DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
    ]
    return CollectionSchema(fields, enable_dynamic_field=False)


def main() -> None:
    settings = get_settings()
    client = MilvusClient(uri=settings.vector_uri)
    embedding_client = EmbeddingClient(
        base_url=settings.embedding_base_url,
        api_key=settings.embedding_api_key.get_secret_value(),
        model=settings.embedding_model,
    )

    # 1. Load identity mappings
    mappings = load_identity_mappings(IDENTITY_CSV)
    print(f"Loaded {len(mappings)} identity mappings")

    # 2. Read JSONL source data
    records = []
    with open(JSONL_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    print(f"Read {len(records)} records from {JSONL_PATH.name}")

    # 3. Drop existing collection (if any)
    if COLLECTION_NAME in client.list_collections():
        print(f"Dropping existing {COLLECTION_NAME}...")
        client.drop_collection(COLLECTION_NAME)

    # 4. Create new collection
    print(f"Creating {COLLECTION_NAME} with lease_room_id field...")
    schema = build_schema()
    client.create_collection(collection_name=COLLECTION_NAME, schema=schema)
    index_params = IndexParams()
    index_params.add_index(
        field_name="vector",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": 128},
    )
    client.create_index(collection_name=COLLECTION_NAME, index_params=index_params)

    # 5. Generate embeddings and insert
    insert_data = []
    matched = 0
    errors = 0
    for i, record in enumerate(records):
        source_id = f"wechat-{i + 1:03d}"
        lease_id = mappings.get(source_id)
        if lease_id is not None:
            matched += 1

        content = build_text_content(record)
        vector = embedding_client.embed(content)
        if not vector:
            print(f"  WARNING: embedding failed for {source_id}, skipping")
            errors += 1
            continue

        insert_data.append({
            "id": source_id,
            "content": content,
            "district": record.get("district_name", ""),
            "area_label": record.get("area_label", ""),
            "rent_min": record.get("rent_min", 0),
            "rent_max": record.get("rent_max", 0),
            "tags": record.get("rental_tags", []),
            "metro_stations": record.get("metro_stations", []),
            "facility_tags": record.get("facility_tags", []),
            "payment_tags": record.get("payment_tags", []),
            "lease_room_id": lease_id,
            "vector": vector,
        })

        if (i + 1) % 10 == 0:
            print(f"  Embedded {i + 1}/{len(records)}...")

    print(f"Inserting {len(insert_data)} rows ({matched} with lease_room_id, {errors} errors)...")
    client.insert(collection_name=COLLECTION_NAME, data=insert_data)

    # 6. Verify
    client.load_collection(COLLECTION_NAME)
    import time
    time.sleep(2)
    stats = client.get_collection_stats(COLLECTION_NAME)
    print(f"\nVerification:")
    print(f"  Collection: {COLLECTION_NAME}")
    print(f"  Total rows: {stats.get('row_count', '?')}")

    sample = client.query(
        collection_name=COLLECTION_NAME,
        filter='id == "wechat-001"',
        output_fields=["id", "lease_room_id", "district", "area_label"],
        limit=1,
    )
    if sample:
        print(f"  Sample: {sample[0]}")

    with_lease = client.query(
        collection_name=COLLECTION_NAME,
        filter="lease_room_id > 0",
        output_fields=["id"],
        limit=100,
    )
    print(f"  Rows with lease_room_id > 0: {len(with_lease)}")
    print("\nDone!")


if __name__ == "__main__":
    main()
