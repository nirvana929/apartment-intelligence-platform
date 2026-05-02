# AptGuide 阶段 1：知识问答实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现租房规则 FAQ 问答系统，用户可通过浏览器输入问题获得基于 Milvus 知识库的回答

**Architecture:** FastAPI + LangGraph 工作流，Milvus 向量检索，纯 HTML/CSS/JS 前端

**Tech Stack:** Python 3.12, FastAPI, LangGraph, pymilvus, OpenAI SDK, uv

---

## 文件结构

```text
src/aptguide/
├── core/
│   ├── __init__.py
│   ├── config.py          # pydantic-settings 配置
│   └── logging.py         # JSON 日志
├── llm/
│   ├── __init__.py
│   └── client.py          # OpenAI 兼容客户端
├── vector/
│   ├── __init__.py
│   ├── client.py          # Milvus 连接
│   ├── embedding.py       # Embedding 封装
│   └── kb_search.py       # 知识库检索
├── agent/
│   ├── __init__.py
│   ├── state.py           # 状态定义
│   ├── graph.py           # LangGraph 工作流
│   └── nodes/
│       ├── __init__.py
│       ├── intent.py      # 意图识别
│       ├── kb_search.py   # 知识检索节点
│       └── reply.py       # 回复生成
├── schemas/
│   ├── __init__.py
│   ├── request.py         # 请求模型
│   └── response.py        # 响应模型
├── api/
│   ├── __init__.py
│   ├── chat.py            # /api/chat 路由
│   └── health.py          # /health 路由
├── ui/
│   ├── index.html         # 主页面
│   ├── style.css          # 样式
│   └── app.js             # 交互逻辑
└── main.py                # FastAPI 入口

scripts/
└── seed_kb.py             # 知识库初始化

tests/
├── unit/
│   ├── test_config.py
│   ├── test_vector.py
│   └── test_agent.py
└── contract/
    └── test_api.py
```

---

## Task 1: 项目配置与日志

**Files:**
- Create: `src/aptguide/core/__init__.py`
- Create: `src/aptguide/core/config.py`
- Create: `src/aptguide/core/logging.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: 创建配置模块测试**

```python
# tests/unit/test_config.py
import os
from unittest.mock import patch

def test_settings_load_from_env():
    with patch.dict(os.environ, {
        "LLM_API_KEY": "test_key",
        "LLM_BASE_URL": "https://test.api.com/v1",
        "LLM_MODEL": "qwen-plus",
        "EMBEDDING_API_KEY": "test_key",
        "MILVUS_URI": "http://localhost:19530",
    }):
        from aptguide.core.config import Settings
        settings = Settings()
        assert settings.llm_api_key == "test_key"
        assert settings.llm_model == "qwen-plus"
        assert settings.milvus_uri == "http://localhost:19530"

def test_settings_default_values():
    with patch.dict(os.environ, {
        "LLM_API_KEY": "test_key",
        "EMBEDDING_API_KEY": "test_key",
    }):
        from aptguide.core.config import Settings
        settings = Settings()
        assert settings.llm_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert settings.llm_model == "qwen-plus"
        assert settings.app_env == "development"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
uv run pytest tests/unit/test_config.py -v
```

预期：FAIL - ModuleNotFoundError: No module named 'aptguide.core.config'

- [ ] **Step 3: 实现配置模块**

```python
# src/aptguide/core/__init__.py
```

```python
# src/aptguide/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # LLM
    llm_api_key: str
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"

    # Embedding
    embedding_api_key: str
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_model: str = "text-embedding-v3"

    # Milvus
    milvus_uri: str = "http://localhost:19530"
    milvus_token: str = ""

    # Redis（阶段 3 启用）
    redis_url: str = "redis://localhost:6379/1"

    # 应用
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_config.py -v
```

预期：PASS

- [ ] **Step 5: 实现日志模块**

```python
# src/aptguide/core/logging.py
import logging
import sys

from pythonjsonlogger import jsonlogger

from aptguide.core.config import Settings


def setup_logging(settings: Settings) -> None:
    """配置 JSON 日志"""
    logger = logging.getLogger("aptguide")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
```

- [ ] **Step 6: 提交**

```bash
git add src/aptguide/core/ tests/unit/test_config.py
git commit -m "feat: add config and logging modules"
```

---

## Task 2: LLM 客户端

**Files:**
- Create: `src/aptguide/llm/__init__.py`
- Create: `src/aptguide/llm/client.py`
- Create: `tests/unit/test_llm.py`

- [ ] **Step 1: 创建 LLM 客户端测试**

```python
# tests/unit/test_llm.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_llm_client_generate():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="测试回复"))]

    with patch("openai.AsyncOpenAI") as mock_client:
        mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

        from aptguide.llm.client import LLMClient
        from aptguide.core.config import Settings

        settings = Settings(
            llm_api_key="test_key",
            embedding_api_key="test_key",
        )
        client = LLMClient(settings)

        result = await client.generate("测试提示词")
        assert result == "测试回复"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_llm.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现 LLM 客户端**

```python
# src/aptguide/llm/__init__.py
```

```python
# src/aptguide/llm/client.py
from openai import AsyncOpenAI

from aptguide.core.config import Settings


class LLMClient:
    """OpenAI 兼容 LLM 客户端"""

    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
        self.model = settings.llm_model

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """生成回复"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_llm.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/llm/ tests/unit/test_llm.py
git commit -m "feat: add LLM client"
```

---

## Task 3: Milvus 客户端与知识库检索

**Files:**
- Create: `src/aptguide/vector/__init__.py`
- Create: `src/aptguide/vector/client.py`
- Create: `src/aptguide/vector/embedding.py`
- Create: `src/aptguide/vector/kb_search.py`
- Create: `tests/unit/test_vector.py`

- [ ] **Step 1: 创建 Milvus 客户端测试**

```python
# tests/unit/test_vector.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_milvus_client_connect():
    with patch("pymilvus.MilvusClient") as mock_client:
        from aptguide.vector.client import MilvusClientWrapper
        from aptguide.core.config import Settings

        settings = Settings(
            llm_api_key="test_key",
            embedding_api_key="test_key",
            milvus_uri="http://localhost:19530",
        )
        client = MilvusClientWrapper(settings)
        client.connect()
        mock_client.assert_called_once_with(uri="http://localhost:19530", token="")

@pytest.mark.asyncio
async def test_kb_search():
    mock_results = [
        {"id": "KB-RULE-008", "content": "提前退租规则", "score": 0.85}
    ]

    with patch("aptguide.vector.client.MilvusClientWrapper") as mock_client:
        mock_client.return_value.search.return_value = mock_results

        from aptguide.vector.kb_search import KBSearch
        from aptguide.core.config import Settings

        settings = Settings(
            llm_api_key="test_key",
            embedding_api_key="test_key",
        )
        kb = KBSearch(mock_client.return_value, settings)
        results = await kb.search("押金怎么退", top_k=3)

        assert len(results) == 1
        assert results[0]["id"] == "KB-RULE-008"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_vector.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现 Milvus 客户端**

```python
# src/aptguide/vector/__init__.py
```

```python
# src/aptguide/vector/client.py
from pymilvus import MilvusClient

from aptguide.core.config import Settings


class MilvusClientWrapper:
    """Milvus 客户端封装"""

    def __init__(self, settings: Settings):
        self.uri = settings.milvus_uri
        self.token = settings.milvus_token
        self.client: MilvusClient | None = None

    def connect(self) -> None:
        """连接 Milvus"""
        self.client = MilvusClient(uri=self.uri, token=self.token)

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: int = 3,
        output_fields: list[str] | None = None,
    ) -> list[dict]:
        """向量检索"""
        if not self.client:
            raise RuntimeError("Milvus client not connected")

        results = self.client.search(
            collection_name=collection_name,
            data=[query_vector],
            limit=top_k,
            output_fields=output_fields,
        )
        return results[0] if results else []
```

- [ ] **Step 4: 实现 Embedding 封装**

```python
# src/aptguide/vector/embedding.py
from openai import AsyncOpenAI

from aptguide.core.config import Settings


class EmbeddingClient:
    """Embedding 客户端"""

    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
        )
        self.model = settings.embedding_model

    async def embed(self, text: str) -> list[float]:
        """生成向量"""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding
```

- [ ] **Step 5: 实现知识库检索**

```python
# src/aptguide/vector/kb_search.py
from aptguide.core.config import Settings
from aptguide.vector.client import MilvusClientWrapper
from aptguide.vector.embedding import EmbeddingClient


class KBSearch:
    """知识库检索"""

    COLLECTION_NAME = "apt_rental_kb"

    def __init__(self, milvus: MilvusClientWrapper, settings: Settings):
        self.milvus = milvus
        self.embedding = EmbeddingClient(settings)

    async def search(self, query: str, top_k: int = 3) -> list[dict]:
        """检索知识库"""
        query_vector = await self.embedding.embed(query)

        results = self.milvus.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            top_k=top_k,
            output_fields=["id", "content", "category", "title"],
        )

        # 过滤低分结果
        filtered = []
        for result in results:
            if result.get("score", 0) >= 0.7:
                filtered.append({
                    "id": result["id"],
                    "content": result["content"],
                    "category": result.get("category"),
                    "title": result.get("title"),
                    "score": result["score"],
                })

        return filtered
```

- [ ] **Step 6: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_vector.py -v
```

预期：PASS

- [ ] **Step 7: 提交**

```bash
git add src/aptguide/vector/ tests/unit/test_vector.py
git commit -m "feat: add Milvus client and KB search"
```

---

## Task 4: 数据模型

**Files:**
- Create: `src/aptguide/schemas/__init__.py`
- Create: `src/aptguide/schemas/request.py`
- Create: `src/aptguide/schemas/response.py`
- Create: `tests/unit/test_schemas.py`

- [ ] **Step 1: 创建数据模型测试**

```python
# tests/unit/test_schemas.py
from aptguide.schemas.request import ChatRequest
from aptguide.schemas.response import ChatResponse, Card


def test_chat_request():
    req = ChatRequest(session_id="test-001", message="押金怎么退？")
    assert req.session_id == "test-001"
    assert req.message == "押金怎么退？"
    assert req.context is None


def test_chat_request_with_context():
    req = ChatRequest(
        session_id="test-001",
        message="预约第一个",
        context={"last_recommendations": [3001, 3002]},
    )
    assert req.context == {"last_recommendations": [3001, 3002]}


def test_chat_response():
    resp = ChatResponse(
        session_id="test-001",
        request_id="req-uuid",
        intent="kb_qa",
        reply="根据规则...",
        cards=[],
        actions=[],
        pending_confirmation=None,
        sources=["KB-RULE-008"],
    )
    assert resp.intent == "kb_qa"
    assert len(resp.sources) == 1


def test_card():
    card = Card(
        type="room",
        room_id=3001,
        title="天河公寓 302",
        rent=2800,
        district="天河区",
        tags=["独卫", "朝南"],
    )
    assert card.type == "room"
    assert card.rent == 2800
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_schemas.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现请求模型**

```python
# src/aptguide/schemas/__init__.py
```

```python
# src/aptguide/schemas/request.py
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: str
    message: str
    context: dict | None = None
```

- [ ] **Step 4: 实现响应模型**

```python
# src/aptguide/schemas/response.py
from pydantic import BaseModel


class Card(BaseModel):
    """卡片"""
    type: str  # "room" | "faq"
    room_id: int | None = None
    title: str
    rent: int | None = None
    district: str | None = None
    tags: list[str] = []
    description: str | None = None
    thumbnail_url: str | None = None


class Action(BaseModel):
    """操作按钮"""
    type: str  # "view_detail" | "create_appointment"
    room_id: int | None = None


class PendingConfirmation(BaseModel):
    """待确认操作"""
    type: str
    params: dict
    summary: str


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    request_id: str
    intent: str
    reply: str
    cards: list[Card] = []
    actions: list[Action] = []
    pending_confirmation: PendingConfirmation | None = None
    sources: list[str] = []
```

- [ ] **Step 5: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_schemas.py -v
```

预期：PASS

- [ ] **Step 6: 提交**

```bash
git add src/aptguide/schemas/ tests/unit/test_schemas.py
git commit -m "feat: add request/response models"
```

---

## Task 5: LangGraph 状态与节点

**Files:**
- Create: `src/aptguide/agent/__init__.py`
- Create: `src/aptguide/agent/state.py`
- Create: `src/aptguide/agent/nodes/__init__.py`
- Create: `src/aptguide/agent/nodes/intent.py`
- Create: `src/aptguide/agent/nodes/kb_search.py`
- Create: `src/aptguide/agent/nodes/reply.py`
- Create: `src/aptguide/agent/graph.py`
- Create: `tests/unit/test_agent.py`

- [ ] **Step 1: 创建 Agent 状态测试**

```python
# tests/unit/test_agent.py
from aptguide.agent.state import AgentState


def test_agent_state():
    state: AgentState = {
        "session_id": "test-001",
        "message": "押金怎么退？",
        "intent": None,
        "slots": {},
        "search_results": [],
        "confirmation": None,
        "reply": "",
        "cards": [],
        "actions": [],
        "sources": [],
    }
    assert state["session_id"] == "test-001"
    assert state["intent"] is None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_agent.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现 Agent 状态**

```python
# src/aptguide/agent/__init__.py
```

```python
# src/aptguide/agent/state.py
from typing import TypedDict


class AgentState(TypedDict):
    """Agent 状态"""
    session_id: str
    message: str
    intent: str | None
    slots: dict
    search_results: list
    confirmation: dict | None
    reply: str
    cards: list
    actions: list
    sources: list
```

- [ ] **Step 4: 实现意图识别节点**

```python
# src/aptguide/agent/nodes/__init__.py
```

```python
# src/aptguide/agent/nodes/intent.py
from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient


INTENT_PROMPT = """你是一个租房助手的意图识别模块。根据用户消息，判断用户意图。

可能的意图：
- kb_qa: 租房规则问答（押金、退租、续约、预约规则等）
- room_search: 找房需求（预算、区域、偏好等）
- appointment_create: 预约看房
- other: 其他

只返回意图名称，不要返回其他内容。

用户消息：{message}"""


async def intent_node(state: AgentState, llm: LLMClient) -> dict:
    """意图识别节点"""
    prompt = INTENT_PROMPT.format(message=state["message"])
    intent = await llm.generate(prompt)

    # 清理响应
    intent = intent.strip().lower()
    if intent not in ["kb_qa", "room_search", "appointment_create"]:
        intent = "other"

    return {"intent": intent}
```

- [ ] **Step 5: 实现知识检索节点**

```python
# src/aptguide/agent/nodes/kb_search.py
from aptguide.agent.state import AgentState
from aptguide.vector.kb_search import KBSearch


async def kb_search_node(state: AgentState, kb: KBSearch) -> dict:
    """知识检索节点"""
    results = await kb.search(state["message"], top_k=3)

    search_results = []
    sources = []
    for result in results:
        search_results.append(result)
        sources.append(result["id"])

    return {
        "search_results": search_results,
        "sources": sources,
    }
```

- [ ] **Step 6: 实现回复生成节点**

```python
# src/aptguide/agent/nodes/reply.py
from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient


REPLY_PROMPT = """你是一个租房助手。根据检索到的知识库内容，回答用户问题。

要求：
1. 回答要简洁明了
2. 如果涉及具体规则，引用来源
3. 如果没有找到相关信息，告知用户联系门店

用户问题：{message}

检索结果：
{search_results}"""


async def reply_node(state: AgentState, llm: LLMClient) -> dict:
    """回复生成节点"""
    if not state["search_results"]:
        return {
            "reply": "抱歉，我暂时无法回答这个问题。建议联系门店咨询。",
            "cards": [],
            "actions": [],
        }

    # 格式化检索结果
    results_text = "\n".join([
        f"- {r['title']}: {r['content']}"
        for r in state["search_results"]
    ])

    prompt = REPLY_PROMPT.format(
        message=state["message"],
        search_results=results_text,
    )
    reply = await llm.generate(prompt)

    return {
        "reply": reply,
        "cards": [],
        "actions": [],
    }
```

- [ ] **Step 7: 实现 LangGraph 工作流**

```python
# src/aptguide/agent/graph.py
from langgraph.graph import StateGraph, END

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.vector.kb_search import KBSearch


def create_agent_graph(llm: LLMClient, kb: KBSearch):
    """创建 Agent 工作流"""
    from aptguide.agent.nodes.intent import intent_node
    from aptguide.agent.nodes.kb_search import kb_search_node
    from aptguide.agent.nodes.reply import reply_node

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent", lambda state: intent_node(state, llm))
    workflow.add_node("kb_search", lambda state: kb_search_node(state, kb))
    workflow.add_node("reply", lambda state: reply_node(state, llm))

    # 定义边
    workflow.set_entry_point("intent")

    def route_intent(state: AgentState) -> str:
        if state["intent"] == "kb_qa":
            return "kb_search"
        return "reply"

    workflow.add_conditional_edges(
        "intent",
        route_intent,
        {
            "kb_search": "kb_search",
            "reply": "reply",
        },
    )

    workflow.add_edge("kb_search", "reply")
    workflow.add_edge("reply", END)

    return workflow.compile()
```

- [ ] **Step 8: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_agent.py -v
```

预期：PASS

- [ ] **Step 9: 提交**

```bash
git add src/aptguide/agent/ tests/unit/test_agent.py
git commit -m "feat: add LangGraph agent workflow"
```

---

## Task 6: API 路由

**Files:**
- Create: `src/aptguide/api/__init__.py`
- Create: `src/aptguide/api/chat.py`
- Create: `src/aptguide/api/health.py`
- Create: `src/aptguide/main.py`
- Create: `tests/contract/test_api.py`

- [ ] **Step 1: 创建 API 测试**

```python
# tests/contract/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health():
    from aptguide.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat():
    from aptguide.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "test-001",
                "message": "押金怎么退？",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "sources" in data
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/contract/test_api.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现健康检查路由**

```python
# src/aptguide/api/__init__.py
```

```python
# src/aptguide/api/health.py
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
```

- [ ] **Step 4: 实现聊天路由**

```python
# src/aptguide/api/chat.py
import uuid

from fastapi import APIRouter

from aptguide.schemas.request import ChatRequest
from aptguide.schemas.response import ChatResponse

router = APIRouter()

# 会话存储（阶段 1 使用内存）
sessions: dict[str, dict] = {}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天接口"""
    from aptguide.main import agent_graph

    request_id = str(uuid.uuid4())

    # 获取或创建会话状态
    session = sessions.get(request.session_id, {
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
    })

    # 更新消息
    session["message"] = request.message

    # 执行 Agent
    result = await agent_graph.ainvoke(session)

    # 更新会话
    sessions[request.session_id] = result

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

- [ ] **Step 5: 实现 FastAPI 入口**

```python
# src/aptguide/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from aptguide.core.config import Settings
from aptguide.core.logging import setup_logging
from aptguide.llm.client import LLMClient
from aptguide.vector.client import MilvusClientWrapper
from aptguide.vector.kb_search import KBSearch
from aptguide.agent.graph import create_agent_graph
from aptguide.api import health, chat


# 全局实例
settings = Settings()
setup_logging(settings)

llm = LLMClient(settings)
milvus = MilvusClientWrapper(settings)
kb = KBSearch(milvus, settings)
agent_graph = create_agent_graph(llm, kb)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    milvus.connect()
    yield


app = FastAPI(
    title="AptGuide",
    description="智能找房助手",
    version="0.1.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(health.router)
app.include_router(chat.router)

# 静态文件
app.mount("/", StaticFiles(directory="src/aptguide/ui", html=True), name="ui")
```

- [ ] **Step 6: 运行测试验证通过**

```bash
uv run pytest tests/contract/test_api.py -v
```

预期：PASS

- [ ] **Step 7: 提交**

```bash
git add src/aptguide/api/ src/aptguide/main.py tests/contract/test_api.py
git commit -m "feat: add API routes and main entry"
```

---

## Task 7: 前端界面

**Files:**
- Create: `src/aptguide/ui/index.html`
- Create: `src/aptguide/ui/style.css`
- Create: `src/aptguide/ui/app.js`

- [ ] **Step 1: 创建 HTML 页面**

```html
<!-- src/aptguide/ui/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AptGuide - 智能找房助手</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>AptGuide</h1>
            <p>智能找房助手</p>
        </header>

        <main class="chat-container">
            <div id="messages" class="messages">
                <div class="message assistant">
                    <div class="message-content">
                        你好！我是 AptGuide 智能找房助手。你可以问我关于租房规则的问题，比如押金、退租、预约等。
                    </div>
                </div>
            </div>
        </main>

        <footer class="input-container">
            <input
                type="text"
                id="messageInput"
                placeholder="输入你的问题..."
                autocomplete="off"
            >
            <button id="sendButton">发送</button>
        </footer>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 创建 CSS 样式**

```css
/* src/aptguide/ui/style.css */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background-color: #f5f5f5;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.container {
    width: 100%;
    max-width: 600px;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: #fff;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.header {
    padding: 20px;
    background-color: #007AFF;
    color: #fff;
    text-align: center;
}

.header h1 {
    font-size: 24px;
    margin-bottom: 4px;
}

.header p {
    font-size: 14px;
    opacity: 0.8;
}

.chat-container {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.messages {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.message {
    display: flex;
    flex-direction: column;
    max-width: 80%;
}

.message.user {
    align-self: flex-end;
}

.message.assistant {
    align-self: flex-start;
}

.message-content {
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.5;
}

.message.user .message-content {
    background-color: #007AFF;
    color: #fff;
    border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
    background-color: #f0f0f0;
    color: #333;
    border-bottom-left-radius: 4px;
}

.source {
    font-size: 12px;
    color: #666;
    margin-top: 8px;
    padding: 8px;
    background-color: #f8f8f8;
    border-radius: 8px;
}

.input-container {
    display: flex;
    padding: 16px;
    border-top: 1px solid #eee;
    background-color: #fff;
}

#messageInput {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid #ddd;
    border-radius: 24px;
    font-size: 14px;
    outline: none;
}

#messageInput:focus {
    border-color: #007AFF;
}

#sendButton {
    margin-left: 12px;
    padding: 12px 24px;
    background-color: #007AFF;
    color: #fff;
    border: none;
    border-radius: 24px;
    font-size: 14px;
    cursor: pointer;
}

#sendButton:hover {
    background-color: #0056CC;
}

#sendButton:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}
```

- [ ] **Step 3: 创建 JavaScript 交互**

```javascript
// src/aptguide/ui/app.js
const messagesContainer = document.getElementById("messages");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");

let sessionId = "demo-" + Date.now();

function addMessage(content, isUser = false, sources = []) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user" : "assistant"}`;

    let html = `<div class="message-content">${content}</div>`;

    if (sources.length > 0) {
        html += `<div class="source">来源：${sources.join(", ")}</div>`;
    }

    messageDiv.innerHTML = html;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

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
        addMessage(data.reply, false, data.sources);
    } catch (error) {
        addMessage("抱歉，发生了错误。请稍后重试。", false);
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "发送";
    }
}

// 事件监听
sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendMessage();
    }
});
```

- [ ] **Step 4: 提交**

```bash
git add src/aptguide/ui/
git commit -m "feat: add chat UI"
```

---

## Task 8: 知识库初始化脚本

**Files:**
- Create: `scripts/seed_kb.py`

- [ ] **Step 1: 创建知识库初始化脚本**

```python
# scripts/seed_kb.py
"""初始化知识库到 Milvus"""

import yaml
from pathlib import Path
from pymilvus import MilvusClient, DataType

from aptguide.core.config import Settings
from aptguide.vector.embedding import EmbeddingClient


COLLECTION_NAME = "apt_rental_kb"


def create_collection(client: MilvusClient) -> None:
    """创建 Collection"""
    if client.has_collection(COLLECTION_NAME):
        client.drop_collection(COLLECTION_NAME)

    schema = client.create_schema(
        auto_id=False,
        enable_dynamic_field=True,
    )

    schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=32)
    schema.add_field("content", DataType.VARCHAR, max_length=4096)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=1024)
    schema.add_field("category", DataType.VARCHAR, max_length=32)
    schema.add_field("title", DataType.VARCHAR, max_length=128)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": 128},
    )

    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params,
    )

    print(f"Collection {COLLECTION_NAME} created")


def load_rules() -> list[dict]:
    """加载规则文件"""
    rules_dir = Path("src/aptguide/knowledge/rules")
    all_rules = []

    for yaml_file in rules_dir.glob("*.yaml"):
        if yaml_file.name.startswith("_"):
            continue

        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if "rules" in data:
                for rule in data["rules"]:
                    rule["category"] = yaml_file.stem
                    all_rules.append(rule)

    return all_rules


async def seed_kb() -> None:
    """初始化知识库"""
    settings = Settings()
    embedding = EmbeddingClient(settings)

    # 连接 Milvus
    milvus = MilvusClient(uri=settings.milvus_uri, token=settings.milvus_token)

    # 创建 Collection
    create_collection(milvus)

    # 加载规则
    rules = load_rules()
    print(f"Loaded {len(rules)} rules")

    # 生成向量并插入
    for rule in rules:
        vector = await embedding.embed(rule["content"])
        milvus.insert(
            collection_name=COLLECTION_NAME,
            data=[{
                "id": rule["doc_id"],
                "content": rule["content"],
                "vector": vector,
                "category": rule.get("category", ""),
                "title": rule.get("title", ""),
            }],
        )
        print(f"Inserted {rule['doc_id']}")

    print(f"Successfully seeded {len(rules)} rules")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_kb())
```

- [ ] **Step 2: 运行脚本测试**

```bash
# 确保 Milvus 已启动
docker-compose up -d milvus

# 运行初始化脚本
uv run python scripts/seed_kb.py
```

预期：成功创建 Collection 并插入规则

- [ ] **Step 3: 提交**

```bash
git add scripts/seed_kb.py
git commit -m "feat: add knowledge base seed script"
```

---

## Task 9: Docker Compose 配置

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: 创建 Docker Compose 配置**

```yaml
# docker-compose.yml
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

volumes:
  etcd-data:
  minio-data:
  milvus-data:
```

- [ ] **Step 2: 测试 Docker Compose**

```bash
docker-compose up -d
docker-compose ps
```

预期：所有服务正常运行

- [ ] **Step 3: 提交**

```bash
git add docker-compose.yml
git commit -m "feat: add Docker Compose for Milvus"
```

---

## Task 10: 端到端测试

**Files:**
- Create: `tests/e2e/test_e2e.py`

- [ ] **Step 1: 创建端到端测试**

```python
# tests/e2e/test_e2e.py
"""端到端测试"""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_full_conversation():
    """测试完整对话流程"""
    from aptguide.main import app

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

        # 第二轮：继续问答
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
```

- [ ] **Step 2: 运行端到端测试**

```bash
uv run pytest tests/e2e/test_e2e.py -v
```

预期：PASS

- [ ] **Step 3: 提交**

```bash
git add tests/e2e/
git commit -m "test: add end-to-end tests"
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

# 3. 启动应用
make dev

# 4. 浏览器访问
# 打开 http://localhost:8100
# 输入"押金怎么退？"验证功能
```

---

**计划状态**：已完成
**下一步**：用户审查后，选择执行方式
