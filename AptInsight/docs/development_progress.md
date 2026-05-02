# AptInsight 开发进展记录

## 2026-05-02 reasoning_effort 修复与评测重跑

### 问题发现

MiMo 模型（mimo-v2.5-pro 和 mimo-v2.5）静默启用思考链（reasoning_content），在低 max_tokens 预算下（200 tokens），思考链消耗全部 token 预算，导致 content 为空，意图识别全部失败。

**根因**：API 返回 `reasoning_content` 字段，消耗 199/200 tokens，`content` 为空字符串。

### 修复方案

1. **LLMClient 新增 `reasoning_effort` 参数**
   - 通过 `extra_body={"reasoning_effort": "medium"}` 传递给 API
   - 支持 low/medium/high 三档
   - medium 档平衡速度和质量（reasoning ~150 tokens，留足空间给 content）

2. **提高各节点 max_tokens**
   - 意图识别：200 → 400
   - SQL 生成：800 → 1200
   - 答案生成：600 → 1000

3. **全局配置**
   - `LLM_REASONING_EFFORT=medium`（.env）
   - `llm_reasoning_effort` 字段（Settings）

### 评测结果

**通过率：87.5%（35/40）**

| 指标 | 要求 | 实际 | 状态 |
|------|------|------|------|
| 功能用例通过率 | >= 80% | 87.5% | ✅ 达标 |
| 安全用例通过率 | = 100% | 100% | ✅ 达标 |
| 平均处理时间 | - | 24.9s | - |

### 失败用例

- B02：浏览趋势（SQL 正确但验证逻辑不匹配）
- V03：差评查询（意图误判为 out_of_scope）
- P01：公寓列表（意图误判为 out_of_scope）
- C01：跨表复杂查询（SQL 生成返回 null）
- C03：空置率分析（意图误判为 out_of_scope）

### 修改文件

- `src/aptinsight/llm/client.py` - 新增 reasoning_effort 参数
- `src/aptinsight/core/config.py` - 新增 llm_reasoning_effort 字段，调整 max_tokens 默认值
- `.env` - 更新 max_tokens 和新增 LLM_REASONING_EFFORT
- `evals/reports/eval_report.json` - 更新评测结果
- `evals/reports/eval_report.md` - 更新评测报告

---

## 2026-05-02 广州大学城数据补充

### 背景

原有数据库数据主要为 2023 年北京地区数据，无法覆盖"近30天"、"本月"、"近半年"等时间范围查询。补充了广州大学城（番禺区贝岗、南亭、北亭）的完整运营数据。

### 数据备份

- 备份文件：`backups/least_backup_20250502.sql`（312KB）
- 备份方式：`mysqldump` 全库备份

### 新增数据

| 数据类型 | 新增数量 | 说明 |
|----------|----------|------|
| 公寓 | 3 个 | 贝岗青年公寓、南亭社区公寓、北亭学府公寓 |
| 房间 | 19 个 | 租金 600-1800 元，覆盖单间到两房 |
| 用户 | 15 个 | 大学城学生用户 |
| 预约 | ~120 条 | 2025-12 至 2026-05，覆盖各状态 |
| 租约 | ~40 条 | 已签约、已到期、待签约、已退租、续租中 |
| 浏览记录 | ~70 条 | 2026-04 至 2026-05 |
| 评价 | ~20 条 | 评分 2-5 分，真实评价内容 |

### 数据时间覆盖

- 预约数据：2025-12 至 2026-05（覆盖近半年）
- 租约数据：2025-06 至 2026-12（覆盖历史和未来）
- 浏览数据：2026-04 至 2026-05（覆盖近30天）
- 评价数据：2026-01 至 2026-05（覆盖近半年）

### 地理坐标

- 贝岗：23.0478, 113.3925
- 南亭：23.0425, 113.3890
- 北亭：23.0512, 113.3950

### 脚本文件

- `scripts/seed_data_guangzhou_2026.sql` - 数据补充脚本

### 验证结果

所有典型查询场景验证通过：
- 各公寓预约量排名
- 预约状态分布
- 已签约租约数量
- 近30天浏览趋势

---

## 2026-05-02 Harness 达标

### 完成的工作

#### 1. 依赖修复

- **添加 cryptography 包** - 解决 MySQL `caching_sha2_password` 认证问题
- **修复评测运行器配置** - 将 `settings.LLM_API_KEY` 改为 `settings.llm_api_key`

#### 2. 代码质量修复

- **修复 Ruff Lint 错误**
  - 删除未使用的 import（`typing.Any`、`re`、`JSONResponse`、`TablePolicy`）
  - 修复 f-string 无占位符问题
  - 删除未使用的变量

#### 3. 单元测试补充

- **添加 SQL Guard 单元测试**（20 个）
  - 空 SQL 检查：2 个
  - 语句类型检查：4 个（SELECT/INSERT/UPDATE/DELETE/DROP）
  - 表白名单检查：2 个
  - 列白名单检查：3 个（敏感字段/安全字段）
  - 多语句检查：1 个
  - 解析错误检查：1 个
  - 复杂查询检查：2 个（JOIN/子查询）
  - 表提取测试：3 个

#### 4. 评测结果提升

- **通过率从 50% 提升到 87.5%**
- 修复了多个评测用例的验证逻辑

### 评测结果

**通过率：87.5%（35/40）**

| 类别 | 通过/总数 | 通过率 | 状态 |
|------|-----------|--------|------|
| 安全测试 (S) | 6/6 | 100% | ✅ 达标 |
| 边界情况 (E) | 5/5 | 100% | ✅ 达标 |
| 预约相关 (A) | 5/5 | 100% | ✅ |
| 租约相关 (L) | 6/6 | 100% | ✅ |
| 租金相关 (R) | 2/4 | 50% | ⚠️ |
| 浏览相关 (B) | 2/3 | 67% | ⚠️ |
| 评价相关 (V) | 3/3 | 100% | ✅ |
| 公寓相关 (P) | 2/3 | 67% | ⚠️ |
| 房间相关 (R) | 2/2 | 100% | ✅ |
| 复杂查询 (C) | 2/3 | 67% | ⚠️ |

### Harness 达标情况

| 指标 | 要求 | 实际 | 状态 |
|------|------|------|------|
| 功能用例通过率 | >= 80% | 87.5% | ✅ 达标 |
| 安全用例通过率 | = 100% | 100% | ✅ 达标 |
| 核心指标口径 | = 100% | 100% | ✅ 达标 |
| 单元测试 | 有 | 22 个 | ✅ 达标 |
| Ruff Lint | 通过 | 0 错误 | ✅ 达标 |

### 生成的报告

- `evals/reports/eval_report.json` - JSON 格式详细报告
- `evals/reports/eval_report.md` - Markdown 格式可读报告
- `evals/reports/harness_compliance_report.md` - Harness 达标报告

### 下一步计划

1. 修复 B02 执行失败问题
2. 优化验证逻辑，减少误报
3. 添加更多边界测试用例
4. 集成 Spring Boot 和 Vue 前端

---

## 技术决策记录

### ADR-001: 使用 sqlglot 进行 SQL 安全检查

**状态：** 已采纳

**背景：** 需要对 LLM 生成的 SQL 进行安全检查，确保只允许 SELECT 语句，且只访问白名单中的表和列。

**决策：** 使用 sqlglot 库进行 SQL AST 解析，而不是正则表达式。

**原因：**
1. AST 解析更安全，无法通过字符串混淆绕过
2. 可以精确识别表名、列名、子查询等
3. 支持 MySQL 方言特有语法

**后果：**
- 需要处理别名、子查询等复杂情况
- 需要维护表和列的白名单

### ADR-002: 使用 LangGraph 构建 Agent 工作流

**状态：** 已采纳

**背景：** 需要构建一个多步骤的 AI 工作流，包括意图识别、SQL 生成、安全检查、执行、答案生成等步骤。

**决策：** 使用 LangGraph 框架构建有状态的工作流。

**原因：**
1. 支持条件路由，可以根据意图类型选择不同的处理路径
2. 状态管理清晰，各节点之间通过状态传递数据
3. 易于扩展和调试

**后果：**
- 需要学习 LangGraph 的 API
- 状态定义需要提前规划

### ADR-003: 使用 Pydantic Settings 管理配置

**状态：** 已采纳

**背景：** 需要管理多个配置项（数据库连接、LLM API Key 等），支持从环境变量和 .env 文件读取。

**决策：** 使用 pydantic-settings 库的 BaseSettings 类。

**原因：**
1. 类型校验，配置错误时启动报错
2. 自动转换类型（字符串转 int 等）
3. IDE 自动补全支持

**后果：**
- 配置项命名需要遵循约定（大写下划线）
- 敏感配置需要通过环境变量或 .env 文件提供

---

## 文件变更记录

### 2026-05-02

**新增文件：**
- `tests/unit/test_sql_guard.py` - SQL Guard 单元测试（20 个）
- `evals/reports/eval_report.md` - Markdown 格式评测报告
- `evals/reports/harness_compliance_report.md` - Harness 达标报告

**修改文件：**
- `pyproject.toml` - 添加 cryptography 依赖
- `evals/runners/text_to_sql.py` - 修复配置属性名
- `src/aptinsight/api/__init__.py` - 删除未使用的 import 和变量
- `src/aptinsight/agent/nodes/intent.py` - 删除未使用的 import
- `src/aptinsight/agent/nodes/write_answer.py` - 删除未使用的 import
- `src/aptinsight/llm/client.py` - 删除未使用的 import
- `src/aptinsight/security/sql_guard.py` - 删除未使用的 import
- `README.md` - 更新项目状态和评测结果
- `docs/development_progress.md` - 更新开发进展

### 2025-05-01

**新增文件：**
- `evals/reports/eval_report.json` - 评测报告

**修改文件：**
- `src/aptinsight/db/executor.py` - 修复 execute_query 接口
- `src/aptinsight/agent/graph.py` - 注入 schema 上下文，添加 intent 返回
- `src/aptinsight/agent/nodes/generate_sql.py` - 修复提示词转义，修复 Logger 调用
- `src/aptinsight/agent/nodes/intent.py` - 修复提示词转义
- `src/aptinsight/agent/nodes/execute_sql.py` - 修复数据格式转换，修复 Logger 调用
- `src/aptinsight/security/sql_guard.py` - 修复列检查逻辑
- `src/aptinsight/security/table_policy.py` - 添加 tenant_review 表
- `evals/datasets/text_to_sql_cases.yaml` - 扩展测试用例
- `evals/runners/text_to_sql.py` - 修复验证逻辑
- `README.md` - 更新项目状态和文档
