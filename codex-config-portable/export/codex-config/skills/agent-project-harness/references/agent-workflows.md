# Agent Workflows

## Planning Agent

The planning agent writes executable plans and absorbs execution feedback.

Use **Generate Next Plan** when the user asks to create, revise, or regenerate the next plan.
Use **Answer Clarification** before unrelated planning when open clarifications exist.

Input files:

- `docs/plans/execution-log.md`
- `docs/plans/checkpoints/`
- `docs/plans/known-issues.md`
- `docs/plans/next-steps.md`
- `docs/plans/clarifications/`
- `docs/tests/verification-log.md`
- `.agent-state/last-checkpoint.json`
- `.agent-state/clarifications/open.json`

Output files:

- `docs/plans/current-plan.md`
- `docs/plans/sprint-plan.md`
- `docs/plans/handoff.md`
- `.agent-state/handoff.json`

Required plan contents:

- Goal.
- Context.
- Files likely involved.
- Step-by-step implementation.
- Parallel execution guidance.
- Serial dependencies.
- Acceptance criteria.
- Verification commands.
- Risks and rollback.

Generate Next Plan steps:

1. Read recent checkpoints and execution logs.
2. Check open clarifications.
3. Answer blocking clarifications before planning unrelated work.
4. Compare completed work against the previous plan.
5. Pick the next smallest executable task.
6. Identify safe parallel workstreams and serial dependencies.
7. Write `docs/plans/current-plan.md`.
8. Write `docs/plans/handoff.md`.
9. Update `.agent-state/handoff.json`.
10. Stop before implementation unless the user explicitly asks to execute.

## Execution Agent

The execution agent reads the plan, performs the task, verifies it, and checkpoints the result.

Use **Execute Next Plan** when the user asks to execute the current plan, continue a handoff, or start implementation.
Use **Raise Clarification** when execution finds a blocking ambiguity, contradiction, unsafe step, or plan/code mismatch.

Input files:

- `docs/plans/current-plan.md`
- `docs/plans/handoff.md`
- `docs/plans/known-issues.md`
- `docs/plans/clarifications/`
- `.agent-state/clarifications/open.json`

Output files:

- `docs/plans/execution-log.md`
- `docs/plans/checkpoints/YYYY-MM-DD-HHMMSS-task-name.md`
- `docs/plans/known-issues.md`
- `docs/plans/next-steps.md`
- `docs/plans/clarifications/YYYY-MM-DD-HHMMSS-task-question.md`
- `docs/tests/verification-log.md`
- `.agent-state/last-checkpoint.json`

Execute Next Plan steps:

1. Read `current-plan.md`, `handoff.md`, known issues, verification history, and `.agent-state/handoff.json`.
2. Confirm the plan is executable. Raise clarification if a missing decision blocks execution.
3. Follow the plan's parallel execution guidance. Run explicitly parallel workstreams in parallel when supported; keep serial tasks in order; if guidance is missing or unclear, execute conservatively.
4. Implement the planned task.
5. Record any errors, failed commands, root causes, attempted fixes, and unresolved issues.
6. Run verification.
7. Create a permanent checkpoint under `docs/plans/checkpoints/`.
8. Update execution log, verification log, known issues, next steps, and `.agent-state/last-checkpoint.json`.
9. Finish with a checkpoint summary.

## Clarification Loop

Clarifications are durable records for handoff mismatches and planning gaps.

Raise Clarification:

1. Create `docs/plans/clarifications/YYYY-MM-DD-HHMMSS-task-question.md`.
2. Record original plan reference, observed mismatch, evidence, question, options, and execution-agent recommendation.
3. Add the item to `.agent-state/clarifications/open.json`.
4. Stop if blocking; continue only unaffected work if non-blocking.

Answer Clarification:

1. Planning agent reads open clarification state and the Markdown record.
2. Planning agent inspects relevant code, plan, handoff, and checkpoints.
3. Planning agent writes a concrete answer under `Planning Agent Response`.
4. Planning agent updates current plan, handoff, known issues, or next steps when needed.
5. If user judgment is required, record the user's decision in the clarification.

Resolve Clarification:

1. Execution agent reads answered clarification and updated handoff.
2. Execution agent continues the plan using that answer.
3. Execution agent marks the clarification resolved after the issue is handled.
4. Execution agent references the clarification in the checkpoint.

## Handoff Contract

A handoff must answer:

- What is the current goal?
- What should the execution agent do next?
- What files or modules are in scope?
- Which workstreams can run in parallel?
- Which dependencies require serial execution?
- What must not be touched?
- What commands prove success?
- What risks or known failures exist?

## Validation Integrity

- Do not mark tests passing without evidence.
- If tests were not run, write `not_run`.
- If verification was skipped, explain why.
- Preserve failed command output summaries in `docs/tests/verification-log.md`.
