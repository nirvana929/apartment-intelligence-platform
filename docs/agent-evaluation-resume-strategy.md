# Agent Evaluation Resume Strategy

**日期:** 2026-05-07
**目标:** 为求职、简历和技术面试准备可展示的 AI Agent 评估证据

---

## 1. 为什么要重新定义评估目标

这个项目用于求职展示时，评估目标不应该等同于生产系统上线验收。

生产验收追求：

- 全量覆盖；
- 高通过率；
- 持续 CI；
- 压测、灰度、监控；
- 长期线上反馈闭环。

求职展示更应该追求：

- 能证明你理解 Agent 不只是 prompt；
- 能证明你会设计 task / trace / outcome / grader；
- 能证明你能评估 RAG、Tool Calling、Text-to-SQL 和安全边界；
- 能证明你能读失败样本并归因；
- 能用少量高质量案例讲清楚工程判断。

因此，本项目的求职评估策略是：

```text
精选高价值样本
+ 覆盖关键风险路径
+ 输出可复现报告
+ 保留失败归因
+ 转化成简历 bullet 和面试讲解材料
```

不建议为了简历盲目追求 800+ 条全量评测全部跑完。全量评测可以作为加分项，但不是当前性价比最高的工作。

## 2. 推荐评估范围

### 2.1 最推荐的组合

| 项目 | 用例量 | 时间 | 目的 |
| --- | ---: | ---: | --- |
| AptGuide 核心回归 | 10-15 | 30-60 分钟 | 证明 C 端 Agent 能完成真实租客任务 |
| AptGuide RAG / 检索 | 30-50 | 1-2 小时 | 证明不是纯聊天，而有知识库和向量检索评估 |
| AptGuide 安全专项 | 10-20 | 1-2 小时 | 证明理解 Tool Calling 写操作风险和身份隔离 |
| AptInsight Text-to-SQL | 40 | 1-2 小时 | 证明有 SQL Guard、指标口径和业务分析 harness |
| AptGuide 2.0 eval-first 设计 | 30 条设计用例 | 文档即可 | 证明能做新一代 Agent 架构和评估设计 |

总计实际运行约 **90-125 条自动 / 半自动评估**，加上 AptGuide 2.0 的设计用例。

这是简历展示的最佳平衡点：覆盖足够广，工作量可控，且每一类都能讲出技术含量。

### 2.2 时间预估

| 阶段 | 工作 | 时间 |
| --- | --- | --- |
| 环境准备 | 启动 AptGuide、AptInsight、lease、Milvus、Redis、MySQL | 1-2 小时 |
| 核心样本运行 | B1-B10、AptInsight 40 条 harness | 1-2 小时 |
| AptGuide 样本评估 | dialog 50 + retrieval 50 + safety 10-20 | 2-4 小时 |
| 失败归因 | 读失败 trace，区分 Agent / 数据 / grader / 环境 | 2-3 小时 |
| 报告整理 | 写 2-3 份报告和简历 bullet | 2-3 小时 |

建议预留 **1-2 天** 完成一个质量不错的求职展示版评估闭环。

如果只做最小展示版，半天也可以完成：

```text
AptGuide B1-B10
+ AptInsight 40 条 harness
+ 一份总报告
```

## 3. 应该重点证明的能力

### 3.1 Agent outcome 评估能力

面试官会关心你是否知道 Agent 不能只看最终文本。

需要展示：

- 预约创建必须查后端状态；
- 查询预约 / 租约必须验证用户隔离；
- FAQ 必须验证 source；
- 找房必须验证 cards 和回复一致；
- 工具失败不能让模型说成功。

可写进简历：

```text
参考 Anthropic Agent Eval 方法，将租房 Agent 评估拆解为 task、trace、outcome、grader 四层，覆盖找房、预约、RAG 问答和身份隔离等核心场景。
```

### 3.2 RAG 评估能力

需要展示：

- Milvus knowledge base；
- top-k 命中；
- source 引用；
- 低置信度回退；
- 答案不编造。

可写进简历：

```text
构建租房规则 RAG 评测集，评估 FAQ source 命中、top-3 检索质量和低置信度回退，避免模型编造业务规则。
```

### 3.3 Tool Calling 安全能力

需要展示：

- 预约写操作二次确认；
- pending confirmation；
- stale / duplicate confirmation 拦截；
- `X-User-Id` 身份透传；
- body `user_id` 伪造无效；
- 内部信息和数据库表名拒绝泄露。

可写进简历：

```text
设计 Agent 写操作安全评测，验证预约创建必须经过二次确认，并覆盖 user_id 越权、prompt injection、内部信息泄露和工具失败恢复。
```

### 3.4 Text-to-SQL 安全和业务口径能力

AptInsight 是简历里更硬核的一部分，因为它包含 SQL AST 安全守卫。

需要展示：

- sqlglot AST；
- SELECT-only；
- 表列白名单；
- 敏感字段拦截；
- 多语句拒绝；
- 40 条业务和安全用例；
- 87.5% harness 通过率，安全 100%。

可写进简历：

```text
为 Text-to-SQL 运营分析 Agent 构建 Eval Harness，覆盖 40 个业务与安全用例，整体通过率 87.5%，安全用例 100%；基于 sqlglot AST 实现只读 SQL Guard、表列白名单和敏感字段拦截。
```

### 3.5 失败归因能力

这是最容易拉开差距的部分。

不要只说“跑了多少条，通过率多少”。要说明你能把失败拆成：

| 分类 | 说明 |
| --- | --- |
| Agent reasoning | 模型意图、规划、槽位、回答错误 |
| Tool contract | 字段映射、状态码、工具返回不一致 |
| Data coverage | Milvus 或测试库数据不足 |
| Grader too strict | Agent 合理但评估脚本太死 |
| Product ambiguity | 业务定义本身未定 |
| Environment | 依赖、密钥、容器状态问题 |

可写进简历：

```text
建立 Agent 评估失败归因体系，将失败样本按 Agent 推理、工具契约、数据覆盖、grader 过严和环境问题分类，指导后续 prompt、数据和评测脚本优化。
```

## 4. 不建议投入过多的评估

为了求职展示，以下内容可以暂缓：

- 不必把 AptGuide 800+ 条样本全部优化到 95% 以上；
- 不必做生产级大并发压测；
- 不必做线上 A/B 测试；
- 不必做大规模人工标注；
- 不必把所有评估都接入 CI；
- 不必追求复杂 LLM judge 平台。

更重要的是准备好能讲清楚的闭环：

```text
我为什么选这些 case
我怎么判断 pass/fail
我发现了什么失败
我如何区分 Agent 问题和评测问题
我下一步会怎么改
```

## 5. 建议产出的证据文件

| 文件 | 面试用途 |
| --- | --- |
| `AptGuide/docs/anthropic-agent-eval-methodology.md` | C 端 Agent eval 方法 |
| `AptGuide/docs/test-report-2026-05-05.md` | 真实系统集成测试样例 |
| `AptInsight/docs/anthropic-agent-eval-methodology.md` | Text-to-SQL eval 方法 |
| `AptInsight/evals/reports/eval_report.md` | AptInsight 真实 harness 报告 |
| `AptGuide 2.0/docs/19-anthropic-agent-eval-methodology.md` | 新一代 Agent eval-first 架构 |
| `docs/agent-evaluation-resume-strategy.md` | 求职展示总策略 |
| `docs/agent-evaluation-portfolio-report-2026-05-07.md` | 最终可用于简历和面试复盘的总评估报告 |

建议再补一份总报告：

```text
docs/agent-evaluation-portfolio-report-2026-05-xx.md
```

该报告面向简历和面试，不必像生产测试报告那样冗长，应聚焦：

- 项目背景；
- 评估方法；
- 用例规模；
- 核心结果；
- 安全能力；
- 失败归因；
- 简历 bullet。

## 6. 推荐最终简历写法

### 6.1 综合版

```text
基于 FastAPI、LangGraph、Milvus、Spring Boot 和 MySQL 构建公寓租赁双 Agent 平台，包含租客侧 AptGuide 和运营侧 AptInsight；参考 Anthropic Agent Eval 方法设计 task / trace / outcome / grader 四层评估体系，覆盖 RAG 问答、Tool Calling、预约写操作安全、身份隔离和 Text-to-SQL 安全分析。
```

### 6.2 AptGuide 版

```text
实现租客侧智能找房 Agent，支持自然语言找房、Milvus RAG 租房规则问答、lease 工具调用、预约二次确认和本人租约 / 预约查询；设计端到端回归评测，覆盖核心任务、安全拒答、user_id 越权和工具失败恢复。
```

### 6.3 AptInsight 版

```text
实现运营侧 Text-to-SQL 分析 Agent，使用 LangGraph 编排意图识别、SQL 生成、SQL Guard、查询执行、图表构建和答案总结；基于 sqlglot AST 实现只读 SQL 安全守卫，并构建 40 条业务 / 安全评测 harness，安全用例 100% 通过。
```

### 6.4 评估能力版

```text
建立 AI Agent 评估闭环，沉淀自动化评测数据集、测试报告和失败归因流程，将失败按 Agent 推理、工具契约、数据覆盖、grader 过严和环境问题分类，用于指导 prompt、数据和工具接口迭代。
```

## 7. 面试讲解顺序

建议按这个顺序讲，最容易体现深度：

1. 先讲业务系统不是 demo：有 lease 后端、H5、后台、MySQL、Redis、Milvus。
2. 再讲两个 Agent 角色不同：AptGuide 面向租客任务，AptInsight 面向运营分析。
3. 讲为什么普通聊天评估不够：Agent 要看 trace 和 outcome。
4. 讲 AptGuide 的安全：预约必须确认，个人数据只看 `X-User-Id`。
5. 讲 AptInsight 的安全：SQL AST、白名单、敏感字段。
6. 讲评测结果和失败归因：不是只晒分数，而是能解释失败。
7. 讲 AptGuide 2.0：说明你已经设计下一代 eval-first 架构。

## 8. 执行状态

当前求职展示版评估整理已经完成，后续可选实验暂不执行。

- [x] AptInsight 使用已有 40 条正式 harness 报告，不重跑 47 条。
- [x] AptGuide 测试文档整理为 `AptGuide/docs/test-coverage-summary.md`。
- [x] AptGuide B1-B10 固化为 `regression_core.yaml`，不重跑。
- [x] AptGuide 预约安全专项 8 条已设计为 `appointment_safety_cases.yaml`，不执行。
- [x] 已新增最终总报告 `docs/agent-evaluation-portfolio-report-2026-05-07.md`。
- [ ] 可选：以后如需更强证据，只单独执行 AptGuide 8 条 appointment safety，不跑全量 800 条。
