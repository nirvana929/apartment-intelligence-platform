# AptGuide 阶段 3：预约流程实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现看房预约功能，包含槽位抽取、确认机制、Mock 工具调用

**Architecture:** 基于阶段 2 的工作流，新增预约确认节点和 Mock 工具层

**Tech Stack:** Python 3.12, FastAPI, LangGraph, pymilvus, OpenAI SDK, Redis, uv

---

## 文件结构变更

```text
src/aptguide/tools/
├── __init__.py
├── mock.py          # Mock 工具实现
└── schemas.py       # 工具入参出参

src/aptguide/agent/nodes/
├── confirm.py       # 预约确认节点
└── tool.py          # 工具调用节点

src/aptguide/memory/
├── __init__.py
└── session.py       # 会话状态管理（Redis）

tests/unit/
├── test_tools.py
├── test_confirm.py
└── test_memory.py
```

---

## Task 1: 工具数据模型

**Files:**
- Create: `src/aptguide/tools/__init__.py`
- Create: `src/aptguide/tools/schemas.py`
- Create: `tests/unit/test_tools.py`

- [ ] **Step 1: 创建工具数据模型测试**

```python
# tests/unit/test_tools.py
from aptguide.tools.schemas import (
    AppointmentCreateRequest,
    AppointmentCreateResponse,
    AppointmentQueryResponse,
)


def test_appointment_create_request():
    req = AppointmentCreateRequest(
        room_id=3001,
        appointment_time="2026-05-03 15:00",
        user_id="user-001",
    )
    assert req.room_id == 3001
    assert req.appointment_time == "2026-05-03 15:00"


def test_appointment_create_response():
    resp = AppointmentCreateResponse(
        appointment_id="A20260503302",
        room_id=3001,
        room_title="天河公寓 302",
        appointment_time="2026-05-03 15:00",
        status="confirmed",
    )
    assert resp.appointment_id == "A20260503302"
    assert resp.status == "confirmed"


def test_appointment_query_response():
    resp = AppointmentQueryResponse(
        appointments=[
            {
                "appointment_id": "A20260503302",
                "room_title": "天河公寓 302",
                "appointment_time": "2026-05-03 15:00",
                "status": "confirmed",
            }
        ]
    )
    assert len(resp.appointments) == 1
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_tools.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现工具数据模型**

```python
# src/aptguide/tools/__init__.py
```

```python
# src/aptguide/tools/schemas.py
from pydantic import BaseModel


class AppointmentCreateRequest(BaseModel):
    """预约创建请求"""
    room_id: int
    appointment_time: str
    user_id: str
    remark: str | None = None


class AppointmentCreateResponse(BaseModel):
    """预约创建响应"""
    appointment_id: str
    room_id: int
    room_title: str
    appointment_time: str
    status: str
    created_at: str | None = None


class AppointmentQueryRequest(BaseModel):
    """预约查询请求"""
    user_id: str


class AppointmentQueryResponse(BaseModel):
    """预约查询响应"""
    appointments: list[dict]


class LeaseQueryRequest(BaseModel):
    """租约查询请求"""
    user_id: str


class LeaseQueryResponse(BaseModel):
    """租约查询响应"""
    leases: list[dict]
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_tools.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/tools/ tests/unit/test_tools.py
git commit -m "feat: add tool schemas"
```

---

## Task 2: Mock 工具实现

**Files:**
- Create: `src/aptguide/tools/mock.py`
- Create: `tests/unit/test_mock.py`

- [ ] **Step 1: 创建 Mock 工具测试**

```python
# tests/unit/test_mock.py
import pytest
from datetime import datetime


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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_mock.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现 Mock 工具**

```python
# src/aptguide/tools/mock.py
from datetime import datetime, timedelta


class MockToolClient:
    """Mock 工具客户端"""

    def __init__(self):
        self.appointments = {}
        self.appointment_counter = 1000

    async def create_appointment(
        self,
        room_id: int,
        appointment_time: str,
        user_id: str,
        remark: str | None = None,
    ) -> dict:
        """创建预约"""
        self.appointment_counter += 1
        appointment_id = f"A{datetime.now().strftime('%Y%m%d')}{self.appointment_counter}"

        # 房间标题映射
        room_titles = {
            3001: "天河公寓 302",
            3002: "科韵公寓 506",
            3003: "棠德公寓 412",
        }

        appointment = {
            "appointment_id": appointment_id,
            "room_id": room_id,
            "room_title": room_titles.get(room_id, f"房间 {room_id}"),
            "appointment_time": appointment_time,
            "status": "confirmed",
            "created_at": datetime.now().isoformat(),
            "user_id": user_id,
            "remark": remark,
        }

        self.appointments[appointment_id] = appointment
        return appointment

    async def query_appointments(self, user_id: str) -> dict:
        """查询用户预约"""
        user_appointments = [
            appt for appt in self.appointments.values()
            if appt["user_id"] == user_id
        ]

        # 如果没有预约，返回 Mock 数据
        if not user_appointments:
            user_appointments = [
                {
                    "appointment_id": "A20260501001",
                    "room_title": "天河公寓 302",
                    "appointment_time": "2026-05-05 14:00",
                    "status": "confirmed",
                }
            ]

        return {"appointments": user_appointments}

    async def query_leases(self, user_id: str) -> dict:
        """查询用户租约"""
        # 返回 Mock 数据
        return {
            "leases": [
                {
                    "lease_id": "L20250801001",
                    "room_title": "科韵公寓 506",
                    "start_date": "2025-08-01",
                    "end_date": "2026-07-31",
                    "rent": 2950,
                    "status": "active",
                }
            ]
        }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_mock.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/tools/mock.py tests/unit/test_mock.py
git commit -m "feat: add mock tool client"
```

---

## Task 3: 会话状态管理

**Files:**
- Create: `src/aptguide/memory/__init__.py`
- Create: `src/aptguide/memory/session.py`
- Create: `tests/unit/test_memory.py`

- [ ] **Step 1: 创建会话状态测试**

```python
# tests/unit/test_memory.py
import pytest
from unittest.mock import AsyncMock, MagicMock


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
    import json

    redis = AsyncMock()
    redis.get = AsyncMock(return_value=json.dumps({"key": "value"}))

    memory = SessionMemory(redis)
    result = await memory.get("test-001")

    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_memory_get_pending_confirmation():
    from aptguide.memory.session import SessionMemory
    import json

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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_memory.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现会话状态管理**

```python
# src/aptguide/memory/__init__.py
```

```python
# src/aptguide/memory/session.py
import json
from typing import Any


class SessionMemory:
    """会话状态管理（Redis）"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 小时过期

    async def store(self, session_id: str, data: dict[str, Any]) -> None:
        """存储会话状态"""
        key = f"session:{session_id}"
        value = json.dumps(data, ensure_ascii=False)
        await self.redis.set(key, value, ex=self.ttl)

    async def get(self, session_id: str) -> dict[str, Any] | None:
        """获取会话状态"""
        key = f"session:{session_id}"
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def update(self, session_id: str, updates: dict[str, Any]) -> None:
        """更新会话状态"""
        data = await self.get(session_id) or {}
        data.update(updates)
        await self.store(session_id, data)

    async def store_pending_confirmation(
        self,
        session_id: str,
        confirmation: dict[str, Any],
    ) -> None:
        """存储待确认操作"""
        await self.update(session_id, {"pending_confirmation": confirmation})

    async def get_pending_confirmation(self, session_id: str) -> dict[str, Any] | None:
        """获取待确认操作"""
        data = await self.get(session_id)
        if data:
            return data.get("pending_confirmation")
        return None

    async def clear_pending_confirmation(self, session_id: str) -> None:
        """清除待确认操作"""
        data = await self.get(session_id) or {}
        data.pop("pending_confirmation", None)
        await self.store(session_id, data)

    async def store_last_recommendations(
        self,
        session_id: str,
        recommendations: list[dict],
    ) -> None:
        """存储最近推荐"""
        await self.update(session_id, {"last_recommendations": recommendations})

    async def get_last_recommendations(self, session_id: str) -> list[dict]:
        """获取最近推荐"""
        data = await self.get(session_id)
        if data:
            return data.get("last_recommendations", [])
        return []
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_memory.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/memory/ tests/unit/test_memory.py
git commit -m "feat: add session memory management"
```

---

## Task 4: 预约确认节点

**Files:**
- Create: `src/aptguide/agent/nodes/confirm.py`
- Create: `tests/unit/test_confirm.py`

- [ ] **Step 1: 创建预约确认节点测试**

```python
# tests/unit/test_confirm.py
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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_confirm.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现预约确认节点**

```python
# src/aptguide/agent/nodes/confirm.py
from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.memory.session import SessionMemory


CONFIRM_PROMPT = """你是一个租房助手。用户想要预约看房，需要生成操作摘要等待确认。

用户消息：{message}
预约信息：
- 房间：{room_title}
- 时间：{appointment_time}

请生成一个友好的确认摘要，询问用户是否确认预约。"""


async def confirm_node(
    state: AgentState,
    llm: LLMClient,
    memory: SessionMemory,
) -> dict:
    """预约确认节点"""
    slots = state["slots"]
    room_id = slots.get("room_id")
    appointment_time = slots.get("appointment_time")

    # 获取房间标题
    room_title = f"房间 {room_id}"
    for room in state["search_results"]:
        if room["room_id"] == room_id:
            room_title = room["title"]
            break

    # 生成确认摘要
    prompt = CONFIRM_PROMPT.format(
        message=state["message"],
        room_title=room_title,
        appointment_time=appointment_time,
    )
    reply = await llm.generate(prompt)

    # 存储待确认操作
    confirmation = {
        "type": "appointment_create",
        "params": {
            "room_id": room_id,
            "appointment_time": appointment_time,
            "room_title": room_title,
        },
        "summary": f"{room_title}，{appointment_time}",
    }

    await memory.store_pending_confirmation(state["session_id"], confirmation)

    return {
        "reply": reply,
        "confirmation": confirmation,
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_confirm.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/agent/nodes/confirm.py tests/unit/test_confirm.py
git commit -m "feat: add confirmation node"
```

---

## Task 5: 工具调用节点

**Files:**
- Create: `src/aptguide/agent/nodes/tool.py`
- Create: `tests/unit/test_tool_node.py`

- [ ] **Step 1: 创建工具调用节点测试**

```python
# tests/unit/test_tool_node.py
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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_tool_node.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现工具调用节点**

```python
# src/aptguide/agent/nodes/tool.py
from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.tools.mock import MockToolClient
from aptguide.memory.session import SessionMemory


TOOL_REPLY_PROMPT = """你是一个租房助手。工具调用已完成，请生成回复。

工具类型：{tool_type}
工具结果：{tool_result}

请生成一个友好的回复，告知用户操作结果。"""


async def tool_node(
    state: AgentState,
    llm: LLMClient,
    tool_client: MockToolClient,
    memory: SessionMemory,
) -> dict:
    """工具调用节点"""
    confirmation = state["confirmation"]

    if not confirmation:
        return {
            "reply": "没有待执行的操作。",
            "confirmation": None,
        }

    tool_type = confirmation["type"]
    params = confirmation["params"]

    # 调用对应工具
    if tool_type == "appointment_create":
        result = await tool_client.create_appointment(
            room_id=params["room_id"],
            appointment_time=params["appointment_time"],
            user_id="demo-user",  # 阶段 3 使用演示用户
        )
    else:
        result = {"error": f"未知工具类型：{tool_type}"}

    # 生成回复
    prompt = TOOL_REPLY_PROMPT.format(
        tool_type=tool_type,
        tool_result=result,
    )
    reply = await llm.generate(prompt)

    # 清除待确认操作
    await memory.clear_pending_confirmation(state["session_id"])

    return {
        "reply": reply,
        "confirmation": None,
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_tool_node.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/agent/nodes/tool.py tests/unit/test_tool_node.py
git commit -m "feat: add tool execution node"
```

---

## Task 6: 更新 LangGraph 工作流

**Files:**
- Modify: `src/aptguide/agent/graph.py`

- [ ] **Step 1: 更新工作流添加预约节点**

```python
# src/aptguide/agent/graph.py (完整更新)
from langgraph.graph import StateGraph, END

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.vector.kb_search import KBSearch
from aptguide.vector.room_index import RoomIndex
from aptguide.tools.mock import MockToolClient
from aptguide.memory.session import SessionMemory


def create_agent_graph(
    llm: LLMClient,
    kb: KBSearch,
    room_index: RoomIndex,
    tool_client: MockToolClient,
    memory: SessionMemory,
):
    """创建 Agent 工作流"""
    from aptguide.agent.nodes.intent import intent_node
    from aptguide.agent.nodes.slot import slot_node
    from aptguide.agent.nodes.ask import ask_node
    from aptguide.agent.nodes.kb_search import kb_search_node
    from aptguide.agent.nodes.room_search import room_search_node
    from aptguide.agent.nodes.rerank import rerank_node
    from aptguide.agent.nodes.confirm import confirm_node
    from aptguide.agent.nodes.tool import tool_node
    from aptguide.agent.nodes.reply import reply_node

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent", lambda state: intent_node(state, llm))
    workflow.add_node("slot", lambda state: slot_node(state, llm))
    workflow.add_node("ask", lambda state: ask_node(state, llm))
    workflow.add_node("kb_search", lambda state: kb_search_node(state, kb))
    workflow.add_node("room_search", lambda state: room_search_node(state, room_index))
    workflow.add_node("rerank", lambda state: rerank_node(state, llm))
    workflow.add_node("confirm", lambda state: confirm_node(state, llm, memory))
    workflow.add_node("tool", lambda state: tool_node(state, llm, tool_client, memory))
    workflow.add_node("reply", lambda state: reply_node(state, llm))

    # 定义边
    workflow.set_entry_point("intent")

    def route_intent(state: AgentState) -> str:
        if state["intent"] == "kb_qa":
            return "kb_search"
        elif state["intent"] == "room_search":
            return "slot"
        elif state["intent"] == "appointment_create":
            return "slot"
        return "reply"

    workflow.add_conditional_edges(
        "intent",
        route_intent,
        {
            "kb_search": "kb_search",
            "slot": "slot",
            "reply": "reply",
        },
    )

    def check_slots(state: AgentState) -> str:
        slots = state["slots"]
        if state["intent"] == "room_search":
            if not slots.get("max_rent") or not slots.get("district"):
                return "ask"
            return "room_search"
        elif state["intent"] == "appointment_create":
            if not slots.get("room_id") or not slots.get("appointment_time"):
                return "ask"
            return "confirm"
        return "reply"

    workflow.add_conditional_edges(
        "slot",
        check_slots,
        {
            "ask": "ask",
            "room_search": "room_search",
            "confirm": "confirm",
            "reply": "reply",
        },
    )

    def check_confirmation(state: AgentState) -> str:
        if state["confirmation"]:
            # 检查用户是否确认
            message = state["message"].lower()
            if "确认" in message or "确定" in message or "是" in message:
                return "tool"
            elif "取消" in message or "不" in message:
                return "reply"
        return "reply"

    workflow.add_conditional_edges(
        "confirm",
        check_confirmation,
        {
            "tool": "tool",
            "reply": "reply",
        },
    )

    workflow.add_edge("room_search", "rerank")
    workflow.add_edge("rerank", "reply")
    workflow.add_edge("kb_search", "reply")
    workflow.add_edge("tool", "reply")
    workflow.add_edge("ask", END)
    workflow.add_edge("reply", END)

    return workflow.compile()
```

- [ ] **Step 2: 更新 main.py**

```python
# src/aptguide/main.py (部分更新)
from aptguide.tools.mock import MockToolClient
from aptguide.memory.session import SessionMemory

# 在全局实例部分添加
tool_client = MockToolClient()

# Redis 连接（阶段 3）
import redis.asyncio as redis
redis_client = redis.from_url(settings.redis_url)
memory = SessionMemory(redis_client)

# 更新 agent_graph 创建
agent_graph = create_agent_graph(llm, kb, room_index, tool_client, memory)
```

- [ ] **Step 3: 运行测试验证**

```bash
uv run pytest tests/unit/test_agent.py -v
```

预期：PASS

- [ ] **Step 4: 提交**

```bash
git add src/aptguide/agent/graph.py src/aptguide/main.py
git commit -m "feat: update agent graph with appointment nodes"
```

---

## Task 7: 更新 API 路由

**Files:**
- Modify: `src/aptguide/api/chat.py`

- [ ] **Step 1: 更新聊天路由支持确认操作**

```python
# src/aptguide/api/chat.py (完整更新)
import uuid

from fastapi import APIRouter

from aptguide.schemas.request import ChatRequest
from aptguide.schemas.response import ChatResponse

router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天接口"""
    from aptguide.main import agent_graph, memory

    request_id = str(uuid.uuid4())

    # 获取会话状态
    session = await memory.get(request.session_id)

    if not session:
        session = {
            "session_id": request.session_id,
            "message": request.message,
            "intent": None,
            "slots": {},
            "search_results": [],
            "confirmation": None,
            "reply": "",
            "cards": [],
            "actions": [],
            "sources": [],
        }

    # 更新消息
    session["message"] = request.message

    # 执行 Agent
    result = await agent_graph.ainvoke(session)

    # 更新会话状态
    await memory.store(request.session_id, result)

    # 如果有房源推荐，存储最近推荐
    if result.get("cards"):
        await memory.store_last_recommendations(
            request.session_id,
            result["cards"],
        )

    return ChatResponse(
        session_id=request.session_id,
        request_id=request_id,
        intent=result.get("intent", "other"),
        reply=result.get("reply", ""),
        cards=result.get("cards", []),
        actions=result.get("actions", []),
        pending_confirmation=result.get("confirmation"),
        sources=result.get("sources", []),
    )
```

- [ ] **Step 2: 运行测试验证**

```bash
uv run pytest tests/contract/test_api.py -v
```

预期：PASS

- [ ] **Step 3: 提交**

```bash
git add src/aptguide/api/chat.py
git commit -m "feat: update chat API with confirmation support"
```

---

## Task 8: 更新前端界面

**Files:**
- Modify: `src/aptguide/ui/index.html`
- Modify: `src/aptguide/ui/style.css`
- Modify: `src/aptguide/ui/app.js`

- [ ] **Step 1: 更新 HTML 添加确认区域**

```html
<!-- src/aptguide/ui/index.html (部分更新) -->
<!-- 在 message-content 后添加确认按钮容器 -->
<div class="message assistant">
    <div class="message-content"></div>
    <div class="cards-container"></div>
    <div class="confirmation-container"></div>
    <div class="source"></div>
</div>
```

- [ ] **Step 2: 更新 CSS 添加确认按钮样式**

```css
/* src/aptguide/ui/style.css (添加) */
.confirmation-container {
    margin-top: 12px;
    padding: 12px;
    background-color: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
}

.confirmation-summary {
    font-size: 14px;
    color: #856404;
    margin-bottom: 12px;
}

.confirmation-actions {
    display: flex;
    gap: 8px;
}

.confirmation-actions button {
    flex: 1;
    padding: 8px 16px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
}

.confirmation-actions .btn-confirm {
    background-color: #28a745;
    color: #fff;
}

.confirmation-actions .btn-cancel {
    background-color: #dc3545;
    color: #fff;
}
```

- [ ] **Step 3: 更新 JavaScript 处理确认操作**

```javascript
// src/aptguide/ui/app.js (部分更新)
function addMessage(content, isUser = false, sources = [], cards = [], pendingConfirmation = null) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user" : "assistant"}`;

    let html = `<div class="message-content">${content}</div>`;

    // 添加房源卡片
    if (cards.length > 0) {
        html += '<div class="cards-container">';
        cards.forEach(card => {
            if (card.type === "room") {
                html += `
                    <div class="room-card">
                        <div class="room-card-header">
                            <div class="room-card-title">${card.title}</div>
                            <div class="room-card-rent">¥${card.rent}/月</div>
                        </div>
                        <div class="room-card-district">${card.district}</div>
                        <div class="room-card-tags">
                            ${card.tags.map(tag => `<span class="room-card-tag">${tag}</span>`).join('')}
                        </div>
                        <div class="room-card-description">${card.description || ''}</div>
                        <div class="room-card-actions">
                            <button class="btn-primary" onclick="createAppointment(${card.room_id})">预约看房</button>
                            <button class="btn-secondary" onclick="viewDetail(${card.room_id})">查看详情</button>
                        </div>
                    </div>
                `;
            }
        });
        html += '</div>';
    }

    // 添加确认区域
    if (pendingConfirmation) {
        html += `
            <div class="confirmation-container">
                <div class="confirmation-summary">${pendingConfirmation.summary}</div>
                <div class="confirmation-actions">
                    <button class="btn-confirm" onclick="confirmAction()">确认</button>
                    <button class="btn-cancel" onclick="cancelAction()">取消</button>
                </div>
            </div>
        `;
    }

    if (sources.length > 0) {
        html += `<div class="source">来源：${sources.join(", ")}</div>`;
    }

    messageDiv.innerHTML = html;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 添加确认操作函数
function confirmAction() {
    messageInput.value = "确认";
    sendMessage();
}

function cancelAction() {
    messageInput.value = "取消";
    sendMessage();
}

// 更新 sendMessage 函数
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // 添加用户消息
    addMessage(message, true);
    messageInput.value = "";

    // 禁用发送按钮
    sendButton.disabled = true;
    sendButton.textContent = "发送中...";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message,
            }),
        });

        const data = await response.json();

        // 添加助手回复
        addMessage(
            data.reply,
            false,
            data.sources,
            data.cards,
            data.pending_confirmation,
        );
    } catch (error) {
        addMessage("抱歉，发生了错误。请稍后重试。", false);
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "发送";
    }
}
```

- [ ] **Step 4: 提交**

```bash
git add src/aptguide/ui/
git commit -m "feat: add confirmation UI components"
```

---

## Task 9: 更新 Docker Compose

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: 添加 Redis 服务**

```yaml
# docker-compose.yml (添加 redis 服务)
version: '3.8'

services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.0
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - etcd-data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - minio-data:/minio_data
    command: minio server /minio_data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  milvus:
    image: milvusdb/milvus:v2.4-latest
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus-data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  etcd-data:
  minio-data:
  milvus-data:
  redis-data:
```

- [ ] **Step 2: 测试 Docker Compose**

```bash
docker-compose up -d
docker-compose ps
```

预期：所有服务正常运行，包括 Redis

- [ ] **Step 3: 提交**

```bash
git add docker-compose.yml
git commit -m "feat: add Redis to Docker Compose"
```

---

## Task 10: 端到端测试

**Files:**
- Modify: `tests/e2e/test_e2e.py`

- [ ] **Step 1: 添加预约端到端测试**

```python
# tests/e2e/test_e2e.py (添加)
@pytest.mark.asyncio
async def test_appointment_conversation():
    """测试预约对话流程"""
    from aptguide.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # 第一轮：表达找房需求
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "e2e-test-003",
                "message": "想找安静、适合考研的房子",
            },
        )
        assert response.status_code == 200

        # 第二轮：补充预算和区域
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "e2e-test-003",
                "message": "预算3000，天河区",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["cards"]) > 0

        # 第三轮：预约第一个房源
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "e2e-test-003",
                "message": "预约第一个房源明天下午3点看房",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pending_confirmation"] is not None

        # 第四轮：确认预约
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "e2e-test-003",
                "message": "确认",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "预约成功" in data["reply"]
```

- [ ] **Step 2: 运行端到端测试**

```bash
uv run pytest tests/e2e/test_e2e.py -v
```

预期：PASS

- [ ] **Step 3: 提交**

```bash
git add tests/e2e/test_e2e.py
git commit -m "test: add appointment e2e tests"
```

---

## 里程碑检查

完成所有任务后，运行以下检查：

```bash
# 1. 运行所有测试
uv run pytest

# 2. 代码检查
uv run ruff check src tests
uv run ruff format src tests

# 3. 启动依赖服务
docker-compose up -d

# 4. 初始化知识库和房源
uv run python scripts/seed_kb.py
uv run python scripts/sync_room_vectors.py

# 5. 启动应用
make dev

# 6. 浏览器测试
# 打开 http://localhost:8100
# 测试完整预约流程：
# 1) "想找安静、适合考研的房子"
# 2) "预算3000，天河区"
# 3) "预约第一个房源明天下午3点看房"
# 4) "确认"
```

---

**计划状态**：已完成
**下一步**：用户审查后，选择执行方式
