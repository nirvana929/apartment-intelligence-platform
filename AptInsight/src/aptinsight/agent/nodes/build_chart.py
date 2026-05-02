"""
图表构建节点模块

本模块负责根据查询结果构建 ECharts 图表配置。

三层设计：
1. LLM 决策：generate_sql 输出 chart_type（语义决策）
2. 代码校验：检查 chart_type 是否合法、数据是否适合（可用性检查）
3. 启发式兜底：LLM 缺失/错误时，基于数据约束选一个不会太离谱的图

支持的图表类型：
- bar: 柱状图 - 适合对比数据（如各公寓预约量对比）
- line: 折线图 - 适合趋势分析（如预约量趋势）
- pie: 饼图 - 适合占比分析（必须用户明确询问占比时才用）
- table: 表格 - 适合详细数据展示
- none: 不需要图表（单个数值）
"""

from __future__ import annotations

from typing import Any

from ...core.logging import get_logger
from ..state import SUPPORTED_CHART_TYPES, AgentState

# 获取日志记录器
logger = get_logger(__name__)

# 默认图表颜色方案
# 学习要点：使用专业的颜色方案，提升视觉效果
DEFAULT_COLORS = [
    "#5470c6",
    "#91cc75",
    "#fac858",
    "#ee6666",
    "#73c0de",
    "#3ba272",
    "#fc8452",
    "#9a60b4",
    "#ea7ccc",
    "#48b8d0",
]

# 默认最大数据点数量
# 学习要点：限制数据点数量，防止图表过于拥挤
MAX_DATA_POINTS = 20


# ============================================================================
# 图表构建节点函数
# ============================================================================


async def build_chart(state: AgentState) -> AgentState:
    """
    图表构建节点

    三层设计：
    1. LLM 决策：优先使用 state["chart_type"]（由 generate_sql 设置）
    2. 代码校验：检查 chart_type 是否合法、数据是否适合
    3. 启发式兜底：LLM 缺失/错误时，基于数据约束选择图表类型

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    rows = state.get("rows", [])
    columns = state.get("columns", [])
    question = state.get("question", "")
    need_chart = state.get("need_chart", False)

    # 如果不需要图表或没有数据，跳过
    if not need_chart or not rows:
        logger.info(f"跳过图表构建，需要图表: {need_chart}，有数据: {bool(rows)}")
        return state

    logger.info(f"开始构建图表，行数: {len(rows)}，列数: {len(columns)}")

    try:
        # ===== 第一层：LLM 决策 =====
        llm_chart_type = state.get("chart_type")

        # ===== 第二层：代码校验 =====
        if llm_chart_type and llm_chart_type in SUPPORTED_CHART_TYPES:
            # LLM 输出了合法的 chart_type，检查数据是否适合
            if _is_chart_compatible(llm_chart_type, rows, columns):
                chart_type = llm_chart_type
                logger.info(f"使用 LLM 判断的图表类型: {chart_type}")
            else:
                # 数据不适合 LLM 选择的图表类型，降级
                logger.warning(f"数据不适合 {llm_chart_type}，使用启发式兜底")
                chart_type = _determine_chart_type(question, rows, columns)
                logger.info(f"启发式兜底图表类型: {chart_type}")
        else:
            # ===== 第三层：启发式兜底 =====
            if llm_chart_type:
                logger.warning(f"LLM 输出的图表类型不合法: {llm_chart_type}，使用启发式兜底")
            else:
                logger.info("LLM 未输出 chart_type，使用启发式兜底")
            chart_type = _determine_chart_type(question, rows, columns)
            logger.info(f"启发式兜底图表类型: {chart_type}")

        # 构建图表配置
        chart_option = _build_chart_option(rows, columns, chart_type)

        logger.info(f"图表构建完成，类型: {chart_type}")

        return {
            **state,
            "chart_type": chart_type,
            "chart_option": chart_option,
        }

    except Exception as e:
        logger.error(f"图表构建失败，错误: {e}")
        # 图表构建失败不影响主流程，只记录警告
        return {
            **state,
            "warnings": state.get("warnings", []) + [f"图表构建失败: {str(e)}"],
        }


# ============================================================================
# 第二层：代码校验
# ============================================================================


def _is_chart_compatible(chart_type: str, rows: list[dict[str, Any]], columns: list[str]) -> bool:
    """
    检查数据是否适合指定的图表类型（第二层：代码校验）

    Args:
        chart_type: 图表类型
        rows: 查询结果行
        columns: 列名列表

    Returns:
        True 如果数据适合该图表类型，否则 False
    """
    if not rows or not columns:
        return chart_type == "table"

    # bar：至少2列，第二列必须是数值
    if chart_type == "bar":
        if len(columns) < 2:
            return False
        return _is_numeric_column(rows, columns[1])

    # line：至少2列，第二列必须是数值
    if chart_type == "line":
        if len(columns) < 2:
            return False
        return _is_numeric_column(rows, columns[1])

    # pie：必须2列，第二列数值，3-10行，数值不全为0
    if chart_type == "pie":
        if len(columns) != 2:
            return False
        if len(rows) < 3 or len(rows) > 10:
            return False
        if not _is_numeric_column(rows, columns[1]):
            return False
        if _all_zeros(rows, columns[1]):
            return False
        return True

    # table：任何结构都可以
    if chart_type == "table":
        return True

    # none 或未知类型：不兼容
    return False


def _is_numeric_column(rows: list[dict[str, Any]], col: str) -> bool:
    """检查列是否为数值类型"""
    for row in rows[:5]:
        val = row.get(col)
        if val is not None and not isinstance(val, (int, float)):
            return False
    return True


def _all_zeros(rows: list[dict[str, Any]], col: str) -> bool:
    """检查数值列是否全为 0"""
    for row in rows:
        val = row.get(col)
        if val is not None and val != 0:
            return False
    return True


# ============================================================================
# 第三层：启发式兜底
# ============================================================================

# 占比/比例/构成/分布相关关键词
_RATIO_KEYWORDS = ("占比", "比例", "构成", "分布", "份额", "百分比")


def _has_ratio_intent(question: str) -> bool:
    """检查用户问题是否包含占比/比例/构成/分布意图"""
    return any(kw in question for kw in _RATIO_KEYWORDS)


def _determine_chart_type(question: str, rows: list[dict[str, Any]], columns: list[str]) -> str:
    """
    启发式兜底：基于数据约束选择图表类型（第三层）

    只在 LLM 缺失/错误时启用，目标是选一个不会太离谱的图。

    优先级：
    1. 空数据 → table
    2. 1行1列 → table（单个数值）
    3. 多列明细（>2列）→ table
    4. 时间序列 → line
    5. 明确占比/比例/构成/分布 + 2列分类数值 → pie
    6. 2列分类数值 → bar（默认）
    7. 兜底 → table

    Args:
        question: 用户问题（用于判断语义意图）
        rows: 查询结果行
        columns: 列名列表

    Returns:
        图表类型字符串
    """
    # 1. 空数据 → table
    if not rows or not columns:
        return "table"

    # 2. 1行1列 → table（单个数值）
    if len(rows) <= 1 and len(columns) <= 1:
        return "table"

    # 3. 多列明细（>2列）→ table
    if len(columns) > 2:
        return "table"

    # 4. 时间序列 → line
    if _is_time_series(rows, columns):
        return "line"

    # 5. 明确占比/比例/构成/分布 + 2列分类数值 → pie
    if _has_ratio_intent(question) and _is_category_numeric(rows, columns):
        return "pie"

    # 6. 2列分类数值 → bar（默认，不用 pie）
    if _is_category_numeric(rows, columns):
        return "bar"

    # 7. 兜底 → table
    return "table"


def _is_time_series(rows: list[dict[str, Any]], columns: list[str]) -> bool:
    """
    判断是否为时间序列数据

    检查第一列是否为日期格式的字符串
    """
    if not columns or not rows:
        return False

    first_col = columns[0]
    first_values = [row.get(first_col) for row in rows[:5]]

    date_patterns = [
        r"\d{4}-\d{2}",  # 2024-01
        r"\d{4}/\d{2}",  # 2024/01
        r"\d{4}-\d{2}-\d{2}",  # 2024-01-01
    ]

    import re

    for value in first_values:
        if isinstance(value, str):
            for pattern in date_patterns:
                if re.match(pattern, value):
                    return True

    return False


def _is_category_numeric(rows: list[dict[str, Any]], columns: list[str]) -> bool:
    """
    判断是否为分类+数值结构（2列，第一列分类，第二列数值）
    """
    if len(columns) != 2:
        return False

    first_col = columns[0]
    second_col = columns[1]

    # 检查第一列是否为分类数据（字符串）
    for row in rows[:5]:
        val = row.get(first_col)
        if val is not None and not isinstance(val, str):
            return False

    # 检查第二列是否为数值数据
    return _is_numeric_column(rows, second_col)


# ============================================================================
# 图表配置构建
# ============================================================================


def _build_chart_option(
    rows: list[dict[str, Any]],
    columns: list[str],
    chart_type: str,
) -> dict[str, Any]:
    """
    构建 ECharts 配置对象

    Args:
        rows: 查询结果行
        columns: 列名列表
        chart_type: 图表类型

    Returns:
        ECharts 配置字典

    学习要点：
    - ECharts 配置结构：了解 ECharts 的标准配置格式
    - 数据转换：将查询结果转换为图表数据格式
    - 响应式设计：配置图表适应不同屏幕尺寸
    """
    if chart_type == "bar":
        return _build_bar_option(rows, columns)
    elif chart_type == "line":
        return _build_line_option(rows, columns)
    elif chart_type == "pie":
        return _build_pie_option(rows, columns)
    else:
        return _build_table_option(rows, columns)


def _build_bar_option(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
    """
    构建柱状图配置

    Args:
        rows: 查询结果行
        columns: 列名列表

    Returns:
        柱状图配置

    学习要点：
    - 柱状图配置：xAxis（分类轴）、yAxis（数值轴）、series（系列）
    - 数据格式化：将查询结果转换为图表数据格式
    """
    # 提取分类轴数据（第一列）
    x_data = [str(row.get(columns[0], "")) for row in rows]

    # 提取数值轴数据（第二列）
    y_data = [row.get(columns[1], 0) for row in rows]

    return {
        "tooltip": {"trigger": "axis"},
        "legend": {"data": [columns[1]]},
        "xAxis": {
            "type": "category",
            "data": x_data,
            "axisLabel": {
                "rotate": 30 if len(x_data) > 5 else 0,
                "interval": 0,
            },
        },
        "yAxis": {"type": "value"},
        "series": [
            {
                "name": columns[1],
                "type": "bar",
                "data": y_data,
                "itemStyle": {"color": DEFAULT_COLORS[0]},
                "label": {"show": True, "position": "top"},
            }
        ],
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "15%",
            "containLabel": True,
        },
    }


def _build_line_option(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
    """
    构建折线图配置

    Args:
        rows: 查询结果行
        columns: 列名列表

    Returns:
        折线图配置

    学习要点：
    - 折线图配置：适合展示趋势数据
    - 平滑曲线：使用 smooth 属性使曲线平滑
    """
    # 提取时间轴数据（第一列）
    x_data = [str(row.get(columns[0], "")) for row in rows]

    # 提取数值数据（第二列）
    y_data = [row.get(columns[1], 0) for row in rows]

    return {
        "tooltip": {"trigger": "axis"},
        "legend": {"data": [columns[1]]},
        "xAxis": {
            "type": "category",
            "data": x_data,
            "boundaryGap": False,
        },
        "yAxis": {"type": "value"},
        "series": [
            {
                "name": columns[1],
                "type": "line",
                "data": y_data,
                "smooth": True,
                "itemStyle": {"color": DEFAULT_COLORS[0]},
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0,
                        "y": 0,
                        "x2": 0,
                        "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": DEFAULT_COLORS[0] + "80"},
                            {"offset": 1, "color": DEFAULT_COLORS[0] + "10"},
                        ],
                    }
                },
                "label": {"show": True, "position": "top"},
            }
        ],
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True,
        },
    }


def _build_pie_option(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
    """
    构建饼图配置

    Args:
        rows: 查询结果行
        columns: 列名列表

    Returns:
        饼图配置

    学习要点：
    - 饼图配置：name（名称）、value（数值）
    - 标签格式：显示名称和百分比
    """
    # 构建饼图数据
    pie_data = []
    for row in rows:
        pie_data.append(
            {
                "name": str(row.get(columns[0], "")),
                "value": row.get(columns[1], 0),
            }
        )

    return {
        "tooltip": {
            "trigger": "item",
            "formatter": "{a} <br/>{b}: {c} ({d}%)",
        },
        "legend": {
            "orient": "vertical",
            "left": "left",
            "data": [item["name"] for item in pie_data],
        },
        "series": [
            {
                "name": columns[0],
                "type": "pie",
                "radius": "55%",
                "center": ["50%", "60%"],
                "data": pie_data,
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)",
                    }
                },
                "label": {
                    "show": True,
                    "formatter": "{b}: {c} ({d}%)",
                },
            }
        ],
        "color": DEFAULT_COLORS,
    }


def _build_table_option(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
    """
    构建表格配置

    Args:
        rows: 查询结果行
        columns: 列名列表

    Returns:
        表格配置

    学习要点：
    - 表格配置：列定义和数据
    - 适用于明细数据展示
    """
    # 构建列定义
    column_defs = [
        {
            "title": col,
            "dataIndex": col,
            "key": col,
            "width": 150,
        }
        for col in columns
    ]

    # 构建数据（添加 key 字段）
    data_with_key = []
    for idx, row in enumerate(rows):
        data_with_key.append(
            {
                **row,
                "key": idx,
            }
        )

    return {
        "type": "table",
        "columns": column_defs,
        "dataSource": data_with_key,
        "pagination": {
            "pageSize": 10,
            "showSizeChanger": True,
            "showTotal": lambda total: f"共 {total} 条",
        },
        "scroll": {"x": "max-content"},
    }
