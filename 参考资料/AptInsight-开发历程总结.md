# AptInsight 智能运营分析助手 -- 开发历程总结

**文档版本：** v1.0
**编写日期：** 2026-05-15
**项目位置：** `/home/chove/桌面/apartment-intelligence-platform/AptInsight/`

---

## 一、系统概述

### 1.1 AptInsight 是什么

AptInsight 是面向尚庭公寓管理系统的智能运营分析助手。它不是普通客服机器人，也不是替管理员操作页面的按钮助手，而是一个基于现有业务数据库、提供自然语言数据分析能力的 AI Agent 系统。

核心工作流程：

```text
管理员输入经营问题
  -> Agent 理解问题（意图识别）
  -> 生成安全的只读 SQL
  -> 查询 MySQL 业务数据库
  -> 返回表格、ECharts 图表和运营总结
```

一句话定义：AptInsight 让公寓运营人员可以用自然语言提问，系统自动完成 SQL 生成、安全校验、只读查询、数据可视化和经营分析总结。

### 1.2 解决的业务问题

传统后台系统只能查询固定条件下的列表数据，运营人员的临时分析需求难以满足：

| 问题类型 | 传统后台不足 | AptInsight 的价值 |
|---------|------------|------------------|
| 跨表统计 | 页面只展示单表或固定联表结果 | 自动关联公寓、房间、预约、租约 |
| 趋势对比 | 需要手动导出后再统计 | 自动按日、按月聚合并生成图表 |
| 经营诊断 | 页面只给数据，不给结论 | 输出业务总结和风险提示 |
| 临时问题 | 每个问题都要开发新接口 | 自然语言转 SQL 即时查询 |

### 1.3 与 AptGuide 系列的关系

AptInsight 是公寓智能平台（apartment-intelligence-platform）下的一个独立子项目。与 AptGuide（面向租客的客服助手）不同，AptInsight 面向的是后台运营管理人员，专注于数据分析而非客户服务。两者共享同一套业务数据库（least/lease），但定位和用户群体完全不同。

### 1.4 技术栈

| 层级 | 技术 | 选型理由 |
|------|------|---------|
| 运行时 | Python 3.12 | AI Agent 生态成熟，适合独立服务 |
| 包管理 | uv | 依赖锁定和启动速度快 |
| API 服务 | FastAPI + Pydantic v2 | 类型化接口，请求响应强校验 |
| Agent 编排 | LangGraph | 有状态工作流，支持条件路由和分支 |
| 模型接入 | OpenAI-compatible client | 兼容阿里百炼 DashScope API |
| 数据库 | SQLAlchemy 2.x async + asyncmy | 异步连接现有 MySQL |
| SQL 解析 | sqlglot | AST 级安全校验，无法通过字符串混淆绕过 |
| 数据处理 | pandas | 查询结果表格化和图表映射 |
| 配置管理 | pydantic-settings | 类型校验，环境变量自动转换 |
| 测试 | pytest + Agent Eval Harness | 回归测试 SQL 生成和安全 |
| 代码质量 | Ruff | 格式化和 lint |

### 1.5 架构设计

AptInsight 采用分阶段架构：

**第一阶段（独立验证）：**
```text
调试入口（Swagger/Postman/简单页面）
        |
        v
Python FastAPI Agent 服务
        |
        +--> LLM 服务（阿里百炼 Qwen）
        +--> Schema/指标知识库
        +--> SQL 安全校验器（sqlglot AST）
        +--> MySQL 只读连接池
        |
        v
现有 MySQL 业务数据库
```

**第二阶段（后台集成）：**
```text
Vue3 管理后台
        |
        v
Spring Boot web-admin（/admin/ai/chat）
        |
        v
Python FastAPI Agent 服务
        |
        v
MySQL 业务数据库
```

---

## 二、开发过程

### 2.1 开发阶段时间线

#### 阶段一：项目规划与设计（2026-05-01 之前）

完成了 11 份详细的设计文档，覆盖：

- `01-助手总体设计.md` -- 项目定位、阶段规划、能力边界
- `02-产品需求文档.md` -- 用户场景、功能需求、验收口径
- `03-技术架构与模块设计.md` -- 架构、部署、配置
- `04-Agent设计与提示词规范.md` -- Agent 工作流、提示词、安全策略
- `05-数据库字典与指标口径.md` -- 表结构、字段含义、枚举值、核心指标
- `06-接口契约与集成方案.md` -- API 契约、Spring Boot 集成
- `07-测试验收方案.md` -- 测试策略
- `08-企业工程规范与Harness.md` -- Harness 定义、企业工程取舍
- `09-系统升级路线与缺陷改进.md` -- 已知缺陷和改进计划
- `10-系统集成实施文档.md` -- Spring Boot / Vue 集成步骤
- `11-最终版系统测试测评方案.md` -- 最终版测评方案

关键决策：
- 选择 Python + FastAPI 独立于现有 Java/Vue 代码库
- 选择 LangGraph 做 Agent 编排（不是简单问答，需要状态管理）
- 选择 sqlglot 做 SQL AST 安全校验（不是正则表达式）
- 选择 Agent Eval Harness 做回归测试

#### 阶段二：核心功能开发（2026-05-01 -- 2026-05-02）

按照 CLAUDE.md 中定义的开发顺序逐步实现：

1. **配置管理和 JSON 日志** -- 使用 pydantic-settings，支持 .env 文件和环境变量
2. **表白名单和 SQL 守卫** -- 基于 sqlglot 的 AST 解析，只允许 SELECT，限制白名单表和列
3. **async MySQL 引擎和只读执行器** -- SQLAlchemy 2.x async + asyncmy
4. **LLM 客户端和结构化输出** -- OpenAI-compatible client，支持 reasoning_effort 参数
5. **LangGraph 工作流节点** -- 6 个节点：classify_intent -> generate_sql -> guard_sql -> execute_sql -> build_chart -> write_answer
6. **/api/chat 接口接入工作流** -- FastAPI 路由，trace_id 链路追踪

#### 阶段三：数据补充与调试（2026-05-02）

**数据补充：** 原有数据库数据主要为 2023 年北京地区数据，无法覆盖"近30天"、"本月"等时间范围查询。补充了广州大学城（番禺区贝岗、南亭、北亭）的完整运营数据：

| 数据类型 | 新增数量 | 时间覆盖 |
|---------|---------|---------|
| 公寓 | 3 个 | -- |
| 房间 | 19 个 | -- |
| 用户 | 15 个 | -- |
| 预约 | ~120 条 | 2025-12 至 2026-05 |
| 租约 | ~40 条 | 2025-06 至 2026-12 |
| 浏览记录 | ~70 条 | 2026-04 至 2026-05 |
| 评价 | ~20 条 | 2026-01 至 2026-05 |

**Bug 修复：** 修复了多个影响调试体验的问题：
- CASE-001：闲聊/超范围问题返回"没有找到符合条件的数据"（write_answer 用 if not rows 做一刀切判断）
- CASE-002：API 响应中 summary 字段为空或固定值（JSON 解析不够健壮）
- CASE-003：SQL 别名绕过敏感字段脱敏（安全漏洞，已记录待修复方案）
- CASE-004：MiMo 模型静默启用思考链导致响应为空（核心问题，详见第三节）
- CASE-005：拒答和失败回答过于模板化

#### 阶段四：Harness 达标（2026-05-02）

完成以下工作达到 Harness 标准：

- 依赖修复：添加 cryptography 包解决 MySQL caching_sha2_password 认证问题
- 代码质量修复：修复 Ruff Lint 错误（未使用 import、f-string 问题等）
- 单元测试补充：20 个 SQL Guard 单元测试
- 评测结果提升：通过率从 50% 提升到 87.5%

#### 阶段五：模型选型与系统失败调查（2026-05-07）

这是项目中最深入的技术探索阶段。完成了 4 个 Phase 的系统化模型选型：

- **Phase 0**：实现 targeted_eval.py 轻量评测运行器
- **Phase 1**：Qwen/Qwen3.6/DeepSeek Intent 节点评测（23 cases x 15 runs）
- **Phase 2**：SQL 生成节点评测（12 cases x 11 runs）
- **Phase 3**：MiMo 截断问题验证（4 cases x 6 runs）
- **Phase 4**：最终端到端组合验证（45 cases）

最终结论：三个节点统一使用 qwen-turbo-latest（DashScope API）。

### 2.2 关键里程碑

| 日期 | 里程碑 | 产出 |
|------|--------|------|
| 2026-05-01 之前 | 设计文档完成 | 11 份详细设计文档 |
| 2026-05-01 | MVP 核心功能完成 | LangGraph 工作流、API 接口、SQL Guard |
| 2026-05-02 | 数据补充 | 广州大学城完整运营数据 |
| 2026-05-02 | Harness 达标 | 87.5% 通过率，22 个单元测试 |
| 2026-05-02 | 模型基准测试 | 14+ 模型横向对比 |
| 2026-05-07 | 系统失败根因报告 | 4 条 MiMo 失败的完整根因分析 |
| 2026-05-07 | 模型选型完成 | Phase 1-4 验证，最终选 qwen-turbo-latest |

### 2.3 开发过程中的关键决策

#### ADR-001：使用 sqlglot 进行 SQL 安全检查

**决策：** 使用 sqlglot 库进行 SQL AST 解析，而不是正则表达式。

**原因：**
1. AST 解析更安全，无法通过字符串混淆绕过
2. 可以精确识别表名、列名、子查询等
3. 支持 MySQL 方言特有语法

#### ADR-002：使用 LangGraph 构建 Agent 工作流

**决策：** 使用 LangGraph 框架构建有状态的工作流。

**原因：**
1. 支持条件路由，可以根据意图类型选择不同的处理路径
2. 状态管理清晰，各节点之间通过状态传递数据
3. 易于扩展和调试

#### ADR-003：按节点选型模型而非全链路统一

**决策：** 不采用"一个大模型跑所有节点"的方案，而是按 Agent 节点做模型选型。

**原因：**
1. Intent 节点需要稳定 JSON 和低延迟，适合快模型
2. SQL 生成节点需要指标口径和多表推理，适合强模型
3. SQL Guard 用确定性 AST 规则，不交给 LLM
4. 最终三个节点统一用 qwen-turbo-latest 是因为没有单一模型全面优于它

#### ADR-004：Agent 服务独立于现有 Java/Vue 代码库

**决策：** AptInsight 作为独立的 Python 服务，不嵌入现有 Spring Boot 工程。

**原因：**
1. AI Agent 生态更适合 Python
2. 不影响现有前后端主流程
3. 可以集中验证 Text-to-SQL 准确率
4. 第二阶段通过 Spring Boot 网关集成

---

## 三、遇到的困难与解决方案

### 3.1 核心难题：MiMo 模型 reasoning_content 消耗 max_tokens 预算

**这是项目中最重要、最深入的技术问题。**

#### 问题发现

在运行 Agent Eval Harness 时，37.5% 的用例在意图识别阶段失败，报错"解析意图响应失败: 响应中没有找到 JSON"。直接调用 LLM 简短 prompt 正常，但使用完整意图提示词时返回空字符串。

#### 根因分析

MiMo 模型（mimo-v2.5-pro 和 mimo-v2.5）内置思考链模式，无法通过 API 参数完全关闭。API 返回的响应结构中：

```json
{
  "choices": [{"message": {"content": "", "reasoning_content": "首先，用户的问题是..."}}],
  "usage": {"completion_tokens": 500, "completion_tokens_details": {"reasoning_tokens": 499}}
}
```

499/500 tokens 被思考链消耗，0 tokens 留给实际输出。`reasoning_content` 字段有大量内容，`content` 为空字符串。

关键证据表：

| Case | 节点 | content_len | reasoning_len | completion_tokens | max_tokens | finish_reason |
|------|------|-------------|---------------|-------------------|------------|---------------|
| V03 | intent | 0 | 820 | 400 | 400 | length |
| P01 | intent | 83 | 134 | 113 | 400 | stop |
| C01 | intent | 83 | 605 | 371 | 400 | stop |
| C01 | sql | 1229 | 2244 | 1189 | 1200 | stop |
| C03 | intent | 60 | 733 | 400 | 400 | length |

注意：API 返回的 `reasoning_tokens` 始终为 0，说明 MiMo API 不单独追踪 reasoning token，它们被计入 `completion_tokens`。

#### 失败链路

```text
MiMo mimo-v2.5-pro 的 reasoning_content（思考链）消耗 max_tokens 预算
  -> content 为空或被截断
  -> JSON 解析失败
  -> fallback 文本推断不稳定
  -> intent 降级为 out_of_scope 或 SQL 生成返回 null
```

受影响的 4 条 case：

| Case | 用户问题 | 失败节点 | failure_type |
|------|---------|---------|-------------|
| V03 | 最近一个月的评价数量趋势 | classify_intent | llm_empty_content |
| P01 | 有多少个已发布的公寓 | classify_intent | llm_empty_content |
| C01 | 预约量高但签约量低的公寓有哪些 | generate_sql | llm_empty_content |
| C03 | 租金和评分的关系是什么 | classify_intent | llm_content_truncated |

#### 解决方案

**短期修复（已实施）：**

1. LLMClient 新增 `reasoning_effort` 参数，通过 `extra_body={"reasoning_effort": "medium"}` 传递给 API
2. 提高各节点 max_tokens：intent 200->400, SQL 800->1200, answer 600->1000
3. 全局配置 `LLM_REASONING_EFFORT=medium`

修复后效果：通过率从 37.5% 恢复到 87.5%，但平均处理时间从 7.9s 增加到 24.9s。

**长期方案（已验证并实施）：**

切换到 qwen-turbo-latest（阿里百炼 DashScope API），该模型没有思考链开销，同批 case 通过率 87.5%，平均延迟仅 6.4s（比 MiMo 快 3.9 倍）。

#### 经验教训

1. 新模型接入时必须检查原始 HTTP 响应，不能只看 SDK 封装后的 content 字段
2. reasoning_effort 参数的语义因模型而异，low 不一定意味着"少思考"
3. max_tokens 需要为思考链预留空间，实际可用输出 = max_tokens - reasoning_tokens
4. 不能只看总通过率，要看失败集合和失败类型

### 3.2 闲聊/超范围问题返回"没有找到符合条件的数据"

**根因：** `write_answer` 用 `if not rows` 做一刀切判断，不区分"没数据"的原因。chitchat 和 out_of_scope 路径根本没有查库，rows 必然是空列表，直接命中了这个分支。

**解决方案：** 新增 5 个分支替代 `if not rows` 一刀切：
- `intent == "chitchat"` -- 用独立 prompt 调 LLM 生成闲聊回复
- `intent == "out_of_scope"` -- 返回固定的超出范围提示
- `state["error"]` 存在 -- 返回具体错误信息
- `rows` 为空且无明确错误 -- 保留原有兜底提示
- `rows` 有数据 -- 原有 LLM 分析逻辑不变

### 3.3 SQL 别名绕过敏感字段脱敏（安全漏洞）

**根因：** 脱敏模块依赖结果字典的 key 做敏感字段识别，但 LLM 生成 SQL 时可以自由使用别名（`AS tenant_name`），导致脱敏逻辑失效。

**改进方案（已记录，待实施）：**
- 方案 A（推荐）：结果集后处理时，反查 SQL AST 中的别名映射
- 方案 B：在 SQL Guard 层禁止 SELECT 敏感字段时使用别名
- 方案 C：在提示词中约束 LLM 不要给敏感字段加别名

### 3.4 拒答和失败回答过于模板化

**问题：** 用户提问具体租客或入住记录时，系统只返回固定话术，没有说明具体不能答的原因。

**改进方案：** 新增失败解释生成器，用大模型生成用户可理解的拒答，包含具体原因和改问建议。

### 3.5 一次性 SQL 生成缺少执行后反思

**问题：** 用户问题表达不够精确时，模型会直接猜字段和过滤条件。SQL 执行返回 0 行时，系统直接回答"没有找到符合条件的数据"，不会判断是数据库确实没有数据还是 SQL 条件过严。

**典型例子：** 用户问"大学城哪个公寓的房源最多"，模型生成 `district_name = '大学城'`，但实际 district_name 存的是"番禺区"等行政区。

**规划的解决方案（09-系统升级路线与缺陷改进.md）：**
- P1：增加空结果修正节点（diagnose_empty_result -> repair_sql，最多一次）
- P2：增加澄清问题机制
- P3：轻量多轮记忆
- P4：Schema 和样例检索
- P5：评测体系升级

---

## 四、系统功能详解

### 4.1 核心功能模块

#### 4.1.1 意图识别模块（classify_intent）

判断用户问题是否属于公寓运营分析，输出三种意图之一：
- `analysis` -- 需要查库的业务分析
- `chitchat` -- 闲聊
- `out_of_scope` -- 超出范围

#### 4.1.2 SQL 生成模块（generate_sql）

将自然语言问题转换为 MySQL SELECT 语句。注入 schema 上下文、指标口径和 few-shot 示例。

#### 4.1.3 SQL 安全校验模块（guard_sql）

基于 sqlglot 的 AST 级安全检查：
- 只允许 SELECT 语句
- 表和列白名单机制
- 敏感字段拦截（身份证号、密码等）
- 多语句 SQL 拒绝
- 系统库访问拒绝

#### 4.1.4 数据库执行模块（execute_sql）

使用只读账号执行 SQL，设置查询超时（10s），限制最大返回行数（200），返回列名、列类型、行数据和耗时。

#### 4.1.5 图表构建模块（build_chart）

根据结果列类型选择图表：
- 日期/月份 + 数值 -- 折线图
- 类别 + 数值 -- 柱状图
- 状态 + 数量/占比 -- 饼图
- 多列明细 -- 表格

#### 4.1.6 答案生成模块（write_answer）

基于查询结果生成中文总结，要求不编造、先给结论、说明口径。

### 4.2 数据分析能力

覆盖六大分析场景：

| 场景 | 典型问题 | 涉及表 |
|------|---------|-------|
| 预约分析 | 本月各公寓预约量排名 | view_appointment, apartment_info |
| 租约分析 | 当前有效租约数量 | lease_agreement |
| 房源分析 | 各公寓房间数量 | room_info, apartment_info |
| 租金分析 | 各公寓平均租金 | room_info, apartment_info |
| 浏览热度 | 最近30天浏览趋势 | browsing_history |
| 经营诊断 | 预约量高但签约量低的公寓 | view_appointment, lease_agreement |

### 4.3 安全机制

1. **SQL 守卫** -- sqlglot AST 级安全检查，只允许 SELECT
2. **数据脱敏** -- 手机号 138****1234，姓名 张*
3. **只读账号** -- 数据库使用只读权限账号
4. **表白名单** -- 只允许访问业务表，禁止系统库
5. **敏感字段拦截** -- 身份证号、密码等字段不允许查询
6. **查询超时** -- 10 秒超时中断
7. **最大行数限制** -- 默认 200 行

### 4.4 评测系统

评测系统包含：
- **40 条测试用例** -- 覆盖预约、租约、租金、浏览、评价、公寓、房间、安全、边界、复杂查询
- **评测运行器** -- `evals/runners/text_to_sql.py`（端到端）和 `targeted_eval.py`（节点级）
- **评测报告** -- JSON 和 Markdown 格式，包含通过率、失败分析、耗时统计
- **Harness 达标报告** -- 对照企业工程规范的达标情况

---

## 五、最终评估

### 5.1 测试结果

#### Agent Eval Harness 结果（MiMo 全链路，2026-05-02）

| 指标 | 值 |
|------|-----|
| 总测试用例 | 40 |
| 通过 | 35 |
| 失败 | 5 |
| 通过率 | 87.5% |
| 平均处理时间 | 24.9s |
| 安全测试 | 6/6 (100%) |
| 边界测试 | 5/5 (100%) |

#### Agent Eval Harness 结果（qwen-turbo-latest 全链路，2026-05-02）

| 指标 | 值 |
|------|-----|
| 总测试用例 | 40 |
| 通过 | 35 |
| 失败 | 5 |
| 通过率 | 87.5% |
| 平均处理时间 | 6.4s |
| 安全测试 | 6/6 (100%) |
| 边界测试 | 5/5 (100%) |

#### 最终 E2E 验证（qwen-turbo-latest，2026-05-07）

| 指标 | 值 |
|------|-----|
| 总测试用例 | 45 |
| 通过 | 39 |
| 失败 | 6 |
| 通过率 | 86.7% |
| 平均延迟 | 5.4s |

#### 单元测试

| 测试套件 | 用例数 | 通过率 |
|----------|--------|--------|
| SQL Guard 测试 | 20 | 100% |
| 健康检查测试 | 1 | 100% |
| 接口契约测试 | 1 | 100% |
| **总计** | **22** | **100%** |

#### 代码质量

| 检查项 | 结果 |
|--------|------|
| Ruff Lint | 0 错误 |
| Ruff Format | 通过 |

### 5.2 Harness 达标情况

| 指标 | 要求 | 实际 | 状态 |
|------|------|------|------|
| 功能用例通过率 | >= 80% | 87.5% | 达标 |
| 安全用例通过率 | = 100% | 100% | 达标 |
| 核心指标口径通过率 | = 100% | 100% | 达标 |
| 单元测试 | 有 | 22 个全部通过 | 达标 |
| Ruff Lint | 通过 | 0 错误 | 达标 |

### 5.3 失败用例分析

两个模型（MiMo 和 Qwen）的失败用例完全不重叠：

| 用例 | 问题 | MiMo | Qwen | 说明 |
|------|------|------|------|------|
| B02 | 近30天浏览趋势 | 失败 | 通过 | MiMo 验证失败（DATE vs DATE_FORMAT） |
| V03 | 近一月评价趋势 | 失败 | 通过 | MiMo 意图误判（reasoning_content 消耗） |
| P01 | 已发布公寓数量 | 失败 | 通过 | MiMo 意图误判 |
| C01 | 预约量高签约量低 | 失败 | 通过 | MiMo SQL 生成 null |
| C03 | 租金和评分关系 | 失败 | 通过 | MiMo 意图误判 |
| L02 | 租约状态分布 | 通过 | 失败 | Qwen 验证失败 |
| R02 | 租金最高公寓 | 通过 | 失败 | Qwen 验证失败（MAX vs AVG） |
| R04 | 各价位段分布 | 通过 | 失败 | Qwen 图表类型不匹配（bar vs pie） |
| P02 | 各城市公寓数量 | 通过 | 失败 | Qwen 图表类型不匹配 |
| C02 | 预约转化率 | 通过 | 失败 | Qwen 指标口径问题 |

重要结论：harness failed 不等于系统出错。需要区分：
- 主系统链路确实失败
- SQL 等价但 grader 不接受
- 图表类型偏好不一致
- 业务指标口径有歧义
- 模型输出受 max_tokens / reasoning 配置影响

### 5.4 系统完成度

**已完成：**
- MVP 核心功能全部完成
- Harness 达标
- 模型选型完成（qwen-turbo-latest）
- 系统失败根因分析完成
- 单元测试和契约测试通过
- 评测系统完整

**未完成（第二阶段）：**
- Spring Boot 集成
- Vue 前端页面
- 多轮记忆
- SQL 空结果自动修复
- 澄清问题机制
- Docker 部署
- CI/CD 流水线

### 5.5 已知问题

| ID | 问题 | 优先级 | 状态 |
|----|------|--------|------|
| BUG-001 | write_answer logger 参数错误导致答案生成失败 | P0 | 已修复 |
| BUG-002 | fallback 答案漏掉核心指标列 | P0 | 已修复 |
| BUG-003 | "大学城"被误映射为 district_name = '大学城' | P0 | 待修复 |
| BUG-004 | 空结果后缺少自动修正或澄清流程 | P1 | 待设计 |
| BUG-005 | "租金最高"容易被生成"平均租金最高" | P0 | 待修复 |
| BUG-006 | session_id 暂未形成真正多轮记忆 | P3 | 待设计 |
| BUG-007 | 闲聊意图可能返回无数据提示 | P0 | 已修复 |
| CASE-003 | SQL 别名绕过敏感字段脱敏 | 高 | 待修复 |

---

## 六、经验总结

### 6.1 最大经验：harness failed 不等于系统出错

这是项目中最重要的认知。AptInsight 主系统链路是：

```text
classify_intent -> generate_sql -> guard_sql -> execute_sql -> build_chart -> write_answer
```

评测链路是：

```text
text_to_sql.py -> run_agent() -> _validate_result() -> passed / failed
```

一条 case 在 harness 中 failed，可能是主系统链路真的失败，也可能是 grader 规则过严、图表偏好不一致或业务指标口径有歧义。必须逐条拆失败、归因，不能只看总通过率。

### 6.2 模型选型不能只看总分

两个模型（MiMo 和 Qwen）同样是 87.5% 通过率，但失败位置完全不同：
- MiMo 的主要问题是 reasoning_content 消耗 token 导致 content 为空或 JSON 截断
- Qwen 的失败更多集中在图表偏好、grader 规则或业务指标口径

最终没有采用"一个大模型跑所有节点"的方案，而是按 Agent 节点做模型选型。这个过程形成了"按节点选模型"的思路：router 用快模型，SQL 生成用强模型，SQL Guard 用确定性 AST 规则。

### 6.3 reasoning 模型的陷阱

MiMo 是 reasoning 型模型，思考链计入 completion_tokens。这个特性导致：
- 当 max_tokens 较低时，思考链消耗几乎全部 token 预算
- reasoning_effort 参数的语义因模型而异（low 不一定意味着"少思考"）
- 新模型接入时必须检查原始 HTTP 响应，不能只看 SDK 封装后的 content 字段

### 6.4 安全不能依赖 LLM

SQL Guard 使用 sqlglot AST 做确定性安全检查，而不是让 LLM 自己判断 SQL 是否安全。这是一个关键的架构决策：
- AST 解析无法通过字符串混淆绕过
- 表和列白名单是硬编码的规则
- 安全边界必须是确定性的，不能依赖概率性的模型输出

### 6.5 评测体系的价值

Agent Eval Harness 不仅是测试工具，更是：
- prompt 改动的回归保障
- 模型选型的量化依据
- 失败归因的数据来源
- 面试和简历的硬核证据

### 6.6 渐进式开发策略

项目采用了"先独立验证，再集成后台"的策略：
1. 第一阶段不改动已有前后端系统，单独验证 Agent 能力
2. Agent 行为稳定后再接入 Spring Boot 和 Vue 集成
3. 这样避免了 AI 服务的不确定性影响现有业务系统

### 6.7 面试表达要点

可以这样讲：

> 为 Text-to-SQL 运营分析 Agent 构建 Eval Harness，覆盖 40 个业务与安全用例，整体通过率 87.5%，安全用例 100%。基于 sqlglot AST 实现只读 SQL Guard、表列白名单、多语句拒绝和敏感字段拦截。在模型选型过程中，发现 MiMo reasoning 模型的思考链会消耗 max_tokens 预算导致 content 为空，通过 Phase 1-4 系统化评测，最终三个节点统一使用 qwen-turbo-latest（5.4s 平均延迟，比 MiMo 快 4.6 倍）。这个过程让我形成了按节点选模型的思路：router 用快模型，SQL 生成用强模型，SQL Guard 用确定性 AST，而不是一个模型跑全链路。

---

## 附录：关键文件索引

| 文件 | 说明 |
|------|------|
| `AptInsight/README.md` | 项目说明和快速开始 |
| `AptInsight/CLAUDE.md` | Claude Code 项目指引 |
| `AptInsight/AGENTS.md` | 编码 Agent 通用指引 |
| `AptInsight/AptInsight文档/01-助手总体设计.md` | 项目定位和阶段规划 |
| `AptInsight/AptInsight文档/03-技术架构与模块设计.md` | 架构和模块设计 |
| `AptInsight/AptInsight文档/04-Agent设计与提示词规范.md` | Agent 工作流和提示词 |
| `AptInsight/AptInsight文档/05-数据库字典与指标口径.md` | 表结构和指标定义 |
| `AptInsight/AptInsight文档/09-系统升级路线与缺陷改进.md` | 升级路线和已知缺陷 |
| `AptInsight/AptInsight文档/11-最终版系统测试测评方案.md` | 最终测评方案 |
| `AptInsight/docs/development_progress.md` | 开发进展记录 |
| `AptInsight/docs/bug排错文档.md` | Bug 排错记录（5 个 CASE） |
| `AptInsight/docs/aptinsight-system-failure-root-cause-report.md` | 系统失败根因分析 |
| `AptInsight/docs/model-selection-eval-report.md` | 模型选型评测报告 |
| `AptInsight/docs/eval-error-analysis-lessons.md` | 评测错误分析经验 |
| `AptInsight/docs/benchmark_results.md` | 模型基准测试结果 |
| `AptInsight/docs/anthropic-agent-eval-methodology.md` | Anthropic Agent Eval 方法论 |
| `AptInsight/evals/reports/eval_report.md` | 评测报告（MiMo + Qwen 对比） |
| `AptInsight/evals/reports/harness_compliance_report.md` | Harness 达标报告 |
| `AptInsight/src/aptinsight/agent/graph.py` | LangGraph 工作流组装 |
| `AptInsight/src/aptinsight/security/sql_guard.py` | SQL 安全校验 |
| `AptInsight/src/aptinsight/llm/client.py` | LLM 客户端 |
| `AptInsight/src/aptinsight/core/config.py` | 配置管理 |
| `AptInsight/pyproject.toml` | 项目依赖配置 |
| `AptInsight/SECURITY.md` | 安全约束 |
