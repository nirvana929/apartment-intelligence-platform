"""测试 Agent 工作流图结构。"""

from unittest.mock import MagicMock

from aptguide.agent.graph import create_agent_graph


def test_graph_creation():
    """图可以被创建并包含预期节点。"""
    llm = MagicMock()
    kb = MagicMock()
    room_index = MagicMock()

    graph = create_agent_graph(llm, kb, room_index)

    # 图应成功编译
    assert graph is not None


def test_graph_has_expected_nodes():
    """图包含所有预期的节点。"""
    llm = MagicMock()
    kb = MagicMock()
    room_index = MagicMock()

    graph = create_agent_graph(llm, kb, room_index)

    expected_nodes = {"intent", "kb_search", "reply", "slot", "ask", "room_search", "rerank"}

    # LangGraph CompiledGraph 的节点信息
    graph_nodes = set(graph.get_graph().nodes.keys())
    for node in expected_nodes:
        assert node in graph_nodes, f"缺少节点: {node}"


def test_route_intent_kb_qa():
    """kb_qa 意图路由到 kb_search。"""
    from aptguide.agent.graph import route_intent

    state = {"intent": "kb_qa"}
    assert route_intent(state) == "kb_search"


def test_route_intent_room_search():
    """room_search 意图路由到 slot。"""
    from aptguide.agent.graph import route_intent

    state = {"intent": "room_search"}
    assert route_intent(state) == "slot"


def test_route_intent_other():
    """其他意图路由到 reply。"""
    from aptguide.agent.graph import route_intent

    state = {"intent": "other"}
    assert route_intent(state) == "reply"


def test_route_after_slot_missing():
    """缺少必要槽位时路由到 ask。"""
    from aptguide.agent.graph import route_after_slot

    state = {"slots": {"district": "浦东"}}
    assert route_after_slot(state) == "ask"


def test_route_after_slot_complete():
    """槽位完整时路由到 room_search。"""
    from aptguide.agent.graph import route_after_slot

    state = {"slots": {"max_rent": 5000, "district": "浦东"}}
    assert route_after_slot(state) == "room_search"
