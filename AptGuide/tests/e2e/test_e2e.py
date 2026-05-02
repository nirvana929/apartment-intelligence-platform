"""端到端测试。"""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

# 会话存储需在测试间隔离，避免用例互相干扰
import aptguide.api.chat as chat_module


@pytest.fixture(autouse=True)
def _clear_sessions():
    """每个测试前后清空会话存储。"""
    chat_module.sessions.clear()
    yield
    chat_module.sessions.clear()


def _make_mock_graph(intent: str = "kb_qa", sources: list[str] | None = None):
    """构建一个可 await 的 Agent 图 mock。

    参数意图: 控制每次 ainvoke 返回的 intent 和 sources 字段，
    让断言可以验证端到端路径。
    """
    if sources is None:
        sources = ["《租客常见问题解答》"]

    async def fake_ainvoke(state: dict) -> dict:
        """模拟 Agent 图执行：原样透传大部分状态，填充 reply/sources。"""
        return {
            "session_id": state["session_id"],
            "message": state["message"],
            "intent": intent,
            "slots": {},
            "search_results": [],
            "confirmation": None,
            "reply": f"模拟回复: {state['message']}",
            "cards": [],
            "actions": [],
            "sources": sources,
        }

    mock = AsyncMock()
    mock.ainvoke = fake_ainvoke
    return mock


@pytest.mark.asyncio
async def test_full_conversation(monkeypatch):
    """测试完整对话流程：两轮知识问答共享同一会话。"""
    from aptguide.main import app

    # Mock agent_graph，避免真实 LLM/Milvus 调用
    mock_graph = _make_mock_graph(intent="kb_qa")
    monkeypatch.setattr("aptguide.main.agent_graph", mock_graph)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # 第一轮：知识问答
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "e2e-test-001",
                "message": "押金怎么退？",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "kb_qa"
        assert len(data["sources"]) > 0
        assert data["session_id"] == "e2e-test-001"

        # 第二轮：继续问答（同一会话）
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "e2e-test-001",
                "message": "可以提前退租吗？",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "kb_qa"
        assert data["session_id"] == "e2e-test-001"


@pytest.mark.asyncio
async def test_search_intent(monkeypatch):
    """测试找房意图路径。"""
    from aptguide.main import app

    mock_graph = _make_mock_graph(intent="search")
    monkeypatch.setattr("aptguide.main.agent_graph", mock_graph)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "e2e-test-002",
                "message": "帮我找一间朝阳区的两居室",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "search"
        assert data["session_id"] == "e2e-test-002"


@pytest.mark.asyncio
async def test_separate_sessions_isolated(monkeypatch):
    """不同 session_id 的会话互不干扰。"""
    from aptguide.main import app

    mock_graph = _make_mock_graph(intent="kb_qa")
    monkeypatch.setattr("aptguide.main.agent_graph", mock_graph)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # 会话 A
        resp_a = await client.post(
            "/api/chat",
            json={"session_id": "session-a", "message": "你好"},
        )
        # 会话 B
        resp_b = await client.post(
            "/api/chat",
            json={"session_id": "session-b", "message": "租房"},
        )
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        assert resp_a.json()["session_id"] == "session-a"
        assert resp_b.json()["session_id"] == "session-b"
