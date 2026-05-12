# 09 · Human Handoff And Operations

> 相关文档：[产品需求](01-product-requirements.md)、[领域边界策略](03-domain-boundary-and-interaction-policy.md)、[前端交互协议](05-frontend-interaction-protocol.md)、[运行时设计](08-procedure-driven-agent-runtime.md)、[Trace/Eval](10-trace-eval-and-observability.md)、[实施任务](12-implementation-task-plan.md)。

## 1. 设计目标

`AptGuide 2.0` 不能假设 AI 能解决所有租房问题。真实客服场景必须支持人工接管、运营复盘和知识库持续改进。

目标：

- 高风险、低置信度、强情绪和工具异常场景可以转人工；
- 人工接管时不丢上下文；
- 人工回复可以沉淀为后续知识库和流程改进材料；
- 运营人员能看到 AI 解决率、失败原因和知识缺口。

## 2. Handoff 状态

```text
ai_active
handoff_suggested
handoff_requested
human_active
ai_paused
handoff_resolved
ai_resumed
```

状态说明：

| 状态 | 说明 |
| --- | --- |
| `ai_active` | AI 正常处理 |
| `handoff_suggested` | AI 建议转人工，但等待用户确认 |
| `handoff_requested` | 用户或系统已发起转人工 |
| `human_active` | 人工客服接管 |
| `ai_paused` | AI 只记录，不自动回复 |
| `handoff_resolved` | 人工处理完成 |
| `ai_resumed` | 新会话或人工释放后恢复 AI |

## 3. 触发条件

### 3.1 用户主动要求

```text
转人工
我要找真人
客服在吗
这个我要投诉
```

处理：

```text
trigger_handoff
  -> summarize_context
  -> pause_ai_auto_reply
```

### 3.2 工具失败

触发条件：

- 同一工具连续失败；
- appointment.create 超时；
- lease 后端不可用；
- user_id 缺失导致个人数据无法查询；
- 房源详情和搜索结果不一致。

处理：

```text
explain_failure
  -> retry_or_alternative
  -> if still failed, handoff
```

### 3.3 高风险业务

必须转人工或建议人工：

- 押金争议；
- 合同纠纷；
- 投诉；
- 退款/赔偿；
- 身份认证异常；
- 用户要求查看他人预约/租约；
- 房源规则缺少可靠来源但用户要求承诺。

### 3.4 用户情绪

触发信号：

- 明确辱骂；
- 重复说“你听不懂”；
- 多轮循环；
- 连续拒绝推荐；
- 多次工具失败后用户抱怨。

MVP 可先用规则识别，后续加入情绪分类。

## 4. Handoff Summary

人工接管必须携带摘要。

```json
{
  "handoff_id": "h-001",
  "session_id": "s-001",
  "user_id": "u-001",
  "reason": "appointment_tool_failed_twice",
  "priority": "medium",
  "user_goal": "预约大学城南亭附近房源明天下午看房",
  "known_preferences": {
    "area": "大学城南亭",
    "budget": "1500-2200",
    "preferences": ["安静", "可月付"]
  },
  "last_recommendations": [
    {
      "room_id": 3001,
      "apartment_id": 101,
      "title": "大学城南亭寓 301"
    }
  ],
  "failed_tools": [
    {
      "tool": "appointment.create",
      "error_code": "TIMEOUT",
      "attempts": 2
    }
  ],
  "recent_summary": "用户先找大学城南亭附近房源，预算1500左右，系统放宽预算后推荐3个房源。用户选择第一个并希望明天下午看房，但预约工具连续超时。",
  "suggested_next_step": "人工确认房源可预约时间，并协助创建预约。"
}
```

## 5. AI 暂停和恢复

人工接管后：

- AI 不再自动回复用户消息；
- 用户消息仍写入 recent_messages；
- 人工回复写入 conversation history；
- AI 可继续做后台摘要和标签，但不能发给用户；
- 人工关闭工单或用户开启新问题后，AI 才可恢复。

恢复条件：

```text
人工标记 resolved
用户开启新会话
人工发送恢复命令
超过配置时间后进入新问题流程
```

## 6. 运营后台能力

运营后台不要求 MVP 立即完整实现，但架构应预留数据。

建议看板：

| 看板 | 指标 |
| --- | --- |
| AI 解决率 | 自动解决、转人工、失败 |
| 找房效果 | 搜索次数、空结果率、放宽策略成功率 |
| 预约转化 | 推荐到预约、确认到成功、失败原因 |
| 知识库缺口 | 低置信度问题、无来源问题 |
| 用户偏好 | 热门区域、预算分布、付款偏好 |
| 质量风险 | stale action、越权请求、工具错误 |

## 7. 与 AptInsight 的闭环

`AptGuide 2.0` 产生的行为数据可以进入运营分析。

```text
AptGuide conversation trace
  -> lease records AI source / room recommendation / appointment result
  -> AptInsight analyzes conversion, failure, demand distribution
  -> operations improves room tags, KB, pricing, service policies
  -> Milvus / KB resync
  -> AptGuide recommendation improves
```

## 8. 知识库改进流程

当 AI 低置信度或转人工时，生成知识缺口记录。

```json
{
  "gap_id": "kg-001",
  "question": "大学城南亭寓能不能养大型犬？",
  "domain": "rental_policy",
  "source": "handoff",
  "current_answer": "没有可靠规则来源",
  "needed_source": "房源规则或门店政策",
  "frequency": 12
}
```

运营可将其转为：

- FAQ；
- 房源规则字段；
- 门店政策；
- 工具接口补充；
- 标签体系更新。

## 9. 风险边界

AI 不应承诺：

- 法律意见；
- 押金最终处理结果；
- 合同争议裁定；
- 未经后端确认的房源可租状态；
- 未经工具确认的预约成功；
- 非本人租约或预约信息。

这些问题应转人工或给出保守说明。

## 10. MVP 建议

Phase 1 可以先实现：

- 用户主动转人工；
- 工具连续失败转人工；
- handoff summary；
- AI paused 状态；
- trace 中记录 handoff；
- 后台日志而不是完整运营 UI。

后续再实现：

- 情绪识别；
- 工单系统集成；
- 运营看板；
- 知识缺口自动归类；
- 人工回复反哺知识库。
