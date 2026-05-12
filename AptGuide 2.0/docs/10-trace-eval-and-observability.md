# 10 · Trace Eval And Observability

> 相关文档：[Agent 架构](02-agent-framework-architecture.md)、[工具与集成契约](04-tool-and-integration-contract.md)、[工具注册与错误码](15-tool-registry-and-error-codes.md)、[评测路线](06-evaluation-roadmap-and-upgrade-assessment.md)、[Prompt/Eval 契约](17-prompt-and-eval-contract.md)、[运行时设计](08-procedure-driven-agent-runtime.md)、[实施任务](12-implementation-task-plan.md)。

## 1. 设计目标

`AptGuide 2.0` 需要可解释、可测试、可运营。系统不暴露原始思维链，但必须记录可审计的执行轨迹。

Trace 的用途：

- 开发调试；
- 用户问题复盘；
- 工具失败定位；
- 对话质量评测；
- 运营分析；
- 安全审计。

## 2. Trace 原则

应该记录：

- 系统做了什么；
- 为什么选择某个流程；
- 调用了哪些工具；
- 工具返回了什么类型的结果；
- 是否触发恢复；
- 是否触发人工接管；
- 最终回复用了哪些证据。

不应该记录：

- 原始 Chain-of-Thought；
- 敏感个人信息明文；
- LLM 完整 prompt 中的隐私内容；
- 未脱敏的合同、电话、身份证等。

## 3. Trace Event Schema

```json
{
  "trace_id": "t-001",
  "request_id": "r-001",
  "session_id": "s-001",
  "user_id_hash": "u_hash",
  "event": "tool_call_finished",
  "timestamp": "2026-05-05T10:00:00+08:00",
  "phase": "searching_rooms",
  "payload": {
    "tool": "room.search",
    "strategy": "relaxed_budget_search",
    "ok": true,
    "result_count": 3,
    "latency_ms": 120
  }
}
```

## 4. 推荐事件

| Event | 说明 |
| --- | --- |
| `message_received` | 收到用户消息 |
| `event_filtered` | 完成事件过滤 |
| `memory_loaded` | 加载短期/长期记忆 |
| `memory_updated` | 更新短期状态或长期候选 |
| `summary_compacted` | 完成上下文压缩 |
| `boundary_classified` | 完成领域边界判断 |
| `phase_detected` | 完成阶段判断 |
| `procedure_selected` | 选择任务流程 |
| `plan_created` | 生成小型任务计划 |
| `tool_call_started` | 工具调用开始 |
| `tool_call_finished` | 工具调用结束 |
| `recovery_started` | 启动恢复策略 |
| `handoff_triggered` | 触发人工接管 |
| `response_composed` | 生成最终结构化响应 |
| `action_rejected` | 拒绝过期/重复/越权 action |

## 5. 搜索 Trace

找房必须记录每次搜索策略。

```json
{
  "event": "tool_call_finished",
  "payload": {
    "tool": "room.search",
    "strategy": "exact_search",
    "query": "大学城 南亭 安静",
    "filters": {
      "district": "番禺区",
      "max_rent": 1500,
      "payment_type": "月付"
    },
    "result_count": 0
  }
}
```

恢复后：

```json
{
  "event": "recovery_started",
  "payload": {
    "type": "relax_budget",
    "reason": "exact_search_empty",
    "from": 1500,
    "to": 2200
  }
}
```

## 6. 写操作 Trace

预约必须记录确认链路。

```json
[
  {
    "event": "pending_action_created",
    "payload": {
      "type": "appointment.create",
      "confirmation_id": "c-001",
      "room_id": 3001,
      "apartment_id": 101,
      "expires_at": "2026-05-05T10:10:00+08:00"
    }
  },
  {
    "event": "action_confirmed",
    "payload": {
      "confirmation_id": "c-001"
    }
  },
  {
    "event": "tool_call_finished",
    "payload": {
      "tool": "appointment.create",
      "ok": true
    }
  }
]
```

任何失败不能被隐藏：

```json
{
  "event": "tool_call_finished",
  "payload": {
    "tool": "appointment.create",
    "ok": false,
    "error_code": "MISSING_APARTMENT_ID",
    "recoverable": true
  }
}
```

## 7. Eval 分类

评测集按能力拆分：

```text
boundary_eval
memory_eval
context_compression_eval
room_search_eval
knowledge_eval
appointment_safety_eval
tool_failure_eval
handoff_eval
response_consistency_eval
```

## 8. Eval Case Schema

```yaml
- id: room-search-relax-budget
  category: room_search_eval
  turns:
    - user: 找大学城南亭附近1500以内的房子
  expected_tool_results:
    room.search.exact_search:
      result_count: 0
    room.search.relaxed_budget_search:
      result_count: 3
  assistant_should:
    - normalize_area
    - try_exact_search
    - relax_budget
    - explain_recovery
    - return_room_cards
  assistant_must_not:
    - fabricate_rooms
    - dead_end_reply
```

## 9. 指标

| 指标 | 目标 |
| --- | --- |
| in-domain 不误拒率 | >= 95% |
| out-of-domain 拒答准确率 | >= 95% |
| 写操作未确认执行率 | 0% |
| stale confirmation 拦截率 | 100% |
| 空搜索恢复触发率 | >= 90% |
| 推荐卡片与文本一致率 | >= 95% |
| 长期记忆误写率 | <= 2% |
| 上下文压缩关键状态保留率 | >= 99% |
| 工具失败可解释率 | >= 95% |
| 人工接管摘要完整率 | >= 95% |

## 10. 可观测性

日志字段：

```text
request_id
trace_id
session_id
user_id_hash
phase
domain_category
procedure
tool_name
tool_status
latency_ms
error_code
recovery_used
handoff_status
prompt_version
model_name
```

开发环境可展示 trace panel；生产环境应脱敏并按权限查看。

## 11. 运营报表

Trace 可以生成：

- 热门找房区域；
- 空结果最多的条件；
- 常见知识库缺口；
- 工具失败分布；
- 预约失败原因；
- 人工接管原因；
- 长期偏好分布；
- 推荐到预约转化率。

## 12. MVP 建议

第一版必须做：

- request_id / trace_id；
- tool call trace；
- recovery trace；
- pending action trace；
- eval YAML 数据结构；
- 10-20 条核心回归用例。

后续增强：

- trace 可视化；
- 自动评分；
- 线上抽样评测；
- prompt 版本对比；
- 运营指标看板。
