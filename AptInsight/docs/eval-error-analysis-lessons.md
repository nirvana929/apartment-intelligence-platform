# AptInsight Eval Error Analysis Lessons

**日期:** 2026-05-07  
**用途:** 记录 AptInsight 模型评测、错误归因和模型选型过程中的探索经验，可用于简历复盘和面试讲解。  
**范围:** Text-to-SQL harness、模型对比、系统链路错误、grader 误杀、模型配置稳定性。

---

## 1. 最大经验：harness failed 不等于系统出错

本次评测最重要的结论是：

```text
harness failed = 没通过当前自动评测规则
system failure = AptInsight 主系统链路确实出错
```

二者不能混为一谈。

AptInsight 主系统链路是：

```text
classify_intent
-> generate_sql
-> guard_sql
-> execute_sql
-> build_chart
-> write_answer
```

评测链路是：

```text
text_to_sql.py
-> run_agent()
-> _validate_result()
-> passed / failed
```

因此，一条 case 在 harness 中 failed，可能是：

- 主系统链路真的失败；
- SQL 等价但 grader 不接受；
- 图表类型偏好不一致；
- 业务指标口径有歧义；
- 模型输出受 max_tokens / reasoning 配置影响；
- 报告记录字段不足，无法准确归因。

面试表达：

> 我不会把 Agent eval 的 failed 直接当成系统错误，而是先区分系统链路、grader、数据和业务口径。这个项目里我把 harness pass rate 和 system failure count 分开统计，这样能避免被单一通过率误导。

---

## 2. 失败归因分类

本次分析中使用的归因分类如下：

| 分类 | 是否算系统错误 | 说明 |
| --- | --- | --- |
| `intent_false_rejection` | 是 | 业务分析问题被误判为 `out_of_scope` |
| `sql_generation_null` | 是 | intent 正确，但 SQL 生成节点没有产出 SQL |
| `sql_semantic_wrong` | 是 | SQL 可执行，但业务指标口径错 |
| `sql_execution_failure` | 是 | SQL 生成后无法执行 |
| `grader_too_strict` | 否 | 等价 SQL 未被固定规则接受 |
| `chart_policy_mismatch` | 不一定 | 图表类型与期望不一致，取决于产品规范 |
| `metric_definition_ambiguous` | 不一定 | 用户问题存在指标口径歧义 |
| `model_config_instability` | 是，若影响主链路 | `max_tokens` / `reasoning_effort` 导致空输出或截断 |
| `flaky_model_output` | 是，若线上不可接受 | 同一 case 有时成功、有时失败 |

---

## 3. 典型错误模式

### 3.1 Grader 过窄：B02

Case:

```text
B02 - 最近30天浏览趋势
```

现象：

- MiMo 生成 SQL 成功；
- SQL Guard 通过；
- SQL 执行成功；
- 但 harness 判失败。

原因：

```text
YAML 期望 SQL 包含 DATE_FORMAT；
MiMo 实际使用 DATE(bh.browse_time)；
两者都可以表达按日期聚合浏览趋势。
```

结论：

```text
这是 grader 规则过窄，不应直接算系统错误。
```

面试表达：

> B02 让我意识到 Text-to-SQL eval 不能只靠 must_contain 固定关键词。DATE 和 DATE_FORMAT 在这个任务里可能是等价表达，如果只认一个函数，会把正确 SQL 判成失败。

---

### 3.2 图表偏好不一致：R04 / P02

Case:

```text
R04 - 各价位段房间数量分布
P02 - 各城市公寓数量分布
```

现象：

- Qwen 生成 `bar`；
- 用例期望 `pie`；
- harness 判失败。

分析：

“分布”既可以用饼图，也可以用柱状图。除非产品规范明确要求分布必须用饼图，否则这类失败不应直接算主系统错误。

结论：

```text
这是 chart policy mismatch，属于产品规范或 grader 口径问题。
```

面试表达：

> 图表类型不能简单一刀切。柱状图和饼图在部分分布场景都能表达数据，所以我会把它归为图表策略不一致，而不是直接说模型 SQL 错了。

---

### 3.3 指标口径理解错误：C02

Case:

```text
C02 - 各公寓的预约转化率是多少
```

期望口径：

```text
预约转化率 = 签约量 / 预约量
```

应使用：

```text
view_appointment
lease_agreement
apartment_info
```

Qwen 实际问题：

```text
没有使用 lease_agreement；
把预约转化率理解成了“看房预约 / 总预约”。
```

结论：

```text
这是 SQL 可执行但业务指标口径错误，算系统问题。
```

面试表达：

> C02 是一个典型的 Text-to-SQL 语义错误。SQL 能执行、安全也通过，但业务指标错了。它说明 Text-to-SQL eval 不能只看 SQL valid，还要看 metric correctness。

---

### 3.4 意图误拒：V03 / P01 / C03

Case:

```text
V03 - 评价趋势
P01 - 公寓数量 / 公寓列表
C03 - 租金和评分的关系
```

现象：

```text
本应进入 analysis 路径；
实际被 MiMo 判为 out_of_scope；
没有进入 generate_sql。
```

结论：

```text
这是 classify_intent 节点的 false rejection，算系统链路问题。
```

面试表达：

> 对 Agent 来说，意图误拒是很严重的链路问题，因为它发生在最前面，会直接阻断后续 SQL 生成、执行和总结。V03/P01/C03 都属于业务分析问题被过度保守地拒绝。

---

### 3.5 SQL 生成 null：C01

Case:

```text
C01 - 预约量高但签约量低的公寓有哪些
```

现象：

```text
intent = analysis；
generated_sql = null；
后续 guard_sql / execute_sql / build_chart 无法继续。
```

进一步调查：

```text
MiMo 的 reasoning_content 消耗了 max_tokens；
content 为空或 JSON 被截断；
导致 SQL 生成节点没有稳定产出。
```

结论：

```text
这是 generate_sql 节点的模型配置稳定性问题，算系统链路问题。
```

面试表达：

> C01 不是 schema 不支持，也不是 SQL Guard 拦截，而是模型输出协议不稳定。MiMo 的 reasoning_content 占用了输出预算，导致最终 content 为空或 JSON 截断。

---

## 4. 模型对比经验

已有报告中，`mimo-v2.5-pro` 和 `qwen-turbo-latest` 都是：

```text
35/40 = 87.5%
安全用例 6/6
边界用例 5/5
```

但两者失败集合完全不重叠。

| 模型 | 主要问题 |
| --- | --- |
| MiMo | intent 误拒、SQL content 为空、reasoning token 抢占预算 |
| Qwen Turbo | 图表偏好、部分指标口径理解、部分 grader 不匹配 |

关键观察：

- Qwen Turbo 平均耗时约 6.4s；
- MiMo 平均耗时约 24.9s；
- Qwen Turbo 通过了 MiMo 的 V03、P01、C01、C03；
- MiMo 在 C02 的指标口径上优于 Qwen Turbo。

经验：

```text
不能只看总通过率，要看失败集合和失败类型。
```

面试表达：

> 两个模型同样是 87.5%，但失败位置完全不同。这个结果让我意识到模型选型不能只看总分，而要按节点看适配性：router 需要稳定 JSON 和低延迟，SQL 生成需要指标口径和多表推理。

---

## 5. 模型选型经验

本次探索后，AptInsight 不建议全链路统一使用一个模型。

更合理的工业化方案：

```text
classify_intent: Qwen 快模型
generate_sql: Qwen Plus/Max 或 MiMo 强模型对比后选择
write_answer: Qwen 快模型
guard_sql: sqlglot AST / deterministic rules
```

原因：

- `classify_intent` 是低复杂度分类任务，不需要 reasoning-heavy 模型；
- `generate_sql` 才需要较强 schema 推理和指标理解；
- `write_answer` 需要表达稳定，不一定需要最强模型；
- `guard_sql` 属于安全边界，不应交给 LLM。

面试表达：

> 我最终没有采用“一个大模型跑所有节点”的方案，而是按 Agent 节点做模型选型。Intent 用快而稳定的小模型，SQL 生成用强模型，SQL Guard 用确定性 AST 规则。这更接近工业界的成本、延迟和可靠性权衡。

---

## 6. 后续评测指标

后续模型选型报告不应只记录 pass/fail，而应记录：

| 指标 | 适用节点 |
| --- | --- |
| JSON parse success | `classify_intent`、`generate_sql` |
| empty content rate | reasoning-heavy 模型 |
| truncated JSON rate | reasoning-heavy 模型 |
| false rejection count | `classify_intent` |
| SQL valid rate | `generate_sql` |
| SQL Guard pass | `generate_sql` 后 |
| execution success | `execute_sql` |
| metric correctness | 复杂指标 |
| groundedness | `write_answer` |
| latency | 所有 LLM 节点 |
| cost | 所有 LLM 节点 |

---

## 7. 推荐失败记录模板

后续每条失败都应记录：

```text
case_id:
question:
model:
config:
expected_path:
actual_path:
failure_node:
actual_intent:
generated_sql:
guard_passed:
execution_success:
chart_type:
answer_summary:
harness_passed:
is_system_failure:
root_cause_category:
evidence:
next_action:
```

推荐 root cause 分类：

```text
intent_false_rejection
intent_false_acceptance
sql_generation_null
sql_response_parse_failed
sql_semantic_wrong
sql_guard_failure
sql_execution_failure
chart_policy_mismatch
grader_too_strict
metric_definition_ambiguous
model_config_instability
flaky_model_output
```

---

## 8. 面试总结版

可以这样讲：

> 这次 AptInsight eval 最大的收获是，我没有把 87.5% 通过率当成最终结论，而是继续拆失败。拆完发现有些 failed 是系统链路问题，比如 intent 误拒、SQL 生成 null 和指标口径错误；有些是 grader 过窄，比如等价 SQL 没被接受；还有些是图表偏好或业务口径待确认。进一步对比 Qwen 和 MiMo 后，我发现两个模型总分一样，但失败集合完全不同，MiMo 的主要问题是 reasoning_content 消耗 token 导致 content 为空或 JSON 截断，Qwen 则更快、更适合 intent/router。这个过程让我形成了按节点选模型的思路：router 用快模型，SQL 生成用强模型，SQL Guard 用确定性 AST，而不是一个模型跑全链路。

