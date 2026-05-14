# Sprint Plan

## Scope

AptGuide 3.0 Milestone 1: Independent Backend Backbone.

## Commitments

- Keep AptGuide 3.0 as an AptGuide main-system upgrade, not a disconnected product.
- Preserve LLM-first understanding with no keyword fallback.
- Add MySQL schema and repository contracts for Agent runtime state.
- Add Redis hot state for sessions and pending-action TTL.
- Persist messages, procedure runs, trace events, memories, handoff tickets, and audit events.
- Add auth boundary for `lease -> AptGuide 3.0` internal-header integration.
- Add readiness checks for MySQL, Redis, lease, vector, embedding, and LLM config.
- Keep the independent frontend as validation UI, not the final integrated entry.

## Deferred

- Final rentHouseH5/lease gateway integration.
- Full operator console production UI.
- Business procedure expansion beyond repository contract wiring.
- Production readiness claims without live dependency verification.
