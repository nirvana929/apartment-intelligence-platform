from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "aptguide3"

# All RAG runtime files that must remain free of keyword-fallback logic.
ALL_FILES = [
    # understanding layer
    SRC / "understanding" / "llm_understanding.py",
    SRC / "understanding" / "validation.py",
    # application layer
    SRC / "application" / "chat_service.py",
    # RAG runtime
    SRC / "rag" / "planning.py",
    SRC / "rag" / "room_retrieval.py",
    SRC / "rag" / "room_ranking.py",
    SRC / "rag" / "preference_scorer.py",
    SRC / "rag" / "kb_retrieval.py",
    SRC / "rag" / "kb_rerank.py",
    # procedure wrappers
    SRC / "procedures" / "room_search.py",
    SRC / "procedures" / "kb_qa.py",
]

# Patterns that indicate keyword-based fallback or rule-based intent
# classification -- banned in all scanned files.
KEYWORD_FALLBACK_PATTERNS = [
    "any(term in message",
    ' if "',
    "_looks_like",
    "_detect_task",
    "_extract_budget",
    "_extract_district",
    "_extract_preferences",
    "keyword",
    "fallback_patterns",
    "room_keywords",
    "kb_keywords",
]

# "regex" is forbidden only in understanding + RAG runtime files.
# Procedures, chunking (sync ingestion), and lease clients legitimately use
# regex, so they are excluded.
REGEX_PROHIBITED_FILES = [
    SRC / "understanding" / "llm_understanding.py",
    SRC / "understanding" / "validation.py",
    SRC / "application" / "chat_service.py",
    SRC / "rag" / "planning.py",
    SRC / "rag" / "room_retrieval.py",
    SRC / "rag" / "room_ranking.py",
    SRC / "rag" / "preference_scorer.py",
    SRC / "rag" / "kb_retrieval.py",
    SRC / "rag" / "kb_rerank.py",
]


def _assert_no_pattern(text: str, pattern: str, path: Path) -> None:
    """Fail with a clear message if *pattern* appears in *text*."""
    for lineno, line in enumerate(text.splitlines(), start=1):
        assert pattern not in line, (
            f"Forbidden pattern {pattern!r} found in {path} at line {lineno}"
        )


def test_rag_runtime_has_no_keyword_fallback_patterns():
    """All scanned files must be free of keyword-fallback patterns."""
    for path in ALL_FILES:
        text = path.read_text(encoding="utf-8")
        for pattern in KEYWORD_FALLBACK_PATTERNS:
            _assert_no_pattern(text, pattern, path)


def test_rag_runtime_has_no_regex_imports():
    """Understanding and RAG runtime files must not use regex."""
    for path in REGEX_PROHIBITED_FILES:
        text = path.read_text(encoding="utf-8")
        _assert_no_pattern(text, "regex", path)
