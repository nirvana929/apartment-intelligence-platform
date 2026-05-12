"""Tests for vector adapter — verifies constants and logic without hitting Milvus."""

from aptguide2.tools.vector_adapter import (
    DEFAULT_METRIC,
    KB_COLLECTION,
    ROOM_COLLECTION,
    VectorAdapter,
)


def test_room_collection_name():
    assert ROOM_COLLECTION == "apt_room_vector"


def test_kb_collection_name():
    assert KB_COLLECTION == "apt_rental_kb"


def test_default_metric():
    assert DEFAULT_METRIC == "COSINE"


def test_normalize_results_empty():
    assert VectorAdapter._normalize_results([]) == []


def test_normalize_results_flattens():
    raw = [[
        {"id": "room-3001", "distance": 0.85, "entity": {"room_id": 3001, "rent": 1800}},
        {"id": "room-3002", "distance": 0.72, "entity": {"room_id": 3002, "rent": 2200}},
    ]]
    result = VectorAdapter._normalize_results(raw)
    assert len(result) == 2
    assert result[0]["room_id"] == 3001
    assert result[0]["distance"] == 0.85
    assert result[1]["rent"] == 2200


def test_adapter_init():
    """Verify adapter initializes correctly with custom params."""
    adapter = VectorAdapter(uri="http://test:19530", token="", dim=768)
    assert adapter.dim == 768
    assert adapter.uri == "http://test:19530"
