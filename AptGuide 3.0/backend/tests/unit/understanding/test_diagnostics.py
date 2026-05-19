from aptguide3.understanding.diagnostics import UnderstandingDiagnostic, sanitize_for_report


def test_sanitize_for_report_redacts_sensitive_keys():
    payload = {
        "api_key": "secret",
        "nested": {"token": "secret-token", "safe": "ok"},
        "items": [{"password": "pw", "value": 1}],
    }

    assert sanitize_for_report(payload) == {
        "api_key": "<redacted>",
        "nested": {"token": "<redacted>", "safe": "ok"},
        "items": [{"password": "<redacted>", "value": 1}],
    }


def test_understanding_diagnostic_report_dict_is_sanitized():
    diagnostic = UnderstandingDiagnostic(
        raw_message="找番禺1500以内安静一点的房子",
        raw_llm_json='{"api_key":"secret"}',
        parsed_route="rag",
        parsed_task="room_search",
        parsed_confidence=0.9,
        parsed_clarification_needed=False,
        final_route="rag",
        final_task="room_search",
        final_confidence=0.9,
    )

    report = diagnostic.to_report_dict()

    assert report["parsed_route"] == "rag"
    assert report["parsed_task"] == "room_search"
