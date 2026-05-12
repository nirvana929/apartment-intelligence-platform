# AptInsight 系统失败原因定位指南

> **For agentic workers:** REQUIRED SUB-SKILL: Use systematic-debugging before changing code. This document is an investigation guide, not a fix plan. Do not modify source code until the root cause is recorded with evidence.

**Goal:** 定位 AptInsight 评测中真正属于系统链路失败的原因，排除 grader 误杀、图表偏好不一致和等价 SQL 未识别问题。

**Scope:** 只研究 AptInsight 主 Agent 链路错误：`classify_intent`、`generate_sql`、`guard_sql`、`execute_sql`、`build_chart`、`write_answer`。本轮不处理 `_validate_result()`、`must_contain`、`chart_type` 等 grader 问题。

**Key Files:**

- [Agent 图结构](../AptInsight/src/aptinsight/agent/graph.py)
- [意图识别节点](../AptInsight/src/aptinsight/agent/nodes/intent.py)
- [SQL 生成节点](../AptInsight/src/aptinsight/agent/nodes/generate_sql.py)
- [评测报告 JSON - MiMo](../AptInsight/evals/reports/eval_report.json)
- [评测报告 Markdown](../AptInsight/evals/reports/eval_report.md)
- [Text-to-SQL 用例集](../AptInsight/evals/datasets/text_to_sql_cases.yaml)
- [LLM Client](../AptInsight/src/aptinsight/llm/client.py)
- [配置](../AptInsight/src/aptinsight/core/config.py)
- [MiMo reasoning 问题记录](../AptInsight/docs/bug排错文档.md)

---

## 1. 先明确哪些失败算系统问题

本次只调查下面 4 条 MiMo 系统失败：

| Case | 用户问题 | 失败节点 | 当前现象 |
| --- | --- | --- | --- |
| V03 | 近一月/近半年评价趋势 | `classify_intent` | 被判为 `out_of_scope`，没有进入 SQL 生成 |
| P01 | 已发布公寓数量 / 公寓列表 | `classify_intent` | 被判为 `out_of_scope`，没有进入 SQL 生成 |
| C01 | 预约量高但签约量低的公寓有哪些 | `generate_sql` | intent 是 `analysis`，但 SQL 生成结果是 `null` |
| C03 | 租金和评分的关系是什么 | `classify_intent` | 被判为 `out_of_scope`，没有进入 SQL 生成 |

明确不调查这些 grader 类失败：

| Case | 不调查原因 |
| --- | --- |
| B02 | SQL 生成并执行成功，疑似 `DATE()` 与 `DATE_FORMAT` 的等价 SQL 未被 grader 接受 |
| L02 | SQL 生成并执行成功，疑似 chart_type / grader 记录不足 |
| R04 / P02 | 图表类型偏好不一致，不属于主系统链路故障 |

---

## 2. AptInsight 主链路地图

先阅读 [graph.py](../AptInsight/src/aptinsight/agent/graph.py)。

主链路是：

```text
用户问题
  ↓
classify_intent
  ↓
按 intent 分流
  ├─ analysis      -> generate_sql
  ├─ chitchat      -> write_answer
  └─ out_of_scope  -> write_answer

analysis 路径：
generate_sql
  ↓
guard_sql
  ↓
execute_sql
  ↓
build_chart
  ↓
write_answer
```

关键路由：

- `classify_intent` 返回 `analysis` 才能进入 `generate_sql`。
- `classify_intent` 返回 `out_of_scope` 会直接进入 `write_answer`，不会生成 SQL。
- `generate_sql` 没有写入 `generated_sql`，会走错误分支到 `write_answer`。

---

## 3. 调查任务 A：V03 / P01 / C03 为什么被判 out_of_scope

### 目标

证明这 3 条到底是：

1. prompt 分类标准不完整；
2. MiMo 模型误判；
3. LLM 返回 JSON 解析失败后被 fallback 成 `out_of_scope`；
4. 用户问题与 schema/指标口径真的不支持。

### 必读代码

- [intent.py](../AptInsight/src/aptinsight/agent/nodes/intent.py)

重点看：

- `INTENT_PROMPT` 分类标准；
- `analysis` 示例是否覆盖评价、公寓列表、租金评分关系；
- `out_of_scope` 示例是否让模型过度拒绝；
- `_parse_intent_response()` 是否因为 JSON 解析失败降级为 `out_of_scope`。

### 需要采集的证据

对 V03、P01、C03 分别记录：

```text
case_id:
question:
expected_intent:
actual_intent:
actual_sql:
error:
是否进入 generate_sql:
intent LLM 原始 response:
解析后的 intent:
解析后的 reason:
是否发生 JSON parse fallback:
```

当前报告中可直接读取：

- [eval_report.json](../AptInsight/evals/reports/eval_report.json)

但注意：当前 JSON 报告没有保存 `intent_reason` 和 LLM 原始 response。如果日志里也找不到，需要重新执行这 3 条单 case，并开启日志采集。重跑时只跑这 3 条，不要全量重跑。

### 逐项判断标准

#### V03

如果问题是“评价趋势 / 差评趋势”：

- 业务上应该属于 `analysis`；
- 可能需要 `tenant_review` 或评价相关表；
- 如果被判 `out_of_scope`，重点看 MiMo 是否把“差评”误认为隐私或敏感信息。

根因记录格式：

```text
V03 root cause:
- failure_node: classify_intent
- failure_type: intent_false_rejection
- evidence:
  - expected analysis, actual out_of_scope
  - intent response reason: ...
  - prompt gap: analysis examples do not mention review/rating/negative review trend
- conclusion:
  - This is a system intent boundary issue, not a grader issue.
```

#### P01

如果问题是“已发布公寓数量 / 公寓列表”：

- 业务上应该属于 `analysis`；
- `analysis` prompt 已写“公寓信息查询”；
- 如果仍判 `out_of_scope`，说明模型对“列出所有”或“公寓列表”理解过保守。

根因记录格式：

```text
P01 root cause:
- failure_node: classify_intent
- failure_type: intent_false_rejection
- evidence:
  - expected analysis, actual out_of_scope
  - prompt has apartment info query, but examples do not include list/count published apartments
  - intent response reason: ...
- conclusion:
  - This is a system intent classification issue.
```

#### C03

如果问题是“租金和评分的关系是什么”：

- 业务上应该属于 `analysis`；
- 它需要 `room_info`、`tenant_review`、`apartment_info`；
- 如果 MiMo 判 `out_of_scope`，要确认是因为 prompt 没提到评分/评价分析，还是模型认为“关系分析”超出范围。

根因记录格式：

```text
C03 root cause:
- failure_node: classify_intent
- failure_type: intent_false_rejection
- evidence:
  - expected analysis, actual out_of_scope
  - Qwen can pass same case, so schema likely supports it
  - intent response reason: ...
- conclusion:
  - This is a MiMo-specific intent boundary issue.
```

---

## 4. 调查任务 B：C01 为什么 SQL 生成 null

### 目标

证明 C01 的失败具体发生在 `generate_sql` 的哪一步：

1. LLM `content` 为空；
2. LLM content 有内容但不是 JSON；
3. JSON 中缺少 `sql` 字段；
4. `sql` 字段是 null / 空字符串；
5. `_validate_sql()` 判为无效；
6. max_tokens / reasoning_content 消耗导致输出缺失。

### 必读代码

- [generate_sql.py](../AptInsight/src/aptinsight/agent/nodes/generate_sql.py)
- [llm/client.py](../AptInsight/src/aptinsight/llm/client.py)
- [config.py](../AptInsight/src/aptinsight/core/config.py)
- [bug 排错文档：reasoning_content 问题](../AptInsight/docs/bug排错文档.md)

重点看 `generate_sql()`：

```text
读取 question/schema_context/metric_context
-> 拼 SQL_GENERATION_PROMPT
-> llm_client.chat()
-> _parse_sql_response(response)
-> _validate_sql(result["sql"])
-> 写入 generated_sql
```

### 需要采集的证据

对 C01 记录：

```text
case_id: C01
question: 预约量高但签约量低的公寓有哪些
actual_intent:
generated_sql:
error:
guard_passed:
execution_success:
raw SQL LLM response:
raw response content length:
raw response startswith:
是否包含 JSON:
是否包含 sql 字段:
sql 字段值:
是否触发 _parse_sql_response fallback:
是否触发 _validate_sql:
settings.llm_model_sql:
settings.llm_max_tokens_sql:
settings.llm_reasoning_effort:
```

### 判断标准

#### 如果 raw response content 为空

记录为：

```text
failure_type: llm_empty_content
likely_cause: MiMo reasoning_content consumed output budget
evidence:
  - content length = 0
  - generated_sql = null
  - model = mimo-v2.5-pro
  - max_tokens_sql = ...
  - reasoning_effort = ...
```

#### 如果 content 有内容但没有 JSON

记录为：

```text
failure_type: sql_response_parse_failed
likely_cause: SQL generation prompt did not force stable JSON output for this complex case
evidence:
  - raw response contains text but no JSON object
  - _parse_sql_response could not find JSON
```

#### 如果 JSON 有 `sql: null`

记录为：

```text
failure_type: llm_returned_null_sql
likely_cause: model declined or failed to synthesize multi-table query
evidence:
  - raw response JSON has sql null
  - expected tables: view_appointment, lease_agreement, apartment_info
```

#### 如果 SQL 存在但 `_validate_sql()` 拒绝

记录为：

```text
failure_type: generated_sql_invalid
likely_cause: generated non-SELECT, multi-statement, empty SQL, or unsafe keyword
evidence:
  - validation_error: ...
  - generated_sql: ...
```

---

## 5. 最小复现建议

不要全量重跑。只复现系统问题 case：

```text
V03
P01
C01
C03
```

建议做一个临时 filtered YAML，只包含这 4 条，或在 runner 中通过 case id 过滤。不要提交临时文件，除非团队决定保留它作为 debug suite。

每条 case 只需要 1-3 次 trial：

- 如果每次都失败：稳定系统缺陷；
- 如果偶发失败：模型稳定性问题；
- 如果重跑通过：历史报告可能受模型状态、token、并发或环境影响，需要记录为 flaky。

---

## 6. 最终记录模板

调查完成后，在新文档中记录每条系统失败：

```markdown
## Case C01 - 预约量高但签约量低的公寓有哪些

**Expected path**

classify_intent -> generate_sql -> guard_sql -> execute_sql -> build_chart -> write_answer

**Actual path**

classify_intent -> generate_sql -> write_answer

**Failure node**

generate_sql

**Observed state**

- intent:
- generated_sql:
- error:
- guard_passed:
- execution_success:

**Raw LLM evidence**

```text
paste short sanitized raw response excerpt here
```

**Root cause**

One of:
- intent_false_rejection
- llm_empty_content
- sql_response_parse_failed
- llm_returned_null_sql
- generated_sql_invalid
- metric_semantics_wrong
- flaky_model_output

**Why this is a system issue**

Explain why this failure happened before grader validation and affected the main user-facing path.

**Suggested fix direction**

Keep it high-level. Do not implement in this investigation document.
```

---

## 7. Expected Deliverable

The investigating agent should produce one Markdown report:

```text
docs/aptinsight-system-failure-root-cause-report.md
```

The report must include:

- confirmed system failure count;
- one section per case: V03, P01, C01, C03;
- exact failing node;
- actual path vs expected path;
- evidence from report JSON and raw logs or rerun trace;
- root cause category;
- whether the issue is deterministic or flaky;
- suggested fix direction.

Do not include grader-only failures in the system failure count.

