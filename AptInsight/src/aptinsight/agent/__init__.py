"""
LangGraph Agent 编排模块

本模块是 AptInsight Agent 的核心，负责：
1. 定义工作流状态
2. 实现各个处理节点
3. 组装 LangGraph 工作流图
4. 提供 Agent 执行接口

学习要点：
1. 模块组织 - 如何组织复杂的 AI 应用代码
2. LangGraph 框架 - 构建有状态的多步骤 AI 应用
3. 节点设计 - 每个节点负责一个独立的处理步骤
4. 状态管理 - 在节点之间传递和管理数据

模块结构：
- state.py: 状态定义
- nodes/: 各个处理节点
- graph.py: 工作流组装

使用示例：
    from aptinsight.agent import AgentExecutor, run_agent

    # 创建执行器
    executor = AgentExecutor(llm_client)

    # 执行查询
    result = await executor.run("本月各公寓预约量是多少？")
    print(result["answer"])
"""

from .graph import AgentExecutor, run_agent
from .state import (
    AgentState,
    INTENT_ANALYSIS,
    INTENT_CHITCHAT,
    INTENT_OUT_OF_SCOPE,
    create_initial_state,
    has_error,
    is_analysis_intent,
)

__all__ = [
    # 执行器
    "AgentExecutor",
    "run_agent",

    # 状态
    "AgentState",
    "create_initial_state",
    "has_error",
    "is_analysis_intent",

    # 常量
    "INTENT_ANALYSIS",
    "INTENT_CHITCHAT",
    "INTENT_OUT_OF_SCOPE",
]
