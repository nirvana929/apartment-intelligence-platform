"""
答案生成节点模块

本模块负责根据查询结果生成用户友好的业务答案。
这是工作流的最后一个节点，将数据转换为可理解的文字描述。

学习要点：
1. 数据解读 - 如何将数据转换为业务洞察
2. 自然语言生成 - 使用 LLM 生成自然语言答案
3. 摘要生成 - 提取关键信息生成摘要
4. 格式化输出 - 组织答案的结构和格式

答案生成策略：
1. 简单统计：直接描述数字
2. 趋势分析：描述变化趋势
3. 对比分析：指出差异和排名
4. 占比分析：描述分布情况

工作流程：
查询结果 → 分析数据 → 调用 LLM → 生成答案 → 更新状态
"""

from __future__ import annotations

from typing import Any

from ...core.logging import get_logger
from ...llm.client import LLMClient
from ..state import AgentState, INTENT_CHITCHAT, INTENT_OUT_OF_SCOPE

# 获取日志记录器
logger = get_logger(__name__)


# ============================================================================
# 答案生成提示词
# ============================================================================

# 学习要点：提示词设计的关键要素：
# 1. 角色定义 - 明确 LLM 的身份
# 2. 任务说明 - 清晰描述要做什么
# 3. 输入数据 - 提供必要的上下文
# 4. 输出格式 - 指定期望的输出结构
# 5. 示例 - 展示期望的输出样式

ANSWER_PROMPT = """你是一个专业的公寓运营数据分析助手。
你的任务是根据查询结果，生成清晰、准确、有价值的业务分析答案。

## 你的回答原则

1. **准确性**：只基于提供的数据回答，不编造信息
2. **清晰性**：使用简洁明了的语言，避免专业术语
3. **价值性**：提供有业务意义的洞察，不仅仅是数据罗列
4. **完整性**：覆盖数据的主要特征和趋势

## 回答结构

请按以下结构组织答案：

1. **开场白**：简要说明查询了什么
2. **核心发现**：指出最重要的数据点
3. **详细分析**：描述数据的特征、趋势、对比等
4. **业务洞察**：提供有业务价值的见解（可选）
5. **总结**：一句话概括主要结论

## 用户问题

{question}

## 查询结果

### 数据概况
- 结果行数：{row_count}
- 结果列数：{column_count}
- 列名：{columns}

### 数据内容
{data_preview}

## 图表信息

{chart_info}

## 输出要求

请生成两个部分：

### 1. 完整答案（answer）
详细的数据分析和业务洞察，200-500字。

### 2. 简短摘要（summary）
一句话概括主要结论，20-50字。

请以 JSON 格式输出：
{{
    "answer": "完整的分析答案...",
    "summary": "一句话摘要..."
}}
"""

CHITCHAT_PROMPT = """你是尚庭公寓的智能运营分析助手。

用户和你闲聊，请友好地简短回复，并自然地引导用户提出与公寓运营相关的问题。

## 用户消息

{question}

## 回复要求

- 简短友好，1-2 句话
- 说明你的能力范围（公寓运营数据分析）
- 不要编造数据或业务信息

请直接输出回复文本，不需要 JSON 格式。"""

OUT_OF_SCOPE_MESSAGE = (
    "我是尚庭公寓的运营分析助手，只能回答与公寓运营相关的问题，"
    "比如预约量、签约情况、租金分析、空置率等。"
    "请尝试用运营相关的角度重新提问。"
)


# ============================================================================
# 答案生成节点函数
# ============================================================================


async def write_answer(state: AgentState, llm_client: LLMClient) -> AgentState:
    """
    答案生成节点

    这个节点负责：
    1. 读取查询结果
    2. 分析数据特征
    3. 调用 LLM 生成答案
    4. 更新状态

    Args:
        state: 当前状态
        llm_client: LLM 客户端实例

    Returns:
        更新后的状态

    学习要点：
    - 数据分析：分析查询结果的特征
    - LLM 调用：使用 LLM 生成自然语言答案
    - 结果处理：解析和验证 LLM 输出
    """
    question = state.get("question", "")
    rows = state.get("rows", [])
    columns = state.get("columns", [])
    chart_type = state.get("chart_type")
    chart_option = state.get("chart_option")
    intent = state.get("intent", "")
    error = state.get("error")

    # ===== 分支 1：闲聊 =====
    if intent == INTENT_CHITCHAT:
        logger.info("闲聊意图，生成闲聊回复")
        try:
            prompt = CHITCHAT_PROMPT.format(question=question)
            response = await llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return {**state, "answer": response.strip(), "summary": "闲聊回复"}
        except Exception as e:
            logger.error(f"闲聊回复生成失败: {e}")
            return {
                **state,
                "answer": "你好！我是尚庭公寓的运营分析助手，可以帮你分析预约、签约、租金等运营数据。请问有什么想了解的？",
                "summary": "闲聊回复",
            }

    # ===== 分支 2：超出范围 =====
    if intent == INTENT_OUT_OF_SCOPE:
        logger.info("超出范围意图，返回提示")
        return {**state, "answer": OUT_OF_SCOPE_MESSAGE, "summary": "问题超出分析范围"}

    # ===== 分支 3：有错误（SQL 生成失败 / SQL 被拦截等）=====
    if error:
        logger.info(f"存在错误，生成错误提示: {error}")
        warnings = state.get("warnings", [])
        detail = error
        if warnings:
            detail = f"{error}（{'；'.join(warnings)}）"
        return {
            **state,
            "answer": f"处理您的问题时遇到困难：{detail}。请尝试换一种方式描述您的问题。",
            "summary": "处理失败",
        }

    # ===== 分支 4：没有数据（意外兜底）=====
    if not rows:
        logger.warning("没有查询结果且无明确错误，生成兜底提示")
        return {
            **state,
            "answer": "抱歉，没有找到符合条件的数据。请尝试调整查询条件或问题描述。",
            "summary": "未找到符合条件的数据",
        }

    # ===== 分支 5：正常数据 → 调 LLM 生成分析答案 =====
    logger.info(f"开始生成答案，行数: {len(rows)}")

    try:
        data_preview = _format_data_preview(rows, columns)
        chart_info = _format_chart_info(chart_type, chart_option)

        prompt = ANSWER_PROMPT.format(
            question=question,
            row_count=len(rows),
            column_count=len(columns),
            columns=", ".join(columns),
            data_preview=data_preview,
            chart_info=chart_info,
        )

        response = await llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4000,
        )

        result = _parse_answer_response(response)

        logger.info(
            "答案生成完成",
            extra={"answer_length": len(result["answer"]), "summary": result["summary"][:50]},
        )

        return {
            **state,
            "answer": result["answer"],
            "summary": result["summary"],
        }

    except Exception as e:
        logger.error(f"答案生成失败，错误: {e}")
        fallback_answer = _generate_fallback_answer(question, rows, columns)
        return {
            **state,
            "answer": fallback_answer,
            "summary": f"查询到 {len(rows)} 条数据",
            "warnings": state.get("warnings", []) + ["答案生成失败，已返回原始数据"],
        }


def _parse_answer_response(response: str) -> dict[str, str]:
    """
    解析 LLM 的答案生成响应

    Args:
        response: LLM 的原始响应文本

    Returns:
        解析后的结果字典，包含 answer 和 summary

    学习要点：
    - JSON 提取：从 LLM 响应中提取 JSON 数据
    - 错误处理：处理解析失败的情况
    - 默认值：为缺失字段提供默认值
    """
    import json
    import re

    # 去除 markdown 代码块包裹：```json ... ``` 或 ``` ... ```
    cleaned = response.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        json_start = cleaned.find("{")
        json_end = cleaned.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("响应中没有找到 JSON")

        json_str = cleaned[json_start:json_end]
        result = json.loads(json_str)

        answer = result.get("answer", cleaned)
        summary = result.get("summary", "")

        # 如果 LLM 没返回 summary，从 answer 前 50 字提取
        if not summary:
            summary = answer[:50].replace("\n", " ").strip()
            if len(answer) > 50:
                summary += "..."

        return {"answer": answer, "summary": summary}

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"解析答案响应失败: {e}")
        # 解析失败，用整个响应作为 answer，提取前 50 字作为 summary
        summary = response[:50].replace("\n", " ").strip()
        if len(response) > 50:
            summary += "..."
        return {"answer": response, "summary": summary}


def _format_data_preview(rows: list[dict[str, Any]], columns: list[str]) -> str:
    """
    格式化数据预览

    Args:
        rows: 查询结果行
        columns: 列名列表

    Returns:
        格式化的数据预览文本

    学习要点：
    - 数据格式化：将结构化数据转换为文本格式
    - 可读性：使数据易于理解
    """
    if not rows or not columns:
        return "无数据"

    # 只显示前5行数据
    preview_rows = rows[:5]
    lines = []

    for i, row in enumerate(preview_rows, 1):
        line_parts = []
        for col in columns:
            value = row.get(col, "-")
            line_parts.append(f"{col}: {value}")
        lines.append(f"第{i}行: {', '.join(line_parts)}")

    if len(rows) > 5:
        lines.append(f"... 还有 {len(rows) - 5} 行数据")

    return "\n".join(lines)


def _format_chart_info(chart_type: str | None, chart_option: dict[str, Any] | None) -> str:
    """
    格式化图表信息

    Args:
        chart_type: 图表类型
        chart_option: 图表配置

    Returns:
        格式化的图表信息文本
    """
    if not chart_type:
        return "未生成图表"

    chart_type_names = {
        "bar": "柱状图",
        "line": "折线图",
        "pie": "饼图",
        "table": "表格",
    }

    chart_name = chart_type_names.get(chart_type, chart_type)

    if chart_type == "table":
        return f"数据以{chart_name}形式展示"

    return f"数据以{chart_name}形式展示，便于直观理解数据分布和趋势"


def _generate_fallback_answer(
    question: str,
    rows: list[dict[str, Any]],
    columns: list[str],
) -> str:
    """
    生成备用答案（当 LLM 调用失败时使用）

    Args:
        question: 用户问题
        rows: 查询结果行
        columns: 列名列表

    Returns:
        简单的备用答案

    学习要点：
    - 降级处理：当主流程失败时提供基本功能
    - 用户体验：即使失败也要提供有用的信息
    """
    if not rows:
        return "抱歉，没有找到符合条件的数据。"

    # 构建简单的答案
    lines = [f"根据您的问题「{question}」，查询到 {len(rows)} 条结果：\n"]

    # 显示前3行数据
    for i, row in enumerate(rows[:3], 1):
        line_parts = []
        for col in columns[:3]:  # 只显示前3列
            value = row.get(col, "-")
            line_parts.append(f"{col}: {value}")
        lines.append(f"{i}. {', '.join(line_parts)}")

    if len(rows) > 3:
        lines.append(f"\n... 还有 {len(rows) - 3} 条数据")

    return "\n".join(lines)
