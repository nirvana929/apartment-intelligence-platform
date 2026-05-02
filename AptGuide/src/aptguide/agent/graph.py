from langgraph.graph import END, StateGraph

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.vector.kb_search import KBSearch
from aptguide.vector.room_index import RoomIndex


def create_agent_graph(llm: LLMClient, kb: KBSearch, room_index: RoomIndex):
    """创建 Agent 工作流。"""
    from aptguide.agent.nodes.ask import ask_node
    from aptguide.agent.nodes.intent import intent_node
    from aptguide.agent.nodes.kb_search import kb_search_node
    from aptguide.agent.nodes.rerank import rerank_node
    from aptguide.agent.nodes.reply import reply_node
    from aptguide.agent.nodes.room_search import room_search_node
    from aptguide.agent.nodes.slot import slot_node

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent", lambda state: intent_node(state, llm))
    workflow.add_node("kb_search", lambda state: kb_search_node(state, kb))
    workflow.add_node("reply", lambda state: reply_node(state, llm))
    workflow.add_node("slot", lambda state: slot_node(state, llm))
    workflow.add_node("ask", lambda state: ask_node(state, llm))
    workflow.add_node("room_search", lambda state: room_search_node(state, room_index))
    workflow.add_node("rerank", lambda state: rerank_node(state, llm))

    # 定义边
    workflow.set_entry_point("intent")

    workflow.add_conditional_edges(
        "intent",
        route_intent,
        {
            "kb_search": "kb_search",
            "slot": "slot",
            "reply": "reply",
        },
    )

    workflow.add_conditional_edges(
        "slot",
        route_after_slot,
        {
            "ask": "ask",
            "room_search": "room_search",
        },
    )

    workflow.add_edge("kb_search", "reply")
    workflow.add_edge("room_search", "rerank")
    workflow.add_edge("rerank", "reply")
    workflow.add_edge("ask", END)
    workflow.add_edge("reply", END)

    return workflow.compile()


def route_intent(state: AgentState) -> str:
    """根据意图路由到对应节点。"""
    if state["intent"] == "kb_qa":
        return "kb_search"
    if state["intent"] == "room_search":
        return "slot"
    return "reply"


def route_after_slot(state: AgentState) -> str:
    """槽位抽取后判断是否需要追问。"""
    slots = state.get("slots", {})
    if not slots.get("max_rent") or not slots.get("district"):
        return "ask"
    return "room_search"
