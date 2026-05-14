# AptGuide 2.0 系统文档索引

系统文档说明 AptGuide 2.0 的产品边界、Agent 架构、工具契约、前端协议、记忆状态、RAG 方案和当前实现。

| 文档 | 内容 | 状态 |
| --- | --- | --- |
| [00-start-here](../00-start-here.md) | 阅读入口、当前状态、推荐路径和任务检索 | active |
| [01-product-requirements](../01-product-requirements.md) | 产品目标、用户场景、能力边界和需求范围 | existing |
| [02-agent-framework-architecture](../02-agent-framework-architecture.md) | Agent 框架、规划器、专家工作流和恢复机制 | existing |
| [enterprise-harness-architecture](./enterprise-harness-architecture.md) | 企业级 AptGuide 2.0 harness 总体架构；明确 RAG 是子模块 | active |
| [harness-method-selection](./harness-method-selection.md) | AptGuide 2.0 采用的 harness 方法选型；定义 Product Harness、Engineering Harness 和外部状态门禁 | active |
| [03-domain-boundary-and-interaction-policy](../03-domain-boundary-and-interaction-policy.md) | 领域边界、可答/不可答范围和交互策略 | existing |
| [04-tool-and-integration-contract](../04-tool-and-integration-contract.md) | 工具调用、旧项目接口接入和集成契约 | existing |
| [05-frontend-interaction-protocol](../05-frontend-interaction-protocol.md) | 前端交互协议、消息结构和动作协议 | existing |
| [07-memory-and-context-architecture](../07-memory-and-context-architecture.md) | 长短期记忆、上下文压缩和状态管理 | existing |
| [08-procedure-driven-agent-runtime](../08-procedure-driven-agent-runtime.md) | 流程驱动的 Agent 运行时和多专家协作 | existing |
| [09-human-handoff-and-operations](../09-human-handoff-and-operations.md) | 人工接管、运营闭环和异常升级策略 | existing |
| [14-api-and-schema-contract](../14-api-and-schema-contract.md) | API、cards、actions、SSE 和错误响应结构 | existing |
| [15-tool-registry-and-error-codes](../15-tool-registry-and-error-codes.md) | 工具注册表、字段映射和错误码 | existing |
| [enterprise-harness-architecture](./enterprise-harness-architecture.md) 中 "Tool Governance Layer" 章节 | 已实现的 harness.tools 包：contracts, registry, runtime, executors, trace | active |
| [16-memory-state-schema](../16-memory-state-schema.md) | 会话状态、任务状态、pending action 和长期记忆 | existing |
| [20-rag-retrieval-vector-mcp-evaluation-upgrade](../20-rag-retrieval-vector-mcp-evaluation-upgrade.md) | RAG、向量库、Query Rewrite、RAGAS 和 MCP 升级 | existing |
| [21-rag-final-implementation-scheme](../21-rag-final-implementation-scheme.md) | RAG 最终实施方案和关键设计 | existing |
| [27-current-implementation-guide](../27-current-implementation-guide.md) | 当前代码实现导览和实际能力说明 | active |
| `backend/src/aptguide2/system/readiness.py` | Live 依赖 readiness 检查：DependencyCheck、ReadinessReport、CLI 脚本 | active |
| `backend/scripts/check_live_dependencies.py` | Live 依赖检查 CLI：Milvus、embedding、lease 连通性验证 | active |
