"""Tests for lease adapter."""

import pytest
import respx
import httpx

from aptguide2.tools.lease_adapter import (
    LeaseAdapter,
    LeaseAdapterError,
    _camel_to_snake,
    _snake_to_camel,
    convert_keys_to_camel,
    convert_keys_to_snake,
)


# ---------------------------------------------------------------------------
# Key conversion tests
# ---------------------------------------------------------------------------

def test_snake_to_camel():
    assert _snake_to_camel("district_id") == "districtId"
    assert _snake_to_camel("max_rent") == "maxRent"
    assert _snake_to_camel("room_ids") == "roomIds"
    assert _snake_to_camel("is_appointable") == "isAppointable"
    assert _snake_to_camel("rent") == "rent"


def test_camel_to_snake():
    assert _camel_to_snake("districtId") == "district_id"
    assert _camel_to_snake("maxRent") == "max_rent"
    assert _camel_to_snake("roomIds") == "room_ids"
    assert _camel_to_snake("isAppointable") == "is_appointable"
    assert _camel_to_snake("rent") == "rent"


def test_convert_keys_to_camel_nested():
    inp = {"district_id": 1005, "max_rent": 1800, "room_ids": [3001]}
    out = convert_keys_to_camel(inp)
    assert out == {"districtId": 1005, "maxRent": 1800, "roomIds": [3001]}


def test_convert_keys_to_snake_nested():
    inp = {"roomId": 3001, "apartmentId": 2001, "isAppointable": True}
    out = convert_keys_to_snake(inp)
    assert out == {"room_id": 3001, "apartment_id": 2001, "is_appointable": True}


def test_convert_keys_roundtrip():
    original = {"district_id": 1005, "payment_type": "MONTHLY", "tags": ["安静"]}
    assert convert_keys_to_snake(convert_keys_to_camel(original)) == original


# ---------------------------------------------------------------------------
# Adapter tests with mocked HTTP
# ---------------------------------------------------------------------------

BASE_URL = "http://lease-test:8080"


@pytest.fixture
def adapter():
    return LeaseAdapter(base_url=BASE_URL, timeout=2.0)


@pytest.fixture
def mock_router():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.mark.asyncio
async def test_health_ok(adapter, mock_router):
    mock_router.get("/internal/ai/tools/health").respond(json={"code": 0, "data": {"healthy": True}})
    assert await adapter.health() is True


@pytest.mark.asyncio
async def test_health_unreachable(adapter):
    adapter = LeaseAdapter(base_url="http://unreachable:9999", timeout=0.1)
    assert await adapter.health() is False


@pytest.mark.asyncio
async def test_health_error_code(adapter, mock_router):
    mock_router.get("/internal/ai/tools/health").respond(json={"code": 0, "data": {"healthy": False}})
    assert await adapter.health() is False


@pytest.mark.asyncio
async def test_sync_rooms(adapter, mock_router):
    mock_router.get("/internal/ai/tools/sync/rooms").respond(json={
        "code": 0,
        "data": [
            {"roomId": 3001, "apartmentId": 2001, "rent": 1800, "districtName": "番禺区"},
            {"roomId": 3002, "apartmentId": 2001, "rent": 2200, "districtName": "天河区"},
        ],
    })
    rooms = await adapter.sync_rooms(limit=10)
    assert len(rooms) == 2
    assert rooms[0]["room_id"] == 3001
    assert rooms[0]["district_name"] == "番禺区"


@pytest.mark.asyncio
async def test_search_rooms_converts_keys(adapter, mock_router):
    mock_router.post("/internal/ai/tools/room/search").respond(json={
        "code": 0,
        "data": {
            "rooms": [{"roomId": 3001, "apartmentId": 2001, "isAppointable": True}],
            "total": 1,
            "strategy": "exact_search",
        },
    })
    result = await adapter.search_rooms({"district_id": 1005, "max_rent": 1800})
    assert result["rooms"][0]["room_id"] == 3001
    assert result["rooms"][0]["is_appointable"] is True


@pytest.mark.asyncio
async def test_search_rooms_sends_camel_case(adapter, mock_router):
    captured = {}

    def capture_request(request):
        captured["json"] = json.loads(request.content) if request.content else {}
        return httpx.Response(200, json={"code": 0, "data": {"rooms": [], "total": 0}})

    import json
    mock_router.post("/internal/ai/tools/room/search").mock(side_effect=capture_request)
    await adapter.search_rooms({"district_id": 1005, "max_rent": 1800})
    assert captured["json"]["districtId"] == 1005
    assert captured["json"]["maxRent"] == 1800


@pytest.mark.asyncio
async def test_get_room_detail(adapter, mock_router):
    mock_router.get("/internal/ai/tools/room/3001").respond(json={
        "code": 0,
        "data": {"roomId": 3001, "apartmentName": "大学城南亭寓", "rent": 1800},
    })
    detail = await adapter.get_room_detail(3001)
    assert detail["room_id"] == 3001
    assert detail["apartment_name"] == "大学城南亭寓"


@pytest.mark.asyncio
async def test_lease_error_in_health_returns_false(adapter, mock_router):
    """health() catches errors and returns False for health checks."""
    mock_router.get("/internal/ai/tools/health").respond(json={
        "code": 500,
        "errorCode": "LEASE_UNAVAILABLE",
        "message": "lease backend down",
    })
    assert await adapter.health() is False


@pytest.mark.asyncio
async def test_http_500_in_health_returns_false(adapter, mock_router):
    """health() catches HTTP errors and returns False."""
    mock_router.get("/internal/ai/tools/health").respond(500, text="Internal Server Error")
    assert await adapter.health() is False


@pytest.mark.asyncio
async def test_lease_error_in_search_raises(adapter, mock_router):
    """Non-health methods should raise LeaseAdapterError."""
    mock_router.post("/internal/ai/tools/room/search").respond(json={
        "code": 500,
        "errorCode": "LEASE_UNAVAILABLE",
        "message": "lease backend down",
    })
    with pytest.raises(LeaseAdapterError) as exc_info:
        await adapter.search_rooms({"district_id": 1005})
    assert exc_info.value.code == "LEASE_UNAVAILABLE"
    assert exc_info.value.recoverable is True
