"""Sparse lexical signal for RAG v2.

This is not the primary relevance mechanism. It is a transparent lexical
baseline used inside hybrid retrieval and eval tests.
"""

from __future__ import annotations

import re


def sparse_score(query: str, text: str) -> float:
    query_terms = _tokenize(query)
    text_terms = _tokenize(text)
    if not query_terms or not text_terms:
        return 0.0
    overlap = query_terms & text_terms
    return min(len(overlap) / max(len(query_terms), 1), 1.0)


def _tokenize(text: str) -> set[str]:
    ascii_terms = set(re.findall(r"[A-Za-z0-9_]+", text.lower()))
    cjk_terms = {ch for ch in text if "一" <= ch <= "鿿"}
    return ascii_terms | cjk_terms
