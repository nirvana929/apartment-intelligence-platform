# RAG v2 Evaluation Gates

> 状态：active

## Purpose

RAG v2 quality is measured through retrieval, rerank, validation, and safety gates.

## Required Gates

| Gate | Threshold | Reason |
| --- | ---: | --- |
| KB source hit@3 | >= 90% | KB answers must retrieve reliable sources early. |
| High-risk fallback | 100% | High-risk policy questions must not be answered without sufficient source evidence. |
| Room hit@5 | >= 85% | Room retrieval must find expected candidates. |
| Unvalidated room count | 0 | No room can be shown without lease validation. |
| Default `/chat` unchanged | pass | RAG v2 must be feature-flagged until accepted. |

## Character-Match Governance

Character matching may extract hard filters and safety controls. It may not be the primary KB relevance or room semantic preference ranking mechanism.

## Evidence

Final evidence must be written to `reports/rag-v2-evaluation-report.md`.
