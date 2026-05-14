from __future__ import annotations

from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.procedures.room_search import RoomSearchProcedure


class StubLeaseClient:
    def __init__(self, rooms: list[dict[str, Any]] | None = None, fail: bool = False):
        self._rooms = rooms or []
        self._fail = fail
        self.calls: list[tuple[list[int], dict]] = []

    async def validate_rooms(self, room_ids: list[int], filters: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append((room_ids, filters))
        if self._fail:
            raise ConnectionError("lease unavailable")
        return self._rooms


def _frame() -> ConversationFrame:
    return ConversationFrame(message="找房", session_id="s-1")


def _understanding(**overrides: Any) -> UnderstandingResult:
    defaults = dict(
        raw_message="找房",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
        hard_filters={},
        soft_preferences=[],
    )
    defaults.update(overrides)
    return UnderstandingResult(**defaults)


def test_room_search_with_rooms_returns_cards():
    rooms = [
        {"room_id": 1, "rent": 1500, "payment_types": ["月付"], "tags": ["近地铁"], "facilities": ["空调"]},
        {"room_id": 2, "rent": 2000, "payment_types": ["季付"], "tags": ["独立卫浴"], "facilities": ["洗衣机"]},
    ]
    client = StubLeaseClient(rooms=rooms)
    proc = RoomSearchProcedure(lease_client=client)

    result = proc.run(_frame(), _understanding())

    assert result.phase == "room_search"
    assert len(result.cards) == 2
    assert result.cards[0]["type"] == "room"
    assert result.cards[0]["room_id"] == 1
    assert result.cards[0]["rent"] == 1500
    assert result.cards[1]["room_id"] == 2
    assert result.metadata["room_count"] == 2


def test_room_search_with_empty_rooms_falls_back():
    client = StubLeaseClient(rooms=[])
    proc = RoomSearchProcedure(lease_client=client)

    result = proc.run(_frame(), _understanding())

    assert result.phase == "room_search"
    assert result.cards == []
    assert "找房需求" in result.message


def test_room_search_with_no_client_uses_placeholder():
    proc = RoomSearchProcedure()

    result = proc.run(_frame(), _understanding())

    assert result.phase == "room_search"
    assert result.cards == []
    assert "找房需求" in result.message


def test_room_search_with_client_error_falls_back():
    client = StubLeaseClient(fail=True)
    proc = RoomSearchProcedure(lease_client=client)

    result = proc.run(_frame(), _understanding())

    assert result.phase == "room_search"
    assert result.cards == []
    assert "找房需求" in result.message


def test_room_search_passes_filters_to_client():
    client = StubLeaseClient(rooms=[])
    proc = RoomSearchProcedure(lease_client=client)

    proc.run(_frame(), _understanding(hard_filters={"max_rent": 2000, "payment_type": "月付"}))

    assert len(client.calls) == 1
    _, filters = client.calls[0]
    assert filters["max_rent"] == 2000
    assert filters["payment_type"] == "月付"
