# 05 · Frontend Interaction Protocol

> 相关文档：[产品需求](01-product-requirements.md)、[Agent 架构](02-agent-framework-architecture.md)、[API Schema](14-api-and-schema-contract.md)、[工具与集成契约](04-tool-and-integration-contract.md)、[运行时设计](08-procedure-driven-agent-runtime.md)、[Trace/Eval](10-trace-eval-and-observability.md)、[实施任务](12-implementation-task-plan.md)。

## 1. 前端目标

`AptGuide 2.0` 的前端不是简单聊天框，而是一个租房任务界面。

它需要支持：

- 普通聊天消息；
- 房源卡片；
- 规则来源；
- 看房预约确认；
- 结构化 action；
- stale action 禁用；
- 长期偏好查看和确认；
- 人工接管状态；
- 流式进度；
- 错误和恢复提示。

## 2. Chat Request

基础请求：

```json
{
  "session_id": "s-001",
  "message": "帮我找大学城南亭附近的房子",
  "action": null,
  "client_context": {
    "timezone": "Asia/Shanghai",
    "source": "standalone_web"
  }
}
```

按钮 action 请求：

```json
{
  "session_id": "s-001",
  "message": "",
  "action": {
    "type": "confirmation_confirm",
    "action_id": "a-001",
    "confirmation_id": "c-20260504-001"
  }
}
```

前端可以在按钮上显示“确认”，但请求中的业务语义必须来自 `action.type` 和 `confirmation_id`，不能依赖 `message` 模拟点击。

## 3. Chat Response

```json
{
  "session_id": "s-001",
  "request_id": "r-001",
  "trace_id": "t-001",
  "reply": "我先按大学城南亭附近帮你找房...",
  "phase": "showing_room_results",
  "domain_category": "in_domain_task",
  "cards": [],
  "actions": [],
  "pending_action": null,
  "sources": [],
  "metadata": {
    "recovery_used": true,
    "memory_used": true,
    "handoff_status": null
  }
}
```

## 4. Card Types

### 4.1 Room Card

```json
{
  "type": "room",
  "room_id": 3001,
  "apartment_id": 101,
  "title": "大学城南亭寓 301",
  "rent": 1800,
  "district": "番禺区",
  "area_label": "大学城南亭附近",
  "tags": ["近大学城", "可月付", "安静"],
  "description": "距离大学城南亭步行约 12 分钟",
  "available_for_appointment": true
}
```

### 4.2 Confirmation Card

```json
{
  "type": "confirmation",
  "confirmation_id": "c-20260504-001",
  "status": "pending",
  "summary": "预约大学城南亭寓 301，时间 2026-05-05 14:00",
  "expires_at": "2026-05-04T12:30:00+08:00"
}
```

确认卡片状态：

```text
pending
confirmed
cancelled
expired
failed
stale
```

前端规则：

- 用户点击确认/取消后立即禁用按钮；
- 后端返回最终状态后更新卡片；
- 旧卡片不能再次发送有效 action；
- 如果用户手动输入“确认”，后端仍需检查当前 pending action。

### 4.3 Memory Card

```json
{
  "type": "memory_candidate",
  "candidate_id": "mc-001",
  "summary": "记住你偏好大学城附近、安静、可月付的房源",
  "status": "pending",
  "actions": ["memory_accept", "memory_reject"]
}
```

状态：

```text
pending
accepted
rejected
deleted
expired
```

### 4.4 Handoff Card

```json
{
  "type": "handoff",
  "handoff_id": "h-001",
  "status": "created",
  "reason": "预约工具连续失败，已为人工客服整理上下文",
  "summary": "你想预约大学城南亭附近房源，系统已尝试创建预约但暂未成功。"
}
```

## 5. Action Types

```json
{
  "type": "create_appointment",
  "label": "预约看房",
  "payload": {
    "room_id": 3001,
    "apartment_id": 101
  }
}
```

推荐 action：

| Action | 用途 |
| --- | --- |
| `view_room_detail` | 查看房源详情 |
| `create_appointment` | 发起预约 |
| `search_more` | 换一批 |
| `relax_budget` | 放宽预算 |
| `change_area` | 修改区域 |
| `confirmation_confirm` | 确认写操作 |
| `confirmation_cancel` | 取消写操作 |
| `memory_accept` | 保存长期偏好 |
| `memory_reject` | 不保存长期偏好 |
| `memory_delete` | 删除长期偏好 |
| `handoff_request` | 请求人工接管 |
| `handoff_resume_ai` | 恢复 AI 接管 |

## 6. SSE Events

推荐事件：

| Event | 说明 |
| --- | --- |
| `message_received` | 收到消息 |
| `event_filtered` | 完成事件过滤 |
| `memory_loaded` | 加载短期/长期记忆 |
| `memory_updated` | 更新短期记忆 |
| `summary_compacted` | 完成上下文压缩 |
| `boundary_classified` | 完成领域边界判断 |
| `phase_detected` | 完成阶段判断 |
| `procedure_selected` | 选择任务流程 |
| `plan_created` | 生成任务计划 |
| `tool_call_started` | 工具开始 |
| `tool_call_finished` | 工具结束 |
| `recovery_started` | 开始恢复 |
| `handoff_triggered` | 触发人工接管 |
| `answer_delta` | 回复增量 |
| `final` | 最终结构化响应 |
| `error` | 可恢复/不可恢复错误 |

前端可以展示简短状态：

```text
正在理解你的需求...
正在读取你的找房偏好...
正在查找大学城附近房源...
精确条件没有结果，正在放宽预算...
正在生成推荐理由...
```

## 7. 交互体验要求

- 不用大段解释系统内部流程；
- 用户需要知道“现在系统在帮我做什么”；
- 空结果时必须给下一步按钮；
- 拒答时必须给可继续的租房入口；
- 长期记忆写入必须让用户知道并能撤销；
- 人工接管后前端应显示 AI 已暂停；
- 卡片和回复不能互相矛盾；
- 移动端优先，桌面端可复用。

## 8. 独立前端建议

第一阶段可以用轻量前端：

- Vite + React 或 Vue；
- 单页面聊天；
- 右侧/底部调试面板仅开发环境展示；
- 支持真实 session 和本地开发 trace；
- 支持查看 trace metadata。

正式接入 `rentHouseH5` 时再适配 Vant 风格和 H5 路由。
