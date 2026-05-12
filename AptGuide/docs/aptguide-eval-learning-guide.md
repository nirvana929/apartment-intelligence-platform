# AptGuide Eval 学习清单

**目标:** 按顺序系统学习 AptGuide 的 Agent 测评体系，先理解原理，再落到项目文件和测试证据。

**边界:** 本清单只用于学习和复盘，不要求跑测试，不要求修改业务代码。

## 1. 主系统链路

**读哪个文件**

- [AptGuide/src/aptguide/api/chat.py](../src/aptguide/api/chat.py)
- [AptGuide/src/aptguide/agent/graph.py](../src/aptguide/agent/graph.py)
- [AptGuide/src/aptguide/agent/state.py](../src/aptguide/agent/state.py)
- [AptGuide/src/aptguide/agent/nodes/intent.py](../src/aptguide/agent/nodes/intent.py)
- [AptGuide/src/aptguide/agent/nodes/slot.py](../src/aptguide/agent/nodes/slot.py)
- [AptGuide/src/aptguide/agent/nodes/ask.py](../src/aptguide/agent/nodes/ask.py)
- [AptGuide/src/aptguide/agent/nodes/kb_search.py](../src/aptguide/agent/nodes/kb_search.py)
- [AptGuide/src/aptguide/agent/nodes/room_search.py](../src/aptguide/agent/nodes/room_search.py)
- [AptGuide/src/aptguide/agent/nodes/rerank.py](../src/aptguide/agent/nodes/rerank.py)
- [AptGuide/src/aptguide/agent/nodes/confirm.py](../src/aptguide/agent/nodes/confirm.py)
- [AptGuide/src/aptguide/agent/nodes/tool.py](../src/aptguide/agent/nodes/tool.py)
- [AptGuide/src/aptguide/memory/session.py](../src/aptguide/memory/session.py)
- [AptGuide/src/aptguide/tools/client.py](../src/aptguide/tools/client.py)

**重点看什么**

- 用户消息从 `/api/chat` 进入后，会带着 `session_id`、`message` 和 header `X-User-Id` 进入 LangGraph。
- `intent` 决定进入 KB 问答、找房、预约创建、本人预约查询、本人租约查询还是兜底回复。
- `slots` 把自然语言里的预算、区域、标签、房间、预约时间抽成结构化参数。
- `memory` 保存跨轮次状态，尤其是 pending confirmation。
- `Milvus` 相关链路分两类：KB 规则问答和房源向量召回。
- `lease tool` 是 Java 后端工具接口，用于本人预约查询、本人租约查询和预约创建。
- `pending confirmation` 是写操作安全阀：预约创建先生成待确认操作，用户确认后才调用工具。

**读完要能回答什么**

- 用户说“预算 3000，天河，月付”会经过哪些节点？
- 用户说“押金什么时候退”为什么走 KB 检索而不是 lease tool？
- 用户说“帮我预约”为什么不能直接创建预约？
- 哪些路径是只读查询，哪些路径有写操作风险？
- `body user_id` 为什么不可信，系统实际使用哪个身份来源？

## 2. Anthropic Agent Eval 方法

**读哪个文件**

- [AptGuide/docs/anthropic-agent-eval-methodology.md](anthropic-agent-eval-methodology.md)
- [docs/agent-evaluation-resume-strategy.md](../../docs/agent-evaluation-resume-strategy.md)

**重点看什么**

- Agent eval 不能只看最终回复文本，要同时看 `task`、`trace`、`outcome`、`grader`。
- AptGuide 的 outcome 包括：是否真的创建预约、是否只返回本人数据、是否引用 KB source、是否没有泄露内部信息。
- Grader 分三类：确定性检查、LLM judge、人工复核。
- 写操作安全不能用 LLM judge 做生死线，应该用确定性 outcome 检查。

**读完要能回答什么**

- `task / trace / outcome / grader` 分别是什么？
- 为什么“Agent 回复预约成功”不等于预约真的成功？
- 哪些指标适合自动 grader，哪些必须人工复核？
- 求职展示为什么不必盲目重跑 800 条全量评测？

## 3. 已有测试资产总览

**读哪个文件**

- [AptGuide/docs/test-coverage-summary.md](test-coverage-summary.md)
- [docs/agent-evaluation-portfolio-report-2026-05-07.md](../../docs/agent-evaluation-portfolio-report-2026-05-07.md)

**重点看什么**

- AptGuide 已有 83 个 pytest 用例，覆盖 unit、contract、mock e2e 和 real AI e2e。
- 已有 300 条 dialog 数据集和 500 条 retrieval 数据集。
- 已执行抽样结果是 dialog 50 条和 retrieval 50 条，不是全量 800 条。
- 当前最强证据是 B1-B10 真实系统核心回归 10/10 通过。

**读完要能回答什么**

- 83 个 pytest 用例证明什么，不证明什么？
- 300 条 dialog 和 500 条 retrieval 是测试资产还是已全部执行结果？
- 为什么 B1-B10 比 mock e2e 更适合展示真实系统能力？

## 4. B1-B10 核心真实系统回归

**读哪个文件**

- [AptGuide/docs/test-report-2026-05-05.md](test-report-2026-05-05.md)
- [AptGuide/evals/datasets/regression_core.yaml](../evals/datasets/regression_core.yaml)

**重点看什么**

- B1 测 KB 押金 FAQ。
- B2 测自然语言找房和房源卡片。
- B3 测同 session 多轮补充条件。
- B4 测预约未确认前只生成 pending。
- B5 测确认后才创建预约。
- B6 测本人预约查询。
- B7 测本人租约查询。
- B8 测领域外天气问题兜底。
- B9 测内部数据库表名攻击拒答。
- B10 测 body `user_id` 伪造被忽略。

**读完要能回答什么**

- B1-B10 为什么是核心真实系统回归？
- 10/10 通过代表真实 LLM、Milvus、lease、MySQL 链路在代表样本上可用。
- 10/10 不代表长尾对话全覆盖，也不代表 appointment safety 8 条已经执行。
- B4 和 B5 为什么必须成对看？

## 5. Dialog 和 Retrieval 抽样结果

**读哪个文件**

- [AptGuide/docs/test-coverage-summary.md](test-coverage-summary.md)
- [docs/agent-evaluation-portfolio-report-2026-05-07.md](../../docs/agent-evaluation-portfolio-report-2026-05-07.md)

**重点看什么**

- Dialog 抽样 50 条，36 通过，14 失败，通过率 72%。
- Retrieval 抽样 50 条，50 通过，通过率 100%。
- Dialog 失败不能直接等同于系统差，可能来自数据覆盖不足、grader 过严或合理追问被误判。
- Retrieval 100% 说明抽样检索命中很好，但不代表所有对话任务都会成功，因为对话还依赖 intent、slot、memory、工具和回复生成。

**读完要能回答什么**

- 为什么 retrieval 100% 和 dialog 72% 可以同时成立？
- 哪些 dialog 失败应该先补测试数据，而不是改 Agent？
- 什么是 grader 过严？
- 什么是数据覆盖不足？

## 6. 预约安全专项

**读哪个文件**

- [AptGuide/evals/datasets/appointment_safety_cases.yaml](../evals/datasets/appointment_safety_cases.yaml)
- [AptGuide/src/aptguide/agent/nodes/confirm.py](../src/aptguide/agent/nodes/confirm.py)
- [AptGuide/src/aptguide/agent/nodes/tool.py](../src/aptguide/agent/nodes/tool.py)
- [AptGuide/src/aptguide/memory/session.py](../src/aptguide/memory/session.py)

**重点看什么**

- AS01 未确认前不得创建预约。
- AS02 确认后只创建一次。
- AS03 取消后再确认不得创建。
- AS04 重复确认不得重复创建。
- AS05 房源不存在不得创建。
- AS06 工具失败不得声称成功。
- AS07 body `user_id` 伪造无效。
- AS08 跨 session pending 不得被确认。

**读完要能回答什么**

- 为什么预约是最高风险路径？
- 为什么预约安全必须单独统计，不能混进普通通过率？
- 未确认前创建、重复确认、取消后确认、跨 session pending、body user_id 伪造分别会造成什么业务风险？
- 哪些预约安全用例目前只是设计完成，不能算作已通过？

## 7. 失败归因框架

**读哪个文件**

- [aptguide-system-failure-investigation-guide.md](aptguide-system-failure-investigation-guide.md)
- [AptGuide/docs/anthropic-agent-eval-methodology.md](anthropic-agent-eval-methodology.md)

**重点看什么**

- 先区分 `harness failed`、`grader 过严`、`数据覆盖不足` 和 `真正系统链路错误`。
- 本阶段重点只研究真正系统链路错误，不研究 grader 误杀。
- 系统链路错误按节点归因：intent、slot、memory、Milvus、lease tool、pending confirmation、user_id 隔离、工具失败处理。

**读完要能回答什么**

- 一个失败样本应该如何记录 expected path 和 actual path？
- 如何定位 failure node？
- 怎么证明 root cause 是系统链路问题，而不是 grader 问题？
- B1-B10、dialog 失败、appointment safety 应该分别优先看哪些节点？
