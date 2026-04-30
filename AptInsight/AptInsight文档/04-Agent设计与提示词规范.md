# AptInsight Agent 设计与提示词规范

## 1. Agent 职责

AptInsight Agent 的职责是将用户的自然语言运营问题转换为安全可执行的只读查询，并基于查询结果生成分析回答。

核心职责：

1. 判断问题是否属于公寓运营分析。
2. 根据数据库 schema 生成 SQL。
3. 校验 SQL 安全性。
4. 执行只读查询。
5. 选择图表类型。
6. 生成业务总结和建议。

Agent 不负责：

1. 修改业务数据。
2. 管理用户登录权限。
3. 编造数据库中没有的信息。
4. 绕过 SQL 校验直接查询。

## 2. Agent 工作流

AptInsight 使用 LangGraph 管理 Agent 流程。这里使用 LangGraph 不是为了追求新技术，而是因为 Text-to-SQL 流程天然存在状态、分支和失败恢复。

```text
User Question
   |
   v
Intent Router
   |
   +--> Metric Explanation -> Answer
   |
   +--> Unsupported -> Refusal
   |
   v
SQL Generator
   |
   v
SQL Guard
   |
   +--> Failed -> Repair once -> Guard again
   |
   v
DB Executor
   |
   v
Result Analyzer
   |
   v
Chart Builder
   |
   v
Answer Writer
```

推荐 LangGraph 节点：

| 节点 | 作用 |
| --- | --- |
| `normalize_question` | 规范化用户问题，提取时间范围和业务对象 |
| `classify_intent` | 判断查询、趋势、诊断、指标解释或拒答 |
| `select_schema_context` | 选择相关表、字段、指标和 few-shot |
| `generate_sql` | 根据 schema 和问题生成 SELECT SQL |
| `guard_sql` | 使用 sqlglot 校验 SQL 安全性 |
| `repair_sql` | 对可修复问题尝试修复一次 |
| `execute_sql` | 使用只读账号执行 SQL |
| `analyze_result` | 分析空结果、趋势、排名、异常 |
| `build_chart` | 生成 ECharts 配置 |
| `write_answer` | 生成最终中文总结 |
| `refuse` | 对不支持或不安全问题明确拒答 |

条件分支：

```text
classify_intent
  -> metric_explanation: write_answer
  -> unsupported: refuse
  -> need_sql: generate_sql

guard_sql
  -> safe: execute_sql
  -> repairable: repair_sql
  -> unsafe: refuse

execute_sql
  -> empty_result: write_answer
  -> has_result: analyze_result
```

## 3. 意图分类

| 意图 | 说明 | 是否查库 |
| --- | --- | --- |
| `data_query` | 查询数量、列表、排名 | 是 |
| `trend_analysis` | 按日、按月趋势 | 是 |
| `distribution_analysis` | 状态占比、租金区间分布 | 是 |
| `diagnosis` | 经营诊断、异常识别 | 是 |
| `metric_explanation` | 解释指标怎么算 | 否 |
| `unsupported` | 非公寓运营问题或 schema 不支持 | 否 |

## 4. Prompt 分层

建议将 prompt 拆为 5 层。

```text
System Prompt
  + Safety Rules
  + Schema Dictionary
  + Metric Definitions
  + Few-shot Examples
  + User Question
```

这样便于后续维护 schema、指标和示例。

## 5. System Prompt 模板

```text
你是 AptInsight，公寓管理系统的智能运营分析助手。

你的任务：
1. 只回答公寓运营数据分析相关问题。
2. 如果需要查库，只生成 MySQL SELECT 查询。
3. 必须基于提供的数据库 schema 和指标口径回答。
4. 不允许编造表、字段、枚举和值。
5. 不允许生成 INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE 等语句。
6. 不允许生成多条 SQL。
7. 不允许查询系统库。
8. 不允许返回密码、身份证号、完整手机号等敏感字段。
9. 默认过滤 is_deleted = 0。
10. 默认限制返回行数。

如果用户问题无法根据当前 schema 准确回答，请明确说明缺少哪些数据。
```

## 6. SQL 生成规则

### 6.1 基础规则

1. 只生成 MySQL SQL。
2. 只允许 `SELECT`。
3. 使用明确字段，不使用 `SELECT *`。
4. 使用表别名。
5. 所有关联表都过滤 `is_deleted = 0`。
6. 枚举字段用数字 code 查询，并在结果中转成中文名称。
7. 所有聚合字段需要有清晰别名。
8. 默认 `LIMIT 200`，排名类默认 `LIMIT 10`。

### 6.2 时间规则

| 用户说法 | SQL 口径 |
| --- | --- |
| 今天 | `CURDATE()` 到 `DATE_ADD(CURDATE(), INTERVAL 1 DAY)` |
| 本月 | `DATE_FORMAT(date_col, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')` |
| 最近 30 天 | `date_col >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)` |
| 最近 6 个月 | `date_col >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)` |
| 今年 | `YEAR(date_col) = YEAR(CURDATE())` |

### 6.3 状态枚举规则

模型不能猜状态值，必须使用文档中的枚举。

例如：

```text
已签约租约 = lease_agreement.status = 2
待看房预约 = view_appointment.appointment_status = 1
已发布房间 = room_info.is_release = 1
```

### 6.4 隐私字段规则

禁止直接返回：

```text
password
identification_number
phone
```

如确实需要返回手机号，用脱敏字段：

```sql
CONCAT(LEFT(va.phone, 3), '****', RIGHT(va.phone, 4)) AS phone_masked
```

## 7. SQL Guard 规则

SQL Guard 必须在执行前检查。

### 7.1 允许

允许：

1. `SELECT`
2. `WITH ... SELECT`
3. 聚合函数：`COUNT`、`SUM`、`AVG`、`MIN`、`MAX`
4. 时间函数：`DATE_FORMAT`、`CURDATE`、`DATE_SUB`
5. 条件表达式：`CASE WHEN`

### 7.2 禁止

禁止：

```text
INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
CREATE
REPLACE
GRANT
REVOKE
CALL
LOAD
OUTFILE
INTO DUMPFILE
多语句分号
```

### 7.3 表白名单

第一版允许查询：

```text
apartment_info
room_info
view_appointment
lease_agreement
browsing_history
province_info
city_info
district_info
lease_term
payment_type
label_info
facility_info
fee_key
fee_value
apartment_label
apartment_facility
apartment_fee_value
room_label
room_facility
room_attr_value
room_lease_term
room_payment_type
attr_key
attr_value
user_info
```

谨慎查询：

```text
system_user
system_post
```

默认不用于运营分析，除非后续做后台员工管理分析。

## 8. 输出结构

SQL 生成阶段建议输出 JSON，而不是纯 SQL：

```json
{
  "need_sql": true,
  "chart_type": "bar",
  "sql": "SELECT ...",
  "reason": "统计本月各公寓预约数量，需要关联 view_appointment 和 apartment_info"
}
```

最终回答阶段输出：

```json
{
  "answer": "本月预约量最高的是回龙观社区，共 8 次。",
  "summary": "预约主要集中在回龙观社区，可以重点关注该公寓的看房转化。",
  "sql": "SELECT ...",
  "columns": [],
  "rows": [],
  "chart": {}
}
```

## 9. Few-shot 示例

### 9.1 本月各公寓预约量排名

用户问题：

```text
本月各公寓预约量排名
```

SQL：

```sql
SELECT
  ai.name AS apartment_name,
  COUNT(va.id) AS appointment_count
FROM view_appointment va
JOIN apartment_info ai ON va.apartment_id = ai.id
WHERE va.is_deleted = 0
  AND ai.is_deleted = 0
  AND DATE_FORMAT(va.appointment_time, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')
GROUP BY ai.id, ai.name
ORDER BY appointment_count DESC
LIMIT 10;
```

图表：柱状图。

### 9.2 最近 30 天预约趋势

用户问题：

```text
最近 30 天预约趋势
```

SQL：

```sql
SELECT
  DATE(va.appointment_time) AS appointment_date,
  COUNT(va.id) AS appointment_count
FROM view_appointment va
WHERE va.is_deleted = 0
  AND va.appointment_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY DATE(va.appointment_time)
ORDER BY appointment_date ASC
LIMIT 200;
```

图表：折线图。

### 9.3 当前租约状态占比

用户问题：

```text
当前租约状态占比
```

SQL：

```sql
SELECT
  CASE la.status
    WHEN 1 THEN '签约待确认'
    WHEN 2 THEN '已签约'
    WHEN 3 THEN '已取消'
    WHEN 4 THEN '已到期'
    WHEN 5 THEN '退租待确认'
    WHEN 6 THEN '已退租'
    WHEN 7 THEN '续约待确认'
    ELSE '未知'
  END AS lease_status,
  COUNT(la.id) AS agreement_count
FROM lease_agreement la
WHERE la.is_deleted = 0
GROUP BY la.status
ORDER BY agreement_count DESC
LIMIT 20;
```

图表：饼图。

### 9.4 各区域平均租金

用户问题：

```text
各区域平均租金
```

SQL：

```sql
SELECT
  ai.district_name AS district_name,
  ROUND(AVG(ri.rent), 2) AS avg_rent,
  COUNT(ri.id) AS room_count
FROM room_info ri
JOIN apartment_info ai ON ri.apartment_id = ai.id
WHERE ri.is_deleted = 0
  AND ai.is_deleted = 0
  AND ri.is_release = 1
GROUP BY ai.district_id, ai.district_name
ORDER BY avg_rent DESC
LIMIT 50;
```

图表：柱状图。

### 9.5 已发布但没有有效租约的房间

用户问题：

```text
哪些已发布房间当前没有有效租约
```

SQL：

```sql
SELECT
  ai.name AS apartment_name,
  ri.room_number AS room_number,
  ri.rent AS rent
FROM room_info ri
JOIN apartment_info ai ON ri.apartment_id = ai.id
LEFT JOIN lease_agreement la
  ON la.room_id = ri.id
  AND la.is_deleted = 0
  AND la.status = 2
  AND CURDATE() BETWEEN la.lease_start_date AND la.lease_end_date
WHERE ri.is_deleted = 0
  AND ai.is_deleted = 0
  AND ri.is_release = 1
  AND la.id IS NULL
ORDER BY ri.rent DESC
LIMIT 100;
```

图表：表格。

### 9.6 不支持的房间预约量

用户问题：

```text
预约量最高的房间有哪些？
```

回答策略：

```text
当前数据库的 view_appointment 表只有 apartment_id，没有 room_id，不能准确统计房间维度预约量。可以改为统计各公寓预约量排名，或后续在预约表中增加 room_id 字段后再支持该分析。
```

不要生成错误 SQL。

## 10. 结果总结规范

总结要遵守：

1. 先说核心结论。
2. 再说明数据口径。
3. 最后给出建议。
4. 不超过 200 字。
5. 不编造原因。

示例：

```text
最近 30 天预约量整体集中在回龙观社区和温都水城社区，其中回龙观社区预约量最高。该结果按 view_appointment.appointment_time 统计，仅包含未删除预约记录。建议继续观察预约后的已看房和签约情况，判断高预约是否能形成有效转化。
```

## 11. SQL 修复策略

如果 SQL Guard 失败，可以允许模型修复一次。

常见修复：

| 失败原因 | 修复方式 |
| --- | --- |
| 使用了不存在字段 | 根据 schema 替换字段 |
| 未加 `is_deleted = 0` | 自动补充 |
| 返回敏感字段 | 删除或脱敏 |
| 缺少 LIMIT | 自动追加 |
| 使用多语句 | 拒绝执行 |
| DML/DDL | 拒绝执行，不修复 |

修复后必须再次通过 SQL Guard。

## 12. 防幻觉规则

Agent 必须明确：

1. 不能假设数据库有支付流水表。
2. 不能假设预约记录关联房间。
3. 不能把合同租金说成实际收款。
4. 不能把相关性说成因果。
5. 不能输出“肯定是租金太高”这类无证据结论。

推荐表达：

```text
可能与租金、房源位置、房间配置或看房转化有关，需要结合更多数据确认。
```

不推荐表达：

```text
原因就是租金太高。
```
