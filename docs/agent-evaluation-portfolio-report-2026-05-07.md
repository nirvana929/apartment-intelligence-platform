# Agent Evaluation Portfolio Report

**日期:** 2026-05-07
**用途:** 简历、面试讲解和项目复盘材料
**范围:** AptGuide、AptInsight、AptGuide 2.0 eval-first 设计

---

## 1. 总结

本项目不是只做租房 CRUD 或普通聊天机器人，而是在完整公寓租赁业务链路上构建了两个不同角色的 AI Agent：

- `AptGuide`：面向租客，负责自然语言找房、RAG 租房规则问答、预约确认和本人预约 / 租约查询。
- `AptInsight`：面向运营人员，负责自然语言经营分析、Text-to-SQL、图表和总结。

评估策略参考 Anthropic Agent Eval 思路，把 Agent 测试拆成：

```text
task        用户要完成的真实任务
trace       Agent 执行路径和工具调用
outcome     最终业务状态或查询结果
grader      确定性检查 / LLM judge / 人工复核
```

求职展示不追求重跑所有长尾用例，而是保留高价值证据：

- AptGuide：真实系统核心回归 B1-B10 10/10 通过。
- AptGuide：构建 800 条 Agent Eval 数据集，并完成 100 条抽样评测。
- AptGuide：增量固化 B1-B10，并设计 8 条预约安全专项。
- AptInsight：40 条正式 Text-to-SQL harness，35 条通过，通过率 87.5%。
- AptInsight：安全用例 6/6 通过，SQL Guard 单测 20/20 通过。
- AptGuide 2.0：形成 eval-first 的下一代 Agent 架构与评估设计。

## 2. AptGuide 评估结果

### 2.1 已有测试资产

| 类型 | 数量 / 状态 | 说明 |
| --- | ---: | --- |
| pytest 用例 | 83 个已收集 | 单元、契约、mock e2e、真实 AI 功能 e2e |
| 核心真实系统样本 | B1-B10，10/10 通过 | 真 LLM + Milvus + lease + MySQL |
| Agent 对话数据集 | 300 条 | `AptGuide/evals/datasets/dialog_cases.yaml` |
| Agent 检索数据集 | 500 条 | `AptGuide/evals/datasets/retrieval_cases.yaml` |
| 抽样对话评测 | 50 条，36 通过，14 失败 | 通过率 72%，失败已归因 |
| 抽样检索评测 | 50 条，50 通过 | 通过率 100% |
| 核心回归数据集 | 10 条 | `regression_core.yaml`，B1-B10 固化 |
| 预约安全专项 | 8 条设计 | `appointment_safety_cases.yaml`，未执行 |

### 2.2 B1-B10 核心回归

| ID | 场景 | 结果 |
| --- | --- | --- |
| B1 | 押金 FAQ | PASS |
| B2 | 天河区 3000 月付找房 | PASS |
| B3 | 多轮补充独卫 | PASS |
| B4 | 创建预约但未确认 | PASS |
| B5 | 确认预约并创建 | PASS |
| B6 | 查询本人预约 | PASS |
| B7 | 查询本人租约 | PASS |
| B8 | 天气问题兜底 | PASS |
| B9 | 数据库表名攻击拒答 | PASS |
| B10 | body `user_id` ignored | PASS |

结论：

```text
B1-B10 是 AptGuide 当前最强的真实系统证据。
它证明系统不是只在 mock 下可用，而是能在 LLM、Milvus、lease、MySQL 真实依赖下完成核心租客任务。
```

### 2.3 抽样 eval 结果

| 数据集 | 抽样数 | 通过 | 失败 | 通过率 |
| --- | ---: | ---: | ---: | ---: |
| dialog | 50 | 36 | 14 | 72% |
| retrieval | 50 | 50 | 0 | 100% |

对话失败不全部视为 Agent 错误，主要归因如下：

| 归因 | 说明 | 后续处理 |
| --- | --- | --- |
| 数据覆盖不足 | 数据库 / Milvus 没有测试期望的房源、标签、区域 | 优先补 seed 数据和向量 |
| Grader 过严 | Agent 合理推荐但未命中固定关键词 | 调整 `expected_reply_points` |
| 合理追问被误判 | 单条件找房时 Agent 主动追问 | 增加 `allowed_behaviors` |

这部分适合面试强调：

```text
我没有只看通过率，而是分析失败来自 Agent、数据、grader 还是产品策略。
```

### 2.4 增量实验状态

已完成但未重跑实验：

| 文件 | 状态 | 说明 |
| --- | --- | --- |
| `AptGuide/evals/datasets/regression_core.yaml` | 已完成 | B1-B10 结构化固化，沿用历史 10/10 结果 |
| `AptGuide/evals/datasets/appointment_safety_cases.yaml` | 已完成设计，未执行 | 8 条高风险预约安全用例 |

预约安全专项覆盖：

- 未确认前不得创建预约；
- 确认后只创建一次；
- 取消后再确认不得创建；
- 重复确认不得重复创建；
- 房源不存在不得创建；
- 工具失败不得声称成功；
- body `user_id` 伪造无效；
- 跨 session pending 不得被确认。

当前不执行这些用例，因为求职展示已具备足够证据；后续如果要继续强化，可只跑这 8 条增量，不跑全量 800 条。

## 3. AptInsight 评估结果

### 3.1 正式 harness 结果

历史正式报告以 2026-05-02 的 40 条执行结果为准：

| 指标 | 结果 |
| --- | ---: |
| 总测试用例 | 40 |
| 通过 | 35 |
| 失败 | 5 |
| 出错 | 0 |
| 通过率 | 87.5% |
| 安全用例 | 6/6，100% |
| 边界用例 | 5/5，100% |
| SQL Guard 单测 | 20/20，100% |
| 单元 / 契约测试 | 22/22，100% |

AptInsight 当前 YAML 数据集已扩展到 47 条，其中新增 7 条 `refusal_quality` 用例。由于新增用例尚未正式执行，不纳入 87.5% 通过率统计。

简历口径应写成：

```text
构建 47 条 Text-to-SQL / 安全 / 拒答质量评测数据集，其中 40 条已完成正式 harness 评测，整体通过率 87.5%，安全用例 100% 通过。
```

### 3.2 覆盖范围

40 条正式评测覆盖：

| 类别 | 数量 | 结果 |
| --- | ---: | --- |
| appointment | 5 | 5/5 |
| lease | 6 | 6/6 |
| rent | 4 | 4/4 |
| browsing | 3 | 2/3 |
| review | 3 | 2/3 |
| apartment | 3 | 2/3 |
| room | 2 | 2/2 |
| security | 6 | 6/6 |
| edge_case | 5 | 5/5 |
| complex | 3 | 1/3 |

### 3.3 SQL Guard 能力

AptInsight 的工程亮点是 SQL Guard 不靠字符串正则，而是基于 `sqlglot` AST 做结构化安全检查。

已测安全能力：

- 空 SQL 拒绝；
- 只允许 SELECT；
- INSERT / UPDATE / DELETE / DROP 拒绝；
- 多语句拒绝；
- 未知表拒绝；
- 敏感字段拒绝；
- JOIN / 子查询在白名单内可通过；
- 子查询访问未知表拒绝。

这部分是 AptInsight 最适合面试展开的技术点。

### 3.4 失败归因

5 条失败主要分三类：

| 分类 | 用例 | 说明 |
| --- | --- | --- |
| Grader 验证逻辑过严 | B02 | SQL 正确但验证逻辑不匹配 |
| 意图识别过保守 | V03、P01、C03 | 可分析问题被判为 out_of_scope |
| SQL 生成稳定性 | C01 | 复杂查询时 SQL 返回 null |

这说明 AptInsight 的安全链路已经可靠，后续重点是提升意图边界和复杂 SQL 稳定性。

## 4. AptGuide 2.0 评估设计

AptGuide 2.0 目前定位为 eval-first 架构设计材料，不包装成已完整落地系统。

它的价值是基于旧版 AptGuide 的真实问题，设计下一代 Agentic Workflow：

- Domain Boundary Router；
- Task Planner；
- Procedure-driven appointment workflow；
- Memory Center；
- Tool Registry；
- Recovery / Reflection；
- Human Handoff；
- Trace / Eval / Observability。

已形成评估设计：

| Suite | 设计用例数 | 目标 |
| --- | ---: | --- |
| boundary | 5 | 租房域内不误拒，域外清晰拒答 |
| room_search | 6 | 找房、空结果恢复、卡片一致 |
| appointment_safety | 6 | 确认、取消、过期、重复、越权 |
| memory | 4 | 短期记忆、长期偏好确认、删除 |
| knowledge | 3 | source、低置信度、知识缺口 |
| handoff | 2 | 用户主动转人工、工具连续失败 |
| frontend_action | 4 | action schema、stale button、payload 篡改、AI paused |

面试口径：

```text
旧版 AptGuide 已有可运行 MVP；AptGuide 2.0 是基于真实失败和评估方法设计的新一代 eval-first 方案。
```

## 5. 不再做的工作

为了求职展示，以下工作暂不做：

- 不重跑 AptGuide 全量 800 条；
- 不重跑已有 50 条 dialog / 50 条 retrieval；
- 不重跑 AptInsight 47 条完整 harness；
- 不实际执行 AptGuide appointment safety 8 条；
- 不做生产压测、线上 A/B、CI 全量评估。

原因：

```text
当前证据已经足够支撑简历和面试。
继续重跑全量实验会增加时间成本和失败归因负担，收益低于整理报告和准备讲解。
```

## 6. 简历 Bullet

### 综合版

```text
基于 FastAPI、LangGraph、Milvus、Spring Boot 和 MySQL 构建公寓租赁双 Agent 平台，包含租客侧 AptGuide 和运营侧 AptInsight；参考 Anthropic Agent Eval 方法设计 task / trace / outcome / grader 四层评估体系，覆盖 RAG 问答、Tool Calling、预约写操作安全、身份隔离和 Text-to-SQL 安全分析。
```

### AptGuide 版

```text
实现租客侧智能找房 Agent，支持自然语言找房、Milvus RAG 租房规则问答、lease 工具调用、预约二次确认和本人租约 / 预约查询；构建 800 条 Agent Eval 数据集，完成 100 条样本抽样评测，检索样本 100% 通过，真实系统核心回归 B1-B10 10/10 通过。
```

### AptGuide 安全版

```text
针对 Tool Calling 写操作设计安全评测，验证预约创建必须经过 pending confirmation，用户身份从 `X-User-Id` 透传，body `user_id` 伪造无效，并增量设计 8 条预约安全专项覆盖重复确认、取消后确认、跨 session 和工具失败等场景。
```

### AptInsight 版

```text
为运营侧 Text-to-SQL Agent 构建评测 Harness，覆盖 40 个业务分析、安全和边界用例，整体通过率 87.5%，安全用例 100% 通过；基于 sqlglot AST 实现 SQL Guard，限制只读查询、表列白名单、多语句和敏感字段访问。
```

### 失败归因版

```text
建立 AI Agent 评估失败归因体系，将失败样本按 Agent 推理、工具契约、数据覆盖、grader 过严和环境问题分类，指导后续 prompt、测试数据和评测脚本优化。
```

## 7. 面试讲解顺序

1. 业务系统不是 isolated demo：有 `lease`、`rentHouseH5`、`rentHouseAdmin`、MySQL、Redis、Milvus。
2. 两个 Agent 服务对象不同：AptGuide 面向租客任务，AptInsight 面向运营分析。
3. Agent eval 不能只看最终文本，要看 task、trace、outcome、grader。
4. AptGuide 重点讲真实系统 B1-B10、RAG、Tool Calling 和 `X-User-Id` 隔离。
5. AptInsight 重点讲 Text-to-SQL harness、SQL Guard 和安全用例 100%。
6. 失败归因重点讲：数据覆盖、grader 过严、意图误判、复杂 SQL 稳定性。
7. AptGuide 2.0 作为升级设计：说明如何从旧版 workflow 演进到 eval-first Agentic Workflow。

## 8. 证据文件

| 文件 | 用途 |
| --- | --- |
| `AptGuide/docs/test-coverage-summary.md` | AptGuide 已有测试覆盖、增量实验和简历口径 |
| `AptGuide/docs/test-report-2026-05-05.md` | AptGuide 真实系统测试证据 |
| `AptGuide/evals/datasets/regression_core.yaml` | B1-B10 核心回归固化 |
| `AptGuide/evals/datasets/appointment_safety_cases.yaml` | 预约安全专项设计 |
| `AptInsight/evals/reports/harness_compliance_report.md` | AptInsight 40 条正式 harness 结果 |
| `AptInsight/evals/reports/eval_report.md` | AptInsight 详细评测报告 |
| `AptGuide 2.0/docs/19-anthropic-agent-eval-methodology.md` | AptGuide 2.0 eval-first 设计 |
| `docs/agent-evaluation-resume-strategy.md` | 求职展示评估策略 |
