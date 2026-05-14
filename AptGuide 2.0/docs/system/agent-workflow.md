# Agent Workflow

## Roles

- Planning agent: reads execution results and writes executable plans.
- Execution agent: reads the handoff, implements work, verifies results, and checkpoints status.

## Handoff Files

- `docs/plans/current-plan.md`
- `docs/plans/handoff.md`
- `docs/plans/execution-log.md`
- `docs/tests/verification-log.md`
- `.agent-state/handoff.json`
- `.agent-state/last-checkpoint.json`
