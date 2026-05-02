import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_confirm_node():
    from aptguide.agent.nodes.confirm import confirm_node

    state = {
        "session_id": "test-001",
        "message": "预约第一个房源明天下午3点看房",
        "intent": "appointment_create",
        "slots": {
            "room_id": 3001,
            "appointment_time": "2026-05-03 15:00",
        },
        "search_results": [
            {
                "room_id": 3001,
                "title": "天河公寓 302",
                "rent": 2800,
            }
        ],
        "confirmation": None,
        "reply": "",
        "cards": [],
        "actions": [],
        "sources": [],
    }

    memory = AsyncMock()
    memory.store_pending_confirmation = AsyncMock()

    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="准备为你创建预约：\n房源：天河公寓 302\n时间：2026-05-03 15:00\n是否确认？")

    result = await confirm_node(state, llm, memory)

    assert "天河公寓" in result["reply"]
    assert "15:00" in result["reply"]
    assert result["confirmation"]["type"] == "appointment_create"


@pytest.mark.asyncio
async def test_confirm_node_default_room_title():
    """Test when room_id is not in search_results"""
    from aptguide.agent.nodes.confirm import confirm_node

    state = {
        "session_id": "test-002",
        "message": "预约看房",
        "intent": "appointment_create",
        "slots": {
            "room_id": 9999,
            "appointment_time": "2026-05-04 10:00",
        },
        "search_results": [],
        "confirmation": None,
        "reply": "",
        "cards": [],
        "actions": [],
        "sources": [],
    }

    memory = AsyncMock()
    memory.store_pending_confirmation = AsyncMock()

    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="准备为你创建预约：房间 9999")

    result = await confirm_node(state, llm, memory)

    assert result["confirmation"]["params"]["room_title"] == "房间 9999"
