"""Tests for lease tool executors using a fake adapter (no real HTTP)."""

from __future__ import annotations

from typing import Any

import httpx

from aptguide2.harness.tools.contracts import ToolCallRequest
from aptguide2.harness.tools.lease_tools import (
    AppointmentCancelExecutor,
    AppointmentCreateExecutor,
    AppointmentListMineExecutor,
    LeaseHealthExecutor,
    LeaseListMineExecutor,
    RoomDetailExecutor,
    RoomSearchExecutor,
)

# ---------------------------------------------------------------------------
# Fake adapter
# ---------------------------------------------------------------------------


class FakeLeaseAdapter:
    """In-memory adapter with controlled return values."""

    def __init__(self) -> None:
        self.healthy = True
        self._rooms: list[dict[str, Any]] = [
            {"room_id": 1, "name": "Room A", "rent": 1500},
            {"room_id": 2, "name": "Room B", "rent": 2000},
        ]
        self._room_details: dict[int, dict[str, Any]] = {
            1: {"room_id": 1, "name": "Room A", "rent": 1500, "district": "Chaoyang"},
            2: {"room_id": 2, "name": "Room B", "rent": 2000, "district": "Haidian"},
        }
        self.raise_exc: Exception | None = None

    # -- Synchronous methods (no await) ------------------------------------

    def health(self) -> bool:
        if self.raise_exc:
            raise self.raise_exc
        return self.healthy

    def search_rooms(self, payload: dict) -> dict:
        if self.raise_exc:
            raise self.raise_exc
        limit = payload.get("limit", 10)
        rooms = self._rooms[:limit]
        return {"rooms": rooms}

    def get_room_detail(self, room_id: int) -> dict:
        if self.raise_exc:
            raise self.raise_exc
        return self._room_details.get(room_id, {})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _req(tool: str, **kwargs: Any) -> ToolCallRequest:
    defaults = {"tool": tool, "request_id": "r-test", "payload": {}}
    defaults.update(kwargs)
    return ToolCallRequest(**defaults)


# ---------------------------------------------------------------------------
# LeaseHealthExecutor
# ---------------------------------------------------------------------------


class TestLeaseHealthExecutor:
    def test_health_ok(self):
        adapter = FakeLeaseAdapter()
        executor = LeaseHealthExecutor(adapter)
        result = executor.execute(_req("lease.health"))
        assert result.ok is True
        assert result.data["healthy"] is True

    def test_health_unhealthy(self):
        adapter = FakeLeaseAdapter()
        adapter.healthy = False
        executor = LeaseHealthExecutor(adapter)
        result = executor.execute(_req("lease.health"))
        assert result.ok is True
        assert result.data["healthy"] is False

    def test_health_exception_maps_to_unknown_error(self):
        adapter = FakeLeaseAdapter()
        adapter.raise_exc = ConnectionError("refused")
        executor = LeaseHealthExecutor(adapter)
        result = executor.execute(_req("lease.health"))
        assert result.ok is False
        assert result.error.code == "UNKNOWN_TOOL_ERROR"
        assert "ConnectionError" in result.error.message


# ---------------------------------------------------------------------------
# RoomSearchExecutor
# ---------------------------------------------------------------------------


class TestRoomSearchExecutor:
    def test_search_returns_rooms_with_result_count(self):
        adapter = FakeLeaseAdapter()
        executor = RoomSearchExecutor(adapter)
        result = executor.execute(_req("room.search", payload={"limit": 5}))
        assert result.ok is True
        assert len(result.data["rooms"]) == 2
        assert result.metadata["result_count"] == 2

    def test_search_with_empty_payload(self):
        adapter = FakeLeaseAdapter()
        executor = RoomSearchExecutor(adapter)
        result = executor.execute(_req("room.search"))
        assert result.ok is True
        assert result.metadata["result_count"] == 2

    def test_search_timeout_maps_to_tool_timeout(self):
        adapter = FakeLeaseAdapter()
        adapter.raise_exc = httpx.TimeoutException("read timed out")
        executor = RoomSearchExecutor(adapter)
        result = executor.execute(_req("room.search"))
        assert result.ok is False
        assert result.error.code == "TOOL_TIMEOUT"
        assert result.error.recoverable is True

    def test_search_generic_exception_maps_to_unknown_error(self):
        adapter = FakeLeaseAdapter()
        adapter.raise_exc = RuntimeError("oops")
        executor = RoomSearchExecutor(adapter)
        result = executor.execute(_req("room.search"))
        assert result.ok is False
        assert result.error.code == "UNKNOWN_TOOL_ERROR"


# ---------------------------------------------------------------------------
# RoomDetailExecutor
# ---------------------------------------------------------------------------


class TestRoomDetailExecutor:
    def test_detail_returns_room(self):
        adapter = FakeLeaseAdapter()
        executor = RoomDetailExecutor(adapter)
        result = executor.execute(_req("room.detail", payload={"room_id": 1}))
        assert result.ok is True
        assert result.data["room"]["room_id"] == 1
        assert result.data["room"]["district"] == "Chaoyang"

    def test_detail_missing_room_id_returns_invalid_payload(self):
        adapter = FakeLeaseAdapter()
        executor = RoomDetailExecutor(adapter)
        result = executor.execute(_req("room.detail"))
        assert result.ok is False
        assert result.error.code == "INVALID_PAYLOAD"

    def test_detail_timeout_maps_to_tool_timeout(self):
        adapter = FakeLeaseAdapter()
        adapter.raise_exc = httpx.TimeoutException("connect timed out")
        executor = RoomDetailExecutor(adapter)
        result = executor.execute(_req("room.detail", payload={"room_id": 1}))
        assert result.ok is False
        assert result.error.code == "TOOL_TIMEOUT"


# ---------------------------------------------------------------------------
# AppointmentCreateExecutor
# ---------------------------------------------------------------------------


class TestAppointmentCreateExecutor:
    def test_not_implemented_when_adapter_lacks_method(self):
        adapter = FakeLeaseAdapter()
        executor = AppointmentCreateExecutor(adapter)
        result = executor.execute(
            _req("appointment.create", payload={"room_id": 1, "user_id": "u-1"})
        )
        assert result.ok is False
        assert result.error.code == "TOOL_NOT_IMPLEMENTED"

    def test_ok_when_adapter_has_method(self):
        adapter = FakeLeaseAdapter()
        adapter.create_appointment = lambda payload: {"appointment_id": "a-1", "status": "pending"}
        executor = AppointmentCreateExecutor(adapter)
        result = executor.execute(
            _req("appointment.create", payload={"room_id": 1, "user_id": "u-1"})
        )
        assert result.ok is True
        assert result.data["appointment_id"] == "a-1"


# ---------------------------------------------------------------------------
# AppointmentListMineExecutor
# ---------------------------------------------------------------------------


class TestAppointmentListMineExecutor:
    def test_not_implemented_when_adapter_lacks_method(self):
        adapter = FakeLeaseAdapter()
        executor = AppointmentListMineExecutor(adapter)
        result = executor.execute(
            _req("appointment.list_mine", payload={"user_id": "u-1"})
        )
        assert result.ok is False
        assert result.error.code == "TOOL_NOT_IMPLEMENTED"

    def test_ok_when_adapter_has_method(self):
        adapter = FakeLeaseAdapter()
        adapter.list_appointments = lambda payload: {"appointments": [{"id": "a-1"}], "total": 1}
        executor = AppointmentListMineExecutor(adapter)
        result = executor.execute(
            _req("appointment.list_mine", payload={"user_id": "u-1"})
        )
        assert result.ok is True
        assert result.data["appointments"][0]["id"] == "a-1"


# ---------------------------------------------------------------------------
# LeaseListMineExecutor
# ---------------------------------------------------------------------------


class TestLeaseListMineExecutor:
    def test_not_implemented_when_adapter_lacks_method(self):
        adapter = FakeLeaseAdapter()
        executor = LeaseListMineExecutor(adapter)
        result = executor.execute(
            _req("lease.list_mine", payload={"user_id": "u-1"})
        )
        assert result.ok is False
        assert result.error.code == "TOOL_NOT_IMPLEMENTED"

    def test_ok_when_adapter_has_method(self):
        adapter = FakeLeaseAdapter()
        adapter.list_leases = lambda payload: {"leases": [{"id": "l-1"}], "total": 1}
        executor = LeaseListMineExecutor(adapter)
        result = executor.execute(
            _req("lease.list_mine", payload={"user_id": "u-1"})
        )
        assert result.ok is True
        assert result.data["leases"][0]["id"] == "l-1"


# ---------------------------------------------------------------------------
# AppointmentCancelExecutor
# ---------------------------------------------------------------------------


class TestAppointmentCancelExecutor:
    def test_not_implemented_when_adapter_lacks_method(self):
        adapter = FakeLeaseAdapter()
        executor = AppointmentCancelExecutor(adapter)
        result = executor.execute(
            _req("appointment.cancel", payload={"appointment_id": "a-1", "user_id": "u-1"})
        )
        assert result.ok is False
        assert result.error.code == "TOOL_NOT_IMPLEMENTED"

    def test_ok_when_adapter_has_method(self):
        adapter = FakeLeaseAdapter()
        adapter.cancel_appointment = lambda payload: {"appointment_id": payload["appointment_id"], "status": "cancelled"}
        executor = AppointmentCancelExecutor(adapter)
        result = executor.execute(
            _req("appointment.cancel", payload={"appointment_id": "a-1", "user_id": "u-1"})
        )
        assert result.ok is True
        assert result.data["status"] == "cancelled"

    def test_exception_maps_to_error(self):
        adapter = FakeLeaseAdapter()
        adapter.cancel_appointment = lambda payload: (_ for _ in ()).throw(ConnectionError("refused"))
        executor = AppointmentCancelExecutor(adapter)
        result = executor.execute(
            _req("appointment.cancel", payload={"appointment_id": "a-1", "user_id": "u-1"})
        )
        assert result.ok is False
        assert result.error.code == "UNKNOWN_TOOL_ERROR"
