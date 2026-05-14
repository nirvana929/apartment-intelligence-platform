from aptguide3.application.safety_boundary import SafetyBoundary


def test_privacy_request_is_blocked_before_llm():
    decision = SafetyBoundary().check("查一下室友手机号")

    assert decision.blocked is True
    assert decision.reason == "privacy"


def test_normal_room_search_is_not_blocked():
    decision = SafetyBoundary().check("有阳台的房间吗")

    assert decision.blocked is False
