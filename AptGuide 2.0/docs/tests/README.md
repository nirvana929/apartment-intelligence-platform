# AptGuide 2.0 测试文档索引

测试文档记录评测路线、Agent Eval 方法、提示词契约、trace/eval/可观测性和实现准备检查。

| 文档 | 内容 | 状态 |
| --- | --- | --- |
| [06-evaluation-roadmap-and-upgrade-assessment](../06-evaluation-roadmap-and-upgrade-assessment.md) | 评测路线、升级评估和旧文档迁移判断 | existing |
| [10-trace-eval-and-observability](../10-trace-eval-and-observability.md) | Trace、审计、可观测性和评测体系 | existing |
| [17-prompt-and-eval-contract](../17-prompt-and-eval-contract.md) | Prompt 输出约束、Eval 回归门槛和验收要求 | existing |
| [18-implementation-readiness-checklist](../18-implementation-readiness-checklist.md) | 实施准备和阶段验收检查 | existing |
| [19-anthropic-agent-eval-methodology](../19-anthropic-agent-eval-methodology.md) | Agent Eval 方法论 | existing |
| [20-rag-retrieval-vector-mcp-evaluation-upgrade](../20-rag-retrieval-vector-mcp-evaluation-upgrade.md) | RAG 检索评估、RAGAS 和 MCP 相关评测设计 | existing |
| [rag-v2-evaluation-gates](./rag-v2-evaluation-gates.md) | RAG v2 hybrid retrieval、governed rerank、lease validation 和高风险 source gate 的验收门槛 | active |
| [system-smoke-checklist](./system-smoke-checklist.md) | AptGuide 2.0 live dependency、harness mainline、RAG v2 内部模块和 `/chat` API smoke 验收命令 | active |
| [evaluation-report](../../reports/evaluation-report.md) | 全阶段评测报告：Harness、Tool Registry、RAG v2、Harness Correction、System Integration、System Feature Completion 验证记录；当前 blocker 为 RAG 检索质量 | generated |
| [live-dependency-readiness-report](../../reports/live-dependency-readiness-report.md) | Live 依赖 readiness 检查结果：Milvus、embedding、lease | generated |
| [rag-v2-live-evaluation-report](../../reports/rag-v2-live-evaluation-report.md) | RAG v2 live eval 真实运行结果：55 cases、retrieval quality 分析 | generated |
