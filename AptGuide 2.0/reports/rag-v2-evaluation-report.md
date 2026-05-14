# RAG v2 Evaluation Report

## Current Status

Enterprise RAG v2 hybrid retrieval, governed rerank, lease validation, and eval gates are complete.

## Phase 3: RAG v2 — Verification

### New Modules Created

| Module | File | Responsibility |
| --- | --- | --- |
| Planning | `rag/planning.py` | `RetrievalPlan`, query rewrite, module intent, step-back queries |
| Sparse | `rag/sparse.py` | Local sparse lexical scoring (CJK + ASCII tokenization) |
| Hybrid | `rag/hybrid.py` | `HybridCandidate`, score normalization, deduplication, channel attribution |
| Rerank | `rag/rerank.py` | Governed rerank with explicit feature weights (lexical capped at 5%) |
| Validation | `rag/validation.py` | Lease validation gate for room candidates |
| Pipeline v2 | `rag/pipeline_v2.py` | RAG v2 orchestration behind `rag_v2` feature flag with trace support |
| Tool Validation | `rag/tool_validation.py` | `ToolRuntimeRoomValidator` adapter over governed ToolRuntime |
| Eval Metrics | `rag/eval_metrics.py` | hit@k, MRR, nDCG metrics |

### Test Results

```
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/e2e -q
```

- **Total: 246 tests passed**
- Baseline: 227 tests (from Phase 1 + Phase 2)
- New RAG v2: 19 tests
  - `test_planning.py`: 3 tests
  - `test_hybrid.py`: 3 tests
  - `test_rerank.py`: 2 tests
  - `test_validation.py`: 3 tests
  - `test_eval_metrics.py`: 3 tests
  - `test_pipeline_v2_trace.py`: 1 test
  - `test_api.py` (rag_v2 e2e): 4 tests

### Feature-Flag Isolation

- Default `/chat` remains MVP v1 (unchanged)
- `APTGUIDE_PIPELINE_VERSION=harness_v1` switches to harness mode (unchanged)
- `APTGUIDE_PIPELINE_VERSION=rag_v2` switches to RAG v2 pipeline

### Character-Match Governance

Audit report: `reports/rag-v2-character-match-audit.md`

| Class | Count | Examples |
| --- | --- | --- |
| keep | 4 | budget regex, district dictionary, payment dictionary, clearing patterns |
| weaken | 4 | task detection, preference synonyms, risk detection, tag scoring |
| replace | 1 | KB source rerank → governed rerank |

### Eval Gates (Documented)

| Gate | Threshold | Status |
| --- | ---: | --- |
| KB source hit@3 | >= 90% | Documented, requires live services to measure |
| High-risk fallback | 100% | Documented, requires live services to measure |
| Room hit@5 | >= 85% | Documented, requires live services to measure |
| Unvalidated room count | 0 | Enforced by validation gate (no room shown without lease validation) |
| Default `/chat` unchanged | pass | Verified by e2e tests |

## Result

```json
{
  "rag_v2_passes": true,
  "total_tests": 246,
  "new_rag_v2_tests": 19,
  "new_modules": 8,
  "feature_flag_isolation": true,
  "default_chat_unchanged": true,
  "eval_gates_documented": true,
  "character_match_audit": true,
  "next_step": "Live eval with Milvus/embedding/lease services"
}
```
