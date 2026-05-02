# AptGuide MVP 设计规范

> **创建时间**：2026-05-02
> **版本**：v1.0
> **状态**：待审批

---

## 1. 项目概述

### 1.1 项目定位

AptGuide 是面向租客用户的智能找房助手，采用渐进式交付策略，分三个阶段实现完整 MVP。

### 1.2 核心目标

- **阶段 1**：知识问答（3 天）- 租房规则 FAQ 检索
- **阶段 2**：找房推荐（4 天）- 自然语言找房 + 房源卡片
- **阶段 3**：预约流程（3 天）- 看房预约 + 确认机制

### 1.3 技术选型

| 组件 | 技术方案 | 说明 |
|------|----------|------|
| 前端 | 纯 HTML/CSS/JS | 集成到 FastAPI 静态文件 |
| 后端 | FastAPI + LangGraph | Python 3.12 + uv |
| 向量库 | Milvus（Docker 本地） | 知识库 + 房源索引 |
| LLM | OpenAI 兼容（Qwen/DashScope） | 通过 API 调用 |
| 会话 | 内存存储（阶段 1）→ Redis（阶段 3） | 渐进式升级 |

---

## 2. 系统架构

### 2.1 整体架构

```text
┌─────────────────────────────────────────────┐
│ 浏览器（纯 HTML/CSS/JS）                     │
│  - 聊天界面                                  │
│  - 消息列表                                  │
│  - 房源卡片（阶段 2）                        │
│  - 预约确认（阶段 3）                        │
└──────────────────┬──────────────────────────┘
                   │ HTTP /api/chat
                   ▼
┌─────────────────────────────────────────────┐
│ FastAPI + LangGraph                         │
│  ├─ api/chat.py        路由                 │
│  ├─ agent/graph.py     工作流               │
│  ├─ agent/nodes/       节点实现             │
│  ├─ vector/            Milvus 客户端        │
│  ├─ tools/             Mock 工具（阶段 3）  │
│  └─ core/              配置、日志           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Milvus（Docker 本地）                        │
│  - apt_rental_kb       知识库 Collection    │
│  - room_index          房源索引（阶段 2）   │
└─────────────────────────────────────────────┘
```

### 2.2 目录结构

```text
AptGuide/
├── src/aptguide/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py          # POST /api/chat
│   │   └── health.py        # GET /health
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py         # LangGraph 工作流
│   │   ├── state.py         # 状态定义
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── intent.py    # 意图识别
│   │   │   ├── slot.py      # 槽位抽取
│   │   │   ├── ask.py       # 追问生成
│   │   │   ├── kb_search.py # 知识检索
│   │   │   ├── room_search.py # 房源召回
│   │   │   ├── confirm.py   # 预约确认
│   │   │   ├── tool.py      # 工具调用
│   │   │   └── reply.py     # 回复生成
│   │   └── prompts/
│   │       ├── intent_classify.md
│   │       ├── slot_extract.md
│   │       ├── recommend_reason.md
│   │       └── answer_generate.md
│   ├── vector/
│   │   ├── __init__.py
│   │   ├── client.py        # Milvus 客户端
│   │   ├── embedding.py     # Embedding 封装
│   │   ├── kb_search.py     # 知识库检索
│   │   └── room_index.py    # 房源索引（阶段 2）
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── mock.py          # Mock 工具实现
│   │   └── schemas.py       # 工具入参出参
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理
│   │   ├── logging.py       # JSON 日志
│   │   └── errors.py        # 错误处理
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py        # LLM 客户端
│   │   └── schemas.py       # 结构化输出
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── request.py       # 请求模型
│   │   └── response.py      # 响应模型
│   └── ui/
│       ├── index.html       # 主页面
│       ├── style.css        # 样式
│       └── app.js           # 交互逻辑
├── scripts/
│   ├── seed_kb.py           # 知识库初始化
│   └── sync_room_vectors.py # 房源同步（阶段 2）
├── tests/
├── docs/
└── AptGuide文档/
```

---

## 3. 阶段 1：知识问答（3 天）

### 3.1 功能范围

- 用户输入自然语言问题
- 系统从 Milvus 知识库检索相关规则
- LLM 生成回答，附来源引用
- 支持多轮对话

### 3.2 前端界面

```text
┌─────────────────────────────────────┐
│  AptGuide - 智能找房助手            │
├─────────────────────────────────────┤
│  [消息列表]                         │
│  用户：押金怎么退？                 │
│  助手：根据租房规则，提前退租分两种 │
│        情况：                       │
│        · 距到期 ≤ 30 天：押金全额  │
│          退还                       │
│        · 距到期 > 30 天：扣除一个月 │
│          违约金，剩余押金退还       │
│        具体以你签订的合同为准。     │
│        — 来源：KB-RULE-008          │
├─────────────────────────────────────┤
│  [输入框]                    [发送] │
└─────────────────────────────────────┘
```

### 3.3 LangGraph 工作流

```text
用户消息
    ↓
意图识别（intent_node）
    ├─ kb_qa → 知识检索
    └─ 其他 → 回复"暂不支持"
    ↓
知识检索（kb_search_node）
    ↓
回复生成（reply_node）
    ↓
返回响应
```

### 3.4 Milvus 配置

**Collection：apt_rental_kb**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR | 主键，如 KB-RULE-008 |
| content | VARCHAR | 规则内容 |
| vector | FLOAT_VECTOR | 向量（1024 维） |
| category | VARCHAR | 分类（appointment/lease/payment/life/room_search/account/policy） |
| title | VARCHAR | 标题 |

**检索参数**：
- top-k：3
- 相似度阈值：0.7
- 检索方式：余弦相似度

### 3.5 API 契约

**请求**：
```http
POST /api/chat
Content-Type: application/json

{
  "session_id": "demo-001",
  "message": "押金怎么退？"
}
```

**响应**：
```json
{
  "session_id": "demo-001",
  "request_id": "req-uuid",
  "intent": "kb_qa",
  "reply": "根据租房规则，提前退租分两种情况...",
  "sources": ["KB-RULE-008"],
  "cards": [],
  "actions": [],
  "pending_confirmation": null
}
```

### 3.6 交付标准

- [ ] 浏览器可打开聊天界面
- [ ] 输入问题可获得回答
- [ ] 回答附来源引用
- [ ] 支持多轮对话
- [ ] 相似度低于阈值时回退

---

## 4. 阶段 2：找房推荐（4 天）

### 4.1 功能范围

- 解析用户找房需求（预算、区域、偏好）
- Milvus 语义召回候选房源
- 生成推荐理由
- 展示房源卡片

### 4.2 前端界面

```text
┌─────────────────────────────────────┐
│  AptGuide - 智能找房助手            │
├─────────────────────────────────────┤
│  [消息列表]                         │
│  用户：想找安静、适合考研的房子     │
│  助手：好的，我先按"安静、适合备考"│
│        为你筛选。能告诉我预算范围和 │
│        希望的区域吗？               │
│  用户：3000 以内，天河区            │
│  助手：为你找到 3 个合适的房源：    │
│  ┌─────────────────────────────┐   │
│  │ 天河公寓 302                │   │
│  │ 月租 2800 · 独卫 · 朝南    │   │
│  │ 周边安静，适合备考          │   │
│  │ [查看详情] [预约看房]       │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 科韵公寓 506                │   │
│  │ 月租 2950 · 靠近图书馆      │   │
│  │ 月付，适合考研              │   │
│  │ [查看详情] [预约看房]       │   │
│  └─────────────────────────────┘   │
├─────────────────────────────────────┤
│  [输入框]                    [发送] │
└─────────────────────────────────────┘
```

### 4.3 LangGraph 工作流

```text
用户消息
    ↓
意图识别（intent_node）
    ├─ room_search → 槽位抽取
    ├─ kb_qa → 知识检索
    └─ 其他 → 回复"暂不支持"
    ↓
槽位抽取（slot_node）
    ├─ max_rent: 3000
    ├─ district: 天河区
    ├─ tags: ["安静", "适合考研"]
    └─ payment_type: null
    ↓
槽位充足？（预算 + 区域）
    ├─ 否 → 追问（ask_node）
    └─ 是 → 语义召回（room_search_node）
              ↓
         生成推荐理由（rerank_node）
              ↓
         返回响应（reply_node）
```

### 4.4 Milvus 配置

**Collection：room_index**

| 字段 | 类型 | 说明 |
|------|------|------|
| room_id | INT64 | 房间 ID |
| title | VARCHAR | 标题，如"天河公寓 302" |
| description | VARCHAR | 描述 |
| vector | FLOAT_VECTOR | 向量（1024 维） |
| rent | INT64 | 月租 |
| district | VARCHAR | 区域 |
| tags | VARCHAR | 标签，JSON 数组 |
| payment_type | VARCHAR | 支付方式 |
| status | VARCHAR | 状态（available/rented） |

**检索参数**：
- top-k：10
- 过滤条件：`status == "available"`
- 后处理：按预算和区域过滤

### 4.5 房源卡片结构

```json
{
  "type": "room",
  "room_id": 3001,
  "title": "天河公寓 302",
  "rent": 2800,
  "district": "天河区",
  "tags": ["独卫", "朝南", "月付"],
  "description": "周边安静，适合备考",
  "thumbnail_url": null,
  "payment_type": "月付",
  "status": "available"
}
```

### 4.6 槽位定义

| 槽位 | 类型 | 必填 | 说明 |
|------|------|------|------|
| max_rent | int | 是 | 最高预算 |
| district | string | 是 | 区域 |
| tags | list[string] | 否 | 偏好标签 |
| payment_type | string | 否 | 支付方式 |
| lease_term | string | 否 | 租期 |

### 4.7 交付标准

- [ ] 输入找房需求可获得房源推荐
- [ ] 房源卡片展示租金、区域、标签
- [ ] 推荐理由基于实际数据
- [ ] 支持多轮追问
- [ ] 信息不足时主动追问

---

## 5. 阶段 3：预约流程（3 天）

### 5.1 功能范围

- 抽取预约槽位（房间、时间）
- 生成操作摘要，等待用户确认
- 调用 Mock 工具创建预约
- 返回预约结果

### 5.2 前端界面

```text
┌─────────────────────────────────────┐
│  AptGuide - 智能找房助手            │
├─────────────────────────────────────┤
│  [消息列表]                         │
│  用户：预约第一个房源明天下午看房   │
│  助手：明天下午有 14/15/16 三个时段 │
│        可选，你希望几点？           │
│  用户：3 点                         │
│  助手：准备为你创建预约：           │
│        ┌─────────────────────┐     │
│        │ 房源：天河公寓 302  │     │
│        │ 时间：2026-05-03    │     │
│        │       15:00         │     │
│        │ [确认预约] [取消]   │     │
│        └─────────────────────┘     │
│  用户：确认                         │
│  助手：预约成功！                   │
│        预约号：A20260503302         │
│        届时门店会有专人接待。       │
├─────────────────────────────────────┤
│  [输入框]                    [发送] │
└─────────────────────────────────────┘
```

### 5.3 LangGraph 工作流

```text
用户消息
    ↓
意图识别（intent_node）
    ├─ appointment_create → 槽位抽取
    ├─ room_search → 槽位抽取
    ├─ kb_qa → 知识检索
    └─ 其他 → 回复"暂不支持"
    ↓
槽位抽取（slot_node）
    ├─ room_id: 3001（可指代上一轮房源）
    ├─ appointment_time: "明天下午"
    └─ remark: null
    ↓
槽位充足？
    ├─ 否 → 追问（ask_node）
    └─ 是 → 确认摘要（confirm_node）
              ↓
         等待用户确认
              ↓
         调用工具（tool_node）
              ↓
         返回结果（reply_node）
```

### 5.4 预约槽位定义

| 槽位 | 类型 | 必填 | 说明 |
|------|------|------|------|
| room_id | int | 是 | 房间 ID（可指代上一轮） |
| appointment_time | datetime | 是 | 预约时间 |
| remark | string | 否 | 备注 |

### 5.5 Mock 工具数据

**预约创建**：
```python
{
  "appointment_id": "A20260503302",
  "room_id": 3001,
  "room_title": "天河公寓 302",
  "appointment_time": "2026-05-03 15:00",
  "status": "confirmed",
  "created_at": "2026-05-02 10:30:00"
}
```

**预约查询**：
```python
{
  "appointments": [
    {
      "appointment_id": "A20260503302",
      "room_title": "天河公寓 302",
      "appointment_time": "2026-05-03 15:00",
      "status": "confirmed"
    }
  ]
}
```

### 5.6 确认机制

**状态流转**：
```text
pending_confirmation
    ├─ 用户确认 → confirmed → 调用工具
    └─ 用户取消 → cancelled → 返回取消提示
```

**会话存储**：
```python
{
  "session_id": "demo-001",
  "pending_confirmation": {
    "type": "appointment_create",
    "params": {
      "room_id": 3001,
      "appointment_time": "2026-05-03 15:00"
    },
    "summary": "天河公寓 302，2026-05-03 15:00"
  }
}
```

### 5.7 交付标准

- [ ] 输入预约需求可获得确认摘要
- [ ] 点击确认后返回预约结果
- [ ] 支持取消操作
- [ ] 写操作前 100% 经过确认
- [ ] 预约结果与 Mock 数据一致

---

## 6. 数据模型

### 6.1 请求模型

```python
class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: dict | None = None
```

### 6.2 响应模型

```python
class ChatResponse(BaseModel):
    session_id: str
    request_id: str
    intent: str
    reply: str
    cards: list[Card]
    actions: list[Action]
    pending_confirmation: PendingConfirmation | None
    sources: list[str]

class Card(BaseModel):
    type: str  # "room" | "faq"
    room_id: int | None = None
    title: str
    rent: int | None = None
    district: str | None = None
    tags: list[str] = []
    description: str | None = None
    thumbnail_url: str | None = None

class Action(BaseModel):
    type: str  # "view_detail" | "create_appointment"
    room_id: int | None = None

class PendingConfirmation(BaseModel):
    type: str  # "appointment_create"
    params: dict
    summary: str
```

### 6.3 状态模型

```python
class AgentState(TypedDict):
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

---

## 7. 配置管理

### 7.1 环境变量

```env
# LLM
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# Embedding
EMBEDDING_API_KEY=your_api_key
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v3

# Milvus
MILVUS_URI=http://localhost:19530
MILVUS_TOKEN=

# Redis（阶段 3）
REDIS_URL=redis://localhost:6379/1

# 应用
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=INFO
```

### 7.2 配置类

```python
class Settings(BaseSettings):
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

    # Redis
    redis_url: str = "redis://localhost:6379/1"

    # 应用
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "INFO"
```

---

## 8. 错误处理

### 8.1 错误分类

| 来源 | 错误码 | 处理方式 |
|------|--------|----------|
| 用户输入 | VALIDATION_ERROR | 返回 400 + 友好提示 |
| LLM 异常 | LLM_TIMEOUT | 重试一次或回退到模板回答 |
| Milvus | VECTOR_UNAVAILABLE | 跳过检索，返回默认回答 |
| 内部 | INTERNAL_ERROR | 返回 500 + 记录堆栈 |

### 8.2 回退策略

**知识检索失败**：
```python
{
  "reply": "抱歉，我暂时无法回答这个问题。建议联系门店咨询。",
  "sources": [],
  "intent": "kb_qa_fallback"
}
```

**房源召回为空**：
```python
{
  "reply": "抱歉，暂未找到符合条件的房源。你可以尝试调整预算或区域。",
  "cards": [],
  "intent": "room_search_empty"
}
```

---

## 9. 测试策略

### 9.1 单元测试

- 意图识别准确率
- 槽位抽取准确率
- 知识检索召回率
- 回复生成质量

### 9.2 集成测试

- API 端到端测试
- Milvus 连接测试
- LLM 调用测试

### 9.3 评测数据集

```yaml
# evals/datasets/kb_qa_cases.yaml
- input: "押金怎么退？"
  expected_intent: "kb_qa"
  expected_sources: ["KB-RULE-008"]

- input: "可以提前退租吗？"
  expected_intent: "kb_qa"
  expected_sources: ["KB-RULE-008"]
```

---

## 10. 部署方案

### 10.1 本地开发

```bash
# 1. 启动 Milvus
docker-compose up -d milvus

# 2. 初始化知识库
uv run python scripts/seed_kb.py

# 3. 启动应用
make dev
```

### 10.2 Docker Compose

```yaml
version: '3.8'
services:
  milvus:
    image: milvusdb/milvus:v2.4-latest
    ports:
      - "19530:19530"
    volumes:
      - milvus-data:/var/lib/milvus

  etcd:
    image: quay.io/coreos/etcd:v3.5.0
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - minio-data:/minio_data

volumes:
  milvus-data:
  minio-data:
```

---

## 11. 里程碑

| 阶段 | 交付物 | 验收标准 |
|------|--------|----------|
| 阶段 1 | 知识问答 | 浏览器可问答，附来源 |
| 阶段 2 | 找房推荐 | 输入需求可得房源卡片 |
| 阶段 3 | 预约流程 | 预约需确认，返回结果 |

---

## 12. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Milvus 部署失败 | 无法检索 | 提供 Mock 数据降级 |
| LLM 调用超时 | 响应慢 | 重试 + 超时设置 |
| 知识库数据不足 | 回答质量差 | 持续补充知识库 |
| 前端兼容性 | 体验差 | 响应式设计 |

---

## 13. 后续路线

- 个性化记忆（长期偏好沉淀）
- 房源对比助手
- 续约/退租流程引导
- 报修助手
- 多模态（图片识别、语音输入）

---

**文档状态**：待审批
**下一步**：用户审查后，调用 writing-plans skill 创建实现计划
