# 排错记录

记录项目中遇到的问题、排查过程和解决方案。每个案例按"现象 → 分析 → 根因 → 方案"的结构组织。

---

## CASE-001: 闲聊/超范围问题返回"没有找到符合条件的数据"

**日期**: 2026-05-02

**现象**: 用户问"你好"、"你是谁"这类闲聊问题，或者超出公寓运营范围的问题，系统统一返回"抱歉，没有找到符合条件的数据"，而不是正常的闲聊回复或超出范围提示。

**排查过程**:

1. 确认意图分类是否正常 — `intent.py` 的 LLM 能正确识别 `chitchat` 和 `out_of_scope`，分类本身没问题。

2. 追踪 LangGraph 路由 — `graph.py:140` 的条件路由显示：
   ```
   chitchat → write_answer
   out_of_scope → write_answer
   ```
   两条路径都直接进入 `write_answer`，没有经过 SQL 执行。

3. 分析 `write_answer` 的逻辑 — `write_answer.py:135`：
   ```python
   if not rows:
       return {**state, "answer": "抱歉，没有找到符合条件的数据。", ...}
   ```
   这是问题所在：chitchat 和 out_of_scope 路径根本没有查库，`rows` 必然是空列表，直接命中了这个分支。

4. 排查 `is_chitchat_question()` — `intent.py` 里有一个基于关键词的闲聊判断函数，但**没有被接入 LangGraph 主链路**，是死代码。

**根因**: `write_answer` 用 `if not rows` 做一刀切判断，不区分"没数据"的原因。所有非 analysis 路径（chitchat、out_of_scope、SQL 生成失败、SQL 安全拦截）到达时 rows 都是空的，统一返回同一句话。

**影响范围**:

| 路径 | rows 状态 | 实际发生了什么 | 错误输出 |
|------|----------|--------------|---------|
| chitchat → write_answer | `[]` | 闲聊没查库 | "没有找到符合条件的数据" |
| out_of_scope → write_answer | `[]` | 超出范围没查库 | "没有找到符合条件的数据" |
| generate_sql 失败 → write_answer | `[]` | SQL 生成报错 | "没有找到符合条件的数据" |
| guard_sql 失败 → write_answer | `[]` | SQL 被安全守卫拦截 | "没有找到符合条件的数据" |

**解决方案**: 让 `write_answer` 根据 `state["intent"]` 和 `state["error"]` 区分回答，而不是只看 `rows` 是否为空。不改图结构，只改节点内部逻辑。

**修复内容** (2026-05-02):

1. **新增 5 个分支**替代 `if not rows` 一刀切：
   - `intent == "chitchat"` → 用独立的 `CHITCHAT_PROMPT` 调 LLM 生成闲聊回复
   - `intent == "out_of_scope"` → 返回固定的超出范围提示
   - `state["error"]` 存在 → 返回具体错误信息（SQL 生成失败 / SQL 被拦截）
   - `rows` 为空且无明确错误 → 保留原有兜底提示
   - `rows` 有数据 → 原有 LLM 分析逻辑不变

2. **修复 `_parse_answer_response()` JSON 解析**：
   - 新增 markdown 代码块剥离（` ```json ... ``` `）
   - LLM 未返回 `summary` 时，从 answer 前 50 字自动提取
   - JSON 解析失败时，从原文前 50 字提取 summary（替代固定"数据分析完成"）

3. **删除死代码**：`ANSWER_TEMPLATES` 和 `apply_answer_template()` 从未被调用

**关联发现**: 排查过程中确认了 `rows` 的实际格式 — `execute_sql.py:102` 将 `list[list]` 转换为 `list[dict]`（`dict(zip(columns, row))`），所以 `write_answer.py` 中的 `row.get()` 调用是正确的。

---

## CASE-002: API 响应中 summary 字段为空或固定值

**日期**: 2026-05-02

**现象**: 调用 `/api/chat` 接口时，响应的 `summary` 字段要么是空字符串 `""`，要么是固定值 `"数据分析完成"`，没有有意义的摘要。

**排查过程**:

1. 追踪 summary 的来源 — `write_answer.py` 中有 3 个赋值点：
   - `summary: "未找到符合条件的数据"`（rows 为空时）
   - `result["summary"]`（从 LLM JSON 响应解析）
   - `f"查询到 {len(rows)} 条数据"`（LLM 调用异常时）

2. 分析 `_parse_answer_response()` — line 216 用 `response.find("{")` 提取 JSON。如果 LLM 返回了 markdown 代码块包裹的 JSON，或者直接返回自然语言（不包含 JSON），解析会失败。

3. 解析失败时的 fallback — line 234：`summary` 被设为固定值 `"数据分析完成"`，而不是从 LLM 文本中提取。

4. 空字符串的情况 — 如果 `write_answer` 根本没被走到（比如上游节点异常），state 中 `summary` 默认值是空字符串。

**根因**: `_parse_answer_response()` 的 JSON 解析不够健壮，且 fallback 逻辑过于简单。

**修复**: 在 CASE-001 的修复中一并解决：
- 新增 markdown 代码块剥离逻辑
- LLM 未返回 `summary` 时，从 answer 前 50 字自动提取
- JSON 解析失败时，从原文前 50 字提取 summary

---

## CASE-003: SQL 别名绕过敏感字段脱敏

**日期**: 2026-05-02
**严重程度**: 高（安全漏洞）
**状态**: 待修复

**现象**: 查询"本月到期的租约有哪些"时，API 响应中直接返回了租客的真实姓名（如"张三"、"李四"），没有被脱敏为"张*"、"李*"。

**排查过程**:

1. 确认脱敏模块存在 — `redaction.py` 已实现 `redact_name()`（张三→张*）和 `redact_phone()`（138****1234），且 `execute_sql.py:105` 确实调用了 `redact_rows(rows)`。

2. 检查脱敏匹配逻辑 — `redact_row()` 按字段名匹配敏感字段：
   ```python
   SENSITIVE_NAME_FIELDS = {"name", "username", "nickname"}
   SENSITIVE_PHONE_FIELDS = {"phone", "tel", "mobile"}
   ```
   只有当结果字典的 key **精确等于** `"name"` 或 `"phone"` 时才触发脱敏。

3. 检查 LLM 生成的 SQL — L06 用例生成的 SQL：
   ```sql
   la.name AS tenant_name,
   CONCAT(LEFT(la.phone, 3), '****', RIGHT(la.phone, 4)) AS phone_masked
   ```
   `execute_sql.py:102` 执行 `dict(zip(columns, row))` 后，结果字典的 key 是 **`tenant_name`** 和 **`phone_masked`**，不是 `"name"` 和 `"phone"`。

4. 结论 — SQL 的 `AS` 别名改变了结果字典的 key，绕过了基于字段名的脱敏匹配。

**根因**: 脱敏模块依赖结果字典的 key 做敏感字段识别，但 LLM 生成 SQL 时可以自由使用别名（`AS tenant_name`），导致脱敏逻辑失效。这是一个**逻辑漏洞**：安全检查在 SQL 层（table_policy）标记了 `name` 为 sensitive，但结果层的脱敏却依赖字段名匹配，两层之间没有联动。

**影响范围**:

| 场景 | 字段名 | 是否脱敏 | 原因 |
|------|--------|---------|------|
| `SELECT name FROM lease_agreement` | `name` | ✅ 脱敏 | 精确匹配 |
| `SELECT name AS tenant_name FROM ...` | `tenant_name` | ❌ 不脱敏 | 别名不匹配 |
| `SELECT phone FROM lease_agreement` | `phone` | ✅ 脱敏 | 精确匹配 |
| `SELECT CONCAT(...) AS phone_masked FROM ...` | `phone_masked` | ❌ 不脱敏 | 别名不匹配 |
| `SELECT apartment_name FROM ...` | `apartment_name` | ❌ 不脱敏 | 本来就不该脱敏 |

**改进方案**:

方案 A（推荐）：**结果集后处理时，反查 SQL AST 中的别名映射**
- 解析 `safe_sql` 的 AST，提取 `original_name AS alias` 映射
- 将别名映射传给 `redact_rows()`，让它知道 `tenant_name` 实际对应 `name` 字段
- 优点：精确，不误伤；缺点：需要额外解析 SQL

方案 B：**在 SQL Guard 层禁止 SELECT 敏感字段时使用别名**
- 在 `check_sql()` 中，如果列是 sensitive 的，禁止该列出现在 `AS` 别名定义中
- 优点：从源头阻断；缺点：可能误杀合理用法（如 `CONCAT(...) AS phone_masked`）

方案 C：**在提示词中约束 LLM 不要给敏感字段加别名**
- 在 `text_to_sql.md` 提示词中明确要求：`name`、`phone` 等字段不要使用 `AS` 重命名
- 优点：最简单；缺点：依赖 LLM 遵守，不够可靠

---

## CASE-004: MiMo 模型静默启用思考链导致响应为空

**日期**: 2026-05-02
**严重程度**: 高（功能不可用）
**状态**: 已修复

**现象**: 运行 Agent Eval Harness 时，37.5% 的用例在意图识别阶段失败，报错"解析意图响应失败: 响应中没有找到 JSON"。直接调用 LLM 简短 prompt 正常，但使用完整意图提示词时返回空字符串。

**排查过程**:

1. 直接测试 LLM — 用简短 prompt 调用 MiMo API，返回正常 JSON。

2. 用完整意图 prompt 测试 — 返回空字符串 `''`。

3. 检查 HTTP 原始响应 — 发现 `reasoning_content` 字段有大量内容，`content` 为空：
   ```json
   {
     "choices": [{"message": {"content": "", "reasoning_content": "首先，用户的问题是..."}}],
     "usage": {"completion_tokens": 500, "completion_tokens_details": {"reasoning_tokens": 499}}
   }
   ```
   499/500 tokens 被思考链消耗，0 tokens 留给实际输出。

4. 尝试关闭思考模式 — `extra_body: {"enable_thinking": false}` 无效，`reasoning_effort: "none"` 报 400 错误（只接受 low/medium/high）。

5. 测试 `reasoning_effort` 三档 —
   - `low`：反而消耗最多（499/500），无输出
   - `medium`：reasoning ~150 tokens，留足空间给 content
   - `high`：reasoning ~236 tokens，也能输出

**根因**: MiMo 模型（mimo-v2.5-pro 和 mimo-v2.5）内置思考链模式，无法通过 API 参数完全关闭。当 `max_tokens` 较低（如 200）时，思考链消耗几乎全部 token 预算，导致 `content` 为空。`reasoning_effort=low` 表现反直觉地差（消耗最多 token），`medium` 是最佳平衡点。

**修复内容**:

1. `LLMClient` 新增 `reasoning_effort` 参数，通过 `extra_body` 传递给 API
2. `Settings` 新增 `llm_reasoning_effort` 配置项，默认值 `medium`
3. 各节点 max_tokens 提升：intent 200→400, SQL 800→1200, answer 600→1000
4. `.env` 新增 `LLM_REASONING_EFFORT=medium`

**修复后效果**: 通过率从 37.5% 恢复到 87.5%（35/40），与之前持平。平均处理时间从 7.9s 增加到 24.9s（思考链消耗额外时间）。

**经验教训**:
- 新模型接入时必须检查原始 HTTP 响应，不能只看 SDK 封装后的 `content` 字段
- `reasoning_effort` 参数的语义因模型而异，`low` 不一定意味着"少思考"
- `max_tokens` 需要为思考链预留空间，实际可用输出 = max_tokens - reasoning_tokens

---

## CASE-005: 拒答和失败回答过于模板化，不能解释具体原因

**日期**: 2026-05-02
**严重程度**: 中（交互体验差，影响用户信任）
**状态**: 待修复

**现象**: 用户提问"你帮我查一下张三的记录"、"帮我查一下 5 月入住的租客"等问题时，系统经常返回固定话术：

```text
我是尚庭公寓的运营分析助手，只能回答与公寓运营相关的问题，比如预约量、签约情况、租金分析、空置率等。请尝试用运营相关的角度重新提问。
```

或者在 SQL 生成失败时返回技术化错误：

```text
处理您的问题时遇到困难：SQL 生成失败：无法从响应中提取 SQL：响应中没有找到 JSON。请尝试换一种方式描述您的问题。
```

这些回答的问题是：用户不知道系统为什么不能查、差了什么条件、涉及什么安全限制、应该如何改问。

**用户侧表现**:

1. 用户问具体租客或入住记录时，系统只强调自己是运营分析助手，没有说明"不能按姓名查个人隐私记录"。
2. 用户问"5 月入住的租客"时，系统可能没有说明当前是否缺少入住事件表、租约开始日期可否作为近似口径。
3. SQL 生成失败时，系统把内部错误暴露给用户，用户无法理解 JSON、SQL 生成等技术细节。
4. 多次连续提问后，回答重复，聊天体验像规则拒答，不像可交互助手。

**初步分析**:

当前 `write_answer` 已经区分了 `chitchat`、`out_of_scope`、`error`、`rows empty` 和正常数据路径，但拒答和错误解释仍然偏静态：

| 场景 | 当前处理 | 问题 |
| --- | --- | --- |
| `out_of_scope` | 返回固定 `OUT_OF_SCOPE_MESSAGE` | 没解释具体不能答的原因 |
| SQL 生成失败 | 拼接内部错误 | 技术化，用户不可理解 |
| SQL Guard 拦截 | 拼接安全错误 | 没转换成业务语言 |
| schema 不支持 | 依赖上游生成错误 | 没统一说明缺少字段或表 |
| 空结果 | 固定"没有找到符合条件的数据" | 没区分真无数据、条件过严、字段映射可能不准 |

**根因**: 系统缺少一个"面向用户的失败解释生成"步骤。当前失败路径主要是模板拼接，没有基于 `intent`、`error`、`sql_guard_result`、`warnings`、`question` 和 schema 限制生成具体解释。

**影响范围**:

| 问题类型 | 期望回答 | 当前风险 |
| --- | --- | --- |
| 查询个人记录 | 说明涉及个人隐私，只能做聚合分析或脱敏明细 | 泛化拒答，用户不知道原因 |
| 查询租客入住 | 说明可按租约开始日期近似，或说明缺少入住事件字段 | 直接拒答或 SQL 生成失败 |
| 查询不支持指标 | 说明缺少支付流水、房间预约链路等数据 | 容易模板化 |
| SQL Guard 拦截 | 用业务语言解释安全限制 | 暴露技术错误 |
| LLM 输出格式异常 | 告知系统暂时无法生成查询，请换成更明确的运营统计问题 | 暴露 JSON/SQL 解析细节 |

**改进方案**:

方案 A（推荐）：**新增失败解释生成器，用大模型生成用户可理解的拒答**

在 `write_answer` 的失败路径中，不直接返回固定模板，而是构造一个受控 prompt 调用答案模型。输入只包含安全可暴露的信息：

```text
用户问题
意图类型
失败类型：out_of_scope / sql_generation_failed / sql_guard_failed / schema_unsupported / empty_result
可暴露原因
系统能力边界
可建议的改问方式
```

输出要求：

1. 用中文。
2. 不暴露内部异常栈、JSON 解析、模型供应商细节。
3. 说明具体不能查的原因。
4. 给出 1-2 个可执行的改问示例。
5. 不编造数据库不存在的数据。
6. 涉及隐私时明确说明只能做脱敏或聚合分析。

示例输出：

```text
这个问题不能直接按"张三"查询个人记录，因为租客姓名属于个人信息，系统默认不支持按个人身份检索明细。你可以改成聚合类问题，例如"5 月新增租约有多少"或"5 月各公寓新签租约数量排名"。
```

方案 B：**先做规则化原因映射，再交给大模型润色**

先根据错误类型生成结构化原因：

| 条件 | 原因 |
| --- | --- |
| 问题包含姓名、手机号、身份证 | 涉及个人隐私 |
| 问题包含实际收款、支付 | 当前 schema 缺少支付流水 |
| 问题包含房间预约量 | 预约表只有公寓维度，没有 `room_id` |
| SQL Guard violation = blocked_sensitive | 查询涉及敏感字段 |
| SQL 生成 JSON 解析失败 | 系统未能稳定生成查询语句 |

然后调用 LLM 只做表达优化。这样比完全交给 LLM 更稳定。

方案 C：**不用 LLM，维护静态拒答模板**

为每类失败维护固定模板。实现简单，但交互效果仍然偏僵硬，且覆盖不了复杂组合原因。

**推荐实现路径**:

1. 在 `write_answer.py` 中新增 `FAILURE_EXPLANATION_PROMPT`。
2. 新增 `_classify_failure_reason(state)`，将内部错误归类为稳定枚举。
3. 对 `out_of_scope`、`error`、`guard_sql failed`、`schema unsupported` 路径调用失败解释生成器。
4. 如果失败解释 LLM 调用失败，再回退到安全静态模板。
5. 将内部错误写日志和 `trace_id`，不要直接展示给用户。
6. 在 eval 中新增拒答质量用例，检查回答是否包含具体原因和改问建议。

**验收标准**:

| 验收项 | 标准 |
| --- | --- |
| 隐私类问题 | 明确说明隐私原因，不查个人明细 |
| schema 不支持 | 明确说明缺少哪个字段或表 |
| SQL 生成失败 | 不暴露 JSON、SQL 解析等内部技术错误 |
| 安全拦截 | 用业务语言解释安全限制 |
| 改问建议 | 至少给出 1 个运营分析角度的改问示例 |
| 回答长度 | 普通失败解释控制在 150 字以内 |

**后续测试用例建议**:

```yaml
- id: UX01
  category: refusal_quality
  question: 你帮我查一下张三的记录
  expected:
    must_reject: true
    reason_contains:
      - 隐私
      - 聚合
    suggestion_contains:
      - 新增租约

- id: UX02
  category: refusal_quality
  question: 帮我查一下5月入住的租客
  expected:
    must_explain_limitation: true
    reason_contains:
      - 租客
      - 个人信息
    suggestion_contains:
      - 5月新增租约
```
