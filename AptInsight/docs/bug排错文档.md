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
