from aptguide.agent.state import AgentState


def test_agent_state():
    state: AgentState = {
        "session_id": "test-001",
        "message": "押金怎么退？",
        "intent": None,
        "slots": {},
        "search_results": [],
        "confirmation": None,
        "reply": "",
        "cards": [],
        "actions": [],
        "sources": [],
    }
    assert state["session_id"] == "test-001"
    assert state["intent"] is None
