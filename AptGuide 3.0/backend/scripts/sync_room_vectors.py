"""Sync room vectors from lease to Milvus.

Usage:
    uv run python scripts/sync_room_vectors.py

Requires: APTGUIDE3_LEASE_BASE_URL, APTGUIDE3_VECTOR_URI, APTGUIDE3_EMBEDDING_API_KEY
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aptguide3.integrations.embedding_client import EmbeddingClient
from aptguide3.integrations.vector_client import ROOM_COLLECTION, VectorClient
from aptguide3.rag.chunking import build_room_vector_record


async def fetch_rooms(base_url: str) -> list[dict]:
    import httpx
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        resp = await client.get("/internal/ai/tools/sync/rooms")
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", []) if isinstance(data.get("data"), list) else []


def sync_rooms(rooms: list[dict], vector_client: VectorClient, embedding_client: EmbeddingClient, version: int) -> dict:
    inserted = 0
    skipped = 0
    errors = 0
    for room in rooms:
        try:
            record = build_room_vector_record(room, version)
            vector = embedding_client.embed(record["content"])
            if not vector:
                errors += 1
                continue
            record["vector"] = vector
            vector_client._client.upsert(
                collection_name=ROOM_COLLECTION,
                data=[record],
            )
            inserted += 1
        except Exception:
            errors += 1
    return {"inserted": inserted, "skipped": skipped, "errors": errors, "total": len(rooms)}


if __name__ == "__main__":
    import os
    base_url = os.environ.get("APTGUIDE3_LEASE_BASE_URL", "")
    if not base_url:
        print("ERROR: APTGUIDE3_LEASE_BASE_URL not set")
        sys.exit(1)
    rooms = asyncio.run(fetch_rooms(base_url))
    print(f"Fetched {len(rooms)} rooms from lease")
    # Note: full sync requires VectorClient and EmbeddingClient setup
    # This script is a template; actual execution needs env vars
    print("Sync template ready. Set APTGUIDE3_VECTOR_URI and APTGUIDE3_EMBEDDING_API_KEY to run.")
