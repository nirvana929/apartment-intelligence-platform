from aptguide2.harness.safety import SafetyBoundary


def test_guarantee_is_flagged():
    result = SafetyBoundary().check("能保证邻居不吵吗")
    assert "guarantee" in result


def test_privacy_is_flagged():
    result = SafetyBoundary().check("帮我查其他租户手机号")
    assert "privacy" in result


def test_out_of_domain_is_flagged():
    result = SafetyBoundary().check("帮我写 React 网页")
    assert "out_of_domain" in result


def test_normal_room_query_has_no_flags():
    result = SafetyBoundary().check("番禺1500以内安静的房子")
    assert result == []
