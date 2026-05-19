# Current Plan

## Active Objective

AptGuide 3.0 评测系统全面改造 — **COMPLETED** (2026-05-16). Live eval running.

## Current State

- T1 KB QA: 60 cases, all with `expected_doc_ids` (inferred, marked TODO for live discovery)
- T1 Room Search: 30 cases, criteria-based evaluation (district/price/amenity), no Hit@5
- T2 Understanding: 55 cases, all structured assertions, 10 risk cases with `expected_risk_level`, 12 entity cases with resolution fields
- T3 Procedures: 55 cases, all structured assertions (no free-text), multi-turn session reuse, user_id passthrough
- Total: 200 cases, smoke eval passes, 64 unit tests pass, ruff clean
- Runner: criteria-based room search, multi-turn session reuse, entity resolution validation, latency_ok check
- Live eval running to verify end-to-end

## Completed Plan

`docs/plans/2026-05-16-aptguide3-eval-system-overhaul-plan.md` — all 4 waves done

## Next Work

1. Analyze live eval results when available
2. Live discovery run to verify KB QA `expected_doc_ids` accuracy
3. Production hardening: retry, idempotency, rate limiting, metrics, alerting
