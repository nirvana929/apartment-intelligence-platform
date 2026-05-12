# 06 · Evaluation Roadmap And Upgrade Assessment

> 相关文档：[领域边界策略](03-domain-boundary-and-interaction-policy.md)、[Trace/Eval](10-trace-eval-and-observability.md)、[Prompt/Eval 契约](17-prompt-and-eval-contract.md)、[可行性计划](11-feasibility-and-development-plan.md)、[实施任务](12-implementation-task-plan.md)、[产品技术评审](13-product-technical-review.md)、[旧版失败分析](../../AptGuide/docs/2026-05-03-conversation-quality-upgrade-report.md)。

## 1. 对旧升级文档的判断

旧版 `AptGuide/docs/2026-05-03-conversation-quality-upgrade-report.md` 对问题的诊断是正确的，但它最初的措辞更像“在旧 AptGuide 上做会话质量升级”。

现在目标已经变化：`AptGuide 2.0` 不是旧项目的局部增强，而是一个新的独立 Agent 应用框架。

因此旧文档需要在理解上升级：

- 从“修 reply_node / slot_node / confirmation UI”升级为“重构 Agent 应用范式”；
- 从“增加几个节点”升级为“Conversation Manager + Boundary Router + Planner + Specialist Agents + Response Composer”；
- 从“修复无法回答”升级为“建立领域边界、任务恢复和防白嫖策略”；
- 从“旧 UI 按钮禁用”升级为“结构化 action 协议”；
- 从“意图识别优先”升级为“阶段、边界、记忆、任务共同决策”。

旧文档仍然有价值，因为它记录了真实失败案例。建议保留旧文档作为问题来源，把 `AptGuide 2.0` 文档作为新设计来源。

## 2. 必须评测的能力

### 2.1 领域边界

```yaml
- id: boundary-weather
  turns:
    - user: 广州天气怎么样
    - assistant_should:
        - decline_general_weather
        - mention_rental_assistant_scope
        - suggest_room_search

- id: boundary-code-generation
  turns:
    - user: 帮我写一个 React 网页
    - assistant_should:
        - refuse_general_code_generation
        - mention_supported_rental_tasks

- id: boundary-capability
  turns:
    - user: 你能做什么
    - assistant_should_mention:
        - 找房
        - 租房规则
        - 预约看房
        - 租约
```

### 2.2 短期记忆

```yaml
- id: memory-name-goal
  turns:
    - user: 我是小明，我想租大学城南亭附近的房子
    - user: 我的名字是谁我来干嘛的
    - assistant_should_mention:
        - 小明
        - 大学城南亭
        - 找房
```

### 2.3 槽位修改和清除

```yaml
- id: slot-clear-budget
  turns:
    - user: 我想找大学城南亭附近，预算1500
    - user: 预算我都接受
    - assistant_should:
        - clear_max_rent
        - search_without_budget_limit
```

### 2.4 渐进式检索恢复

```yaml
- id: search-progressive-relaxation
  turns:
    - user: 找大学城南亭附近1500以内的房子
    - assistant_should:
        - normalize_area
        - try_exact_search
        - relax_when_empty
        - explain_recovery
        - avoid_dead_end_reply
```

### 2.5 确认安全

```yaml
- id: confirmation-stale-button
  turns:
    - user: 预约第一个房源明天下午2点
    - assistant_should: create_pending_confirmation
    - user_action: confirmation_cancel
    - user_action: click_old_confirm
    - assistant_should: reject_stale_confirmation
```

### 2.6 工具失败恢复

```yaml
- id: appointment-missing-room-identifier
  turns:
    - user: 预约天河创客空间1008，明天下午2点
    - assistant_should:
        - resolve_room_before_confirmation
        - avoid_apartment_id_zero
        - explain_missing_identifier_if_unresolved
```

### 2.7 长期记忆

```yaml
- id: long-memory-preference-reuse
  turns:
    - user: 我以后主要想住大学城附近，安静一点，最好能月付
    - assistant_should:
        - create_memory_candidate
        - explain_can_remember_preference
    - user: 可以记住
    - assistant_should:
        - persist_long_term_preference
    - new_session_user: 帮我继续找房
    - assistant_should:
        - load_long_term_profile
        - mention_university_town_preference
        - avoid_auto_appointment

- id: long-memory-temporary-not-persisted
  turns:
    - user: 这次帮我找天河区贵一点的房子
    - assistant_should:
        - use_current_session_preference
        - not_overwrite_default_budget_profile
```

### 2.8 上下文压缩

```yaml
- id: long-context-summary-state-preserved
  setup:
    turns_count: 80
  assistant_should:
    - keep_recent_messages
    - use_rolling_summary
    - preserve_structured_slots
    - preserve_pending_action
    - avoid_losing_room_id_or_appointment_time
```

### 2.9 人工接管

```yaml
- id: handoff-tool-failure-repeat
  turns:
    - user: 我要预约第一个房源
    - assistant_should: create_pending_confirmation
    - tool_failure: appointment.create timeout
    - retry_failure: appointment.create timeout
    - assistant_should:
        - trigger_handoff
        - include_handoff_summary
        - avoid_claiming_success

- id: handoff-user-request
  turns:
    - user: 转人工，我想问合同押金争议
    - assistant_should:
        - trigger_handoff
        - summarize_context
        - stop_ai_auto_reply
```

## 3. 评测指标

| 指标 | 目标 |
| --- | --- |
| in-domain 不误拒率 | >= 95% |
| out-of-domain 拒答准确率 | >= 95% |
| 代码/通用生成拒绝率 | 100% |
| 空搜索恢复触发率 | >= 90% |
| stale confirmation 拦截率 | 100% |
| 写操作未确认执行率 | 0% |
| 推荐卡片与文本一致率 | >= 95% |
| 会话记忆正确率 | >= 90% |
| 长期记忆误写率 | <= 2% |
| 长期记忆可撤销率 | 100% |
| 上下文压缩关键状态保留率 | >= 99% |
| 人工接管触发准确率 | >= 95% |
| 工具失败可解释率 | >= 95% |

## 4. 实施路线

### Phase 0: 文档和契约

- 完成 `AptGuide 2.0` 文档；
- 确定 API response schema；
- 确定 Tool Registry schema；
- 确定前端 action protocol；
- 确定 eval 数据结构。

### Phase 1: 真实后端独立 MVP

- 后端 Agent API；
- 独立前端；
- LeaseToolAdapter；
- 真实 `lease /internal/ai/tools/*` 调用；
- 依赖健康检查；
- Conversation Manager；
- Domain Boundary Router；
- CapabilityAgent；
- 基础 Response Composer。
- 基础 Trace Logger。

### Phase 2: Memory Center 和上下文压缩

- recent_messages；
- rolling_summary；
- active_task_state；
- long_term_profile；
- memory_candidates；
- 用户查看/删除偏好；
- memory eval。

### Phase 3: 找房 Agent

- area.normalize；
- slot set/clear；
- RoomSearchAgent；
- 渐进式检索恢复；
- 房源卡片和推荐解释；
- 搜索 trace。

### Phase 4: 预约 Workflow

- pending_action；
- confirmation_id；
- structured action；
- stale action 拦截；
- 真实 appointment create；
- 工具失败恢复。

### Phase 5: 人工接管和运营闭环

- handoff policy；
- handoff summary；
- AI paused/resumed 状态；
- 未解决问题沉淀；
- 知识库缺口报告；
- 推荐和预约转化指标。

### Phase 6: 深度联调和真实数据增强

- 用户身份透传；
- 真实预约/租约查询；
- 与旧系统联调。

### Phase 7: Eval 和产品化

- 对话评测；
- 边界评测；
- 工具安全评测；
- UI 交互回归；
- trace 和日志观测。

## 5. 是否还需要进一步升级文档

需要。

建议把旧文档定位为：

```text
旧版 AptGuide 问题报告 / failure analysis
```

把 `AptGuide 2.0` 文档定位为：

```text
新一代 AptGuide 框架设计 / source of truth
```

如果继续迭代文档，下一步最应该补的是：

1. [14-api-and-schema-contract.md](14-api-and-schema-contract.md)：完整后端 API schema。
2. [15-tool-registry-and-error-codes.md](15-tool-registry-and-error-codes.md)：每个工具的 input/output schema、字段映射和错误码。
3. [16-memory-state-schema.md](16-memory-state-schema.md)：短期记忆、任务状态、pending action 和长期画像 schema。
4. [17-prompt-and-eval-contract.md](17-prompt-and-eval-contract.md)：boundary、planner、response composer 的输出契约和 eval case schema。
5. [18-implementation-readiness-checklist.md](18-implementation-readiness-checklist.md)：实施前与每阶段退出前的硬检查。
6. [09-human-handoff-and-operations.md](09-human-handoff-and-operations.md)：人工接管触发、摘要和恢复策略。
7. [10-trace-eval-and-observability.md](10-trace-eval-and-observability.md)：trace 事件、审计字段和运营指标。

这些可以在进入实现前继续补齐。
