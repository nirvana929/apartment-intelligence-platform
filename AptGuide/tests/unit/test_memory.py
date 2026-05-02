import json
import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_memory_store():
    from aptguide.memory.session import SessionMemory

    redis = AsyncMock()
    redis.set = AsyncMock()
    redis.get = AsyncMock(return_value=None)

    memory = SessionMemory(redis)
    await memory.store("test-001", {"key": "value"})

    redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_memory_get():
    from aptguide.memory.session import SessionMemory

    redis = AsyncMock()
    redis.get = AsyncMock(return_value=json.dumps({"key": "value"}))

    memory = SessionMemory(redis)
    result = await memory.get("test-001")

    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_memory_get_pending_confirmation():
    from aptguide.memory.session import SessionMemory

    redis = AsyncMock()
    redis.get = AsyncMock(return_value=json.dumps({
        "pending_confirmation": {
            "type": "appointment_create",
            "params": {"room_id": 3001, "appointment_time": "2026-05-03 15:00"},
            "summary": "天河公寓 302，2026-05-03 15:00",
        }
    }))

    memory = SessionMemory(redis)
    result = await memory.get_pending_confirmation("test-001")

    assert result["type"] == "appointment_create"


@pytest.mark.asyncio
async def test_memory_clear_pending_confirmation():
    from aptguide.memory.session import SessionMemory

    redis = AsyncMock()
    redis.get = AsyncMock(return_value=json.dumps({
        "pending_confirmation": {"type": "appointment_create"},
        "other_key": "value",
    }))
    redis.set = AsyncMock()

    memory = SessionMemory(redis)
    await memory.clear_pending_confirmation("test-001")

    # Should have called set with data that doesn't have pending_confirmation
    redis.set.assert_called_once()
    call_args = redis.set.call_args
    stored_data = json.loads(call_args[0][1])
    assert "pending_confirmation" not in stored_data
