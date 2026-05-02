"""
SQL 生成节点模块

本模块负责将用户的自然语言问题转换为 SQL 查询语句。
这是 LangGraph 工作流的核心节点之一，使用 LLM 进行 Text-to-SQL 转换。

学习要点：
1. Text-to-SQL - 自然语言转 SQL 的核心技术
2. 提示词工程 - 如何设计有效的 SQL 生成提示词
3. 上下文注入 - 如何将数据库 schema 信息注入提示词
4. 结构化输出 - 如何让 LLM 输出结构化的 SQL

工作流程：
用户问题 + 数据库 schema → LLM → SQL 语句

关键挑战：
1. 准确性：生成的 SQL 必须正确反映用户意图
2. 安全性：SQL 必须符合安全策略
3. 性能：生成的 SQL 应该高效
"""

from __future__ import annotations

import json
import re
from typing import Any

from ...core.logging import get_logger
from ...llm.client import LLMClient
from ..state import AgentState

# 获取日志记录器
logger = get_logger(__name__)


# ============================================================================
# SQL 生成提示词
# ============================================================================

# 学习要点：这是一个复杂的提示词，包含多个部分：
# 1. 角色定义 - 说明 LLM 的身份
# 2. 任务说明 - 明确要做什么
# 3. 约束条件 - 限制生成的 SQL
# 4. 上下文信息 - 提供数据库 schema
# 5. 示例 - 展示期望的输出
# 6. 输出格式 - 指定输出结构

SQL_GENERATION_PROMPT = """你是一个专业的 SQL 专家，专门将中文自然语言问题转换为 MySQL 查询语句。

## 你的任务

将用户的中文问题转换为安全、准确、高效的 MySQL SELECT 查询。

## 数据库 Schema

{schema_context}

## 指标口径

{metric_context}

## 安全规则（必须严格遵守）

1. 只允许 SELECT 语句，禁止 INSERT/UPDATE/DELETE/DROP 等
2. 只查询白名单中的表和列
3. 禁止多语句 SQL
4. 所有业务表必须添加 `is_deleted = 0` 条件
5. 不要编造不存在的表、列或指标

## SQL 编写规范

1. 使用清晰的表别名（如 apartment_info ai, room_info ri）
2. 添加适当的注释说明复杂逻辑
3. 使用 GROUP BY 进行聚合统计
4. 使用 ORDER BY 排序结果
5. 使用 LIMIT 限制返回行数（默认最多 100 行）
6. 优先使用索引字段进行过滤和排序

## 常用 SQL 模式

### 趋势分析
```sql
SELECT
  DATE_FORMAT(create_time, '%Y-%m') AS month,
  COUNT(*) AS count
FROM table_name
WHERE is_deleted = 0
  AND create_time >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
GROUP BY month
ORDER BY month
```

### 排行榜
```sql
SELECT
  name,
  COUNT(*) AS count
FROM table_name
WHERE is_deleted = 0
GROUP BY id, name
ORDER BY count DESC
LIMIT 10
```

### 转化率
```sql
SELECT
  COUNT(CASE WHEN status = 2 THEN 1 END) AS signed_count,
  COUNT(*) AS total_count,
  ROUND(COUNT(CASE WHEN status = 2 THEN 1 END) / COUNT(*), 4) AS rate
FROM table_name
WHERE is_deleted = 0
```

## 输出要求

请以 JSON 格式输出，包含以下字段：

- sql: 生成的 SQL 语句
- tables_used: SQL 中涉及的表名列表
- explanation: SQL 的简要说明（中文）
- need_chart: 是否需要图表展示（布尔值）
- chart_type: 图表类型
- chart_reason: 选择该图表类型的原因（中文，用于日志）

## 图表类型判断规则

根据用户问题的语义选择图表类型：

- **bar**（柱状图）：对比、排行、各 X 的 Y、排名、比较、最多、最少
- **line**（折线图）：趋势、时间序列、变化、走势、按月/年统计
- **pie**（饼图）：占比、比例、构成、分布、份额（必须是用户明确询问占比/比例时才用）
- **table**（表格）：明细、详情、列表、具体记录
- **none**：单个数值（如 COUNT、SUM 结果只有一行一列）
- **null**：不确定时输出 null，系统会自动判断

重要：饼图只在用户明确询问"占比、比例、构成、分布"时使用。对于"排行、对比、各 X 的 Y"等场景，即使数据形状适合饼图，也应该用柱状图。

示例输出 1（排行 → bar）：
{{
  "sql": "SELECT ai.name, COUNT(va.id) AS count FROM view_appointment va JOIN apartment_info ai ON va.apartment_id = ai.id WHERE va.is_deleted = 0 GROUP BY ai.id, ai.name ORDER BY count DESC LIMIT 10",
  "tables_used": ["view_appointment", "apartment_info"],
  "explanation": "统计各公寓的预约量，按预约量降序排列，取前10名",
  "need_chart": true,
  "chart_type": "bar",
  "chart_reason": "用户询问排行，适合柱状图对比"
}}

示例输出 2（占比 → pie）：
{{
  "sql": "SELECT appointment_status, COUNT(*) AS count FROM view_appointment WHERE is_deleted = 0 GROUP BY appointment_status",
  "tables_used": ["view_appointment"],
  "explanation": "统计各状态的预约数量分布",
  "need_chart": true,
  "chart_type": "pie",
  "chart_reason": "用户询问分布情况，适合饼图展示占比"
}}

示例输出 3（单个数值 → none）：
{{
  "sql": "SELECT COUNT(*) AS total FROM apartment_info WHERE is_deleted = 0",
  "tables_used": ["apartment_info"],
  "explanation": "统计公寓总数",
  "need_chart": false,
  "chart_type": "none",
  "chart_reason": "单个数值，不需要图表"
}}

## 用户问题

{question}"""


# ============================================================================
# SQL 生成节点函数
# ============================================================================

async def generate_sql(state: AgentState, llm_client: LLMClient) -> AgentState:
    """
    SQL 生成节点

    这个节点负责：
    1. 读取用户问题和上下文信息
    2. 构造 SQL 生成提示词
    3. 调用 LLM 生成 SQL
    4. 解析和验证生成的 SQL
    5. 更新状态

    Args:
        state: 当前状态
        llm_client: LLM 客户端实例

    Returns:
        更新后的状态

    学习要点：
    - 节点函数：接收状态，返回更新后的状态
    - LLM 调用：使用异步方式调用 LLM
    - 结果解析：从 LLM 响应中提取结构化数据
    """
    question = state.get("question", "")
    schema_context = state.get("schema_context", "")
    metric_context = state.get("metric_context", "")

    logger.info(f"开始 SQL 生成，问题: {question[:50]}")

    try:
        # 构造提示词
        # 学习要点：使用 format 方法填充模板变量
        prompt = SQL_GENERATION_PROMPT.format(
            question=question,
            schema_context=schema_context,
            metric_context=metric_context,
        )

        # 调用 LLM 生成 SQL
        response = await llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # 低温度，确保 SQL 稳定
        )

        # 解析 LLM 响应
        result = _parse_sql_response(response)

        # 验证生成的 SQL
        validation_error = _validate_sql(result["sql"])
        if validation_error:
            logger.warning(f"SQL 验证失败: {validation_error}")
            return {
                **state,
                "error": f"生成的 SQL 无效: {validation_error}",
            }

        logger.info(
            "SQL 生成完成",
            extra={"sql": result["sql"][:100], "tables": result["tables_used"]},
        )

        # 提取 chart_type 和 chart_reason（chart_reason 只记日志，不存 state）
        chart_type = result.get("chart_type")
        chart_reason = result.get("chart_reason", "")
        if chart_type:
            logger.info(f"LLM 判断图表类型: {chart_type}，原因: {chart_reason}")

        # 更新状态
        return {
            **state,
            "generated_sql": result["sql"],
            "tables_used": result["tables_used"],
            "need_chart": result.get("need_chart", False),
            "chart_type": chart_type,
        }

    except Exception as e:
        logger.error(f"SQL 生成失败，错误: {e}")
        return {
            **state,
            "error": f"SQL 生成失败: {str(e)}",
        }


def _parse_sql_response(response: str) -> dict[str, Any]:
    """
    解析 LLM 的 SQL 生成响应

    Args:
        response: LLM 的原始响应文本

    Returns:
        解析后的结果字典

    学习要点：
    - JSON 提取：从 LLM 响应中提取 JSON 数据
    - 错误处理：处理各种解析失败的情况
    - 数据验证：确保提取的数据符合预期格式
    """
    try:
        # 尝试从响应中提取 JSON
        json_start = response.find("{")
        json_end = response.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("响应中没有找到 JSON")

        json_str = response[json_start:json_end]
        result = json.loads(json_str)

        # 验证必需字段
        if "sql" not in result:
            raise ValueError("响应中缺少 sql 字段")

        # 确保 tables_used 是列表
        if "tables_used" not in result:
            # 尝试从 SQL 中提取表名
            result["tables_used"] = _extract_tables_from_sql(result["sql"])

        return result

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"解析 SQL 响应失败: {e}")

        # 尝试直接从响应中提取 SQL
        sql_match = re.search(r"```sql\s*(.*?)\s*```", response, re.DOTALL)
        if sql_match:
            sql = sql_match.group(1).strip()
            return {
                "sql": sql,
                "tables_used": _extract_tables_from_sql(sql),
                "explanation": "从响应中提取的 SQL",
                "need_chart": True,
            }

        # 如果都无法提取，返回错误
        raise ValueError(f"无法从响应中提取 SQL: {e}")


def _extract_tables_from_sql(sql: str) -> list[str]:
    """
    从 SQL 语句中提取表名

    Args:
        sql: SQL 语句

    Returns:
        表名列表

    学习要点：
    - 正则表达式：用于模式匹配
    - SQL 解析：提取 SQL 中的表名
    """
    # 匹配 FROM 和 JOIN 后面的表名
    pattern = r"(?:FROM|JOIN)\s+(\w+)"
    matches = re.findall(pattern, sql, re.IGNORECASE)

    # 去重并返回
    return list(set(matches))


def _validate_sql(sql: str) -> str | None:
    """
    验证生成的 SQL 是否符合基本要求

    Args:
        sql: SQL 语句

    Returns:
        错误消息，如果验证通过则返回 None

    学习要点：
    - 输入验证：检查 SQL 的基本合法性
    - 安全检查：确保 SQL 不包含危险操作
    """
    if not sql or not sql.strip():
        return "SQL 语句为空"

    sql_upper = sql.upper().strip()

    # 检查是否为 SELECT 语句
    if not sql_upper.startswith("SELECT"):
        return "只允许 SELECT 语句"

    # 检查是否包含危险关键字（使用单词边界匹配，避免误判字段名）
    import re
    dangerous_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "EXEC"]
    for keyword in dangerous_keywords:
        # 使用单词边界匹配，避免匹配到字段名中的子串（如 is_deleted）
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_upper):
            return f"SQL 中包含危险关键字: {keyword}"

    # 检查是否包含多语句（分号）
    # 注意：这个检查比较简单，可能会误判
    if ";" in sql.rstrip(";"):
        return "禁止多语句 SQL"

    return None


# ============================================================================
# 辅助函数
# ============================================================================

def need_chart_for_query(question: str) -> bool:
    """
    根据问题类型判断是否需要图表

    Args:
        question: 用户问题

    Returns:
        True 如果需要图表，否则 False

    学习要点：
    - 启发式规则：基于关键词的快速判断
    - 作为 LLM 判断的补充
    """
    chart_keywords = ["趋势", "排行", "对比", "分布", "占比", "变化"]
    no_chart_keywords = ["多少", "几个", "数量", "总数"]

    question_lower = question.lower()

    # 如果包含图表关键词，需要图表
    if any(keyword in question_lower for keyword in chart_keywords):
        return True

    # 如果只包含数量关键词，不需要图表
    if any(keyword in question_lower for keyword in no_chart_keywords):
        return False

    # 默认需要图表
    return True
