from __future__ import annotations

import hashlib
import json
from typing import Any

try:
    from pymilvus import MilvusClient
except ImportError:
    MilvusClient = None  # type: ignore[assignment,misc]

KB_COLLECTION = "apt_rental_kb"
KB_FIELDS = ["id", "title", "category", "content"]
ROOM_COLLECTION = "room_index"
WECHAT_ROOM_COLLECTION = "wechat_room_index"

# risk_level derivation from category (module)
_CATEGORY_RISK_LEVEL = {
    "lease": "high",
    "payment": "high",
    "account": "high",
    "appointment": "medium",
    "policy": "medium",
    "life": "low",
    "room_search": "low",
}


_DISTRICT_SUFFIXES = ("区", "县", "市")


def _normalize_district(raw: str) -> str:
    """Ensure district name has a proper suffix (区/县/市).

    LLM may extract short form like "番禺" while Milvus stores "番禺区".
    """
    if any(raw.endswith(s) for s in _DISTRICT_SUFFIXES):
        return raw
    return raw + "区"


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
                category = entity.get("category", "")
                hits.append({
                    "chunk_id": entity.get("id", ""),
                    "doc_id": entity.get("id", ""),
                    "title": entity.get("title", ""),
                    "module": category,
                    "content": entity.get("content", ""),
                    "distance": hit.get("distance", 0.0),
                    "risk_level": _CATEGORY_RISK_LEVEL.get(category, "low"),
                })
        return hits

    def search_rooms(
        self,
        vector: list[float],
        filters: dict[str, Any] | None = None,
        top_k: int = 50,
    ) -> list[dict[str, Any]]:
        try:
            self._client.load_collection(ROOM_COLLECTION)
            filter_parts = ['status == "available"']
            if filters:
                if filters.get("district_name") is not None:
                    district = _normalize_district(filters["district_name"])
                    filter_parts.append(f'district == "{district}"')
                if filters.get("max_rent") is not None:
                    filter_parts.append(f'rent <= {int(filters["max_rent"])}')
                if filters.get("min_rent") is not None:
                    filter_parts.append(f'rent >= {int(filters["min_rent"])}')
            results = self._client.search(
                collection_name=ROOM_COLLECTION,
                data=[vector],
                limit=top_k,
                output_fields=[
                    "id", "title", "rent", "district", "tags", "payment_type", "status",
                ],
                filter=" and ".join(filter_parts),
                search_params={"metric_type": "COSINE", "params": {"ef": 64}},
            )
        except Exception:
            return []
        return _map_room_results(results)

    def search_wechat_rooms(
        self,
        vector: list[float],
        filters: dict[str, Any] | None = None,
        top_k: int = 50,
    ) -> list[dict[str, Any]]:
        try:
            self._client.load_collection(WECHAT_ROOM_COLLECTION)
            filter_parts = []
            if filters:
                if filters.get("district_name") is not None:
                    district = _normalize_district(filters["district_name"])
                    filter_parts.append(f'district == "{district}"')
                if filters.get("max_rent") is not None:
                    filter_parts.append(f'rent_min <= {int(filters["max_rent"])}')
            filter_str = " and ".join(filter_parts) if filter_parts else ""
            results = self._client.search(
                collection_name=WECHAT_ROOM_COLLECTION,
                data=[vector],
                limit=top_k,
                output_fields=[
                    "id", "district", "area_label", "rent_min", "rent_max",
                    "tags", "metro_stations", "facility_tags", "payment_tags",
                    "lease_room_id",
                ],
                filter=filter_str,
                search_params={"metric_type": "COSINE", "params": {"ef": 64}},
            )
        except Exception:
            return []
        return _map_wechat_room_results(results)


def _normalize_json_field(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _stable_synthetic_room_id(source_id: str) -> int:
    digest_prefix = hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:8]
    return int(digest_prefix, 16) % 1000000 + 900000


def _map_room_results(results: list) -> list[dict[str, Any]]:
    """Map room_index fields to the schema expected by the RAG pipeline."""
    mapped: list[dict[str, Any]] = []
    if not results:
        return mapped
    for batch in results:
        for hit in batch:
            entity = hit.get("entity", {})
            tags = _normalize_json_field(entity.get("tags", []))
            if isinstance(tags, str):
                tags = [tags] if tags else []
            payment_type = entity.get("payment_type", "")
            payment_types = [payment_type] if payment_type else []
            district = entity.get("district", "")
            mapped.append({
                "room_id": int(entity.get("id", 0)),
                "apartment_id": 0,
                "apartment_name": entity.get("title", ""),
                "district_id": 0,
                "district_name": district,
                "rent": entity.get("rent", 0),
                "payment_types": payment_types,
                "lease_terms": [],
                "tags": tags if isinstance(tags, list) else [],
                "facilities": [],
                "distance": hit.get("distance", 0.0),
            })
    return mapped


def _map_wechat_room_results(results: list) -> list[dict[str, Any]]:
    """Map wechat_room_index fields to the schema expected by the RAG pipeline."""
    mapped: list[dict[str, Any]] = []
    if not results:
        return mapped
    for batch in results:
        for hit in batch:
            entity = hit.get("entity", {})
            tags = _normalize_json_field(entity.get("tags", []))
            if isinstance(tags, str):
                tags = [tags] if tags else []
            payment_tags = _normalize_json_field(entity.get("payment_tags", []))
            if isinstance(payment_tags, str):
                payment_tags = [payment_tags] if payment_tags else []
            metro = _normalize_json_field(entity.get("metro_stations", []))
            if isinstance(metro, str):
                metro = [metro] if metro else []
            facilities = _normalize_json_field(entity.get("facility_tags", []))
            if isinstance(facilities, str):
                facilities = [facilities] if facilities else []
            district = entity.get("district", "")
            area = entity.get("area_label", "")
            rent_min = entity.get("rent_min", 0)
            rent_max = entity.get("rent_max", 0)
            wechat_id = entity.get("id", "")
            synthetic_id = _stable_synthetic_room_id(str(wechat_id))
            lease_room_id = entity.get("lease_room_id") or entity.get("room_id") or None
            mapped.append({
                "room_id": synthetic_id,
                "apartment_id": 0,
                "apartment_name": f"{district} {area}" if area else district,
                "district_id": 0,
                "district_name": district,
                "rent": rent_min,
                "rent_range": f"{rent_min}-{rent_max}",
                "payment_types": payment_tags,
                "lease_terms": [],
                "tags": tags,
                "facilities": facilities,
                "metro_stations": metro,
                "distance": hit.get("distance", 0.0),
                # --- source identity fields (never discard original Milvus ID) ---
                "wechat_room_id": str(wechat_id),
                "source_system": "wechat",
                "source_collection": WECHAT_ROOM_COLLECTION,
                "source_record_id": str(wechat_id),
                "synthetic_room_id": synthetic_id,
                "lease_room_id": lease_room_id,
                "identity_mapping_status": "mapped_verified" if lease_room_id else "unmapped",
            })
    return mapped
