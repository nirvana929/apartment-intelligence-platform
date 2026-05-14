from evals.runners.run_interaction_intent_eval import score_case


def test_score_case_detects_mismatch():
    case = {"expected_route": "rag", "expected_domain": "payment", "expected_action": "ask_policy"}
    prediction = {"route": "rag", "domain": "room", "action": "search"}

    result = score_case(case, prediction)

    assert result["route_ok"] is True
    assert result["domain_ok"] is False
    assert result["action_ok"] is False


def test_score_case_all_match():
    case = {"expected_route": "rag", "expected_domain": "payment", "expected_action": "ask_policy"}
    prediction = {"route": "rag", "rag_task": "kb_qa", "domain": "payment", "action": "ask_policy"}

    result = score_case(case, prediction)

    assert all(result.values())


def test_score_case_optional_fields_not_checked_when_none():
    case = {"expected_route": "rag", "expected_domain": "payment", "expected_action": "ask_policy"}
    prediction = {"route": "rag", "domain": "payment", "action": "ask_policy", "risk_level": "high"}

    result = score_case(case, prediction)

    assert result["risk_ok"] is True  # None expected -> always ok
    assert result["response_mode_ok"] is True
