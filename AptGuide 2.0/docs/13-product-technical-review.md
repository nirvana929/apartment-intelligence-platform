# 13 · Product Technical Review

> 相关文档：[README](../README.md)、[Start Here](00-start-here.md)、[产品需求](01-product-requirements.md)、[Agent 架构](02-agent-framework-architecture.md)、[API Schema](14-api-and-schema-contract.md)、[工具注册与错误码](15-tool-registry-and-error-codes.md)、[记忆状态 Schema](16-memory-state-schema.md)、[实施准备清单](18-implementation-readiness-checklist.md)。

## 1. 评审结论

`AptGuide 2.0` 的项目设计整体合理，适合继续推进。

它不是把旧版 `AptGuide` 继续加节点，而是把租客侧 AI 助手重新定义为一个任务流程驱动的租房客服 Agent。这个方向比旧版固定 `intent -> slot -> search/tool/confirm -> reply` 更合理，因为真实租房对话需要处理模糊需求、空搜索恢复、长期偏好、写操作确认、工具失败、人工接管和运营复盘。

建议保留当前总体方向，但第一版必须严格收敛到“可演示闭环”，不要一次性追求完整客服平台。

## 2. 产品合理性

合理点：

- 产品边界清楚，只服务租房域，避免变成通用 LLM 入口；
- 用户场景真实，包括找房、规则问答、预约、我的预约/租约、记忆、人工接管；
- 交互形态正确，房源、确认、记忆、人工接管都以结构化 card / action 表达；
- 写操作安全意识足够，预约必须有 pending action、`confirmation_id`、过期拦截和后端成功状态；
- 长期记忆采用 candidate + 用户确认，比自动写画像更稳；
- 人工接管被设计成产品能力，而不是失败时的 fallback 文案。

需要收敛的点：

- [01-product-requirements.md](01-product-requirements.md) 里的核心能力都标为 MVP，实际实现时应分层：第一版跑通找房到预约闭环，长期画像、人工接管、运营看板只做最小可用；
- 租房规则问答如果 KB 不完整，应该返回“没有可靠来源 + 下一步建议”，不能硬答；
- 人工接管第一版可以先做日志/摘要和 AI paused，不必一开始做完整工单系统；
- “长期记忆”第一版只保存低敏偏好，不保存身份、合同、电话等信息。

## 3. 技术合理性

合理点：

- [02-agent-framework-architecture.md](02-agent-framework-architecture.md) 把 Conversation Manager、Boundary Router、Phase Router、Task Planner、Tool Registry、Response Composer、Trace Logger 拆开，职责清楚；
- [08-procedure-driven-agent-runtime.md](08-procedure-driven-agent-runtime.md) 把“自由 Agent”压到受控 Procedure 内，写操作仍然走确定性 workflow；
- [04-tool-and-integration-contract.md](04-tool-and-integration-contract.md) 坚持通过受控工具接口访问 `lease`，不直接查 MySQL，这是正确边界；
- [07-memory-and-context-architecture.md](07-memory-and-context-architecture.md) 区分 recent messages、rolling summary、active task state、long-term profile，能降低长对话状态丢失风险；
- [10-trace-eval-and-observability.md](10-trace-eval-and-observability.md) 不暴露原始思维链，但记录可审计事件，符合调试、运营和安全要求；
- [12-implementation-task-plan.md](12-implementation-task-plan.md) 的开发顺序正确：schema、trace、boundary、memory state、tool registry、room search、appointment workflow。

技术上最重要的判断是：LangGraph 可以继续用，但只能作为可观测状态编排层，不应该复用旧版单一 intent/slot/reply 图。

## 4. 与当前仓库匹配度

当前仓库已经具备实现 AptGuide 2.0 的基础：

- 旧版 Agent 已存在：[AptGuide/src/aptguide/agent/graph.py](../../AptGuide/src/aptguide/agent/graph.py)、[AptGuide/src/aptguide/agent/state.py](../../AptGuide/src/aptguide/agent/state.py)；
- 旧版 lease 工具客户端已存在：[AptGuide/src/aptguide/tools/client.py](../../AptGuide/src/aptguide/tools/client.py)；
- `lease/web-app` 已有内部 AI 工具入口：[AiToolController.java](../../lease/web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiToolController.java)；
- H5 到 AptGuide 的入口已存在：[AiController.java](../../lease/web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiController.java)；
- 平台 README 已说明 `/internal/ai/tools/*`、Milvus、Redis、H5 和 AptGuide 的关系：[platform README](../../README.md)。

因此 “AptGuide 2.0 独立前后端 + 调用真实 lease 工具 + Milvus/KB” 的方向是可落地的。

## 5. 主要技术风险

| 风险 | 影响 | 建议 |
| --- | --- | --- |
| 工具 schema 未对齐 | Python adapter 调用 Java 工具失败或字段为空 | 先补 [04-tool-and-integration-contract.md](04-tool-and-integration-contract.md) 中的 API 字段、alias、错误码 |
| 预约接口校验不足 | 可能创建不完整预约 | `appointment.create` 必须校验 apartment、room、time、user 和 confirmation |
| 房源搜索能力不足 | “大学城南亭”“安静”“可月付”推荐质量不稳定 | AptGuide 2.0 先做 area.normalize + vector recall + lease filter 混合检索 |
| 前端协议和旧 H5 response 不一致 | 卡片/action/trace 无法稳定渲染 | 以 [05-frontend-interaction-protocol.md](05-frontend-interaction-protocol.md) 为新契约，旧字段做兼容层 |
| 记忆写入过早自动化 | 用户信任和隐私风险 | 第一版所有长期画像新增都走 memory candidate + 用户确认 |
| Eval 只停留在文档 | 改 prompt 或流程时容易回归 | 把 [06-evaluation-roadmap-and-upgrade-assessment.md](06-evaluation-roadmap-and-upgrade-assessment.md) 样例落到 YAML + pytest |
| Trace 字段过少 | 工具失败、转人工和推荐错误难复盘 | 第一阶段就记录 request_id、trace_id、phase、domain_category、tool、latency、error_code |

## 6. 第一版推荐范围

第一版必须完成：

```text
独立前端聊天
Agent API
Boundary / Capability
ConversationFrame
Tool Registry
LeaseToolAdapter health + room.search
RoomSearch Procedure
Appointment confirmation workflow
Trace Logger
核心 eval cases
```

第一版只做最小能力：

```text
长期画像：candidate + accept/reject/delete
人工接管：handoff_request + summary + ai_paused
上下文压缩：结构化 state 优先，summary 简化
运营分析：trace log 和 knowledge gap log
```

第一版不建议做：

```text
完整运营后台
多自由 Agent 互相对话
自动取消/退款/合同争议裁定
长期记忆无确认自动写入
复杂多渠道接入
```

## 7. 文档链接关系

当前 README 已作为总入口：

- [README](../README.md) 负责总览、评审结论和 Claude 检索入口；
- [00-start-here.md](00-start-here.md) 负责阅读顺序和按任务检索；
- 每个子文档顶部都有“相关文档”链接，方便模型沿产品、架构、契约、运行时、评测和实施路径读取。

已补齐以下 source-of-truth 文档：

1. [14-api-and-schema-contract.md](14-api-and-schema-contract.md)：`/api/chat`、SSE、action request、response schema；
2. [15-tool-registry-and-error-codes.md](15-tool-registry-and-error-codes.md)：每个工具的 input/output schema、权限、错误码；
3. [16-memory-state-schema.md](16-memory-state-schema.md)：Redis key、long-term profile、candidate、audit log；
4. [17-prompt-and-eval-contract.md](17-prompt-and-eval-contract.md)：Boundary、Planner、Recovery、Response Composer prompt 输出契约和 eval case schema；
5. [18-implementation-readiness-checklist.md](18-implementation-readiness-checklist.md)：进入编码和每个阶段退出前的硬检查。

后续如果继续增强文档，优先把 [17-prompt-and-eval-contract.md](17-prompt-and-eval-contract.md) 中的 eval 样例落成真实 `evals/cases/*.yaml` 文件。
