# 11 · Feasibility And Development Plan

> 相关文档：[Start Here](00-start-here.md)、[产品需求](01-product-requirements.md)、[Agent 架构](02-agent-framework-architecture.md)、[API Schema](14-api-and-schema-contract.md)、[工具注册与错误码](15-tool-registry-and-error-codes.md)、[实施任务](12-implementation-task-plan.md)、[实施准备清单](18-implementation-readiness-checklist.md)。

## 1. 总体判断

`AptGuide 2.0` 作为租房任务客服 Agent 是可行的。

可行原因：

- 业务域明确：找房、租房规则、预约、我的租约/预约；
- 数据来源明确：现有 `lease` 后端、Milvus、知识库、Redis；
- 工具边界明确：不直接访问 MySQL，通过受控工具接口调用；
- 风险可控：写操作走 confirmation workflow，个人数据走 user_id 绑定；
- 可分阶段交付：可以先做独立 MVP，再扩展长期记忆、人工接管和运营闭环。

关键前提：

- `lease/web-app` 提供稳定的 `/internal/ai/tools/*`；
- MySQL 有真实可演示房源、预约、租约数据；
- 房源标签和区域数据足以支持语义推荐；
- Milvus / KB 数据可同步；
- 前端支持结构化 cards/actions；
- 有基础 eval 用例防止回归。

## 2. 产品定位

`AptGuide 2.0` 不是通用大模型入口，而是：

```text
面向租客的租房任务 Agent。
它通过长期用户画像、短期任务状态、租房知识库、真实 lease 工具和结构化前端交互，
完成找房、问答、预约、查询和人工接管。
```

产品能力：

- 找房推荐；
- 租房规则问答；
- 看房预约；
- 我的预约/租约查询；
- 当前会话记忆；
- 长期偏好画像；
- 工具失败恢复；
- 人工接管；
- 运营 trace 和 eval。

## 3. 技术路线

推荐架构：

```text
Frontend / H5
  -> Chat API / Stream API
  -> Event Filter
  -> Human Handoff Gate
  -> Conversation Manager
      -> recent messages
      -> rolling summary
      -> active task state
      -> long-term profile
  -> Hybrid Router
      -> rule router
      -> LLM classifier
      -> safety guard
  -> Procedure Layer
      -> Room Search Procedure
      -> Rental Knowledge Procedure
      -> Appointment Workflow
      -> User Data Query
      -> Recovery Procedure
  -> Tool Registry
      -> lease tools
      -> vector / KB tools
      -> memory tools
  -> Response Composer
  -> Structured Response + Trace
```

## 4. 技术选型

| 能力 | 推荐技术 |
| --- | --- |
| HTTP 服务 | FastAPI |
| Agent 编排 | LangGraph |
| 会话状态 | Redis |
| 长期画像 | MySQL/PostgreSQL，开发期可 SQLite |
| 工具调用 | httpx + Tool Registry |
| 向量检索 | Milvus |
| LLM | OpenAI-compatible client |
| 前端 | Vite + React/Vue 独立版，后续接 rentHouseH5 |
| 流式事件 | SSE |
| Eval | YAML cases + pytest runner |
| Trace | JSON logs + request_id/trace_id |

## 5. 分阶段开发计划

### Phase 0: 文档和契约

交付：

- 产品需求；
- Agent 架构；
- Tool Registry schema；
- API response schema；
- Memory schema；
- Handoff policy；
- Trace/Eval schema；
- Prompt/Eval contract；
- Implementation readiness checklist；
- 开发计划。

完成标准：

- 文档能指导实现；
- 每个能力有明确边界；
- 写操作和个人数据安全规则清晰。

### Phase 1: 独立 Agent API MVP

目标：跑通最小租房助手闭环。

实现：

- FastAPI `/api/chat`；
- `/health` 和 `/health/deps`；
- Conversation Manager 基础版；
- Domain Boundary Router；
- CapabilityAgent；
- Response Composer；
- Trace Logger；
- LeaseToolAdapter 基础健康检查。

验收：

- 能回答“你能做什么”；
- 能拒绝天气/代码生成；
- 能输出结构化 response；
- trace 中有 request_id、phase、domain_category。

### Phase 2: Memory Center 和上下文压缩

目标：支持短期任务状态和长期偏好画像。

实现：

- recent_messages；
- rolling_summary；
- active_task_state；
- long_term_profile；
- memory_candidates；
- 用户查看/删除偏好；
- summary compaction；
- memory eval。

验收：

- “我是小明，我想找大学城附近”后能回答“你刚才来找房”；
- “预算我都接受”能清除预算；
- 新会话能加载用户确认过的长期偏好；
- 100 轮对话不丢 pending_action。

### Phase 3: 找房 Procedure

目标：让找房从一次检索升级为可恢复任务。

实现：

- area.normalize；
- hard filter / soft preference 拆分；
- room.search；
- exact_search；
- relaxed_budget_search；
- relaxed_area_search；
- nearby_alternative_search；
- 推荐卡片；
- 搜索 trace。

验收：

- 大学城南亭不会被错误当成 district 硬过滤；
- 空结果能放宽并解释；
- 房源卡片和回复文本一致；
- 不编造房源。

### Phase 4: 预约 Workflow

目标：写操作安全可控。

实现：

- resolve room；
- collect appointment time；
- pending_action；
- confirmation_id；
- confirmation card；
- stale action 拦截；
- appointment.create；
- tool failure recovery。

验收：

- 旧确认按钮不能执行新操作；
- 没有 confirmation_id 不能创建预约；
- apartment_id 缺失时不能默认 0；
- 工具失败能解释并建议下一步。

### Phase 5: 租房知识和用户数据

目标：补齐客服核心能力。

实现：

- kb.search；
- knowledge answer with sources；
- low confidence fallback；
- appointment.list_mine；
- lease.list_mine；
- 用户身份校验。

验收：

- 押金/退租/续约问题有来源；
- KB 不足时不乱答；
- 我的预约/租约只能查本人；
- 未登录时给出登录引导。

### Phase 6: 人工接管和运营闭环

目标：符合真实客服场景。

实现：

- handoff trigger；
- handoff summary；
- AI paused/resumed；
- unresolved question log；
- knowledge gap log；
- basic operations report。

验收：

- 用户说“转人工”能进入 handoff；
- 工具连续失败能建议人工；
- 人工摘要包含用户目标、偏好、失败原因；
- AI 暂停后不自动抢答。

### Phase 7: Eval 和产品化

目标：稳定演示和持续迭代。

实现：

- eval YAML；
- pytest runner；
- prompt version；
- regression suite；
- trace sampling；
- frontend interaction regression。

验收：

- 核心 eval 全通过；
- 每次 prompt/流程改动可回归；
- 线上问题能通过 trace 复盘。

## 6. 风险和应对

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| lease 工具接口不稳定 | Agent 无法真实执行 | 先做 health/deps 和错误映射 |
| 房源标签弱 | 推荐质量差 | 加 room vector sync 和标签补全 |
| 长期记忆误写 | 用户信任受损 | memory candidate + 用户可删除 |
| 上下文压缩丢状态 | 预约/推荐错乱 | 结构化 state 优先，摘要只辅助 |
| LLM 路由不稳定 | 错误流程 | 规则优先 + LLM 兜底 + 后处理 |
| 写操作误执行 | 高风险 | confirmation_id + stale 拦截 |
| 过度自动化 | 客诉风险 | handoff policy + AI paused |
| 成本和延迟 | 体验下降 | 工具缓存、摘要压缩、模型分级 |

## 7. MVP 最小可演示范围

最小演示链路：

```text
用户打开独立前端
  -> 说出找房需求
  -> 系统加载/更新偏好
  -> 归一化区域
  -> 搜索房源
  -> 空结果放宽
  -> 返回房源卡片
  -> 用户点击预约
  -> 系统生成确认卡
  -> 用户确认
  -> 调用真实 lease 创建预约
  -> trace 显示完整过程
```

必须覆盖：

- 域外拒答；
- 短期记忆；
- 长期偏好候选；
- 空搜索恢复；
- 结构化确认；
- stale action 拦截；
- 工具失败解释；
- 人工接管入口。

## 8. 不建议第一版做的事

- 完整运营后台；
- 全自动长期记忆无确认写入；
- 多个自由 Agent 互相对话；
- 自动执行取消/退款/合同类高风险操作；
- 复杂多渠道接入；
- 大规模 prompt 自动优化；
- 过早接入 Kubernetes、Kafka、Nacos。

## 9. 开发顺序建议

```text
1. 先把 response schema 和 tool result schema 定死
2. 再做 ConversationFrame 和 TraceEvent
3. 再做 BoundaryRouter 和 CapabilityAgent
4. 再接 lease health 和 room.search
5. 再做 Memory Center
6. 再做 RoomSearch Procedure
7. 再做 Appointment Workflow
8. 最后做 handoff、eval、运营指标
```

原因：

- schema 是前后端和工具的共同契约；
- trace 能帮助后续所有调试；
- 找房和预约是最有演示价值的闭环；
- 长期记忆和人工接管能体现真实客服产品深度。

## 10. 最终建议

保留 `AptGuide 2.0` 名称。

架构关键词使用：

```text
任务流程驱动
长期用户画像
短期任务状态
混合路由
多专家模块
工具注册表
结构化 action
人工接管
Trace/Eval 闭环
```

避免主文档中过度使用：

```text
自由多 Agent
裸 Chain-of-Thought
全自动执行
通用 AI 助手
```

这样更符合真实企业客服 Agent 背景，也更适合后续实现和答辩展示。
