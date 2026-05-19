from __future__ import annotations

from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.procedures.lease import LeaseProcedure


class StubLeaseClient:
    def __init__(self, leases: list[dict[str, Any]] | None = None, fail: bool = False):
        self._leases = leases or []
        self._fail = fail
        self.calls: list[int] = []

    async def list_leases(self, user_id: int) -> list[dict[str, Any]]:
        self.calls.append(user_id)
        if self._fail:
            raise ConnectionError("lease unavailable")
        return self._leases


class StubAuditRepo:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, str, dict]] = []

    async def append_audit_event(
        self, user_id: str, session_id: str, event_type: str, payload: dict,
    ) -> None:
        self.events.append((user_id, session_id, event_type, payload))


def _frame(user_id: str | None = "1", session_id: str = "s-1") -> ConversationFrame:
    return ConversationFrame(message="查看租约", session_id=session_id, user_id=user_id)


def _understanding(**overrides: Any) -> UnderstandingResult:
    defaults = dict(
        raw_message="查看租约",
        route="lease",
        task="lease",
        domain="lease",
        action="query_status",
        confidence=0.9,
        hard_filters={},
        soft_preferences=[],
    )
    defaults.update(overrides)
    return UnderstandingResult(**defaults)


def test_no_user_id_returns_login_prompt():
    proc = LeaseProcedure(lease_client=StubLeaseClient())

    result = proc.run(_frame(user_id=None), _understanding())

    assert result.phase == "lease"
    assert "登录" in result.message
    assert result.metadata["error"] == "no_user_id"


def test_no_lease_client_returns_unavailable():
    proc = LeaseProcedure()

    result = proc.run(_frame(), _understanding())

    assert result.phase == "lease"
    assert "不可用" in result.message
    assert result.metadata["error"] == "no_lease_client"


def test_empty_leases_returns_empty_state():
    client = StubLeaseClient(leases=[])
    proc = LeaseProcedure(lease_client=client)

    result = proc.run(_frame(), _understanding())

    assert result.phase == "lease"
    assert "暂无租约" in result.message
    assert result.metadata["lease_count"] == 0
    assert result.cards == []
    assert client.calls == [1]


def test_success_with_lease_cards():
    leases = [
        {
            "lease_id": "L001",
            "apartment_name": "阳光花园",
            "room_number": "A-101",
            "status": "active",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "rent": 2500,
        },
        {
            "lease_id": "L002",
            "apartment_name": "翠竹苑",
            "room_number": "B-202",
            "status": "expired",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "rent": 1800,
        },
    ]
    client = StubLeaseClient(leases=leases)
    proc = LeaseProcedure(lease_client=client)

    result = proc.run(_frame(), _understanding())

    assert result.phase == "lease"
    assert "2 条租约" in result.message
    assert len(result.cards) == 2
    assert result.metadata["lease_count"] == 2
    assert result.cards[0]["type"] == "lease_card"
    assert result.cards[0]["lease_id"] == "L001"
    assert result.cards[0]["apartment_name"] == "阳光花园"
    assert result.cards[0]["rent"] == 2500
    assert result.cards[1]["lease_id"] == "L002"


def test_lease_client_failure_returns_empty_state():
    client = StubLeaseClient(fail=True)
    proc = LeaseProcedure(lease_client=client)

    result = proc.run(_frame(), _understanding())

    assert result.phase == "lease"
    assert "暂无租约" in result.message
    assert result.metadata["lease_count"] == 0


def test_audit_write_on_query():
    client = StubLeaseClient(leases=[
        {"lease_id": "L001", "apartment_name": "A", "room_number": "1", "status": "active",
         "start_date": "2025-01-01", "end_date": "2025-12-31", "rent": 1000},
    ])
    audit = StubAuditRepo()
    proc = LeaseProcedure(lease_client=client, audit_repo=audit)

    proc.run(_frame(), _understanding())

    assert len(audit.events) == 1
    user_id, session_id, event_type, payload = audit.events[0]
    assert user_id == "1"
    assert session_id == "s-1"
    assert event_type == "lease_query"
    assert payload == {"lease_count": 1}


def test_more_than_five_leases_limited_to_five():
    leases = [
        {"lease_id": f"L{i:03d}", "apartment_name": f"公寓{i}", "room_number": f"{i}",
         "status": "active", "start_date": "2025-01-01", "end_date": "2025-12-31", "rent": 1000 * i}
        for i in range(1, 8)
    ]
    client = StubLeaseClient(leases=leases)
    proc = LeaseProcedure(lease_client=client)

    result = proc.run(_frame(), _understanding())

    assert result.metadata["lease_count"] == 7
    assert len(result.cards) == 5
    assert result.cards[0]["lease_id"] == "L001"
    assert result.cards[4]["lease_id"] == "L005"
