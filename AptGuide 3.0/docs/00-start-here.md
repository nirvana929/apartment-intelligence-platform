# Start Here

## What This Project Is

AptGuide 3.0 is the next upgrade of the AptGuide C-side rental assistant in `apartment-intelligence-platform`.

It keeps useful product and integration lessons from AptGuide and AptGuide 2.0, but it does not reuse the AptGuide 2.0 keyword-based understanding runtime.

## Delivery Model

```text
Stage 1: independent AptGuide 3.0 service for development, demo, and evaluation.
Stage 2: integration into the AptGuide main-system chain through lease web-app.
```

Final C-side integration:

```text
rentHouseH5
  -> lease web-app /app/ai/chat
      -> AptGuide 3.0 /api/chat
          -> lease internal tools
          -> Milvus
          -> AptGuide 3.0 Agent state DB / Redis
          -> LLM
```

The independent validation frontend is useful for Stage 1, but the final production entry is still the AptGuide main-system frontend through `rentHouseH5` and `lease`.

## Completed Milestones

All 6 milestones are complete (2026-05-15):

- **M0 — Runnable scaffold**: 36 tests, ruff clean. LLM-first understanding, 7 procedures, integrations, in-memory persistence, console trace, Vue3 frontend.
- **M1 — Independent backend backbone**: 55 tests. Database schema (11 tables), repository contracts, MySQL/Redis persistence, auth boundary, readiness checks.
- **M2 — Live integration readiness**: 68 tests, 23 skipped. Docker-compose, skip-safe integration tests for all external services.
- **M3 — Procedure integration**: 129 tests, 28 skipped. All 7 procedures wired with RepoBundle, audit writes, async /ready probes.
- **M4 — LLM-first RAG upgrade**: 207 tests, 28 skipped. Room retrieval, 5-dimension ranking, KB retrieval, confidence gates, eval metrics, vector sync scripts.
- **M5 — Frontend E2E + live RAG eval**: 175 tests. Playwright E2E, live dependency verification, live RAG integration, business scenario routing.
- **M6 — LangSmith + diagnostics**: 22 tests. Opt-in LangSmith tracing, understanding diagnostics, rec-stage diagnostics, eval report integration.

## Current Engineering Objective

Sync room/KB vectors to Milvus and re-run live RAG evaluation with diagnostics to identify optimization targets. The 4 seed eval cases now correctly route through the RAG pipeline (no longer stuck in clarify). Failures are at the vector recall stage (Milvus data missing, not code issues).

## Non-Goals For The First Milestone

- Do not copy AptGuide 2.0 runtime modules.
- No keyword fallback for route, task, domain, filters, preferences, risk posture, or retrieval queries.
- No live room availability claims without lease validation.
- Do not make AptGuide 3.0 the source of truth for rooms, appointments, leases, contracts, or sensitive user data.
- Do not make frontend call lease, Milvus, Redis, MySQL, or LLM directly.

## Current Entry Points

- Architecture: `docs/architecture.md`
- Understanding contract: `docs/understanding-contract.md`
- API contract: `docs/api-contract.md`
- Deployment readiness: `docs/system/deployment-readiness.md`
- Current plan: `docs/plans/current-plan.md`
- Evaluation report: `docs/tests/evaluation-report.md`
