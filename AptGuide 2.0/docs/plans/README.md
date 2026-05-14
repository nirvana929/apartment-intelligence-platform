# AptGuide 2.0 计划文档索引

计划文档面向 Agent 执行，描述开发路线、实施任务、数据补充、RAG 实现、导入流程和验收准备。

| 文档 | 内容 | 状态 |
| --- | --- | --- |
| [11-feasibility-and-development-plan](../11-feasibility-and-development-plan.md) | 可行性分析和开发计划 | existing |
| [12-implementation-task-plan](../12-implementation-task-plan.md) | 具体实施任务和验收顺序 | active |
| [18-implementation-readiness-checklist](../18-implementation-readiness-checklist.md) | 进入编码前和阶段退出前的检查清单 | existing |
| [22-rag-mvp-data-and-implementation-plan](../22-rag-mvp-data-and-implementation-plan.md) | RAG MVP 数据准备和实施计划 | existing |
| [23-rag-data-supplement-agent-plan](../23-rag-data-supplement-agent-plan.md) | RAG 数据补充 Agent 执行计划 | existing |
| [24-rag-implementation-agent-plan](../24-rag-implementation-agent-plan.md) | RAG 实施 Agent 执行计划 | existing |
| [26-wechat-local-mysql-import-agent-plan](../26-wechat-local-mysql-import-agent-plan.md) | 微信租房数据本地 MySQL 导入计划 | existing |
| [2026-05-12-enterprise-aptguide-harness-plan](./2026-05-12-enterprise-aptguide-harness-plan.md) | 企业级 AptGuide 2.0 harness 架构和实施计划；RAG 是其中一个模块 | active |
| [2026-05-12-enterprise-aptguide-harness-agent-execution-plan](./2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md) | 可交给其他 agent 执行的企业级 AptGuide harness 详细任务计划 | active |
| [2026-05-13-enterprise-aptguide-harness-agent-handoff-plan](./2026-05-13-enterprise-aptguide-harness-agent-handoff-plan.md) | 新上下文或其他 agent 接手执行 harness foundation 的总控 handoff plan；连接 feature/sprint/progress 状态 | active |
| [2026-05-13-enterprise-aptguide-tool-registry-adapter-governance-agent-plan](./2026-05-13-enterprise-aptguide-tool-registry-adapter-governance-agent-plan.md) | Tool Registry、工具执行治理、adapter wrapper、错误 envelope 和 trace-safe summaries；已实施完成 | completed |
| [2026-05-14-enterprise-rag-v2-hybrid-retrieval-governed-rerank-agent-plan](./2026-05-14-enterprise-rag-v2-hybrid-retrieval-governed-rerank-agent-plan.md) | Enterprise RAG v2：字符匹配治理、hybrid retrieval、governed rerank、lease validation 和 eval gates 执行计划 | completed |
| [2026-05-14-enterprise-harness-memory-appointment-handoff-correction-agent-plan](./2026-05-14-enterprise-harness-memory-appointment-handoff-correction-agent-plan.md) | 修正剩余 harness 工作：Memory pending_action、预约确认写流程、只读预约查询、工具失败自动转人工 | completed |
| [2026-05-14-aptguide2-system-integration-production-hardening-agent-plan](./2026-05-14-aptguide2-system-integration-production-hardening-agent-plan.md) | 系统集成与生产化验收：live eval、依赖 readiness、API 结构化确认协议、system smoke | completed |
| [2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan](./2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md) | 系统功能完善与主线统一：harness 成为唯一产品运行时，旧 RAG 仅保留不接任何接口，补齐预约/租约/记忆/转人工/API 响应/system smoke；323 tests passed、ruff clean | completed |
| [2026-05-14-aptguide2-standalone-productization-agent-plan](./2026-05-14-aptguide2-standalone-productization-agent-plan.md) | AptGuide 2.0 独立产品化：独立前端、直接 `/chat`、Redis + MySQL 记忆、身份解析、持久化 pending action、人工接管 operator console、readiness 和文档同步；365+2 tests passed | completed |
| [2026-05-14-aptguide2-risk-aware-query-understanding-guardrail-agent-plan](./2026-05-14-aptguide2-risk-aware-query-understanding-guardrail-agent-plan.md) | Risk-aware Query Understanding：规则信号 + 结构化语义分类 + 策略矩阵 + response_mode 路由，重点控制高风险召回和 false block rate；389 tests passed、risk eval 100% | completed |
