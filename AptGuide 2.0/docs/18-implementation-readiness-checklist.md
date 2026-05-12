# 18 · Implementation Readiness Checklist

> 相关文档：[Start Here](00-start-here.md)、[产品技术评审](13-product-technical-review.md)、[API Schema](14-api-and-schema-contract.md)、[工具注册与错误码](15-tool-registry-and-error-codes.md)、[记忆状态 Schema](16-memory-state-schema.md)、[Prompt/Eval 契约](17-prompt-and-eval-contract.md)、[实施任务](12-implementation-task-plan.md)。

## 1. 目标

本文档用于判断 AptGuide 2.0 是否已经准备好进入编码。它不是功能愿景，而是开工前的硬检查清单。

## 2. 开工前必须明确

| 项 | 状态要求 | 对应文档 |
| --- | --- | --- |
| 产品范围 | 明确第一版只做租房闭环，不做通用 AI | [01-product-requirements.md](01-product-requirements.md) |
| 架构边界 | Agent、Procedure、Tool、Memory、Trace 分层清楚 | [02-agent-framework-architecture.md](02-agent-framework-architecture.md) |
| API schema | `/api/chat`、SSE、cards、actions、pending_action 固定 | [14-api-and-schema-contract.md](14-api-and-schema-contract.md) |
| 工具 schema | MVP 工具 input/output、权限、错误码固定 | [15-tool-registry-and-error-codes.md](15-tool-registry-and-error-codes.md) |
| 状态 schema | ConversationFrame、PendingAction、MemoryCandidate 固定 | [16-memory-state-schema.md](16-memory-state-schema.md) |
| 安全策略 | 写操作、个人数据、长期记忆、越权拒绝规则明确 | [03-domain-boundary-and-interaction-policy.md](03-domain-boundary-and-interaction-policy.md) |
| Eval 门槛 | 每个 phase 有可跑用例 | [17-prompt-and-eval-contract.md](17-prompt-and-eval-contract.md) |

## 3. Phase 0 Exit Criteria

Phase 0 完成后，必须满足：

- Pydantic schema 已覆盖 chat、cards、actions、tools、memory、trace；
- FastAPI `/health` 可用；
- `/api/chat` 返回固定 envelope；
- response 必含 `request_id`、`trace_id`、`phase`、`domain_category`；
- Tool Registry 至少注册 `lease.health`；
- Trace Logger 能记录 `message_received`、`boundary_classified`、`response_composed`；
- boundary eval 有最小 YAML 样例；
- README 和 Start Here 能导航到所有 source-of-truth 文档。

## 4. Phase 1 Exit Criteria

Boundary、Capability、Trace 完成后：

- “你能做什么”走固定能力说明；
- 天气/代码生成拒答；
- 越权查询拒绝；
- 租房域内问题不误拒；
- 不调用任何业务写工具；
- trace 中可看到 boundary result；
- boundary eval 通过。

## 5. Phase 2 Exit Criteria

Memory Center 完成后：

- 短期记忆能回答姓名和当前找房目标；
- `active_task_state` 保存 slots；
- “预算我都接受”会清除 `max_rent`；
- 长期偏好只生成 candidate；
- 用户确认后才写 long-term profile；
- 用户可以删除偏好；
- 压缩后不丢 pending action。

## 6. Phase 3 Exit Criteria

Tool Registry 和 Lease Adapter 完成后：

- `/health/deps` 能检查 lease；
- `room.search` 能调用真实 `/internal/ai/tools/room/search`；
- adapter 集中处理 snake_case 到 camelCase；
- 工具调用有 timeout；
- 工具失败返回标准错误码；
- trace 记录 tool name、latency、error_code。

## 7. Phase 4 Exit Criteria

Room Search Procedure 完成后：

- 能识别大学城南亭这类地标；
- hard filter 和 soft preference 分开；
- exact search 空结果后能放宽；
- 用户清除预算后不带旧预算；
- 卡片和文本一致；
- 不编造房源；
- room_search eval 通过。

## 8. Phase 5 Exit Criteria

Appointment Workflow 完成后：

- `resolve_room` 不成功时不创建确认卡；
- confirmation card 包含 `confirmation_id`；
- 无 `confirmation_id` 不执行写操作；
- 旧确认、重复确认、过期确认被拒绝；
- `appointment.create` 失败不显示成功；
- 连续失败能触发 handoff 建议；
- appointment_safety eval 通过。

## 9. Phase 6 Exit Criteria

Knowledge 和 User Data 完成后：

- `kb.search` 有来源；
- 低置信度不强答；
- 个人预约/租约只能查本人；
- 未登录时引导登录；
- 查询失败不泄露内部错误；
- knowledge 和 user_data eval 通过。

## 10. Phase 7 Exit Criteria

Handoff 和 Operations 完成后：

- 用户说“转人工”进入 handoff；
- AI paused 后不自动回复；
- handoff summary 包含目标、偏好、失败原因、最近推荐；
- 高风险合同/押金争议不由 AI 裁定；
- 知识缺口可记录；
- handoff eval 通过。

## 11. Phase 8 Exit Criteria

Frontend 完成后：

- 独立前端能展示 text、room card、confirmation card、memory card、handoff card；
- action 请求不依赖纯文本模拟；
- 旧按钮禁用；
- SSE 状态显示不干扰最终 response；
- 开发环境 trace panel 可查看 request_id / trace_id；
- 移动端布局可用。

## 12. 不允许进入下一阶段的情况

出现以下情况必须停下修文档或修实现：

- schema 字段名在两份文档中冲突；
- 工具没有标准错误码；
- 写操作可以被纯文本确认绕过；
- 前端 action 无法映射到后端 workflow；
- `user_id` 由前端直接传入并被信任；
- 卡片和文本描述不同房源；
- eval 只有自然语言描述，没有可运行样例；
- trace 无法复盘工具失败。

## 13. Mock 零引入门禁

开发开始前、每次合并前、真实演示或产品交付前，都必须执行 mock 零引入检查。

禁止出现：

- 产品启动路径中的 `MockToolClient`；
- 产品配置中的 `mock backend` 或 `APTGUIDE_BACKEND_MODE=mock`；
- 产品链路使用的 mock 房源、mock 预约、mock 租约数据；
- 真实后端失败后自动回退到 mock 成功响应的 fallback；
- 旧版 `AptGuide/src/aptguide/tools/mock.py`、`AptGuide/src/aptguide/knowledge/mock/` 这类会被运行时导入的数据源。

测试材料要求：

- 使用真实测试环境、种子数据、契约样例或录制的只读响应样本；
- 不实现业务成功逻辑；
- 不被应用启动、工具注册表或前端运行时代码导入。

最终验收命令建议：

```bash
rg -n "MockToolClient|BACKEND_MODE=mock|backend.*mock|knowledge/mock|tools/mock" AptGuide\\ 2.0/backend AptGuide\\ 2.0/frontend
curl http://127.0.0.1:8100/health/deps
uv run pytest tests/e2e -q
```

第一条命令在产品代码路径中应无输出；后两条必须证明真实依赖和真实端到端链路可用。
