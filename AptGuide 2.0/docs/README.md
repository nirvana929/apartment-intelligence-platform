# AptGuide 2.0 文档中心

AptGuide 2.0 是面向租客找房场景的新一代 Agent 应用。它不是旧版 AptGuide 的简单补丁，而是围绕独立前后端、领域边界、RAG 检索、工具注册、记忆状态和评测体系重新设计的版本。

本目录采用四类索引组织现有文档，原编号文档暂不移动。

## 当前状态

当前代码已实现 **Harness Foundation + Tool Governance + RAG v2 + System Feature Completion + Standalone Productization** 阶段。`aptguide2.harness` 是唯一产品运行时，`/chat` 默认进入 `AptGuideHarness`；旧 RAG MVP 已断开。预约创建和取消均采用两轮 pending-action 确认流程，工具连续失败自动触发转人工。Auth 支持 dev 模式和 lease_token 模式。Redis + MySQL 持久化上下文、记忆、pending action。Operator API 支持工单管理。Vue 3 前端包含聊天 UI 和运营控制台。**365 backend + 2 frontend tests all passed。**

下一阶段：staging 部署、RAG 检索质量优化（KB hit@3=48.6%→90%，Room hit@5=40%→85%）、平台集成。想理解实际代码现状，先读 [27-current-implementation-guide.md](./27-current-implementation-guide.md)、[plans/current-plan.md](./plans/current-plan.md) 和 [plans/next-steps.md](./plans/next-steps.md)。

## 推荐阅读顺序

1. [00-start-here.md](./00-start-here.md)
2. [27-current-implementation-guide.md](./27-current-implementation-guide.md)
3. [01-product-requirements.md](./01-product-requirements.md)
4. [02-agent-framework-architecture.md](./02-agent-framework-architecture.md)
5. [system/enterprise-harness-architecture.md](./system/enterprise-harness-architecture.md)
6. [system/harness-method-selection.md](./system/harness-method-selection.md)
7. [04-tool-and-integration-contract.md](./04-tool-and-integration-contract.md)
8. [12-implementation-task-plan.md](./12-implementation-task-plan.md)
9. [plans/2026-05-12-enterprise-aptguide-harness-plan.md](./plans/2026-05-12-enterprise-aptguide-harness-plan.md)
10. [plans/2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md](./plans/2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md)
11. [plans/2026-05-13-enterprise-aptguide-harness-agent-handoff-plan.md](./plans/2026-05-13-enterprise-aptguide-harness-agent-handoff-plan.md)
12. [plans/2026-05-13-enterprise-aptguide-tool-registry-adapter-governance-agent-plan.md](./plans/2026-05-13-enterprise-aptguide-tool-registry-adapter-governance-agent-plan.md)
13. [plans/2026-05-14-enterprise-harness-memory-appointment-handoff-correction-agent-plan.md](./plans/2026-05-14-enterprise-harness-memory-appointment-handoff-correction-agent-plan.md)
14. [plans/2026-05-14-aptguide2-system-integration-production-hardening-agent-plan.md](./plans/2026-05-14-aptguide2-system-integration-production-hardening-agent-plan.md)
15. [plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md](./plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md)
16. [plans/2026-05-14-aptguide2-standalone-productization-agent-plan.md](./plans/2026-05-14-aptguide2-standalone-productization-agent-plan.md)
17. [20-rag-retrieval-vector-mcp-evaluation-upgrade.md](./20-rag-retrieval-vector-mcp-evaluation-upgrade.md)
18. [28-rag-mvp-achievement-report.md](./28-rag-mvp-achievement-report.md)
19. [outcomes/rag-learning-review.md](./outcomes/rag-learning-review.md)
20. [outcomes/system-integration-live-eval-review.md](./outcomes/system-integration-live-eval-review.md)

## 文档分类

| 类型 | 用途 | 入口 |
| --- | --- | --- |
| 系统文档 | 产品边界、Agent 架构、工具契约、前端协议、记忆状态、RAG 方案 | [system](./system/README.md) |
| 计划文档 | 可行性、实施计划、Agent 执行计划、数据导入计划、准备清单 | [plans](./plans/README.md) |
| 测试文档 | Eval 方法、评测路线、提示词与评测契约、可观测性 | [tests](./tests/README.md) |
| 成果文档 | 产品技术评审、RAG 方案取舍、MVP 成果、面试复盘素材 | [outcomes](./outcomes/README.md) |

## 与旧版 AptGuide 的关系

- 旧版 AptGuide 文档入口：[../../AptGuide/docs/README.md](../../AptGuide/docs/README.md)
- 旧版可复用：业务知识、`lease` 工具接口、Milvus 设计、评测失败经验、H5 集成链路。
- 2.0 重点新增：领域边界 Router、任务规划、专家工作流、结构化工具注册、记忆状态、trace/eval 体系。

## 维护规则

- 新增正式文档优先写入 `docs/system`、`docs/plans`、`docs/tests` 或 `docs/outcomes`。
- 已有编号文档先保留在 `docs/` 根部，由四类索引引用。
- 更新新增文档后，同步更新对应分类目录的 `README.md`。
