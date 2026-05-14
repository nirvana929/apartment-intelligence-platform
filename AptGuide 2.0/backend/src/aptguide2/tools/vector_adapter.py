"""Vector adapter — wraps pymilvus for apt_room_vector and apt_rental_kb collections.

这个适配器把业务代码和 Milvus SDK 隔开：上层只关心“写入房源/KB 向量”
和“按向量搜索”，不直接依赖 Milvus 的字段、索引和返回格式细节。
"""

from __future__ import annotations

import json
import time
from typing import Any

from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient
from pymilvus.milvus_client.index import IndexParams

from aptguide2.rag.schemas import KBChunk, RoomVectorRecord

# Collection names
ROOM_COLLECTION = "apt_room_vector"
KB_COLLECTION = "apt_rental_kb"

# Defaults
DEFAULT_METRIC = "COSINE"


class VectorAdapter:
    """Manages Milvus collections for room vectors and KB chunks."""

    def __init__(self, uri: str = "http://localhost:19530", token: str = "", dim: int = 1536):
        self.uri = uri
        self.token = token
        self.dim = dim
        self.client: MilvusClient | None = None

    def connect(self) -> None:
        """Connect to Milvus."""
        self.client = MilvusClient(uri=self.uri, token=self.token)

    def _ensure_client(self) -> MilvusClient:
        # 延迟连接：只有真正访问 Milvus 时才创建 client，方便单元测试和脚本启动。
        if self.client is None:
            self.connect()
        assert self.client is not None
        return self.client

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def ensure_room_collection(self) -> None:
        """Create apt_room_vector collection if it doesn't exist."""
        client = self._ensure_client()
        if client.has_collection(ROOM_COLLECTION):
            return

        # 房源 collection 同时保存向量和可过滤字段。
        # district_id/rent/status 等字段用于精确过滤，embedding 用于语义召回。
        schema = CollectionSchema(fields=[
            FieldSchema("vector_id", DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema("room_id", DataType.INT64),
            FieldSchema("apartment_id", DataType.INT64),
            FieldSchema("apartment_name", DataType.VARCHAR, max_length=128),
            FieldSchema("city_id", DataType.INT32),
            FieldSchema("district_id", DataType.INT32),
            FieldSchema("district_name", DataType.VARCHAR, max_length=64),
            FieldSchema("rent", DataType.INT32),
            FieldSchema("payment_types", DataType.VARCHAR, max_length=256),
            FieldSchema("lease_terms", DataType.VARCHAR, max_length=128),
            FieldSchema("tags", DataType.VARCHAR, max_length=512),
            FieldSchema("facilities", DataType.VARCHAR, max_length=512),
            FieldSchema("profile_type", DataType.VARCHAR, max_length=16),
            FieldSchema("content", DataType.VARCHAR, max_length=4096),
            FieldSchema("content_hash", DataType.VARCHAR, max_length=128),
            FieldSchema("source_version", DataType.INT64),
            FieldSchema("status", DataType.VARCHAR, max_length=16),
            FieldSchema("updated_at", DataType.INT64),
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=self.dim),
        ], description="Room vectors for semantic recall")

        client.create_collection(
            collection_name=ROOM_COLLECTION,
            schema=schema,
        )
        index_params = IndexParams()
        index_params.add_index(
            field_name="embedding",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 200},
        )
        client.create_index(
            collection_name=ROOM_COLLECTION,
            index_params=index_params,
        )
        # 标量索引用于加速 filter 表达式，例如 rent <= 2000、status == active。
        for field in ("room_id", "district_id", "rent", "status", "content_hash"):
            scalar_idx = IndexParams()
            scalar_idx.add_index(field_name=field, index_type="AUTOINDEX")
            client.create_index(
                collection_name=ROOM_COLLECTION,
                index_params=scalar_idx,
            )

    def ensure_kb_collection(self) -> None:
        """Create apt_rental_kb collection if it doesn't exist."""
        client = self._ensure_client()
        if client.has_collection(KB_COLLECTION):
            return

        # KB collection 以 chunk 为最小检索单元。
        # module/risk_level/status 用于控制召回范围和回答安全性。
        schema = CollectionSchema(fields=[
            FieldSchema("chunk_id", DataType.VARCHAR, is_primary=True, max_length=128),
            FieldSchema("doc_id", DataType.VARCHAR, max_length=64),
            FieldSchema("doc_type", DataType.VARCHAR, max_length=32),
            FieldSchema("module", DataType.VARCHAR, max_length=32),
            FieldSchema("title", DataType.VARCHAR, max_length=256),
            FieldSchema("tags", DataType.VARCHAR, max_length=512),
            FieldSchema("content", DataType.VARCHAR, max_length=8192),
            FieldSchema("content_hash", DataType.VARCHAR, max_length=128),
            FieldSchema("version", DataType.INT64),
            FieldSchema("release_id", DataType.VARCHAR, max_length=64),
            FieldSchema("status", DataType.VARCHAR, max_length=16),
            FieldSchema("risk_level", DataType.VARCHAR, max_length=8),
            FieldSchema("updated_at", DataType.INT64),
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=self.dim),
        ], description="Knowledge base chunks for rental rules QA")

        client.create_collection(
            collection_name=KB_COLLECTION,
            schema=schema,
        )
        index_params = IndexParams()
        index_params.add_index(
            field_name="embedding",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 200},
        )
        client.create_index(
            collection_name=KB_COLLECTION,
            index_params=index_params,
        )
        for field in ("doc_id", "module", "status", "content_hash", "release_id"):
            scalar_idx = IndexParams()
            scalar_idx.add_index(field_name=field, index_type="AUTOINDEX")
            client.create_index(
                collection_name=KB_COLLECTION,
                index_params=scalar_idx,
            )

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------

    def upsert_room_records(self, records: list[tuple[RoomVectorRecord, list[float]]]) -> int:
        """Upsert room vector records. Each item is (record, embedding).

        Returns number of upserted rows.
        """
        client = self._ensure_client()
        if not records:
            return 0

        now = int(time.time() * 1000)
        # Milvus 标量字段不直接存 Python list，所以 payment_types/tags 等会转成 JSON 字符串。
        data = []
        for rec, emb in records:
            data.append({
                "vector_id": rec.vector_id,
                "room_id": rec.room_id,
                "apartment_id": rec.apartment_id,
                "apartment_name": rec.apartment_name,
                "city_id": rec.city_id or 0,
                "district_id": rec.district_id or 0,
                "district_name": rec.district_name or "",
                "rent": rec.rent or 0,
                "payment_types": json.dumps(rec.payment_types, ensure_ascii=False),
                "lease_terms": json.dumps(rec.lease_terms),
                "tags": json.dumps(rec.tags, ensure_ascii=False),
                "facilities": json.dumps(rec.facilities, ensure_ascii=False),
                "profile_type": rec.profile_type,
                "content": rec.content,
                "content_hash": rec.content_hash,
                "source_version": rec.source_version,
                "status": rec.status,
                "updated_at": now,
                "embedding": emb,
            })

        client.upsert(collection_name=ROOM_COLLECTION, data=data)
        return len(data)

    def upsert_kb_chunks(self, chunks: list[tuple[KBChunk, list[float]]]) -> int:
        """Upsert KB chunks. Each item is (chunk, embedding).

        Returns number of upserted rows.
        """
        client = self._ensure_client()
        if not chunks:
            return 0

        now = int(time.time() * 1000)
        data = []
        for chunk, emb in chunks:
            data.append({
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "doc_type": chunk.doc_type,
                "module": chunk.module,
                "title": chunk.title,
                "tags": json.dumps(chunk.tags, ensure_ascii=False),
                "content": chunk.content,
                "content_hash": chunk.content_hash,
                "version": chunk.version,
                "release_id": chunk.release_id,
                "status": chunk.status,
                "risk_level": chunk.risk_level,
                "updated_at": now,
                "embedding": emb,
            })

        client.upsert(collection_name=KB_COLLECTION, data=data)
        return len(data)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_rooms(
        self,
        vector: list[float],
        filters: dict[str, Any] | None = None,
        top_k: int = 50,
    ) -> list[dict]:
        """Search room vectors. Always filters to status='active'.

        Returns list of dicts with scalar fields + distance.
        """
        client = self._ensure_client()
        client.load_collection(ROOM_COLLECTION)
        # 检索默认只查 active 数据，避免召回已下架或历史版本房源。
        filter_parts = ['status == "active"']
        if filters:
            if "district_id" in filters and filters["district_id"] is not None:
                filter_parts.append(f'district_id == {filters["district_id"]}')
            if "max_rent" in filters and filters["max_rent"] is not None:
                filter_parts.append(f'rent <= {filters["max_rent"]}')
            if "min_rent" in filters and filters["min_rent"] is not None:
                filter_parts.append(f'rent >= {filters["min_rent"]}')

        filter_expr = " and ".join(filter_parts) if filter_parts else ""

        results = client.search(
            collection_name=ROOM_COLLECTION,
            data=[vector],
            limit=top_k,
            output_fields=[
                "room_id", "apartment_id", "apartment_name", "district_id", "district_name",
                "rent", "payment_types", "lease_terms", "tags", "facilities",
                "content", "content_hash",
            ],
            filter=filter_expr,
            search_params={"metric_type": "COSINE", "params": {"ef": 64}},
        )

        return self._normalize_results(results)

    def search_kb(
        self,
        vector: list[float],
        filters: dict[str, Any] | None = None,
        top_k: int = 10,
    ) -> list[dict]:
        """Search KB chunks. Always filters to status in (active, indexed).

        Returns list of dicts with scalar fields + distance.
        """
        client = self._ensure_client()
        client.load_collection(KB_COLLECTION)
        # KB 默认允许 active/indexed：indexed 表示已经入向量库，可用于检索。
        filter_parts = ['status in ["active", "indexed"]']
        if filters:
            if filters.get("module"):
                filter_parts.append(f'module == "{filters["module"]}"')
            if filters.get("risk_level"):
                filter_parts.append(f'risk_level == "{filters["risk_level"]}"')

        filter_expr = " and ".join(filter_parts)

        results = client.search(
            collection_name=KB_COLLECTION,
            data=[vector],
            limit=top_k,
            output_fields=[
                "chunk_id", "doc_id", "doc_type", "module", "title",
                "tags", "content", "content_hash", "version",
                "release_id", "status", "risk_level",
            ],
            filter=filter_expr,
            search_params={"metric_type": "COSINE", "params": {"ef": 64}},
        )

        return self._normalize_results(results)

    def get_room_by_ids(self, room_ids: list[int]) -> list[dict]:
        """Get room vectors by room_ids (for enrichment and content_hash check)."""
        client = self._ensure_client()
        if not room_ids:
            return []
        client.load_collection(ROOM_COLLECTION)
        ids_str = ", ".join(str(r) for r in room_ids)
        results = client.query(
            collection_name=ROOM_COLLECTION,
            filter=f"room_id in [{ids_str}]",
            output_fields=[
                "room_id", "apartment_id", "apartment_name", "district_id", "district_name",
                "rent", "payment_types", "lease_terms", "tags", "facilities",
                "content_hash", "status",
            ],
        )
        return results

    def get_kb_chunks_by_ids(self, chunk_ids: list[str]) -> list[dict]:
        """Get KB chunks by chunk_ids (for checking existing content_hash)."""
        client = self._ensure_client()
        if not chunk_ids:
            return []
        client.load_collection(KB_COLLECTION)
        ids_str = ", ".join(f'"{c}"' for c in chunk_ids)
        results = client.query(
            collection_name=KB_COLLECTION,
            filter=f"chunk_id in [{ids_str}]",
            output_fields=["chunk_id", "content_hash", "status"],
        )
        return results

    def mark_room_inactive(self, vector_ids: list[str]) -> int:
        """Mark room vectors as inactive by vector_id."""
        client = self._ensure_client()
        if not vector_ids:
            return 0
        # Query existing records to get room_id for each vector_id
        ids_str = ", ".join(f'"{vid}"' for vid in vector_ids)
        existing = client.query(
            collection_name=ROOM_COLLECTION,
            filter=f"vector_id in [{ids_str}]",
            output_fields=["vector_id", "room_id"],
        )
        vid_to_rid = {r["vector_id"]: r["room_id"] for r in existing}
        now = int(time.time() * 1000)
        data = [{"vector_id": vid, "room_id": vid_to_rid.get(vid, 0), "status": "inactive", "updated_at": now} for vid in vector_ids]
        client.upsert(collection_name=ROOM_COLLECTION, data=data)
        return len(data)

    def mark_kb_inactive(self, chunk_ids: list[str]) -> int:
        """Mark KB chunks as inactive by chunk_id."""
        client = self._ensure_client()
        if not chunk_ids:
            return 0
        now = int(time.time() * 1000)
        data = [{"chunk_id": cid, "status": "inactive", "updated_at": now} for cid in chunk_ids]
        client.upsert(collection_name=KB_COLLECTION, data=data)
        return len(data)

    @staticmethod
    def _normalize_results(results: list) -> list[dict]:
        """Flatten Milvus search results."""
        if not results:
            return []
        normalized = []
        # Milvus search 返回按 query 分组的二维结构；本项目每次只传一个 query vector。
        for hit in results[0]:
            entry = {"id": hit["id"], "distance": hit.get("distance", 0)}
            entity = hit.get("entity", {})
            entry.update(entity)
            normalized.append(entry)
        return normalized
