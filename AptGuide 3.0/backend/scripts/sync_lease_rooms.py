"""Batch import all lease rooms into Milvus room_index collection.

Fetches rooms from lease API, builds text content, generates embeddings,
and inserts into room_index with the schema expected by search_rooms().

Usage:
    uv run python scripts/sync_lease_rooms.py

Requires: APTGUIDE3_LEASE_BASE_URL, APTGUIDE3_INTERNAL_TOKEN,
          APTGUIDE3_EMBEDDING_BASE_URL, APTGUIDE3_EMBEDDING_API_KEY,
          APTGUIDE3_EMBEDDING_MODEL, APTGUIDE3_VECTOR_URI
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import httpx
from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient
from pymilvus.milvus_client.index import IndexParams

from aptguide3.config import get_settings
from aptguide3.integrations.embedding_client import EmbeddingClient
from aptguide3.integrations.vector_client import ROOM_COLLECTION

# Apartment name -> district mapping (derived from apartment names in lease DB)
_APARTMENT_DISTRICT = {
    "回龙观社区": "白云区",
    "白云山脚下居": "白云区",
    "白云新城白领公寓": "白云区",
    "天河智慧城公寓": "天河区",
    "天河公园学寓": "天河区",
    "珠江新城白领公寓": "天河区",
    "体育中心青年社区": "天河区",
    "五山学生公寓": "天河区",
    "北京路步行街公寓": "越秀区",
    "越秀老城温馨居": "越秀区",
    "海珠广场公寓": "海珠区",
    "江南西青年社区": "海珠区",
    "番禺市桥老城温馨居": "番禺区",
    "番禺万博青年社区": "番禺区",
    "南沙万达青年社区": "南沙区",
    "黄埔科学城白领公寓": "黄埔区",
    "黄埔萝岗青年社区": "黄埔区",
    "花都广场公寓": "花都区",
    "增城万达青年社区": "增城区",
    "从化温泉公寓": "从化区",
    "荔湾老城温馨居": "荔湾区",
    "荔湾西关青年社区": "荔湾区",
    "万博商圈白领居": "番禺区",
    "东风东路白领居": "越秀区",
    "中山大学旁学寓": "海珠区",
    "北亭学府公寓": "番禺区",
    "南亭社区公寓": "番禺区",
    "嘉禾望岗地铁公寓": "白云区",
    "大学城青年社区": "番禺区",
    "客村地铁站公寓": "海珠区",
    "市桥老城温馨居": "番禺区",
    "江南西商圈公寓": "海珠区",
    "海珠湖畔居": "海珠区",
    "琶洲会展公寓": "海珠区",
    "越秀公园旁公寓": "越秀区",
}


def build_room_text(room: dict) -> str:
    """Build embedding text from a lease room record."""
    apt_name = room.get("apartmentName", "")
    district = _APARTMENT_DISTRICT.get(apt_name, "")
    room_num = room.get("roomNumber", "")
    rent = room.get("rent", 0)
    tags = room.get("tags", [])
    payment = room.get("paymentTypes", [])
    lease_terms = room.get("leaseTerms", [])
    area = room.get("area")
    layout = room.get("layout")

    parts = [f"[room][广州市][{district}][{apt_name}]"]
    parts.append(f"房间 {room_num}，月租 {rent} 元")
    if layout:
        parts.append(f"户型 {layout}")
    if area:
        parts.append(f"面积 {area}㎡")
    if tags:
        parts.append(f"标签：{'、'.join(tags)}")
    if payment:
        parts.append(f"付款方式：{'、'.join(payment)}")
    if lease_terms:
        parts.append(f"租期：{'、'.join(str(t) + '个月' for t in lease_terms)}")
    return "\n".join(parts)


def fetch_rooms(base_url: str, token: str) -> list[dict]:
    """Fetch all rooms from lease API."""
    headers = {"X-Internal-Token": token}
    with httpx.Client(base_url=base_url, headers=headers, timeout=30.0) as client:
        resp = client.post(
            "/internal/ai/tools/room/search",
            json={"ids": [], "limit": 500},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("rooms", [])


def build_schema() -> CollectionSchema:
    """Create room_index schema matching search_rooms() expectations."""
    fields = [
        FieldSchema("id", DataType.INT64, is_primary=True),
        FieldSchema("title", DataType.VARCHAR, max_length=256),
        FieldSchema("rent", DataType.INT64),
        FieldSchema("district", DataType.VARCHAR, max_length=64),
        FieldSchema("tags", DataType.JSON),
        FieldSchema("payment_type", DataType.VARCHAR, max_length=128),
        FieldSchema("status", DataType.VARCHAR, max_length=32),
        FieldSchema("content", DataType.VARCHAR, max_length=4096),
        FieldSchema("vector", DataType.FLOAT_VECTOR, dim=1024),
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

    # 1. Fetch rooms
    rooms = fetch_rooms(settings.lease_base_url, settings.internal_token.get_secret_value())
    print(f"Fetched {len(rooms)} rooms from lease API")

    # 2. Drop and recreate room_index
    if ROOM_COLLECTION in client.list_collections():
        print(f"Dropping existing {ROOM_COLLECTION}...")
        client.drop_collection(ROOM_COLLECTION)

    print(f"Creating {ROOM_COLLECTION}...")
    schema = build_schema()
    client.create_collection(collection_name=ROOM_COLLECTION, schema=schema)
    index_params = IndexParams()
    index_params.add_index(
        field_name="vector",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": 128},
    )
    client.create_index(collection_name=ROOM_COLLECTION, index_params=index_params)

    # 3. Embed and insert
    insert_data = []
    errors = 0
    for i, room in enumerate(rooms):
        content = build_room_text(room)
        vector = embedding_client.embed(content)
        if not vector:
            print(f"  WARNING: embedding failed for room {room['roomId']}, skipping")
            errors += 1
            continue

        apt_name = room.get("apartmentName", "")
        district = _APARTMENT_DISTRICT.get(apt_name, "")
        tags = room.get("tags", [])
        payment = room.get("paymentTypes", [])
        payment_str = ",".join(payment) if payment else ""

        insert_data.append({
            "id": int(room["roomId"]),
            "title": f"{apt_name} {room.get('roomNumber', '')}",
            "rent": int(room.get("rent", 0)),
            "district": district,
            "tags": tags,
            "payment_type": payment_str,
            "status": "available",
            "content": content,
            "vector": vector,
        })

        if (i + 1) % 20 == 0:
            print(f"  Embedded {i + 1}/{len(rooms)}...")

    print(f"Inserting {len(insert_data)} rooms ({errors} errors)...")
    client.insert(collection_name=ROOM_COLLECTION, data=insert_data)

    # 4. Verify
    client.load_collection(ROOM_COLLECTION)
    import time; time.sleep(2)
    stats = client.get_collection_stats(ROOM_COLLECTION)
    print(f"\nVerification:")
    print(f"  Collection: {ROOM_COLLECTION}")
    print(f"  Total rows: {stats.get('row_count', '?')}")

    sample = client.query(
        collection_name=ROOM_COLLECTION,
        filter="id == 15",
        output_fields=["id", "title", "rent", "district", "status", "payment_type"],
        limit=1,
    )
    if sample:
        print(f"  Sample: {sample[0]}")

    available = client.query(
        collection_name=ROOM_COLLECTION,
        filter='status == "available"',
        output_fields=["id"],
        limit=200,
    )
    print(f"  Available rooms: {len(available)}")
    print("\nDone!")


if __name__ == "__main__":
    main()
