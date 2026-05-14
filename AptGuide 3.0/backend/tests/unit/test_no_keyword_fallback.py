from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "aptguide3"


def test_understanding_runtime_has_no_keyword_fallback_patterns():
    files = [
        SRC / "understanding" / "llm_understanding.py",
        SRC / "understanding" / "validation.py",
        SRC / "application" / "chat_service.py",
    ]
    forbidden = [
        "any(term in message",
        " if \"",
        "_looks_like",
        "_detect_task",
        "_extract_budget",
        "_extract_district",
        "_extract_preferences",
        "regex",
    ]

    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            assert pattern not in text, f"{pattern} found in {path}"
