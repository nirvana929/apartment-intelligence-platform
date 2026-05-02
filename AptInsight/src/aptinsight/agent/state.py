"""
AptInsight Agent 状态定义模块

本模块定义了 LangGraph 工作流中传递的状态数据结构。
状态是 LangGraph 的核心概念，它在各个节点之间传递数据。

学习要点：
1. TypedDict - Python 的类型提示工具，用于定义字典的结构
2. LangGraph 状态 - 工作流中各个节点共享的数据
3. 数据流向 - 状态如何在节点之间传递

状态流转图：
用户问题 → 意图识别 → SQL生成 → SQL守卫 → SQL执行 → 图表构建 → 答案生成
    ↓           ↓          ↓          ↓          ↓          ↓          ↓
  question   intent     sql       guard      rows     chart     answer
"""

from __future__ import annotations

from typing import Any, TypedDict


# ============================================================================
# Agent 核心状态定义
# ============================================================================

class AgentState(TypedDict, total=False):
    """
    Agent 工作流状态

    这是 LangGraph 工作流的核心状态类，在各个节点之间传递。
    每个节点会读取状态中的数据，处理后更新状态。

    学习要点：
    - TypedDict: Python 3.8+ 的类型提示，定义字典的固定结构
    - total=False: 表示所有字段都是可选的（可以只设置部分字段）
    - 状态模式: 所有节点共享同一个状态字典

    状态流转过程：
    1. 初始状态：只有 question 字段有值
    2. 意图识别后：intent, intent_reason 有值
    3. SQL 生成后：generated_sql, tables_used 有值
    4. SQL 守卫后：safe_sql, sql_guard_result 有值
    5. SQL 执行后：rows, columns 有值
    6. 图表构建后：chart_type, chart_option 有值
    7. 答案生成后：answer, summary 有值

    字段说明：
    - trace_id: 请求追踪 ID，用于日志关联
    - session_id: 会话 ID，用于多轮对话
    - question: 用户的原始问题
    - normalized_question: 标准化后的问题（去除噪音）
    - intent: 识别出的意图类型
    - schema_context: 数据库 schema 上下文（用于 SQL 生成）
    - metric_context: 指标口径上下文（用于 SQL 生成）
    - generated_sql: LLM 生成的原始 SQL
    - safe_sql: 经过安全检查的 SQL
    - sql_guard_result: SQL 守卫检查结果
    - rows: 查询结果行
    - columns: 结果列名
    - chart_type: 图表类型
    - chart_option: ECharts 配置
    - answer: 最终答案
    - warnings: 警告信息列表
    - error: 错误信息
    """

    # ----- 追踪字段 -----
    # 请求追踪 ID，用于在日志中关联同一请求的所有操作
    trace_id: str
    # 会话 ID，用于多轮对话场景
    session_id: str | None

    # ----- 输入字段 -----
    # 用户的原始自然语言问题
    question: str
    # 标准化后的问题（去除标点、纠正错别字等）
    normalized_question: str

    # ----- 意图识别字段 -----
    # 识别出的意图类型（analysis/chitchat/out_of_scope）
    intent: str
    # 数据库 schema 上下文，包含表结构信息
    schema_context: str
    # 指标口径上下文，包含业务指标定义
    metric_context: str

    # ----- SQL 生成字段 -----
    # LLM 生成的原始 SQL 语句
    generated_sql: str | None
    # 经过安全检查的 SQL（可能被重写）
    safe_sql: str | None
    # SQL 守卫检查结果（包含是否通过、违规类型等）
    sql_guard_result: dict[str, Any]

    # ----- SQL 执行字段 -----
    # 查询结果数据行
    rows: list[dict[str, Any]]
    # 结果列信息（列名、类型等）
    columns: list[dict[str, Any]]

    # ----- 图表字段 -----
    # 图表类型（bar/line/pie/table）
    chart_type: str | None
    # ECharts 配置对象
    chart_option: dict[str, Any] | None

    # ----- 答案字段 -----
    # 最终生成的答案文本
    answer: str

    # ----- 辅助字段 -----
    # 警告信息列表（非致命问题）
    warnings: list[str]
    # 错误信息（致命错误）
    error: str | None


# ============================================================================
# 意图类型常量
# ============================================================================

# 学习要点：使用常量字符串而不是枚举，简化代码
# 在 LangGraph 中，状态字段通常是简单的字符串类型

INTENT_ANALYSIS = "analysis"          # 业务分析 - 需要查询数据库
INTENT_CHITCHAT = "chitchat"          # 闲聊 - 不需要查询
INTENT_OUT_OF_SCOPE = "out_of_scope"  # 超出范围 - 无法处理


# ============================================================================
# 图表类型常量
# ============================================================================

CHART_TYPE_BAR = "bar"        # 柱状图 - 适合对比数据
CHART_TYPE_LINE = "line"      # 折线图 - 适合趋势分析
CHART_TYPE_PIE = "pie"        # 饼图 - 适合占比分析
CHART_TYPE_TABLE = "table"    # 表格 - 适合详细数据展示

# 系统支持的图表类型集合，用于校验 LLM 输出
SUPPORTED_CHART_TYPES = frozenset({
    CHART_TYPE_BAR,
    CHART_TYPE_LINE,
    CHART_TYPE_PIE,
    CHART_TYPE_TABLE,
})


# ============================================================================
# 状态辅助函数
# ============================================================================

def create_initial_state(question: str, trace_id: str = "", session_id: str | None = None) -> AgentState:
    """
    创建初始状态

    这是工作流的起点，创建一个只包含问题的状态对象。

    Args:
        question: 用户的原始问题
        trace_id: 请求追踪 ID（可选）
        session_id: 会话 ID（可选）

    Returns:
        初始状态字典

    学习要点：
    - 工厂函数：用于创建复杂的初始状态
    - 默认值：为可选字段提供合理的默认值
    """
    return AgentState(
        trace_id=trace_id,
        session_id=session_id,
        question=question,
        normalized_question="",  # 后续由意图识别节点填充
        intent="",               # 后续由意图识别节点填充
        schema_context="",       # 后续由知识检索节点填充
        metric_context="",       # 后续由知识检索节点填充
        generated_sql=None,      # 后续由 SQL 生成节点填充
        safe_sql=None,           # 后续由 SQL 守卫节点填充
        sql_guard_result={},     # 后续由 SQL 守卫节点填充
        rows=[],                 # 后续由 SQL 执行节点填充
        columns=[],              # 后续由 SQL 执行节点填充
        chart_type=None,         # 后续由图表构建节点填充
        chart_option=None,       # 后续由图表构建节点填充
        answer="",               # 后续由答案生成节点填充
        warnings=[],             # 用于收集非致命警告
        error=None,              # 用于记录致命错误
    )


def has_error(state: AgentState) -> bool:
    """
    检查状态是否包含错误

    Args:
        state: 当前状态

    Returns:
        True 如果有错误，否则 False

    学习要点：
    - 辅助函数：简化状态检查逻辑
    - 布尔表达式：直接返回条件判断结果
    """
    return state.get("error") is not None


def get_sql(state: AgentState) -> str | None:
    """
    获取安全的 SQL（优先使用重写后的 SQL）

    Args:
        state: 当前状态

    Returns:
        安全的 SQL 语句，如果没有则返回 None

    学习要点：
    - 优先级逻辑：优先使用经过安全检查的 SQL
    - 类型提示：返回类型可以是 str 或 None
    """
    # 优先使用经过安全检查的 SQL
    if state.get("safe_sql"):
        return state["safe_sql"]
    # 否则使用原始生成的 SQL
    return state.get("generated_sql")


def add_warning(state: AgentState, warning: str) -> None:
    """
    添加警告信息

    Args:
        state: 当前状态
        warning: 警告消息

    学习要点：
    - 状态修改：直接修改字典的值
    - 列表操作：使用 append 添加元素
    """
    if "warnings" not in state:
        state["warnings"] = []
    state["warnings"].append(warning)


def set_error(state: AgentState, error: str) -> None:
    """
    设置错误信息

    Args:
        state: 当前状态
        error: 错误消息

    学习要点：
    - 错误处理：设置错误状态
    - 一旦设置错误，后续节点应该检查并停止处理
    """
    state["error"] = error


def is_analysis_intent(state: AgentState) -> bool:
    """
    检查是否为业务分析意图

    Args:
        state: 当前状态

    Returns:
        True 如果是业务分析意图，否则 False
    """
    return state.get("intent") == INTENT_ANALYSIS


def is_chitchat_intent(state: AgentState) -> bool:
    """
    检查是否为闲聊意图

    Args:
        state: 当前状态

    Returns:
        True 如果是闲聊意图，否则 False
    """
    return state.get("intent") == INTENT_CHITCHAT


def should_generate_chart(state: AgentState) -> bool:
    """
    检查是否需要生成图表

    Args:
        state: 当前状态

    Returns:
        True 如果需要生成图表，否则 False

    学习要点：
    - 业务逻辑：根据结果行数和意图判断是否需要图表
    - 简单规则：超过 1 行数据时考虑生成图表
    """
    rows = state.get("rows", [])
    # 如果只有 1 行数据（如 COUNT 结果），不需要图表
    if len(rows) <= 1:
        return False
    # 如果有多个数据点，需要图表
    return len(rows) > 1
