import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_tool_node_create_appointment():
    from aptguide.agent.nodes.tool import tool_node

    state = {
        "session_id": "test-001",
        "message": "确认",
        "intent": "appointment_create",
        "slots": {},
        "search_results": [],
        "confirmation": {
            "type": "appointment_create",
            "params": {
                "room_id": 3001,
                "appointment_time": "2026-05-03 15:00",
                "room_title": "天河公寓 302",
            },
        },
        "reply": "",
        "cards": [],
        "actions": [],
        "sources": [],
    }

    tool_client = AsyncMock()
    tool_client.create_appointment = AsyncMock(return_value={
        "appointment_id": "A20260503302",
        "room_id": 3001,
        "room_title": "天河公寓 302",
        "appointment_time": "2026-05-03 15:00",
        "status": "confirmed",
    })

    memory = AsyncMock()
    memory.clear_pending_confirmation = AsyncMock()

    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="预约成功！预约号 A20260503302，届时门店会有专人接待。")

    result = await tool_node(state, llm, tool_client, memory)

    assert "预约成功" in result["reply"]
    assert "A20260503302" in result["reply"]
    assert result["confirmation"] is None


@pytest.mark.asyncio
async def test_tool_node_no_confirmation():
    from aptguide.agent.nodes.tool import tool_node

    state = {
        "session_id": "test-002",
        "message": "确认",
        "intent": "appointment_create",
        "slots": {},
        "search_results": [],
        "confirmation": None,
        "reply": "",
        "cards": [],
        "actions": [],
        "sources": [],
    }

    tool_client = AsyncMock()
    memory = AsyncMock()
    llm = AsyncMock()

    result = await tool_node(state, llm, tool_client, memory)

    assert "没有待执行的操作" in result["reply"]
    assert result["confirmation"] is None
