# RAG v2 Character-Match Dependency Audit

## Summary

This report classifies character-match logic in the current RAG MVP into keep, weaken, and replace categories.

## Audit Table

| File | Function | Current mechanism | Class | RAG v2 decision | Test evidence required |
| --- | --- | --- | --- | --- | --- |
| backend/src/aptguide2/rag/query_understanding.py | _extract_budget | regex budget extraction | keep | Keep as hard-filter extraction | parser unit tests |
| backend/src/aptguide2/rag/query_understanding.py | _extract_district | district dictionary | keep | Keep as hard-filter extraction | parser unit tests |
| backend/src/aptguide2/rag/query_understanding.py | _extract_payment | payment dictionary | keep | Keep as hard-filter extraction | parser unit tests |
| backend/src/aptguide2/rag/query_understanding.py | _detect_task | keyword task routing via fallback_patterns, kb_keywords, room_keywords | weaken | Keep for MVP path; RAG v2 planning must produce explicit routing evidence and eval coverage | planning tests |
| backend/src/aptguide2/rag/query_understanding.py | _extract_preferences | PREFERENCE_SYNONYMS synonym dictionary | weaken | Use only as seed terms for retrieval plan, not final preference relevance | planning/rerank tests |
| backend/src/aptguide2/rag/query_understanding.py | _detect_risk | keyword risk level detection (high_risk, medium_risk) | weaken | Keep as safety signal; cap weight in final ranking | safety/eval tests |
| backend/src/aptguide2/rag/query_understanding.py | _is_budget_clearing | clearing_patterns string inclusion | keep | Keep as hard-filter extraction | parser unit tests |
| backend/src/aptguide2/rag/kb_retrieval.py | _source_rerank | title character overlap and module keyword boosts | replace | Move to governed rerank using normalized dense, sparse, module, and risk features | rerank tests and KB eval |
| backend/src/aptguide2/rag/ranking.py | _score_tags | string inclusion in tags/facilities | weaken | Cap as weak metadata feature; final ranking must include semantic and validation signals | rerank tests and room eval |

## RAG v2 Policy

1. Character matching may extract hard filters and safety controls.
2. Character matching may be a weak feature with a documented maximum weight.
3. Character matching must not be the primary source ranking or semantic relevance mechanism.
4. Any replacement must be proven by eval gates, not subjective inspection.