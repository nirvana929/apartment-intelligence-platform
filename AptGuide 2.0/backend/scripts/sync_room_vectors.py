"""Room vector sync script.

Fetches rooms from lease adapter, builds vector records,
embeds changed rooms, and upserts to Milvus.

学习入口：这条脚本是“租赁系统房源 -> 向量文本 -> embedding -> Milvus”的离线入库链路。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openai import OpenAI

from aptguide2.core.config import Settings
from aptguide2.rag.chunking import build_room_vector_record, compute_content_hash
from aptguide2.rag.schemas import RoomVectorRecord
from aptguide2.tools.lease_adapter import LeaseAdapter
from aptguide2.tools.vector_adapter import VectorAdapter


def embed_texts(texts: list[str], settings: Settings) -> list[list[float]]:
    """Embed texts using OpenAI-compatible API."""
    if not texts:
        return []
    client = OpenAI(
        api_key=settings.embedding_api_key.get_secret_value(),
        base_url=settings.embedding_base_url,
    )
    all_embeddings = []
    batch_size = 10
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
        )
        all_embeddings.extend([d.embedding for d in response.data])
    return all_embeddings


async def fetch_rooms(settings: Settings, limit: int = 200) -> list[dict]:
    """Fetch room sync DTOs from lease adapter."""
    adapter = LeaseAdapter(settings=settings)
    try:
        healthy = await adapter.health()
        if not healthy:
            print("WARNING: Lease backend health check failed, attempting sync anyway")
        rooms = await adapter.sync_rooms(limit=limit)
        return rooms
    finally:
        await adapter.close()


def run_sync(limit: int = 200, source_version: int = 1) -> dict:
    """Run the room vector sync process.

    Returns sync report dict.
    """
    settings = Settings()

    report = {
        "sync_id": f"room-sync-{int(time.time())}",
        "total_fetched": 0,
        "added": 0,
        "updated": 0,
        "inactive": 0,
        "embedded": 0,
        "failed": 0,
        "errors": [],
    }

    # 1. 从租赁后端同步房源 DTO。RAG 不直接拥有房源真相，lease 才是源系统。
    rooms = asyncio.run(fetch_rooms(settings, limit))
    report["total_fetched"] = len(rooms)

    if not rooms:
        report["errors"].append("No rooms fetched from lease backend")
        return report

    # 2. 把房源 DTO 转成 RoomVectorRecord，其中 content 是要被 embedding 的文本。
    records: list[RoomVectorRecord] = []
    for room in rooms:
        try:
            record = build_room_vector_record(room, source_version)
            records.append(record)
        except Exception as e:
            report["failed"] += 1
            report["errors"].append(f"Room {room.get('room_id', '?')}: {e}")

    if not records:
        report["errors"].append("No valid room records built")
        return report

    # 3. 确保房源向量 collection 存在。
    adapter = VectorAdapter(
        uri=settings.milvus_uri,
        token=settings.milvus_token,
        dim=settings.embedding_dim,
    )
    adapter.ensure_room_collection()

    # 4. 用 content_hash 判断哪些房源真的变了，避免重复 embedding。
    room_ids = [r.room_id for r in records]
    existing = adapter.get_room_by_ids(room_ids)
    existing_hashes = {r["room_id"]: r.get("content_hash", "") for r in existing}

    # 5. 只同步新增或内容变化的房源。
    changed_records = []
    for rec in records:
        old_hash = existing_hashes.get(rec.room_id)
        if old_hash != rec.content_hash:
            changed_records.append(rec)

    if not changed_records:
        report["errors"].append("No changes detected")
        return report

    # 6. 对变化房源的 content 生成 embedding。
    texts = [rec.content for rec in changed_records]
    embeddings = embed_texts(texts, settings)

    # 7. 写入 Milvus。vector_id 是主键，同房源重复写入会覆盖。
    upsert_pairs = list(zip(changed_records, embeddings))
    upserted = adapter.upsert_room_records(upsert_pairs)

    # Count added vs updated
    for rec in changed_records:
        if rec.room_id in existing_hashes:
            report["updated"] += 1
        else:
            report["added"] += 1

    report["embedded"] = upserted

    # 8. 本次源系统没有返回的历史房源标记 inactive，检索时默认不会召回。
    all_current_ids = set(room_ids)
    client = adapter._ensure_client()
    all_active = client.query(
        collection_name="apt_room_vector",
        filter='status == "active"',
        output_fields=["vector_id", "room_id"],
    )
    stale_ids = [r["vector_id"] for r in all_active if r["room_id"] not in all_current_ids]
    if stale_ids:
        adapter.mark_room_inactive(stale_ids)
        report["inactive"] = len(stale_ids)

    return report


def main():
    parser = argparse.ArgumentParser(description="Sync room vectors to Milvus")
    parser.add_argument("--limit", type=int, default=200, help="Max rooms to fetch from lease")
    parser.add_argument("--source-version", type=int, default=1, help="Source version tag")
    args = parser.parse_args()

    report = run_sync(limit=args.limit, source_version=args.source_version)

    # Write report
    report_dir = Path(__file__).resolve().parent.parent.parent / "evals" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "room_sync_report.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Room Vector Sync Report\n\n")
        f.write(f"**Sync ID:** {report['sync_id']}\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"| --- | ---: |\n")
        f.write(f"| Total fetched | {report['total_fetched']} |\n")
        f.write(f"| Added | {report['added']} |\n")
        f.write(f"| Updated | {report['updated']} |\n")
        f.write(f"| Inactive | {report['inactive']} |\n")
        f.write(f"| Embedded | {report['embedded']} |\n")
        f.write(f"| Failed | {report['failed']} |\n")
        if report["errors"]:
            f.write(f"\n## Errors\n\n")
            for err in report["errors"]:
                f.write(f"- {err}\n")

    print(f"Sync complete. Report: {report_path}")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
