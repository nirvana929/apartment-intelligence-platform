# AptGuide 阶段 2：找房推荐实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现自然语言找房功能，用户输入找房需求可获得房源卡片推荐

**Architecture:** 基于阶段 1 的 LangGraph 工作流，新增槽位抽取、房源召回、推荐理由生成节点

**Tech Stack:** Python 3.12, FastAPI, LangGraph, pymilvus, OpenAI SDK, uv

---

## 文件结构变更

```text
src/aptguide/agent/nodes/
├── slot.py          # 槽位抽取
├── ask.py           # 追问生成
├── room_search.py   # 房源召回
└── rerank.py        # 推荐理由生成

src/aptguide/vector/
└── room_index.py    # 房源索引检索

scripts/
└── sync_room_vectors.py  # 房源向量同步

tests/unit/
├── test_slot.py
├── test_room_search.py
└── test_rerank.py
```

---

## Task 1: 槽位抽取节点

**Files:**
- Create: `src/aptguide/agent/nodes/slot.py`
- Create: `tests/unit/test_slot.py`

- [ ] **Step 1: 创建槽位抽取测试**

```python
# tests/unit/test_slot.py
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_slot_extract():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content='''```json
{
    "max_rent": 3000,
    "district": "天河区",
    "tags": ["安静", "适合考研"],
    "payment_type": null,
    "lease_term": null
}
```'''))]

    with patch("openai.AsyncOpenAI") as mock_client:
        mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

        from aptguide.agent.nodes.slot import slot_node
        from aptguide.core.config import Settings

        settings = Settings(llm_api_key="test", embedding_api_key="test")
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value=mock_response.choices[0].message.content)

        state = {
            "session_id": "test-001",
            "message": "想找安静、适合考研的房子，预算3000，天河区",
            "intent": "room_search",
            "slots": {},
            "search_results": [],
            "confirmation": None,
            "reply": "",
            "cards": [],
            "actions": [],
            "sources": [],
        }

        result = await slot_node(state, llm)
        assert result["slots"]["max_rent"] == 3000
        assert result["slots"]["district"] == "天河区"
        assert "安静" in result["slots"]["tags"]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_slot.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现槽位抽取节点**

```python
# src/aptguide/agent/nodes/slot.py
import json
import re

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient


SLOT_PROMPT = """从用户找房需求中抽取以下槽位：

槽位定义：
- max_rent: 最高预算（整数）
- district: 区域（字符串）
- tags: 偏好标签（字符串数组，如["安静", "适合考研"]）
- payment_type: 支付方式（"月付" | "季付" | "半年付" | "年付" | null）
- lease_term: 租期（"短期" | "长期" | null）

只返回 JSON，不要返回其他内容。

用户消息：{message}
当前槽位：{current_slots}"""


async def slot_node(state: AgentState, llm: LLMClient) -> dict:
    """槽位抽取节点"""
    prompt = SLOT_PROMPT.format(
        message=state["message"],
        current_slots=json.dumps(state["slots"], ensure_ascii=False),
    )

    response = await llm.generate(prompt)

    # 提取 JSON
    json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = response

    try:
        new_slots = json.loads(json_str)
    except json.JSONDecodeError:
        new_slots = {}

    # 合并槽位（保留已有值）
    slots = state["slots"].copy()
    for key, value in new_slots.items():
        if value is not None:
            slots[key] = value

    return {"slots": slots}
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_slot.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/agent/nodes/slot.py tests/unit/test_slot.py
git commit -m "feat: add slot extraction node"
```

---

## Task 2: 追问生成节点

**Files:**
- Create: `src/aptguide/agent/nodes/ask.py`
- Create: `tests/unit/test_ask.py`

- [ ] **Step 1: 创建追问生成测试**

```python
# tests/unit/test_ask.py
import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_ask_node():
    from aptguide.agent.nodes.ask import ask_node

    state = {
        "session_id": "test-001",
        "message": "想找安静的房子",
        "intent": "room_search",
        "slots": {"tags": ["安静"]},
        "search_results": [],
        "confirmation": None,
        "reply": "",
        "cards": [],
        "actions": [],
        "sources": [],
    }

    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="好的，我先按\"安静\"为你筛选。能告诉我预算范围和希望的区域吗？")

    result = await ask_node(state, llm)
    assert "预算" in result["reply"] or "区域" in result["reply"]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_ask.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现追问生成节点**

```python
# src/aptguide/agent/nodes/ask.py
from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient


ASK_PROMPT = """你是一个租房助手。用户的需求信息不完整，需要追问缺失的槽位。

当前槽位：{slots}
缺失槽位：{missing_slots}

请生成一个友好的追问，询问缺失的信息。"""


def get_missing_slots(slots: dict) -> list[str]:
    """获取缺失的槽位"""
    missing = []
    if not slots.get("max_rent"):
        missing.append("预算")
    if not slots.get("district"):
        missing.append("区域")
    return missing


async def ask_node(state: AgentState, llm: LLMClient) -> dict:
    """追问生成节点"""
    missing = get_missing_slots(state["slots"])

    if not missing:
        # 槽位充足，不需要追问
        return {"reply": ""}

    prompt = ASK_PROMPT.format(
        slots=state["slots"],
        missing_slots=", ".join(missing),
    )

    reply = await llm.generate(prompt)
    return {"reply": reply}
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_ask.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/agent/nodes/ask.py tests/unit/test_ask.py
git commit -m "feat: add ask node"
```

---

## Task 3: 房源索引检索

**Files:**
- Create: `src/aptguide/vector/room_index.py`
- Create: `tests/unit/test_room_index.py`

- [ ] **Step 1: 创建房源索引测试**

```python
# tests/unit/test_room_index.py
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_room_search():
    mock_results = [
        {
            "id": 3001,
            "distance": 0.85,
            "entity": {
                "title": "天河公寓 302",
                "rent": 2800,
                "district": "天河区",
                "tags": '["独卫", "朝南"]',
                "status": "available",
            },
        }
    ]

    milvus = MagicMock()
    milvus.search.return_value = mock_results

    from aptguide.vector.room_index import RoomIndex
    from aptguide.core.config import Settings

    settings = Settings(llm_api_key="test", embedding_api_key="test")
    embedding = AsyncMock()
    embedding.embed = AsyncMock(return_value=[0.1] * 1024)

    room_index = RoomIndex(milvus, settings, embedding)
    results = await room_index.search(
        query="安静适合考研",
        max_rent=3000,
        district="天河区",
    )

    assert len(results) == 1
    assert results[0]["room_id"] == 3001
    assert results[0]["rent"] == 2800
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_room_index.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现房源索引检索**

```python
# src/aptguide/vector/room_index.py
import json

from aptguide.core.config import Settings
from aptguide.vector.client import MilvusClientWrapper
from aptguide.vector.embedding import EmbeddingClient


class RoomIndex:
    """房源索引检索"""

    COLLECTION_NAME = "room_index"

    def __init__(
        self,
        milvus: MilvusClientWrapper,
        settings: Settings,
        embedding: EmbeddingClient,
    ):
        self.milvus = milvus
        self.embedding = embedding

    async def search(
        self,
        query: str,
        max_rent: int | None = None,
        district: str | None = None,
        top_k: int = 10,
    ) -> list[dict]:
        """检索房源"""
        query_vector = await self.embedding.embed(query)

        # 构建过滤条件
        filters = ['status == "available"']
        if max_rent:
            filters.append(f"rent <= {max_rent}")
        if district:
            filters.append(f'district == "{district}"')

        filter_expr = " and ".join(filters) if filters else ""

        results = self.milvus.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            top_k=top_k,
            output_fields=["title", "rent", "district", "tags", "description", "status"],
            filter_expr=filter_expr,
        )

        # 格式化结果
        rooms = []
        for result in results:
            entity = result.get("entity", {})
            tags = entity.get("tags", "[]")
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []

            rooms.append({
                "room_id": result["id"],
                "title": entity.get("title", ""),
                "rent": entity.get("rent", 0),
                "district": entity.get("district", ""),
                "tags": tags,
                "description": entity.get("description", ""),
                "score": result.get("distance", 0),
            })

        return rooms[:5]  # 最多返回 5 个
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_room_index.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/vector/room_index.py tests/unit/test_room_index.py
git commit -m "feat: add room index search"
```

---

## Task 4: 房源召回节点

**Files:**
- Create: `src/aptguide/agent/nodes/room_search.py`
- Create: `tests/unit/test_room_search_node.py`

- [ ] **Step 1: 创建房源召回节点测试**

```python
# tests/unit/test_room_search_node.py
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_room_search_node():
    from aptguide.agent.nodes.room_search import room_search_node

    state = {
        "session_id": "test-001",
        "message": "想找安静、适合考研的房子",
        "intent": "room_search",
        "slots": {"max_rent": 3000, "district": "天河区", "tags": ["安静", "适合考研"]},
        "search_results": [],
        "confirmation": None,
        "reply": "",
        "cards": [],
        "actions": [],
        "sources": [],
    }

    room_index = AsyncMock()
    room_index.search = AsyncMock(return_value=[
        {
            "room_id": 3001,
            "title": "天河公寓 302",
            "rent": 2800,
            "district": "天河区",
            "tags": ["独卫", "朝南"],
            "description": "周边安静，适合备考",
            "score": 0.85,
        }
    ])

    result = await room_search_node(state, room_index)
    assert len(result["search_results"]) == 1
    assert result["search_results"][0]["room_id"] == 3001
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_room_search_node.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现房源召回节点**

```python
# src/aptguide/agent/nodes/room_search.py
from aptguide.agent.state import AgentState
from aptguide.vector.room_index import RoomIndex


async def room_search_node(state: AgentState, room_index: RoomIndex) -> dict:
    """房源召回节点"""
    slots = state["slots"]

    # 构建查询
    query_parts = []
    if slots.get("tags"):
        query_parts.extend(slots["tags"])
    if slots.get("district"):
        query_parts.append(slots["district"])

    query = " ".join(query_parts) if query_parts else state["message"]

    # 检索房源
    rooms = await room_index.search(
        query=query,
        max_rent=slots.get("max_rent"),
        district=slots.get("district"),
    )

    return {"search_results": rooms}
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_room_search_node.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/agent/nodes/room_search.py tests/unit/test_room_search_node.py
git commit -m "feat: add room search node"
```

---

## Task 5: 推荐理由生成节点

**Files:**
- Create: `src/aptguide/agent/nodes/rerank.py`
- Create: `tests/unit/test_rerank.py`

- [ ] **Step 1: 创建推荐理由生成测试**

```python
# tests/unit/test_rerank.py
import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_rerank_node():
    from aptguide.agent.nodes.rerank import rerank_node

    state = {
        "session_id": "test-001",
        "message": "想找安静、适合考研的房子",
        "intent": "room_search",
        "slots": {"max_rent": 3000, "district": "天河区", "tags": ["安静", "适合考研"]},
        "search_results": [
            {
                "room_id": 3001,
                "title": "天河公寓 302",
                "rent": 2800,
                "district": "天河区",
                "tags": ["独卫", "朝南"],
                "description": "周边安静，适合备考",
            }
        ],
        "confirmation": None,
        "reply": "",
        "cards": [],
        "actions": [],
        "sources": [],
    }

    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="为你找到 1 个合适的房源：天河公寓 302，月租 2800，独卫朝南，周边安静适合备考。")

    result = await rerank_node(state, llm)
    assert len(result["cards"]) == 1
    assert result["cards"][0]["room_id"] == 3001
    assert "天河公寓" in result["reply"]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/unit/test_rerank.py -v
```

预期：FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现推荐理由生成节点**

```python
# src/aptguide/agent/nodes/rerank.py
from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.schemas.response import Card, Action


RERANK_PROMPT = """你是一个租房助手。根据用户需求和检索到的房源，生成推荐理由。

用户需求：{message}
用户槽位：{slots}

房源列表：
{rooms}

请生成：
1. 自然语言推荐理由（简洁明了）
2. 突出房源与用户需求的匹配点

只返回推荐理由，不要返回其他内容。"""


async def rerank_node(state: AgentState, llm: LLMClient) -> dict:
    """推荐理由生成节点"""
    if not state["search_results"]:
        return {
            "reply": "抱歉，暂未找到符合条件的房源。你可以尝试调整预算或区域。",
            "cards": [],
            "actions": [],
        }

    # 格式化房源信息
    rooms_text = "\n".join([
        f"- {r['title']}：月租 {r['rent']}，{', '.join(r['tags'])}，{r['description']}"
        for r in state["search_results"]
    ])

    prompt = RERANK_PROMPT.format(
        message=state["message"],
        slots=state["slots"],
        rooms=rooms_text,
    )

    reply = await llm.generate(prompt)

    # 构建卡片
    cards = []
    actions = []
    for room in state["search_results"]:
        cards.append(Card(
            type="room",
            room_id=room["room_id"],
            title=room["title"],
            rent=room["rent"],
            district=room["district"],
            tags=room["tags"],
            description=room["description"],
        ))
        actions.append(Action(type="view_detail", room_id=room["room_id"]))
        actions.append(Action(type="create_appointment", room_id=room["room_id"]))

    return {
        "reply": reply,
        "cards": [card.model_dump() for card in cards],
        "actions": [action.model_dump() for action in actions],
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/unit/test_rerank.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/aptguide/agent/nodes/rerank.py tests/unit/test_rerank.py
git commit -m "feat: add rerank node"
```

---

## Task 6: 更新 LangGraph 工作流

**Files:**
- Modify: `src/aptguide/agent/graph.py`

- [ ] **Step 1: 更新工作流添加新节点**

```python
# src/aptguide/agent/graph.py
from langgraph.graph import StateGraph, END

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.vector.kb_search import KBSearch
from aptguide.vector.room_index import RoomIndex


def create_agent_graph(
    llm: LLMClient,
    kb: KBSearch,
    room_index: RoomIndex,
):
    """创建 Agent 工作流"""
    from aptguide.agent.nodes.intent import intent_node
    from aptguide.agent.nodes.slot import slot_node
    from aptguide.agent.nodes.ask import ask_node
    from aptguide.agent.nodes.kb_search import kb_search_node
    from aptguide.agent.nodes.room_search import room_search_node
    from aptguide.agent.nodes.rerank import rerank_node
    from aptguide.agent.nodes.reply import reply_node

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent", lambda state: intent_node(state, llm))
    workflow.add_node("slot", lambda state: slot_node(state, llm))
    workflow.add_node("ask", lambda state: ask_node(state, llm))
    workflow.add_node("kb_search", lambda state: kb_search_node(state, kb))
    workflow.add_node("room_search", lambda state: room_search_node(state, room_index))
    workflow.add_node("rerank", lambda state: rerank_node(state, llm))
    workflow.add_node("reply", lambda state: reply_node(state, llm))

    # 定义边
    workflow.set_entry_point("intent")

    def route_intent(state: AgentState) -> str:
        if state["intent"] == "kb_qa":
            return "kb_search"
        elif state["intent"] == "room_search":
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
        if not slots.get("max_rent") or not slots.get("district"):
            return "ask"
        return "room_search"

    workflow.add_conditional_edges(
        "slot",
        check_slots,
        {
            "ask": "ask",
            "room_search": "room_search",
        },
    )

    workflow.add_edge("room_search", "rerank")
    workflow.add_edge("rerank", "reply")
    workflow.add_edge("kb_search", "reply")
    workflow.add_edge("ask", END)
    workflow.add_edge("reply", END)

    return workflow.compile()
```

- [ ] **Step 2: 更新 main.py**

```python
# src/aptguide/main.py (部分更新)
from aptguide.vector.room_index import RoomIndex

# 在全局实例部分添加
room_index = RoomIndex(milvus, settings, EmbeddingClient(settings))

# 更新 agent_graph 创建
agent_graph = create_agent_graph(llm, kb, room_index)
```

- [ ] **Step 3: 运行测试验证**

```bash
uv run pytest tests/unit/test_agent.py -v
```

预期：PASS

- [ ] **Step 4: 提交**

```bash
git add src/aptguide/agent/graph.py src/aptguide/main.py
git commit -m "feat: update agent graph with room search nodes"
```

---

## Task 7: 房源同步脚本

**Files:**
- Create: `scripts/sync_room_vectors.py`

- [ ] **Step 1: 创建房源同步脚本**

```python
# scripts/sync_room_vectors.py
"""同步房源向量到 Milvus"""

import json
import yaml
from pathlib import Path
from pymilvus import MilvusClient, DataType

from aptguide.core.config import Settings
from aptguide.vector.embedding import EmbeddingClient


COLLECTION_NAME = "room_index"


def create_collection(client: MilvusClient) -> None:
    """创建 Collection"""
    if client.has_collection(COLLECTION_NAME):
        client.drop_collection(COLLECTION_NAME)

    schema = client.create_schema(
        auto_id=False,
        enable_dynamic_field=True,
    )

    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("title", DataType.VARCHAR, max_length=128)
    schema.add_field("description", DataType.VARCHAR, max_length=4096)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=1024)
    schema.add_field("rent", DataType.INT64)
    schema.add_field("district", DataType.VARCHAR, max_length=32)
    schema.add_field("tags", DataType.VARCHAR, max_length=512)
    schema.add_field("payment_type", DataType.VARCHAR, max_length=16)
    schema.add_field("status", DataType.VARCHAR, max_length=16)

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


def load_mock_rooms() -> list[dict]:
    """加载 Mock 房源数据"""
    return [
        {
            "id": 3001,
            "title": "天河公寓 302",
            "description": "周边安静，适合备考，靠近图书馆",
            "rent": 2800,
            "district": "天河区",
            "tags": '["独卫", "朝南", "安静"]',
            "payment_type": "月付",
            "status": "available",
        },
        {
            "id": 3002,
            "title": "科韵公寓 506",
            "description": "靠近地铁站，交通便利",
            "rent": 2950,
            "district": "天河区",
            "tags": '["独卫", "近地铁"]',
            "payment_type": "月付",
            "status": "available",
        },
        {
            "id": 3003,
            "title": "棠德公寓 412",
            "description": "户型紧凑，性价比高",
            "rent": 2700,
            "district": "天河区",
            "tags": '["独卫", "性价比"]',
            "payment_type": "季付",
            "status": "available",
        },
    ]


async def sync_room_vectors() -> None:
    """同步房源向量"""
    settings = Settings()
    embedding = EmbeddingClient(settings)

    # 连接 Milvus
    milvus = MilvusClient(uri=settings.milvus_uri, token=settings.milvus_token)

    # 创建 Collection
    create_collection(milvus)

    # 加载房源
    rooms = load_mock_rooms()
    print(f"Loaded {len(rooms)} rooms")

    # 生成向量并插入
    for room in rooms:
        text = f"{room['title']} {room['description']} {room['tags']}"
        vector = await embedding.embed(text)

        milvus.insert(
            collection_name=COLLECTION_NAME,
            data=[{
                "id": room["id"],
                "title": room["title"],
                "description": room["description"],
                "vector": vector,
                "rent": room["rent"],
                "district": room["district"],
                "tags": room["tags"],
                "payment_type": room["payment_type"],
                "status": room["status"],
            }],
        )
        print(f"Inserted room {room['id']}: {room['title']}")

    print(f"Successfully synced {len(rooms)} rooms")


if __name__ == "__main__":
    import asyncio
    asyncio.run(sync_room_vectors())
```

- [ ] **Step 2: 运行脚本测试**

```bash
uv run python scripts/sync_room_vectors.py
```

预期：成功创建 Collection 并插入房源

- [ ] **Step 3: 提交**

```bash
git add scripts/sync_room_vectors.py
git commit -m "feat: add room vectors sync script"
```

---

## Task 8: 更新前端界面

**Files:**
- Modify: `src/aptguide/ui/index.html`
- Modify: `src/aptguide/ui/style.css`
- Modify: `src/aptguide/ui/app.js`

- [ ] **Step 1: 更新 HTML 添加房源卡片**

```html
<!-- src/aptguide/ui/index.html (部分更新) -->
<!-- 在 message-content 后添加房源卡片容器 -->
<div class="message assistant">
    <div class="message-content"></div>
    <div class="cards-container"></div>
    <div class="source"></div>
</div>
```

- [ ] **Step 2: 更新 CSS 添加卡片样式**

```css
/* src/aptguide/ui/style.css (添加) */
.cards-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 12px;
}

.room-card {
    border: 1px solid #eee;
    border-radius: 12px;
    padding: 16px;
    background-color: #fff;
}

.room-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.room-card-title {
    font-size: 16px;
    font-weight: 600;
    color: #333;
}

.room-card-rent {
    font-size: 18px;
    font-weight: 700;
    color: #007AFF;
}

.room-card-district {
    font-size: 14px;
    color: #666;
    margin-bottom: 8px;
}

.room-card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 8px;
}

.room-card-tag {
    padding: 4px 8px;
    background-color: #f0f0f0;
    border-radius: 4px;
    font-size: 12px;
    color: #666;
}

.room-card-description {
    font-size: 14px;
    color: #333;
    margin-bottom: 12px;
}

.room-card-actions {
    display: flex;
    gap: 8px;
}

.room-card-actions button {
    flex: 1;
    padding: 8px 16px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
}

.room-card-actions .btn-primary {
    background-color: #007AFF;
    color: #fff;
}

.room-card-actions .btn-secondary {
    background-color: #f0f0f0;
    color: #333;
}
```

- [ ] **Step 3: 更新 JavaScript 处理卡片**

```javascript
// src/aptguide/ui/app.js (部分更新)
function addMessage(content, isUser = false, sources = [], cards = []) {
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

    if (sources.length > 0) {
        html += `<div class="source">来源：${sources.join(", ")}</div>`;
    }

    messageDiv.innerHTML = html;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 添加操作函数
function createAppointment(roomId) {
    messageInput.value = `预约房间 ${roomId} 明天下午看房`;
    sendMessage();
}

function viewDetail(roomId) {
    messageInput.value = `查看房间 ${roomId} 的详情`;
    sendMessage();
}
```

- [ ] **Step 4: 提交**

```bash
git add src/aptguide/ui/
git commit -m "feat: add room card UI components"
```

---

## Task 9: 端到端测试

**Files:**
- Modify: `tests/e2e/test_e2e.py`

- [ ] **Step 1: 添加找房端到端测试**

```python
# tests/e2e/test_e2e.py (添加)
@pytest.mark.asyncio
async def test_room_search_conversation():
    """测试找房对话流程"""
    from aptguide.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # 第一轮：表达找房需求
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "e2e-test-002",
                "message": "想找安静、适合考研的房子",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "room_search"
        assert "预算" in data["reply"] or "区域" in data["reply"]

        # 第二轮：补充预算和区域
        response = await client.post(
            "/api/chat",
            json={
                "session_id": "e2e-test-002",
                "message": "预算3000，天河区",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["cards"]) > 0
        assert data["cards"][0]["type"] == "room"
```

- [ ] **Step 2: 运行端到端测试**

```bash
uv run pytest tests/e2e/test_e2e.py -v
```

预期：PASS

- [ ] **Step 3: 提交**

```bash
git add tests/e2e/test_e2e.py
git commit -m "test: add room search e2e tests"
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

# 3. 同步房源向量
uv run python scripts/sync_room_vectors.py

# 4. 启动应用
make dev

# 5. 浏览器测试
# 打开 http://localhost:8100
# 输入"想找安静、适合考研的房子"
# 补充"预算3000，天河区"
# 验证房源卡片展示
```

---

**计划状态**：已完成
**下一步**：用户审查后，选择执行方式
