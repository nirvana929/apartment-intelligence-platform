# Handoff

## Status

Eval system overhaul **COMPLETED** (2026-05-16). All 4 waves executed successfully.

## Completed

- All 7 milestones (M0-M7) and RAG roadmap (6 plans) complete.
- KB QA pipeline production-ready: 100% Hit@3, all high-risk criteria pass.
- **Eval system overhaul (2026-05-16):**
  - T1: 90 cases (30 room search criteria-based + 60 KB QA with expected_doc_ids)
  - T2: 55 cases, all structured, risk_level + entity resolution fields
  - T3: 55 cases, all structured, multi-turn session reuse, user_id passthrough
  - Runner: criteria-based evaluation, latency_ok, entity resolution validation
  - 64 unit tests pass, ruff clean, smoke eval outputs 200 cases

## Next Steps

1. Live discovery run to verify KB QA `expected_doc_ids`
2. Live eval run to verify criteria-based room search end-to-end
3. Production hardening

## Constraints

- Do not touch RAG pipeline code (room_retrieval.py, kb_retrieval.py, ranking, confidence)
- Do not touch understanding module
- Keep LLM-first, no keyword fallback
