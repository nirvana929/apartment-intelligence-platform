"""Tests for rag.room_v2.retrieve_ranked_rooms_v2."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aptguide2.rag.planning import RetrievalPlan
from aptguide2.rag.schemas import QueryUnderstandingResult, RankedRoom
from aptguide2.rag.room_v2 import retrieve_ranked_rooms_v2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MODULE_PATH = Path(__file__).resolve().parents[3] / "src" / "aptguide2" / "rag" / "room_v2.py"


def _make_plan(task="room_search", semantic_queries=None, hard_filters=None):
    return RetrievalPlan(
        task=task,
        raw_message="test query",
        hard_filters=hard_filters or {},
        semantic_queries=semantic_queries or ["test query"],
    )


def _make_query_result():
    return QueryUnderstandingResult(
        raw_message="test query",
        task="room_search",
    )


class FakeVectorAdapter:
    """Returns deterministic search results."""

    def __init__(self, hits=None):
        self.hits = hits or []
        self.calls: list[dict] = []

    def search_rooms(self, vector=None, filters=None, top_k=30):
        self.calls.append({"vector": vector, "filters": filters, "top_k": top_k})
        return self.hits


class FakeLeaseValidator:
    """Returns all candidates as validated rooms."""

    def __init__(self, rooms=None):
        self.rooms = rooms or []
        self.called_with = None

    def search_rooms(self, payload):
        self.called_with = payload
        return {"rooms": self.rooms}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_retrieve_ranked_rooms_v2_uses_plan_semantic_queries():
    """embed_fn should be called once per semantic query in the plan."""
    plan = _make_plan(semantic_queries=["安静单间", "近地铁"])
    hits = [
        {"room_id": 1, "apartment_id": 10, "distance": 0.2},
        {"room_id": 2, "apartment_id": 10, "distance": 0.3},
    ]
    validator_rooms = [
        {"room_id": 1, "apartment_id": 10, "rent": 1500, "tags": [], "facilities": []},
        {"room_id": 2, "apartment_id": 10, "rent": 2000, "tags": [], "facilities": []},
    ]

    embed_fn = MagicMock(return_value=[0.1, 0.2, 0.3])
    adapter = FakeVectorAdapter(hits)
    validator = FakeLeaseValidator(validator_rooms)

    result = retrieve_ranked_rooms_v2(
        plan, _make_query_result(), adapter, embed_fn, validator,
    )

    assert embed_fn.call_count == 2
    embed_fn.assert_any_call("安静单间")
    embed_fn.assert_any_call("近地铁")
    assert len(result) > 0
    assert all(isinstance(r, RankedRoom) for r in result)


def test_retrieve_ranked_rooms_v2_validates_through_lease():
    """Candidates must pass through the lease validator."""
    plan = _make_plan()
    hits = [{"room_id": 1, "apartment_id": 10, "distance": 0.1}]
    validator_rooms = [
        {"room_id": 1, "apartment_id": 10, "rent": 1500, "tags": [], "facilities": []},
    ]

    embed_fn = MagicMock(return_value=[0.1])
    adapter = FakeVectorAdapter(hits)
    validator = FakeLeaseValidator(validator_rooms)

    result = retrieve_ranked_rooms_v2(
        plan, _make_query_result(), adapter, embed_fn, validator,
    )

    assert validator.called_with is not None
    assert 1 in validator.called_with["room_ids"]
    assert len(result) == 1


def test_retrieve_ranked_rooms_v2_empty_if_no_validated():
    """Return [] when the lease validator returns no rooms."""
    plan = _make_plan()
    hits = [{"room_id": 1, "apartment_id": 10, "distance": 0.1}]

    embed_fn = MagicMock(return_value=[0.1])
    adapter = FakeVectorAdapter(hits)
    validator = FakeLeaseValidator(rooms=[])  # lease returns nothing

    result = retrieve_ranked_rooms_v2(
        plan, _make_query_result(), adapter, embed_fn, validator,
    )

    assert result == []


def test_retrieve_ranked_rooms_v2_empty_for_non_room_task():
    """Return [] immediately when plan.task is not 'room_search'."""
    plan = _make_plan(task="kb_qa")

    embed_fn = MagicMock()
    adapter = FakeVectorAdapter()
    validator = FakeLeaseValidator()

    result = retrieve_ranked_rooms_v2(
        plan, _make_query_result(), adapter, embed_fn, validator,
    )

    assert result == []
    embed_fn.assert_not_called()
    assert adapter.calls == []


def test_retrieve_ranked_rooms_v2_deduplicates_by_room_id():
    """When the same room_id appears in multiple queries, keep the best score."""
    plan = _make_plan(semantic_queries=["q1", "q2"])
    # q1 returns room 1 with distance 0.5 (score 0.5), q2 returns room 1 with distance 0.1 (score 0.9)
    adapter = FakeVectorAdapter(hits=[
        {"room_id": 1, "apartment_id": 10, "distance": 0.1},
    ])
    # embed_fn returns different vectors each call so adapter.hits are reused
    embed_fn = MagicMock(side_effect=[[0.1], [0.2]])
    validator_rooms = [
        {"room_id": 1, "apartment_id": 10, "rent": 1500, "tags": [], "facilities": []},
    ]
    validator = FakeLeaseValidator(validator_rooms)

    result = retrieve_ranked_rooms_v2(
        plan, _make_query_result(), adapter, embed_fn, validator,
    )

    # Should still produce exactly 1 room (deduplicated)
    assert len(result) == 1
    assert result[0].room_id == 1


def test_retrieve_ranked_rooms_v2_does_not_import_old_retrieve_rooms():
    """Source scan: room_v2.py must not import from rag.room_retrieval or rag.pipeline."""
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    forbidden = {"room_retrieval", "pipeline"}
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                for part in parts:
                    if part in forbidden:
                        imported_modules.add(part)
        elif isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            for part in parts:
                if part in forbidden:
                    imported_modules.add(part)

    assert not imported_modules, (
        f"room_v2.py must not import from {forbidden}, found: {imported_modules}"
    )


def test_room_v2_records_raw_validated_and_ranked_diagnostics():
    """Diagnostics dict should capture raw, validated, and final room IDs."""
    diagnostics = {}
    hits = [
        {"room_id": 200013, "apartment_id": 10, "distance": 0.1},
    ]
    validator_rooms = [
        {"room_id": 200013, "apartment_id": 10, "rent": 1500, "tags": [], "facilities": []},
    ]
    adapter = FakeVectorAdapter(hits)
    validator = FakeLeaseValidator(validator_rooms)
    embed_fn = MagicMock(return_value=[0.1])

    plan = _make_plan(
        semantic_queries=["番禺区2000以内适合考研"],
        hard_filters={"district_id": 4, "max_rent": 2000},
    )
    query_result = QueryUnderstandingResult(
        raw_message="番禺区2000以内适合考研",
        task="room_search",
        hard_filters={"district_id": 4, "max_rent": 2000},
        soft_preferences=["适合考研"],
    )

    ranked = retrieve_ranked_rooms_v2(
        plan=plan,
        query_result=query_result,
        vector_adapter=adapter,
        embed_fn=embed_fn,
        lease_validator=validator,
        diagnostics=diagnostics,
    )

    assert [room.room_id for room in ranked] == [200013]
    assert diagnostics["room_raw_room_ids"] == [200013]
    assert diagnostics["room_validated_room_ids"] == [200013]
    assert diagnostics["room_final_room_ids"] == [200013]
    assert diagnostics["room_hard_filters"] == {"district_id": 4, "max_rent": 2000}
