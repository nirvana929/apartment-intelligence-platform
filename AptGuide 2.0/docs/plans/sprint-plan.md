# Sprint Plan

## Status: ACTIVE (2026-05-14)

## Scope

Risk-aware Query Understanding Guardrail for AptGuide 2.0.

## Commitments

- Preserve the existing `risk_level` contract while adding structured risk metadata.
- Replace keyword-only risk decisions with rule signals, classifier output, and a policy matrix.
- Keep medium policy questions answerable through KB instead of refusing them.
- Route high refund/contract requests to controlled templates or human handoff instead of free-form promises.
- Refuse third-party privacy requests.
- Measure both safety and overblocking through risk eval metrics.

## Explicitly Deferred

- Live LLM risk classifier adapter until deterministic contracts and eval are stable.
- Custom trained risk classifier.
- Full enterprise moderation platform.
- RAG retrieval quality optimization.
- Full apartment platform integration through `rentHouseH5`.
- Standalone hardening/observability execution, which remains documented in `2026-05-14-aptguide2-standalone-hardening-observability-agent-plan.md`.

## Execution Notes

- Execute from `docs/plans/2026-05-14-aptguide2-risk-aware-query-understanding-guardrail-agent-plan.md`.
- Treat `risk_level` as routing metadata, not automatic blocking.
- Use `response_mode` for final behavior.
- Do not let LLM/classifier output downgrade strong deterministic red-line signals.
- Do not add live LLM calls before the testable `RiskClassifier` protocol and fallback classifier are stable.
