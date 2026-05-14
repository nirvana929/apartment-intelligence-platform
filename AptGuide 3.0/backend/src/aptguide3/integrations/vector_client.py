from __future__ import annotations

from typing import Any

try:
    from pymilvus import MilvusClient
except ImportError:
    MilvusClient = None  # type: ignore[assignment,misc]

KB_COLLECTION = "apt_rental_kb"
KB_FIELDS = ["chunk_id", "doc_id", "title", "module", "content", "risk_level"]


class VectorClient:
    def __init__(self, uri: str = "http://localhost:19530") -> None:
        if MilvusClient is None:
            raise ImportError("pymilvus is not installed. Install it with: pip install pymilvus")
        self._client = MilvusClient(uri=uri)

    def search_kb(self, vector: list[float], top_k: int = 10) -> list[dict[str, Any]]:
        try:
            results = self._client.search(
                collection_name=KB_COLLECTION,
                data=[vector],
                limit=top_k,
                output_fields=KB_FIELDS,
            )
        except Exception:
            return []

        hits: list[dict[str, Any]] = []
        for batch in results:
            for hit in batch:
                entity = hit.get("entity", {})
                hits.append({
                    "chunk_id": entity.get("chunk_id", ""),
                    "doc_id": entity.get("doc_id", ""),
                    "title": entity.get("title", ""),
                    "module": entity.get("module", ""),
                    "content": entity.get("content", ""),
                    "distance": hit.get("distance", 0.0),
                    "risk_level": entity.get("risk_level", "low"),
                })
        return hits
