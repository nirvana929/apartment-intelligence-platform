from langgraph.graph import END, StateGraph

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.vector.kb_search import KBSearch


def create_agent_graph(llm: LLMClient, kb: KBSearch):
    """创建 Agent 工作流。"""
    from aptguide.agent.nodes.intent import intent_node
    from aptguide.agent.nodes.kb_search import kb_search_node
    from aptguide.agent.nodes.reply import reply_node

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent", lambda state: intent_node(state, llm))
    workflow.add_node("kb_search", lambda state: kb_search_node(state, kb))
    workflow.add_node("reply", lambda state: reply_node(state, llm))

    # 定义边
    workflow.set_entry_point("intent")

    def route_intent(state: AgentState) -> str:
        if state["intent"] == "kb_qa":
            return "kb_search"
        return "reply"

    workflow.add_conditional_edges(
        "intent",
        route_intent,
        {
            "kb_search": "kb_search",
            "reply": "reply",
        },
    )

    workflow.add_edge("kb_search", "reply")
    workflow.add_edge("reply", END)

    return workflow.compile()
