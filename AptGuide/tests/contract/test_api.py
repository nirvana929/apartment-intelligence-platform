import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health():
    """健康检查接口。"""
    from aptguide.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat(monkeypatch):
    """聊天接口 - mock Agent 执行。"""
    from unittest.mock import AsyncMock

    # Mock agent_graph.ainvoke
    mock_result = {
        "intent": "kb_qa",
        "reply": "押金通常在退租后 7 个工作日内退还。",
        "cards": [],
        "actions": [],
        "confirmation": None,
        "sources": ["FAQ-001"],
    }

    async def mock_ainvoke(state):
        return mock_result

    # 延迟导入并 mock
    import aptguide.main

    monkeypatch.setattr(aptguide.main, "agent_graph", AsyncMock(ainvoke=mock_ainvoke))

    from aptguide.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "test-001",
                "message": "押金怎么退?",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-001"
        assert data["intent"] == "kb_qa"
        assert "reply" in data
        assert "sources" in data
        assert data["sources"] == ["FAQ-001"]
