"""测试 Agent 工作流图结构。"""

from unittest.mock import MagicMock

from aptguide.agent.graph import create_agent_graph


def _make_graph():
    """创建测试用图实例。"""
    llm = MagicMock()
    kb = MagicMock()
    room_index = MagicMock()
    tool_client = MagicMock()
    memory = MagicMock()
    return create_agent_graph(llm, kb, room_index, tool_client, memory)


def test_graph_creation():
    """图可以被创建并包含预期节点。"""
    graph = _make_graph()

    # 图应成功编译
    assert graph is not None


def test_graph_has_expected_nodes():
    """图包含所有预期的节点。"""
    graph = _make_graph()

    expected_nodes = {
        "intent",
        "kb_search",
        "reply",
        "slot",
        "ask",
        "room_search",
        "rerank",
        "confirm",
        "tool",
    }

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


def test_route_intent_appointment_create():
    """appointment_create 意图路由到 slot。"""
    from aptguide.agent.graph import route_intent

    state = {"intent": "appointment_create"}
    assert route_intent(state) == "slot"


def test_route_intent_other():
    """其他意图路由到 reply。"""
    from aptguide.agent.graph import route_intent

    state = {"intent": "other"}
    assert route_intent(state) == "reply"


def test_check_slots_room_search_missing():
    """room_search 缺少必要槽位时路由到 ask。"""
    from aptguide.agent.graph import check_slots

    state = {"intent": "room_search", "slots": {"district": "浦东"}}
    assert check_slots(state) == "ask"


def test_check_slots_room_search_complete():
    """room_search 槽位完整时路由到 room_search。"""
    from aptguide.agent.graph import check_slots

    state = {"intent": "room_search", "slots": {"max_rent": 5000, "district": "浦东"}}
    assert check_slots(state) == "room_search"


def test_check_slots_appointment_missing():
    """appointment_create 缺少必要槽位时路由到 ask。"""
    from aptguide.agent.graph import check_slots

    state = {"intent": "appointment_create", "slots": {"room_id": "R101"}}
    assert check_slots(state) == "ask"


def test_check_slots_appointment_complete():
    """appointment_create 槽位完整时路由到 confirm。"""
    from aptguide.agent.graph import check_slots

    state = {
        "intent": "appointment_create",
        "slots": {"room_id": "R101", "appointment_time": "2026-05-03 10:00"},
    }
    assert check_slots(state) == "confirm"


def test_check_slots_unknown_intent():
    """未知意图路由到 reply。"""
    from aptguide.agent.graph import check_slots

    state = {"intent": "other", "slots": {}}
    assert check_slots(state) == "reply"


def test_check_confirmation_confirm():
    """用户确认时路由到 tool。"""
    from aptguide.agent.graph import check_confirmation

    state = {"confirmation": True, "message": "确认预约"}
    assert check_confirmation(state) == "tool"


def test_check_confirmation_cancel():
    """用户取消时路由到 reply。"""
    from aptguide.agent.graph import check_confirmation

    state = {"confirmation": True, "message": "取消"}
    assert check_confirmation(state) == "reply"


def test_check_confirmation_neutral():
    """用户无明确回复时路由到 reply。"""
    from aptguide.agent.graph import check_confirmation

    state = {"confirmation": True, "message": "再看看"}
    assert check_confirmation(state) == "reply"


def test_check_confirmation_false():
    """非确认状态路由到 reply。"""
    from aptguide.agent.graph import check_confirmation

    state = {"confirmation": False, "message": "确认"}
    assert check_confirmation(state) == "reply"
