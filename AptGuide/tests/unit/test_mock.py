import pytest


@pytest.mark.asyncio
async def test_mock_create_appointment():
    from aptguide.tools.mock import MockToolClient

    client = MockToolClient()
    result = await client.create_appointment(
        room_id=3001,
        appointment_time="2026-05-03 15:00",
        user_id="user-001",
    )

    assert result["appointment_id"].startswith("A")
    assert result["room_id"] == 3001
    assert result["status"] == "confirmed"


@pytest.mark.asyncio
async def test_mock_query_appointments():
    from aptguide.tools.mock import MockToolClient

    client = MockToolClient()
    result = await client.query_appointments(user_id="user-001")

    assert "appointments" in result
    assert len(result["appointments"]) > 0


@pytest.mark.asyncio
async def test_mock_query_leases():
    from aptguide.tools.mock import MockToolClient

    client = MockToolClient()
    result = await client.query_leases(user_id="user-001")

    assert "leases" in result
    assert len(result["leases"]) > 0
