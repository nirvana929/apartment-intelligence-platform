from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from aptguide3.integrations.lease_client import LeaseClient


def _make_response(status_code: int = 200, json_body: dict | None = None) -> httpx.Response:
    """Build a real ``httpx.Response`` with the given status and JSON body."""
    resp = httpx.Response(
        status_code=status_code,
        json=json_body if json_body is not None else {},
        request=httpx.Request("POST", "http://localhost"),
    )
    return resp


# ── create_appointment ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_rooms_returns_snake_case_rooms():
    resp = _make_response(
        200,
        {
            "code": 200,
            "message": "成功",
            "data": {
                "rooms": [
                    {
                        "roomId": 15,
                        "roomNumber": "104",
                        "apartmentId": 10,
                        "apartmentName": "回龙观社区",
                        "rent": 3500,
                        "paymentTypes": ["月付"],
                    }
                ],
                "total": 1,
            },
        },
    )
    mock_client = AsyncMock()
    mock_client.post.return_value = resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("aptguide3.integrations.lease_client.httpx.AsyncClient", return_value=mock_client):
        result = await LeaseClient().validate_rooms([15], {})

    assert result == [
        {
            "room_id": 15,
            "room_number": "104",
            "apartment_id": 10,
            "apartment_name": "回龙观社区",
            "rent": 3500,
            "payment_types": ["月付"],
        }
    ]


@pytest.mark.asyncio
async def test_create_appointment_success():
    resp = _make_response(200, {"code": 0, "message": "ok", "data": {"appointmentId": 42}})
    mock_client = AsyncMock()
    mock_client.post.return_value = resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("aptguide3.integrations.lease_client.httpx.AsyncClient", return_value=mock_client):
        result = await LeaseClient().create_appointment(
            user_id=1, apartment_id=10, appointment_time="2026-05-20 10:00", remark="test",
        )

    assert result["ok"] is True
    assert result["data"]["appointment_id"] == 42


@pytest.mark.asyncio
async def test_create_appointment_http_failure():
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.ConnectError("connection refused")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("aptguide3.integrations.lease_client.httpx.AsyncClient", return_value=mock_client):
        result = await LeaseClient().create_appointment(
            user_id=1, apartment_id=10, appointment_time="2026-05-20 10:00",
        )

    assert result["ok"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_create_appointment_nonzero_code():
    resp = _make_response(200, {"code": 1, "message": "slot taken", "data": None})
    mock_client = AsyncMock()
    mock_client.post.return_value = resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("aptguide3.integrations.lease_client.httpx.AsyncClient", return_value=mock_client):
        result = await LeaseClient().create_appointment(
            user_id=1, apartment_id=10, appointment_time="2026-05-20 10:00",
        )

    assert result["ok"] is False
    assert result["error"] == "slot taken"


# ── list_appointments ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_appointments_success():
    resp = _make_response(200, {"code": 0, "message": "ok", "data": [{"appointmentId": 1, "apartmentId": 10}]})
    mock_client = AsyncMock()
    mock_client.get.return_value = resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("aptguide3.integrations.lease_client.httpx.AsyncClient", return_value=mock_client):
        result = await LeaseClient().list_appointments(user_id=1)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["appointment_id"] == 1


@pytest.mark.asyncio
async def test_list_appointments_failure():
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("timeout")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("aptguide3.integrations.lease_client.httpx.AsyncClient", return_value=mock_client):
        result = await LeaseClient().list_appointments(user_id=1)

    assert result == []


# ── list_leases ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_leases_success():
    resp = _make_response(200, {"code": 0, "message": "ok", "data": [{"leaseId": 99, "roomId": 5}]})
    mock_client = AsyncMock()
    mock_client.get.return_value = resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("aptguide3.integrations.lease_client.httpx.AsyncClient", return_value=mock_client):
        result = await LeaseClient().list_leases(user_id=1)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["lease_id"] == 99


@pytest.mark.asyncio
async def test_list_leases_failure():
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("refused")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("aptguide3.integrations.lease_client.httpx.AsyncClient", return_value=mock_client):
        result = await LeaseClient().list_leases(user_id=1)

    assert result == []
