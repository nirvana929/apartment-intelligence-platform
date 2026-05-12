# 07 · Memory And Context Architecture

> 相关文档：[产品需求](01-product-requirements.md)、[Agent 架构](02-agent-framework-architecture.md)、[领域边界策略](03-domain-boundary-and-interaction-policy.md)、[记忆状态 Schema](16-memory-state-schema.md)、[前端交互协议](05-frontend-interaction-protocol.md)、[运行时设计](08-procedure-driven-agent-runtime.md)、[Trace/Eval](10-trace-eval-and-observability.md)。

## 1. 设计目标

`AptGuide 2.0` 的记忆系统不是简单保存聊天记录，而是把当前对话、任务状态和长期用户偏好分开管理。

目标：

- 当前会话中能理解“第一个”“确认”“预算我都接受”等上下文表达；
- 用户下次回来时，可以加载稳定偏好，例如常住区域、预算习惯、通勤偏好；
- 长对话不会因为上下文过长导致成本、延迟和状态丢失；
- 用户可以查看、修改和删除长期记忆；
- 敏感信息不进入长期画像。

## 2. 记忆分层

```text
Memory Center
  -> recent_messages
  -> rolling_summary
  -> active_task_state
  -> long_term_profile
  -> memory_candidates
  -> memory_audit_log
```

| 层级 | 生命周期 | 用途 | 示例 |
| --- | --- | --- | --- |
| `recent_messages` | 当前会话，短窗口 | 保留最近原文 | 最近 6-12 轮对话 |
| `rolling_summary` | 当前会话，可更新 | 压缩长历史 | 用户正在找大学城附近安静房源 |
| `active_task_state` | 当前任务 | 保存结构化任务状态 | 预算、区域、房源、pending action |
| `long_term_profile` | 跨会话 | 保存稳定偏好 | 偏好大学城、可月付、安静 |
| `memory_candidates` | 待确认/待提升 | 暂存可能的长期事实 | 用户这次说自己考研 |
| `memory_audit_log` | 长期 | 记录来源和变更 | 何时写入、为何写入、何时删除 |

## 3. 短期上下文

短期上下文用于回答本轮任务，不等同于长期记忆。

推荐结构：

```json
{
  "session_id": "s-001",
  "recent_messages": [
    {"role": "user", "content": "帮我找大学城附近房子"},
    {"role": "assistant", "content": "预算大概多少？"}
  ],
  "rolling_summary": "用户正在找大学城附近房源，尚未确定预算。",
  "active_task_state": {
    "task_type": "room_search",
    "phase": "collecting_room_requirements",
    "slots": {
      "area_text": "大学城",
      "normalized_district": "番禺区",
      "max_rent": null,
      "payment_type": null
    },
    "last_recommendations": [],
    "pending_action": null
  }
}
```

关键约束：

- 房源 ID、预约时间、confirmation_id 必须保存在结构化字段中，不能只放在摘要里；
- 最近消息用于语气和局部指代，不能承担业务状态；
- rolling summary 只能辅助理解，不能作为写操作依据。

## 4. 长期用户画像

长期画像只保存低敏、稳定、可解释、可撤销的事实。

推荐结构：

```json
{
  "user_id": "u-001",
  "preferred_areas": [
    {
      "value": "大学城",
      "confidence": 0.92,
      "source": "user_confirmed",
      "scope": "recurring_preference",
      "updated_at": "2026-05-05T10:00:00+08:00"
    }
  ],
  "budget_range": {
    "min": 1500,
    "max": 2200,
    "confidence": 0.78,
    "source": "repeated_behavior",
    "scope": "recurring_preference"
  },
  "identity_context": [
    {
      "value": "考研",
      "confidence": 0.72,
      "source": "user_stated",
      "scope": "preference_context"
    }
  ],
  "preferences": ["安静", "可月付", "近地铁"],
  "negative_preferences": ["不要临街"],
  "privacy_flags": []
}
```

长期画像的写入规则：

| 输入 | 处理 |
| --- | --- |
| “以后都按大学城附近帮我找” | 可直接写入长期偏好 |
| “这次想找天河区” | 只写当前任务，不覆盖长期偏好 |
| 多次选择安静房源 | 可生成 memory candidate |
| 电话、身份证、合同编号 | 不进入长期画像 |
| 用户要求删除偏好 | 删除并写 audit log |

## 5. Memory Candidate

Memory Candidate 是长期记忆的缓冲层，避免误写。

```json
{
  "candidate_id": "mc-001",
  "user_id": "u-001",
  "type": "preference",
  "key": "preferred_areas",
  "value": "大学城",
  "reason": "用户明确说以后主要想住大学城附近",
  "confidence": 0.91,
  "requires_confirmation": true,
  "status": "pending"
}
```

候选状态：

```text
pending
accepted
rejected
expired
auto_promoted
```

MVP 可以先采用保守策略：涉及长期画像的新增都要求用户确认。

## 6. 上下文压缩策略

压缩触发条件：

- recent messages 超过配置窗口；
- token 预算超过阈值；
- 任务阶段切换，例如找房结果展示后进入预约；
- 会话结束或进入人工接管。

压缩输出：

```json
{
  "rolling_summary": "用户小明正在找大学城南亭附近安静房源，预算曾为1500，后来表示预算都可接受。系统已推荐3个番禺区房源。",
  "state_patch": {
    "slots.clear": ["max_rent"],
    "slots.set": {
      "area_text": "大学城南亭",
      "normalized_district": "番禺区"
    }
  },
  "memory_candidates": [
    {
      "key": "preferred_areas",
      "value": "大学城南亭",
      "confidence": 0.86
    }
  ]
}
```

压缩不能丢失：

- 当前任务类型；
- 用户最新修正；
- 房源 ID 和 apartment_id；
- pending_action 和 confirmation_id；
- 最近推荐列表；
- 工具失败原因。

## 7. 记忆读取策略

每轮对话不加载全部长期画像，只加载与当前任务相关的部分。

```text
用户说“帮我继续找房”
  -> 读取找房相关偏好：区域、预算、付款方式、房型、通勤
  -> 不读取无关历史

用户问“我之前喜欢哪里”
  -> 读取长期画像和 audit log

用户发起预约
  -> 读取用户身份状态，但不让前端传入可信 user_id
```

## 8. 用户控制

前端应提供“我的偏好”入口：

- 查看系统记住了什么；
- 删除某条长期偏好；
- 修改预算/区域偏好；
- 关闭长期记忆；
- 将某次临时需求保存为长期偏好。

回复中可以轻提示：

```text
我可以记住你偏好大学城附近、安静、可月付。要保存为下次找房偏好吗？
```

## 9. 存储建议

MVP：

```text
Redis:
  session state
  pending action
  recent messages

MySQL/PostgreSQL:
  long_term_profile
  memory_audit_log
  memory_candidates
```

如果第一阶段只做独立演示，可以先用 SQLite 或本地 JSON 作为开发替身，但产品设计应以 Redis + 关系型数据库为准。

## 10. 风险控制

| 风险 | 控制 |
| --- | --- |
| 误记临时偏好 | 使用 scope 和 candidate 确认 |
| 敏感信息长期保存 | 禁止写入敏感字段，增加 redaction |
| 长期画像过时 | 加 updated_at、confidence decay |
| 用户不知道系统记住了什么 | 提供偏好查看/删除入口 |
| 压缩丢状态 | 结构化 state 优先于摘要 |
