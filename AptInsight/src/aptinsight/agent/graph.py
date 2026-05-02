"""
LangGraph 工作流组装模块

本模块负责将各个节点组装成完整的 LangGraph 工作流。
LangGraph 是一个用于构建有状态、多步骤 AI 应用的框架。

学习要点：
1. LangGraph 核心概念 - StateGraph、节点、边、条件边
2. 工作流设计 - 如何设计多步骤的处理流程
3. 条件路由 - 根据状态决定下一步执行哪个节点
4. 错误处理 - 如何在工作流中处理错误

工作流程：
用户问题
    ↓
意图识别（classify_intent）
    ↓
    ├── 业务分析 → SQL 生成（generate_sql）
    │                  ↓
    │              SQL 守卫（guard_sql）
    │                  ↓
    │              SQL 执行（execute_sql）
    │                  ↓
    │              图表构建（build_chart）
    │                  ↓
    │              答案生成（write_answer）
    │                  ↓
    │              结束
    │
    ├── 闲聊 → 直接回答
    │            ↓
    │          结束
    │
    └── 超出范围 → 提示无法处理
                     ↓
                   结束
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from langgraph.graph import END, StateGraph

from ..core.config import settings
from ..core.logging import get_logger
from ..llm.client import LLMClient
from .nodes.build_chart import build_chart
from .nodes.execute_sql import execute_sql
from .nodes.generate_sql import generate_sql
from .nodes.guard_sql import guard_sql
from .nodes.intent import classify_intent
from .nodes.write_answer import write_answer
from .state import (
    AgentState,
    INTENT_ANALYSIS,
    INTENT_CHITCHAT,
    INTENT_OUT_OF_SCOPE,
    create_initial_state,
)

# 知识文件路径
_KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


@lru_cache
def _load_schema_context() -> str:
    """加载数据库 schema 知识"""
    schema_file = _KNOWLEDGE_DIR / "schema_lease.md"
    if schema_file.exists():
        return schema_file.read_text(encoding="utf-8")
    return ""


@lru_cache
def _load_metric_context() -> str:
    """加载指标口径知识"""
    metric_file = _KNOWLEDGE_DIR / "metrics.md"
    if metric_file.exists():
        return metric_file.read_text(encoding="utf-8")
    return ""


@lru_cache
def _load_few_shots() -> str:
    """加载 few-shot 示例"""
    few_shots_file = _KNOWLEDGE_DIR / "few_shots.md"
    if few_shots_file.exists():
        return few_shots_file.read_text(encoding="utf-8")
    return ""

# 获取日志记录器
logger = get_logger(__name__)


# ============================================================================
# 工作流构建
# ============================================================================

def create_agent_graph(llm_client: LLMClient):
    """
    创建 Agent 工作流图

    不同节点使用不同配置的 LLM 客户端：
    - 意图识别：小模型 + 少量 tokens
    - SQL 生成：pro 模型 + 中等 tokens
    - 答案生成：小模型 + 中等 tokens
    """
    # 为不同节点创建独立的 LLM 客户端
    intent_client = LLMClient(
        model=settings.llm_model_intent or llm_client.model,
        default_max_tokens=settings.llm_max_tokens_intent,
    )
    sql_client = LLMClient(
        model=settings.llm_model_sql or llm_client.model,
        default_max_tokens=settings.llm_max_tokens_sql,
    )
    answer_client = LLMClient(
        model=settings.llm_model_answer or llm_client.model,
        default_max_tokens=settings.llm_max_tokens_answer,
    )

    logger.info(
        f"节点模型配置: intent={intent_client.model}({intent_client.default_max_tokens}t), "
        f"sql={sql_client.model}({sql_client.default_max_tokens}t), "
        f"answer={answer_client.model}({answer_client.default_max_tokens}t)"
    )

    workflow = StateGraph(AgentState)

    workflow.add_node("classify_intent", _wrap_node(classify_intent, intent_client))
    workflow.add_node("generate_sql", _wrap_node(generate_sql, sql_client))
    workflow.add_node("guard_sql", guard_sql)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("build_chart", build_chart)
    workflow.add_node("write_answer", _wrap_node(write_answer, answer_client))

    # ----- 定义边 -----
    # 设置入口点
    workflow.set_entry_point("classify_intent")

    # 意图识别后的条件路由
    # 学习要点：add_conditional_edges 根据函数返回值选择下一步
    workflow.add_conditional_edges(
        "classify_intent",  # 源节点
        _route_after_intent,  # 路由函数
        {
            INTENT_ANALYSIS: "generate_sql",  # 业务分析 → SQL 生成
            INTENT_CHITCHAT: "write_answer",  # 闲聊 → 直接生成答案
            INTENT_OUT_OF_SCOPE: "write_answer",  # 超出范围 → 生成提示答案
            "error": END,  # 错误 → 结束
        },
    )

    # SQL 生成后的条件路由
    workflow.add_conditional_edges(
        "generate_sql",
        _route_after_sql_generation,
        {
            "success": "guard_sql",  # 成功 → SQL 守卫
            "error": "write_answer",  # 错误 → 生成错误提示
        },
    )

    # SQL 守卫后的条件路由
    workflow.add_conditional_edges(
        "guard_sql",
        _route_after_sql_guard,
        {
            "passed": "execute_sql",  # 通过 → 执行 SQL
            "failed": "write_answer",  # 失败 → 生成错误提示
        },
    )

    # SQL 执行后的条件路由
    workflow.add_conditional_edges(
        "execute_sql",
        _route_after_sql_execution,
        {
            "success": "build_chart",  # 成功 → 构建图表
            "error": "write_answer",  # 错误 → 生成错误提示
        },
    )

    # 图表构建后 → 答案生成
    workflow.add_edge("build_chart", "write_answer")

    # 答案生成后 → 结束
    workflow.add_edge("write_answer", END)

    # ----- 编译图 -----
    # 学习要点：compile() 将图转换为可执行的形式
    graph = workflow.compile()

    logger.info("Agent 工作流图创建完成")

    return graph


# ============================================================================
# 节点包装器
# ============================================================================

def _wrap_node(
    node_func: Callable[..., Any],
    llm_client: LLMClient,
) -> Callable[[AgentState], AgentState]:
    """
    包装节点函数，注入 LLM 客户端
    """
    # [框架] LangGraph 的 add_node 要求节点函数签名必须是 (state) -> state
    # 但我们的节点函数需要两个参数：(state, llm_client)
    # 所以用闭包把 llm_client "包进去"，让外面只看到 state 一个参数
    #
    # [对比] 两种节点函数签名：
    #   classify_intent(state, llm_client)  → 需要 LLM，用 _wrap_node 包装
    #   guard_sql(state)                    → 不需要 LLM，直接传给 add_node
    #
    # [框架] 这里用了 Python 闭包：wrapped_node 引用了外层的 llm_client 变量
    # 即使 _wrap_node 执行完毕，wrapped_node 依然持有 llm_client 的引用
    # 这是 Python 闭包的基本特性，不是框架特有的
    async def wrapped_node(state: AgentState) -> AgentState:
        return await node_func(state, llm_client)

    return wrapped_node


# ============================================================================
# 路由函数
# ============================================================================

def _route_after_intent(state: AgentState) -> str:
    """
    意图识别后的路由函数

    根据识别出的意图类型，决定下一步执行哪个节点。

    Args:
        state: 当前状态

    Returns:
        下一个节点的名称

    学习要点：
    - 条件路由：根据状态决定执行路径
    - 错误传播：将错误信息传递给后续节点
    """
    # 检查是否有错误
    if state.get("error"):
        logger.warning(f"意图识别出错，跳转到结束，错误: {state['error']}")
        return "error"

    intent = state.get("intent", "")

    logger.info(f"意图路由，意图: {intent}")

    if intent == INTENT_ANALYSIS:
        return INTENT_ANALYSIS
    elif intent == INTENT_CHITCHAT:
        return INTENT_CHITCHAT
    elif intent == INTENT_OUT_OF_SCOPE:
        return INTENT_OUT_OF_SCOPE
    else:
        # 未知意图，视为超出范围
        logger.warning(f"未知意图类型: {intent}")
        return INTENT_OUT_OF_SCOPE


def _route_after_sql_generation(state: AgentState) -> str:
    """
    SQL 生成后的路由函数

    Args:
        state: 当前状态

    Returns:
        "success" 或 "error"
    """
    if state.get("error"):
        logger.warning(f"SQL 生成出错，错误: {state['error']}")
        return "error"

    if not state.get("generated_sql"):
        logger.warning("未生成 SQL")
        return "error"

    return "success"


def _route_after_sql_guard(state: AgentState) -> str:
    """
    SQL 守卫后的路由函数

    Args:
        state: 当前状态

    Returns:
        "passed" 或 "failed"
    """
    if state.get("error"):
        logger.warning(f"SQL 守卫检查失败，错误: {state['error']}")
        return "failed"

    guard_result = state.get("sql_guard_result", {})
    if guard_result.get("passed"):
        return "passed"

    logger.warning(f"SQL 守卫检查未通过，原因: {guard_result.get('message')}")
    return "failed"


def _route_after_sql_execution(state: AgentState) -> str:
    """
    SQL 执行后的路由函数

    Args:
        state: 当前状态

    Returns:
        "success" 或 "error"
    """
    if state.get("error"):
        logger.warning(f"SQL 执行出错，错误: {state['error']}")
        return "error"

    # 检查是否有结果数据
    rows = state.get("rows", [])
    if rows:
        return "success"

    # 没有数据也算成功（可能是空结果）
    return "success"


# ============================================================================
# 工作流执行器
# ============================================================================

class AgentExecutor:
    """
    Agent 执行器

    封装 LangGraph 图，提供简单的执行接口。

    学习要点：
    - 封装：将复杂的内部实现封装成简单的接口
    - 状态管理：管理工作流的状态
    - 错误处理：统一处理执行过程中的错误
    """

    def __init__(self, llm_client: LLMClient):
        """
        初始化执行器

        Args:
            llm_client: LLM 客户端实例
        """
        self.llm_client = llm_client
        self.graph = create_agent_graph(llm_client)
        logger.info("Agent 执行器初始化完成")

    async def run(
        self,
        question: str,
        trace_id: str = "",
        session_id: str | None = None,
    ) -> AgentState:
        """
        执行 Agent 工作流

        Args:
            question: 用户问题
            trace_id: 请求追踪 ID
            session_id: 会话 ID

        Returns:
            最终的 Agent 状态

        学习要点：
        - 异步执行：使用 await 执行异步工作流
        - 状态初始化：创建初始状态
        - 结果返回：返回完整的状态对象
        """
        logger.info(f"开始执行 Agent 工作流，问题: {question[:50]}")

        # 创建初始状态，注入知识上下文
        initial_state = create_initial_state(
            question=question,
            trace_id=trace_id,
            session_id=session_id,
        )
        initial_state["schema_context"] = _load_schema_context()
        initial_state["metric_context"] = _load_metric_context()

        try:
            # 执行工作流
            # 学习要点：graph.ainvoke() 异步执行图
            final_state = await self.graph.ainvoke(initial_state)

            logger.info(
                f"Agent 工作流执行完成，有错误: {bool(final_state.get('error'))}，有答案: {bool(final_state.get('answer'))}"
            )

            return final_state

        except Exception as e:
            logger.error(f"Agent 工作流执行异常，错误: {e}")

            # 返回带有错误信息的状态
            return {
                **initial_state,
                "error": f"工作流执行异常: {str(e)}",
                "answer": "抱歉，处理您的问题时发生了错误，请稍后重试。",
                "summary": "处理出错",
            }


# ============================================================================
# 便捷函数
# ============================================================================

async def run_agent(
    question: str,
    llm_client: LLMClient,
    trace_id: str = "",
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    便捷的 Agent 执行函数

    Args:
        question: 用户问题
        llm_client: LLM 客户端实例
        trace_id: 请求追踪 ID
        session_id: 会话 ID

    Returns:
        包含答案、图表等信息的字典

    学习要点：
    - 便捷函数：简化常见操作
    - 结果格式化：将状态转换为易于使用的格式
    """
    executor = AgentExecutor(llm_client)
    state = await executor.run(question, trace_id, session_id)

    return {
        "answer": state.get("answer", ""),
        "summary": state.get("summary", ""),
        "chart_type": state.get("chart_type"),
        "chart_option": state.get("chart_option"),
        "sql": state.get("safe_sql") or state.get("generated_sql"),
        "rows": state.get("rows", []),
        "columns": state.get("columns", []),
        "error": state.get("error"),
        "warnings": state.get("warnings", []),
        "intent": state.get("intent", ""),
    }
