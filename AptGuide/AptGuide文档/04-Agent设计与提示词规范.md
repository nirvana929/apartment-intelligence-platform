# 04 · Agent 设计与提示词规范

## 1. LangGraph 工作流

```text
                 ┌─────────────┐
                 │  entry      │
                 └──────┬──────┘
                        ▼
                 ┌─────────────┐
                 │ intent_node │  识别意图
                 └──────┬──────┘
                        ▼
                 ┌─────────────┐
                 │ slot_node   │  抽取 / 合并槽位
                 └──────┬──────┘
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
  ┌──────────┐  ┌────────────┐  ┌────────────┐
  │ ask_node │  │confirm_node│  │ tool_node  │
  │ 槽位不足 │  │ 写操作前确认│  │ 调用工具   │
  └────┬─────┘  └─────┬──────┘  └─────┬──────┘
       │              │                │
       │              ▼                ▼
       │       ┌────────────┐   ┌────────────┐
       │       │ reply_node │ ← │rerank_node │
       │       └─────┬──────┘   └────────────┘
       └─────────────┴──────────────────┐
                                        ▼
                                 ┌────────────┐
                                 │   finish   │
                                 └────────────┘
```

## 2. 状态结构

```python
class AgentState(TypedDict):
    # 入参
    session_id: str
    user_id: str
    request_id: str
    message: str
    history: list[Message]
    prompt_version: str

    # 中间产物
    intent: Literal["room_search", "appointment_create",
                    "appointment_query", "lease_query",
                    "kb_qa", "smalltalk", "unknown"]
    slots: dict[str, Any]
    candidate_room_ids: list[int]
    tool_results: dict[str, Any]
    pending_confirmation: ConfirmationPayload | None
    events: list[AgentEvent]

    # 出参
    reply: str
    cards: list[Card]
    actions: list[Action]
    sources: list[str]
```

## 3. 意图清单

| Intent | 触发示例 | 主要槽位 | 主要工具 |
|--------|----------|----------|----------|
| `room_search` | "推荐 3000 以下的房子" | `max_rent`, `district`, `payment_type`, `tags` | `vector.room_index`, `tools.room.search` |
| `appointment_create` | "预约明天下午看 302" | `room_id`, `appointment_time` | `tools.appointment.create` |
| `appointment_query` | "我有几个预约" | — | `tools.appointment.list_mine` |
| `lease_query` | "我的租约什么时候到期" | — | `tools.lease.list_mine` |
| `kb_qa` | "押金怎么退" | — | `vector.kb_search` |
| `smalltalk` | "你好"、"谢谢" | — | — |
| `unknown` | 无法分类 | — | — |

## 4. 槽位抽取规则

- LLM 用结构化输出（JSON Schema）返回槽位，不做自由文本拼接。
- 不能从单轮中抽取的槽位，从 `history`、Redis 会话状态与 `last_recommendations` 中继承。
- 时间槽位统一归一化为 `YYYY-MM-DD HH:mm`，模糊时间（"明天下午"）需要追问到具体时段。
- 区域使用枚举（`district_id` 列表），LLM 输出中文名时由后处理映射。

## 5. 节点行为约定

### 5.1 `intent_node`

- 输入：`message` + `history` 末 N 轮。
- 输出：`intent` 字段（枚举值）。
- 错误兜底：无法分类时落到 `unknown`，由 `reply_node` 给出引导话术。

### 5.2 `slot_node`

- 抽取或合并槽位到 `state.slots`。
- 不调用任何工具。
- 输出 `missing_required: list[str]`，供路由判断是否进入 `ask_node`。

### 5.3 `ask_node`

- 用提示词模板生成 1 个具体问题（一次只问 1~2 个槽位）。
- 不允许追问超过 3 轮；3 轮仍不足则放弃当前意图。

### 5.4 `tool_node`

- 按 `intent` 路由到对应工具。
- 每个工具调用都有超时（默认 10s）+ 单次重试。
- 工具必须来自白名单，不允许模型自由生成 URL、HTTP method 或任意接口路径。
- 工具入参先经过 Pydantic 模型校验，再调用 Mock backend 或 lease HTTP backend。
- 写工具只有在 `pending_confirmation.confirmed == true` 后才能执行。
- 工具返回结果落入 `state.tool_results`。

### 5.5 `confirm_node`

- 仅用于写操作（创建 / 取消预约）。
- 生成结构化 `pending_confirmation` 并直接返回，不调用工具。
- 下一轮用户消息为肯定时（"确认"、"好"、"是"），跳过本节点直接进入 `tool_node`。

### 5.6 `rerank_node`

- 对 `candidate_room_ids` 重新排序：综合 Milvus 相似度、租金贴合度、状态、距离等。
- 取 top-3 ~ top-5。

### 5.7 `reply_node`

- 根据 `intent` + `tool_results` + `slots` 生成自然语言回复。
- 推荐理由必须基于 `tool_results` 中存在的字段，不允许编造。
- FAQ 回答必须在 `sources` 中列出召回的 `kb_doc_id`。

## 6. 会话记忆

AptGuide 是任务型 Agent，不是单轮问答。多轮状态建议存入 Redis：

| Key | 内容 | TTL |
|-----|------|-----|
| `aptguide:session:{session_id}:slots` | 当前意图的槽位草稿 | 30 分钟 |
| `aptguide:session:{session_id}:last_recommendations` | 最近一次推荐的房源 ID 和展示顺序 | 30 分钟 |
| `aptguide:session:{session_id}:pending_confirmation` | 待确认的写操作摘要 | 10 分钟 |
| `aptguide:session:{session_id}:short_preferences` | 本轮会话内预算、区域、通勤、标签偏好 | 24 小时 |

规则：

1. Redis 状态只保存完成任务所需的最小信息。
2. 不保存手机号、身份证、合同全文、支付账号等敏感信息。
3. 用户确认或取消写操作后，必须清理对应 `pending_confirmation`。
4. 第一阶段没有 Redis 时允许使用内存实现，但只能用于本地演示。

## 7. 流式事件

SSE 事件用于让前端展示 Agent 进度。事件名和含义：

| 事件 | 触发时机 | 主要字段 |
|------|----------|----------|
| `message_received` | 收到用户消息 | `session_id`、`request_id` |
| `intent_detected` | 意图识别完成 | `intent`、`confidence` |
| `slot_updated` | 槽位抽取 / 合并完成 | `slots`、`missing_required` |
| `tool_call_started` | 开始调用工具 | `tool_name` |
| `tool_call_finished` | 工具调用结束 | `tool_name`、`status`、`latency_ms` |
| `answer_delta` | LLM 生成增量文本 | `delta` |
| `final` | 最终响应 | `reply`、`cards`、`actions`、`sources` |
| `error` | 出错 | `code`、`message`、`recoverable` |

流式事件不得泄露内部 token、完整工具入参、用户敏感数据。

## 8. 提示词组织

```text
src/aptguide/agent/prompts/
  v1/
    system.md             顶层系统提示
    intent_classify.md    意图识别
    slot_extract.md       槽位抽取（含 JSON schema）
    ask_followup.md       追问问题生成
    recommend_reason.md   推荐理由生成
    kb_qa.md              FAQ 回答（带召回片段）
    confirm_summary.md    写操作摘要
```

每个 `.md` 文件包含：

```markdown
---
name: intent_classify
inputs: [message, history, intents]
output: {intent: enum}
version: 1
---
（提示词正文）
```

提示词更新必须记录版本号，并通过 Agent Eval 对比修改前后的指标。线上配置通过 `PROMPT_VERSION` 选择版本，允许灰度和回滚。

## 9. 提示词规范

1. **始终中文**：用户消息和回答都是中文，提示词主体也用中文。
2. **明确边界**：在 system prompt 中写清"不要编造房源 / 不要承诺合同条款 / 不要泄露内部字段"。
3. **结构化输出**：意图、槽位、确认这类节点统一返回 JSON，并通过 Pydantic 校验。
4. **少样本谨慎使用**：只在意图识别和槽位抽取里放 2~3 条 few-shot，避免提示词膨胀。
5. **可调试**：每个提示词带 `version`，更新时新建版本而不是覆盖。

## 10. RAG 与重排策略

房源推荐和规则问答都应遵循“检索结果可追溯、低置信度不强答”的原则。

### 10.1 房源推荐

```text
query rewrite
  → Milvus vector search + metadata filter
  → lease room.search 精确校验
  → rerank
  → LLM 生成推荐理由
```

重排特征：

- Milvus 相似度；
- 租金与预算的贴合度；
- 区域、支付方式、租期匹配度；
- 房源是否可预约；
- 标签与模糊偏好的匹配度；
- 用户最近浏览或短期偏好。

### 10.2 知识库问答

```text
query rewrite
  → Milvus kb_search top-k
  → score threshold
  → 可选 rerank
  → LLM grounded answer
  → sources
```

约束：

- 召回分数低于阈值时回退，不强答。
- 回答必须引用 `sources`。
- LLM 不得超出召回内容承诺合同、押金或法律结果。

## 11. 失败回退

| 场景 | 回退 |
|------|------|
| LLM 超时 / 输出非法 JSON | 重试 1 次；仍失败时返回模板话术"系统繁忙，请稍后再试" |
| Milvus 不可用 | 跳过语义召回，仅按 Java 显式过滤 |
| Java 工具接口失败 | 不重试 5xx 之外的错误，原样转述给用户 |
| 槽位 3 轮未补齐 | 切到 `unknown` 流程，给出兜底引导 |
| 用户明确要求人工 | 返回客服联系方式，结束本轮 |
| Redis 不可用 | 降级为无状态对话，不允许执行依赖 pending_confirmation 的写操作 |
| SSE 断开 | 前端可重试或降级调用非流式 `/api/chat` |
| RAG 召回低置信度 | 返回无法确认答案，并建议查看房源详情或联系门店 |

## 12. 安全约束（提示词级）

system prompt 必须包含以下硬性规则：

- 不要编造房源、价格、楼盘、地址、楼层、配套。
- 不要承诺合同条款、押金金额、违约金、法律意见。
- 不要返回任何用户的手机号、身份证、合同全文。
- 不要在写操作前直接执行；必须先返回操作摘要等待确认。
- 当工具失败时，如实告知用户，而不是用通用知识"猜"答案。
