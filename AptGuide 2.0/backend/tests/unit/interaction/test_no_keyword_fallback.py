from pathlib import Path


PROJECT_SRC = Path(__file__).resolve().parents[3] / "src" / "aptguide2"


def test_classifier_has_no_keyword_route_helpers():
    text = (PROJECT_SRC / "interaction" / "classifier.py").read_text(encoding="utf-8")

    forbidden = [
        "_looks_like_room_search",
        "_looks_like_kb_policy",
        "_looks_like_policy_question",
        "_infer_kb_domain",
        "any(term in message",
    ]
    for pattern in forbidden:
        assert pattern not in text


def test_query_understanding_has_no_message_keyword_extractors():
    text = (PROJECT_SRC / "rag" / "query_understanding.py").read_text(encoding="utf-8")

    forbidden = [
        "AREA_KEYWORDS",
        "PREFERENCE_SYNONYMS",
        "PAYMENT_PATTERNS",
        "_detect_task",
        "_extract_budget",
        "_extract_district",
        "_extract_payment",
        "_extract_preferences",
        " in message",
    ]
    for pattern in forbidden:
        assert pattern not in text
