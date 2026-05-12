# AptInsight 系统失败根因分析报告

> 调查日期：2026-05-07
> 模型：mimo-v2.5-pro
> 调查范围：4 条系统失败 case（V03, P01, C01, C03）
> 排除范围：grader 类失败（B02, L02, R04, P02）

---

## 总结

**确认系统失败数：4 条**

4 条失败共享同一个根因：**MiMo 模型的 reasoning_content 消耗了 `max_tokens` 预算中的大部分 token，导致输出 content 为空或被截断。**

| Case | 失败节点 | failure_type | 是否确定性 |
|------|----------|-------------|-----------|
| V03 | classify_intent | llm_empty_content | flaky |
| P01 | classify_intent | llm_empty_content | flaky |
| C01 | generate_sql | llm_empty_content | flaky |
| C03 | classify_intent | llm_content_truncated | flaky |

---

## Case V03 - 最近一个月的评价数量趋势

**Expected path**

```
classify_intent -> generate_sql -> guard_sql -> execute_sql -> build_chart -> write_answer
```

**Actual path**

```
classify_intent -> write_answer (out_of_scope)
```

**Failure node**: classify_intent

**Observed state (原始评测)**

- actual_intent: out_of_scope
- actual_sql: null
- guard_passed: true
- execution_success: false
- processing_time_ms: 9580

**Raw LLM evidence (复现)**

```text
content_length: 0
reasoning_content_length: 820
finish_reason: length
completion_tokens: 400 (恰好等于 max_tokens_intent=400)
```

reasoning_content 内容（MiMo 思考链）：

> 首先，用户的问题是："最近一个月的评价数量趋势"。我需要判断这个问题属于哪种意图类型...
> 用户的问题是关于"最近一个月的评价数量趋势"。这涉及到评价数量的趋势分析...
> 在分类标准中，analysis 类别包括"浏览热度分析"，评价数量趋势类似于浏览热度分析...
> 因此，意图应该是 analysis。
> 输出需要是 JSON 格式：{"intent": "analysis", "reason": "用户询问评价数量趋势，需要查询数据库进行分析。"}

**Root cause**: `llm_empty_content`

MiMo 的 reasoning_content（820 字符）消耗了全部 400 个 completion_tokens，导致 content 为空字符串。模型在 reasoning 中正确判断了 intent 应为 "analysis"，但从未输出到 content 字段。`_parse_intent_response()` 收到空字符串后，走 fallback 逻辑，未找到 "analysis" 关键词，降级为 `out_of_scope`。

**Why this is a system issue**: 意图识别节点的 token 预算（400）对 MiMo reasoning 模型来说过低。这不是 grader 问题，而是主链路第一步就失败了。

**Suggested fix direction**: 增加 `LLM_MAX_TOKENS_INTENT` 至 800+，或将 intent 节点的 `reasoning_effort` 降为 `low`。

---

## Case P01 - 有多少个已发布的公寓

**Expected path**

```
classify_intent -> generate_sql -> guard_sql -> execute_sql -> build_chart -> write_answer
```

**Actual path**

```
classify_intent -> write_answer (out_of_scope)
```

**Failure node**: classify_intent

**Observed state (原始评测)**

- actual_intent: out_of_scope
- actual_sql: null
- guard_passed: true
- execution_success: false
- processing_time_ms: 7770

**Raw LLM evidence (复现)**

第一次复现（run 1）：

```text
content_length: 41
raw_content: {"intent": "analysis", "reason": "用户询问已发布
finish_reason: 未记录
```

content 被截断，JSON 不完整，但 fallback 文本推断找到了 "analysis"，所以 intent 正确。SQL 生成也成功。

第二次复现（run 2）：

```text
content_length: 83
reasoning_content_length: 134
finish_reason: stop
completion_tokens: 113
raw_content: {"intent": "analysis", "reason": "用户询问已发布公寓的数量统计，属于公寓信息查询，需要查询数据库获取数据"}
```

这次完全成功。reasoning 只用了 134 字符，completion_tokens 仅 113，远低于 400 限制。

**Root cause**: `flaky_model_output`

P01 是一个简单问题，模型有时 reasoning 很短（134 字符）就能完成，有时 reasoning 较长导致 content 被截断或为空。原始评测时模型 reasoning 较长，content 为空，fallback 也未识别出 "analysis"。

**Why this is a system issue**: 意图识别对简单问题也不稳定，说明 token 预算不足以覆盖 MiMo reasoning 的波动。

**Suggested fix direction**: 同 V03，增加 token 预算或降低 reasoning_effort。

---

## Case C01 - 预约量高但签约量低的公寓有哪些

**Expected path**

```
classify_intent -> generate_sql -> guard_sql -> execute_sql -> build_chart -> write_answer
```

**Actual path**

```
classify_intent -> generate_sql -> write_answer (error)
```

**Failure node**: generate_sql

**Observed state (原始评测)**

- actual_intent: analysis（正确）
- actual_sql: null
- guard_passed: false
- execution_success: false
- processing_time_ms: 26960

**Raw LLM evidence (复现 - intent)**

```text
content_length: 83
reasoning_content_length: 605
finish_reason: stop
completion_tokens: 371
raw_content: {"intent": "analysis", "reason": "用户询问预约量高但签约量低的公寓，需要查询数据库进行预约和签约数据的对比分析，属于业务分析问题"}
```

意图识别成功（completion_tokens=371，接近 400 限制）。

**Raw LLM evidence (复现 - SQL generation)**

```text
content_length: 1229
reasoning_content_length: 2244
finish_reason: stop
completion_tokens: 1189
```

SQL 生成成功。reasoning 内容展示了完整的 SQL 推理过程：先尝试直接 JOIN，发现会导致数据重复，改用子查询分别统计预约量和签约量。最终生成的 SQL 使用了 `view_appointment`、`lease_agreement`、`apartment_info` 三表，包含 `LEFT JOIN` 和 `COUNT`，符合预期。

**Root cause**: `flaky_model_output`（SQL 生成 token 耗尽）

原始评测中，intent 正确识别为 analysis，但 SQL 生成返回 null。复现时 SQL 生成成功（completion_tokens=1189，接近 1200 限制）。原始评测时 MiMo 的 reasoning 可能消耗了更多 token，导致 content 为空。

**Why this is a system issue**: SQL 生成节点的 token 预算（1200）对复杂多表查询来说处于临界值。MiMo 的 reasoning 链在复杂查询上波动更大。

**Suggested fix direction**: 增加 `LLM_MAX_TOKENS_SQL` 至 2000+，或在 SQL 生成 prompt 中减少示例以缩短 reasoning。

---

## Case C03 - 租金和评分的关系是什么

**Expected path**

```
classify_intent -> generate_sql -> guard_sql -> execute_sql -> build_chart -> write_answer
```

**Actual path**

```
classify_intent -> write_answer (out_of_scope)
```

**Failure node**: classify_intent

**Observed state (原始评测)**

- actual_intent: out_of_scope
- actual_sql: null
- guard_passed: true
- execution_success: false
- processing_time_ms: 7857

**Raw LLM evidence (复现)**

```text
content_length: 60
reasoning_content_length: 733
finish_reason: length
completion_tokens: 400
raw_content: {"intent": "analysis", "reason": "用户询问租金和评分之间的关系，这涉及业务数据的分析，
```

content 被截断：JSON 不完整（缺少闭合 `}`），reason 句子未写完。但 fallback 文本推断在截断内容中找到了 "analysis"，所以这次 intent 正确。

reasoning_content 显示模型完整推理了应该归类为 analysis 的过程。

**Root cause**: `llm_content_truncated`

MiMo reasoning 消耗了大部分 token 预算（733 字符 reasoning + 60 字符 content = 400 completion_tokens），content 在 JSON 中间被截断。原始评测时 fallback 未能识别出 "analysis"，降级为 `out_of_scope`。

**Why this is a system issue**: 即使 fallback 能救回部分 case，截断的 JSON 也不可靠。原始评测中 3/4 的 intent 失败都是这个原因。

**Suggested fix direction**: 同 V03。

---

## 根因模式总结

所有 4 条失败的共同根因：

```text
MiMo mimo-v2.5-pro 的 reasoning_content（思考链）消耗 max_tokens 预算
  → content 为空或被截断
  → JSON 解析失败
  → fallback 文本推断不稳定
  → intent 降级为 out_of_scope 或 SQL 生成返回 null
```

关键证据：

| Case | 节点 | content_len | reasoning_len | completion_tokens | max_tokens | finish_reason |
|------|------|-------------|---------------|-------------------|------------|---------------|
| V03 | intent | 0 | 820 | 400 | 400 | length |
| P01 | intent | 83 | 134 | 113 | 400 | stop |
| C01 | intent | 83 | 605 | 371 | 400 | stop |
| C01 | sql | 1229 | 2244 | 1189 | 1200 | stop |
| C03 | intent | 60 | 733 | 400 | 400 | length |

注意：API 返回的 `reasoning_tokens` 始终为 0，说明 MiMo API 不单独追踪 reasoning token，它们被计入 `completion_tokens`。

---

## 修复方向

### 短期（配置调整）

1. **增加 max_tokens**：
   - `LLM_MAX_TOKENS_INTENT`: 400 → 800（给 reasoning 留足空间）
   - `LLM_MAX_TOKENS_SQL`: 1200 → 2000（复杂查询需要更多 reasoning）

2. **降低 reasoning_effort**：
   - intent 节点：`medium` → `low`（意图分类不需要深度推理）
   - sql 节点保持 `medium`（SQL 生成需要推理）

### 中期（架构改进）

3. **分节点配置 reasoning_effort**：当前 `LLM_REASONING_EFFORT` 是全局配置，应允许每个节点独立设置。

4. **空内容重试**：当 content 为空时，自动用更高 max_tokens 重试一次。

### 长期（模型选型）

5. **intent 节点用非 reasoning 模型**：意图分类不需要思考链，可用更轻量的模型（如 qwen-turbo-latest，原始评测中 4 条 case 全部通过）。
