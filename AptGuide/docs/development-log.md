# AptGuide 开发日志

> 记录 AptGuide 智能找房助手的开发过程、遇到的问题及解决方案。

---

## 项目概述

AptGuide 是一个面向租客的智能找房助手，基于 LangGraph Agent 架构，支持自然语言找房、预约看房、租约查询、知识库问答等功能。前端为移动端优先的聊天界面，后端为 Python FastAPI 服务。

**技术栈：** Python 3.12+ / FastAPI / LangGraph / pymilvus / DashScope (qwen-plus + text-embedding-v3) / Redis

---

## 第一阶段：Agent 核心流程搭建

### 1.1 LangGraph 工作流设计

**目标：** 构建 9 节点 Agent 工作流：intent → slot → ask → kb_search → room_search → rerank → confirm → tool → reply

**困难：** Lambda 包装的异步节点未正确等待协程，导致返回 coroutine 对象而非 dict。

**解决：** 将所有 lambda 包装改为正式的 `async def` 函数：

```python
# 错误写法 - lambda 返回 coroutine
workflow.add_node("intent", lambda state: intent_node(state, llm))

# 正确写法 - async def 正确等待
async def _intent(state):
    return await intent_node(state, llm)
workflow.add_node("intent", _intent)
```

### 1.2 意图识别与路由

**目标：** 支持 6 种意图：kb_qa、room_search、appointment_create、appointment_query、lease_query、other

**困难：** 路由函数缺少 `"tool": "tool"` 映射，导致 KeyError。

**解决：** 在 `add_conditional_edges` 中补全所有意图到节点的映射：

```python
workflow.add_conditional_edges(
    "intent",
    route_intent,
    {
        "kb_search": "kb_search",
        "slot": "slot",
        "tool": "tool",      # 补上这一行
        "reply": "reply",
    },
)
```

### 1.3 回复节点字段兼容

**困难：** `reply_node` 读取 `result["content"]`，但房源搜索结果使用 `description` 字段，导致 KeyError。

**解决：** 兼容两种字段名：

```python
results_text = "\n".join([
    f"- {r.get('title', '')}: {r.get('content') or r.get('description', '')}"
    for r in state["search_results"]
])
```

---

## 第二阶段：Milvus 向量知识库

### 2.1 知识库搜索返回空结果

**现象：** "押金怎么退" 等知识库问题返回空结果。

**根因：** Milvus 搜索返回的字段名是 `distance`，但 `kb_search.py` 代码中读取的是 `score`，导致所有结果的距离分数为 0，被阈值过滤掉。

**解决：**
1. `kb_search.py` 改为读取 `distance` 字段
2. `client.py` 中统一做字段归一化（flatten entity fields）

```python
# kb_search.py - 修复前
score = result.get("score", 0)

# 修复后
score = result.get("distance", 0)
```

### 2.2 RoomIndex 初始化参数缺失

**现象：** 启动时报 `RoomIndex.__init__() missing 1 required positional argument: 'embedding'`

**根因：** `main.py` 创建 RoomIndex 时只传了 milvus 和 settings，漏了 embedding。

**解决：** 补全 EmbeddingClient 导入和传参：

```python
from aptguide.vector.embedding import EmbeddingClient
embedding = EmbeddingClient(settings)
room_index = RoomIndex(milvus, settings, embedding)
```

### 2.3 Milvus 客户端未连接

**现象：** 搜索时报连接错误。

**解决：** 在 main.py 中显式调用 `milvus.connect()`。

---

## 第三阶段：会话管理与确认流程

### 3.1 SessionMemory 无 Redis 时崩溃

**现象：** 未配置 Redis 时，`self.redis.get()` 报 AttributeError。

**解决：** 添加内存回退机制：

```python
class SessionMemory:
    def __init__(self, redis_url=None):
        self.redis = redis.from_url(redis_url) if redis_url else None
        self._memory = {}  # 内存回退

    async def get(self, key):
        if self.redis:
            return self.redis.get(key)
        return self._memory.get(key)
```

### 3.2 "确认" 被分类为 "other" 意图

**现象：** 用户点击确认按钮后，系统返回 "建议联系门店"。

**根因：** 两个问题叠加：
1. `chat.py` 在每次请求开始时重置 `confirmation` 为 None，导致 `route_intent` 读不到待确认操作
2. `ask_node` 的 `get_missing_slots` 只检查找房槽位（max_rent、district），不检查预约槽位（room_id、appointment_time），导致预约槽位完整时返回空回复

**解决：**
1. `chat.py` 不再重置 `confirmation`，由 graph 内部消费后自然清除
2. `ask_node` 根据意图检查不同的缺失槽位
3. `check_slots` 允许用 `room_title` 代替 `room_id`（LLM 不一定能从自然语言中提取整数 room_id）

```python
# chat.py - 保留 confirmation 不重置
session["reply"] = ""
session["cards"] = []
session["actions"] = []
# confirmation 不在这里重置

# ask.py - 根据意图检查槽位
def get_missing_slots(slots: dict, intent: str = "") -> list[str]:
    if intent == "appointment_create":
        if not slots.get("room_id") and not slots.get("room_title"):
            missing.append("房间号或房间名称")
        if not slots.get("appointment_time"):
            missing.append("预约时间")

# graph.py - 允许 room_title 替代 room_id
has_room = slots.get("room_id") or slots.get("room_title")
if not has_room or not slots.get("appointment_time"):
    return "ask"
```

### 3.3 tool_node 处理 room_id 类型问题

**困难：** MockToolClient 期望 `room_id` 为 int，但 LLM 可能提取为字符串或 None。

**解决：** tool_node 中做类型兼容：

```python
room_id = params.get("room_id")
if not room_id:
    room_id = params.get("room_title", "unknown")
try:
    room_id = int(room_id)
except (ValueError, TypeError):
    room_id = 0
```

---

## 第四阶段：前端 UI 开发

### 4.1 初始设计

构建移动端优先的聊天界面，包含：
- 欢迎区域（4 个快捷操作按钮）
- 消息气泡（用户/助手）
- 底部输入栏
- 时间选择弹窗（预约看房用）

### 4.2 卡片系统

为不同类型的数据设计专用卡片：
- **房源卡片：** 标题、租金、区域、标签、描述、预约按钮
- **预约卡片：** 房间名、预约时间、状态标签、预约编号
- **租约卡片：** 房间名、租金、起止日期、合同编号、状态标签

前端通过 `cards[0].type` 字段分发到不同的渲染函数。

### 4.3 快捷按钮被滚动隐藏

**现象：** 对话变长后，底部的快捷操作按钮（找房、我的预约等）随内容滚动消失。

**根因：** 快捷按钮和消息区域在同一个滚动容器内。

**解决：** 将底部栏（`.bottom-bar`）独立为 `flex-shrink: 0`，始终固定在视口底部：

```css
.bottom-bar {
    flex-shrink: 0;
    background: #fff;
    border-top: 1px solid #eee;
}
```

---

## 第五阶段：跨请求状态污染（关键 Bug）

### 5.1 每次回答都弹出预约卡片

**现象：** 无论问什么问题，即使与找房无关，都会显示房源预约卡片。

**根因：** `chat.py` 的 session 状态在请求之间没有重置。上一轮 `rerank_node` 设置的 `cards` 和 `reply` 残留到下一轮，导致 `reply_node` 的透传条件被误触发：

```python
# reply_node 的透传条件
if has_reply and (has_cards or is_tool_intent or is_tool_result):
    return {"reply": state["reply"], "cards": state.get("cards", [])}
```

上一轮的 `has_reply=True` + `has_cards=True` → 直接透传旧卡片。

**解决：** 在图执行前重置所有临时字段：

```python
session["message"] = request.message
session["reply"] = ""
session["cards"] = []
session["actions"] = []
session["sources"] = []
session["search_results"] = []
session["intent"] = None
# confirmation 保留，由 graph 内部消费
```

### 5.2 确认流程中 confirmation 被提前清除

**现象：** 修复 5.1 时如果也重置 `confirmation`，会导致确认流程断裂。

**根因：** `confirmation` 由 `confirm_node` 在上一轮设置，本轮 `route_intent` 需要读取它来判断是否走确认流程。如果在图执行前重置，就永远读不到了。

**解决：** `confirmation` 不在 chat.py 中重置，由 `tool_node` 和 `reply_node` 在消费后返回 `"confirmation": None` 自然清除。

---

## 第六阶段：取消流程

### 6.1 点击"取消"返回错误消息

**现象：** 用户点击取消后返回 "抱歉，我暂时无法回答这个问题"。

**根因：** 取消消息路由到 `reply_node`，但它没有处理取消的逻辑，直接走到 `search_results` 为空的分支返回通用错误。

**解决：** 在 `reply_node` 开头添加取消检测：

```python
msg = state.get("message", "").strip()
if state.get("confirmation") and msg in ("取消", "不", "不要", "算了"):
    return {
        "reply": "好的，已取消操作。有其他需要随时告诉我～",
        "cards": [],
        "actions": [],
        "confirmation": None,
    }
```

---

## 测试验证矩阵

| 测试场景 | 请求序列 | 预期结果 | 状态 |
|---------|---------|---------|------|
| 知识库问答 | "押金怎么退" | 返回规则说明 + 来源 | PASS |
| 房源搜索 | "天河区3000以内" | 返回 5 张房源卡片 | PASS |
| 创建预约 | "预约看房..." → "确认" | 返回确认摘要 → 预约创建成功 | PASS |
| 取消预约 | "预约看房..." → "取消" | 返回取消消息，confirmation 清除 | PASS |
| 查询预约 | "查看我的预约" | 返回预约卡片 | PASS |
| 查询租约 | "查看我的租约" | 返回租约卡片 | PASS |
| 跨请求无污染 | 搜房 → 知识库问题 | 第二轮无残留卡片 | PASS |
| 确认后无残留 | 确认 → 知识库问题 | confirmation 清除，无残留 | PASS |

---

## 架构决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 向量数据库 | Milvus v2.4 | 本地部署，支持过滤表达式 |
| Embedding | DashScope text-embedding-v3 (1024d) | 与 LLM 同一服务商，延迟低 |
| LLM | DashScope qwen-plus | OpenAI 兼容接口，中文效果好 |
| 前端方案 | 原生 HTML/CSS/JS + FastAPI StaticFiles | MVP 阶段零依赖，快速迭代 |
| 会话存储 | 内存 dict（Redis 可选） | MVP 阶段简化部署 |
| 工具客户端 | MockToolClient | 后端 Java 服务就绪前用 mock |

---

## 文件结构

```
src/aptguide/
├── agent/
│   ├── graph.py          # LangGraph 工作流定义、路由函数
│   ├── state.py          # AgentState 类型定义
│   ├── nodes/
│   │   ├── intent.py     # 意图识别
│   │   ├── slot.py       # 槽位抽取（意图感知）
│   │   ├── ask.py        # 追问生成（意图感知）
│   │   ├── kb_search.py  # 知识库检索
│   │   ├── room_search.py # 房源检索
│   │   ├── rerank.py     # 重排序 + 卡片生成
│   │   ├── confirm.py    # 确认摘要生成
│   │   ├── tool.py       # 工具调用（预约/租约）
│   │   └── reply.py      # 回复生成 + 取消处理 + 透传
│   └── prompts/          # 提示词模板
├── api/
│   └── chat.py           # /api/chat 接口、会话管理
├── vector/
│   ├── client.py         # Milvus 客户端封装
│   ├── room_index.py     # 房源索引检索
│   ├── kb_search.py      # 知识库检索
│   └── embedding.py      # Embedding 客户端
├── memory/
│   └── session.py        # 会话记忆（Redis/内存）
├── tools/
│   └── mock.py           # Mock 工具客户端
├── schemas/
│   ├── request.py        # 请求模型
│   └── response.py       # 响应模型
└── ui/
    ├── index.html         # 页面结构
    ├── style.css          # 样式（紫色渐变主题）
    └── app.js             # 交互逻辑、卡片渲染
```
