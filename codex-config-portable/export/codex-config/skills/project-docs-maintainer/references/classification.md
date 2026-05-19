# Documentation Classification

Choose one primary type.

## System

Use `system/` for stable explanatory docs:

- Architecture overview.
- Module design.
- API contracts.
- Database schema and metrics.
- Agent graph and prompt design.
- Security boundaries.
- Deployment topology.

## Plans

Use `plans/` for executable work docs:

- Implementation plans.
- Agent task breakdowns.
- Migration plans.
- Integration plans.
- Step-by-step acceptance criteria.
- Risk and rollback instructions.

Plans should be precise enough for an agent to execute.

## Tests

Use `tests/` for verification docs:

- Test strategy.
- Test run records.
- Eval harness reports.
- Coverage summaries.
- Failure analysis.
- Regression baselines.
- Generated report indexes.

Generated reports can remain in their original tool output directory.

## Outcomes

Use `outcomes/` for portfolio and reflection docs:

- Interview summaries.
- Resume bullets.
- Problem-solution-result writeups.
- Lessons learned.
- Pitfall and debugging stories.
- Quantified achievements.

Outcomes should explain why the work matters, not just what files changed.
