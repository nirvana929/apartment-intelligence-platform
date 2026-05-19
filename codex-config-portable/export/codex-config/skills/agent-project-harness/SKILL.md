---
name: agent-project-harness
description: Initialize, resume, plan, execute, clarify, checkpoint, and update documentation for agent-driven software projects. Use when starting a new project scaffold, switching project context, generating the next plan, executing the current or next plan, raising or answering plan clarifications, preserving task progress, handing work between a planning agent and execution agent, restoring context in a new window, or syncing docs after code changes.
---

# Agent Project Harness

## Required Notice

When this skill triggers, first tell the user:

```text
我正在使用 agent-project-harness skill 来维护项目脚手架、计划、进度、测试记录和 agent 交接状态。
```

Keep the notice short, then continue.

## Purpose

Maintain a recoverable project memory system for agent-driven development.

This skill combines three concerns:

- Project scaffold: initialize a new project with predictable docs and state files.
- Project memory: resume and checkpoint work across chat windows.
- Agent loop: generate the next plan, execute the current plan, verify, checkpoint, and feed results back into the next plan.
- Clarification loop: let execution agents stop on plan mismatches, raise questions, receive planning-agent answers, and continue safely.
- Docs impact: update project docs after planning, execution, testing, or code changes.

## Storage Model

Use `docs/` as the long-term human-readable and agent-readable project memory.
Use `.agent-state/` only for machine-readable state that benefits from stable JSON.

```text
<project>/
├── docs/
│   ├── README.md
│   ├── system/
│   │   ├── README.md
│   │   ├── agent-workflow.md
│   │   └── feature-list.md
│   ├── plans/
│   │   ├── README.md
│   │   ├── current-plan.md
│   │   ├── sprint-plan.md
│   │   ├── handoff.md
│   │   ├── execution-log.md
│   │   ├── known-issues.md
│   │   ├── next-steps.md
│   │   ├── checkpoints/
│   │   ├── clarifications/
│   │   └── archive/
│   ├── tests/
│   │   ├── README.md
│   │   ├── verification-log.md
│   │   ├── evaluation-report.md
│   │   └── failure-analysis.md
│   └── outcomes/
│       ├── README.md
│       ├── achievements.md
│       └── lessons-learned.md
└── .agent-state/
    ├── project.json
    ├── handoff.json
    ├── feature-list.json
    ├── sprint-plan.json
    ├── last-checkpoint.json
    ├── checkpoints/
    └── clarifications/
```

Do not create legacy `progress/`, `reports/`, or `project/` folders for new scaffolds. If they already exist, leave them in place and link from `docs/` only when useful.

## Core Commands

Use the bundled script for deterministic scaffold and snapshot operations:

```bash
python3 /home/chove/.codex/skills/agent-project-harness/scripts/project_harness.py init --project "<project path>"
python3 /home/chove/.codex/skills/agent-project-harness/scripts/project_harness.py status
python3 /home/chove/.codex/skills/agent-project-harness/scripts/project_harness.py snapshot --project "<project path>"
python3 /home/chove/.codex/skills/agent-project-harness/scripts/project_harness.py checkpoint --project "<project path>" --task "<task name>"
python3 /home/chove/.codex/skills/agent-project-harness/scripts/project_harness.py clarification --project "<project path>" --task "<task name>" --question "<question>"
```

If no project path is given for `snapshot`, the script uses the saved default project.

## Workflow Decision Tree

- User wants to start or scaffold a project: run **Init**.
- User opens a new window or asks to continue: run **Resume**.
- User asks to generate the next plan, revise the plan, or prepare work for an execution agent: run **Generate Next Plan**.
- User asks to execute the next plan, execute the current plan, continue the handoff, or start implementation: run **Execute Next Plan**.
- Execution finds the plan unclear, contradictory, unsafe, or mismatched with code reality: run **Raise Clarification**.
- Planning agent needs to answer execution-agent questions: run **Answer Clarification**.
- Execution agent continues after an answer: run **Resolve Clarification**.
- User finishes a task or asks to save progress: run **Checkpoint**.
- User asks what docs changed or need updating: run **Docs Impact Update**.
- User asks for the current default project: run **Status**.

## Init

Use when starting a new project, switching default project, or creating the harness scaffold.

1. Resolve the project path. If the user clearly means the current workspace, use `pwd`.
2. Run:

   ```bash
   python3 /home/chove/.codex/skills/agent-project-harness/scripts/project_harness.py init --project "<project path>"
   ```

3. Report the default project and created/existing files.
4. Do not overwrite existing project docs.

## Resume

Use when a planning agent or execution agent needs to restore context.

1. Run `snapshot`.
2. Read only the relevant state files listed by the snapshot, prioritizing:
   - `docs/README.md`
   - `docs/plans/current-plan.md`
   - `docs/plans/handoff.md`
   - `docs/plans/known-issues.md`
   - `docs/plans/next-steps.md`
   - open files in `docs/plans/clarifications/`
   - `docs/tests/verification-log.md`
   - `docs/tests/evaluation-report.md`
   - `.agent-state/last-checkpoint.json`
   - `.agent-state/clarifications/open.json`
3. Output:

```text
Resume Brief
- Project:
- Role context: planning agent / execution agent / general
- Current goal:
- Current plan:
- Latest handoff:
- Completed:
- Known issues:
- Open clarifications:
- Latest verification:
- Git state:
- Recommended next step:
- Do not touch / constraints:
```

Do not edit files during `resume` unless the user asks.

## Generate Next Plan

Use when the planning agent needs to produce the next executable plan.

Trigger examples:

- Generate the next plan.
- Regenerate the plan after execution.
- Plan the next development step.
- Prepare a handoff for the execution agent.

Steps:

1. Run `snapshot`.
2. Read execution feedback:
   - `docs/plans/execution-log.md`
   - latest files in `docs/plans/checkpoints/`
   - open files in `docs/plans/clarifications/`
   - `docs/plans/known-issues.md`
   - `docs/plans/next-steps.md`
   - `docs/tests/verification-log.md`
   - `.agent-state/last-checkpoint.json`
   - `.agent-state/clarifications/open.json`
3. Decide the next smallest executable task.
   - If open clarifications exist, answer them before generating unrelated new work.
   - If a clarification requires user judgment, ask the user and record the answer in the clarification file.
4. Update:
   - `docs/plans/current-plan.md`
   - `docs/plans/handoff.md`
   - `docs/plans/sprint-plan.md` when scope changes
   - `.agent-state/handoff.json`
5. Ensure the handoff includes:
   - Goal.
   - Context and source files.
   - Step-by-step implementation.
   - Parallel execution guidance: which workstreams can run at the same time, which must stay serial, and why.
   - Acceptance criteria.
   - Verification commands.
   - Known risks, constraints, and do-not-touch areas.
6. Prefer plans that expose safe parallelism:
   - Split independent work into named workstreams.
   - Assign each workstream a clear scope and file/module boundary.
   - Mark shared-file, dependency, or sequencing constraints as serial.
   - If no safe parallelism exists, state `Serial only` and explain the dependency.
7. Do not implement code during this workflow unless the user explicitly asks to switch into execution.

## Planning Agent Workflow

Use when the agent is producing or revising plans.

1. Resume first.
2. Read execution results from:
   - `docs/plans/execution-log.md`
   - `docs/tests/verification-log.md`
   - `docs/plans/known-issues.md`
   - `docs/plans/next-steps.md`
3. Update:
   - `docs/plans/current-plan.md`
   - `docs/plans/sprint-plan.md` when sprint scope changes
   - `docs/plans/handoff.md` with a concrete execution brief
   - `.agent-state/handoff.json` for machine-readable task handoff
4. Keep plans executable: include files, steps, parallel execution guidance, serial dependencies, acceptance criteria, verification, risks, and rollback notes.

## Execute Next Plan

Use when the execution agent should carry out the current plan or handoff.

Trigger examples:

- Execute the next plan.
- Execute the current plan.
- Continue the handoff.
- Start implementation from `current-plan.md`.
- Let the execution agent do the work.

Steps:

1. Run `snapshot`.
2. Read the execution source of truth:
   - `docs/plans/current-plan.md`
   - `docs/plans/handoff.md`
   - `docs/plans/known-issues.md`
   - `docs/tests/verification-log.md`
   - `.agent-state/handoff.json`
3. Check whether the plan is executable:
   - If required context is missing, run **Raise Clarification**.
   - If the plan is unsafe or contradicts constraints, run **Raise Clarification** and stop.
   - If the plan mismatches code reality, run **Raise Clarification** and attach evidence.
   - If the plan is executable, proceed without asking for another plan.
4. Follow the plan's parallel execution guidance:
   - Run explicitly parallel workstreams in parallel when your execution environment supports it.
   - Keep tasks marked serial in the specified order.
   - If the plan omits parallel guidance, use conservative judgment; when unsure, execute serially.
5. Implement the planned task using the repository's existing patterns.
6. When errors occur, preserve them for the checkpoint:
   - failed command
   - error output summary
   - suspected root cause
   - attempted fixes
   - final decision or unresolved status
7. Run the verification commands from the plan, or the closest appropriate project verification if the plan omits them.
8. Create a permanent checkpoint:

   ```bash
   python3 /home/chove/.codex/skills/agent-project-harness/scripts/project_harness.py checkpoint --project "<project path>" --task "<task name>"
   ```

9. Fill the checkpoint file with actual execution details. Do not leave the generated placeholders as the final record.
10. Update:
   - `docs/plans/execution-log.md`
   - `docs/plans/known-issues.md`
   - `docs/plans/next-steps.md`
   - `docs/tests/verification-log.md`
   - `.agent-state/last-checkpoint.json`
11. Finish with the **Checkpoint Summary** format.

## Raise Clarification

Use when an execution agent cannot safely continue the plan because something is unclear, contradictory, risky, or different from the actual codebase.

Trigger examples:

- Plan step does not match the repository.
- File path, API, dependency, or behavior described by the plan is wrong.
- Acceptance criteria are ambiguous.
- Two plan instructions conflict.
- Executing the plan would require a product or architecture decision.

Steps:

1. Create a permanent clarification record:

   ```bash
   python3 /home/chove/.codex/skills/agent-project-harness/scripts/project_harness.py clarification --project "<project path>" --task "<task name>" --question "<question>"
   ```

2. Fill the clarification file under `docs/plans/clarifications/` with:
   - original plan reference
   - observed mismatch
   - evidence from files, commands, errors, or repository state
   - precise question
   - options considered
   - execution-agent recommendation, if any
3. Update `.agent-state/clarifications/open.json`.
4. If the issue blocks execution, stop and report the clarification path.
5. If the issue is non-blocking, continue only the parts of the plan that do not depend on the answer.
6. If work stops, checkpoint with status `blocked` or `partial`.

## Answer Clarification

Use when the planning agent responds to an open execution-agent clarification.

Steps:

1. Read `.agent-state/clarifications/open.json`.
2. Read the referenced clarification file in `docs/plans/clarifications/`.
3. Inspect the relevant code, plan, handoff, and checkpoint evidence.
4. Write a concrete answer in the clarification file under `Planning Agent Response`.
5. If needed, update:
   - `docs/plans/current-plan.md`
   - `docs/plans/handoff.md`
   - `docs/plans/known-issues.md`
   - `docs/plans/next-steps.md`
   - `.agent-state/handoff.json`
6. Mark the clarification status as `answered` in the Markdown and JSON state.
7. If the answer requires user judgment, ask the user first, then record the user's decision in the clarification.

## Resolve Clarification

Use when the execution agent continues after a planning-agent answer.

Steps:

1. Read answered clarifications before continuing execution.
2. Apply the planning-agent response and updated handoff.
3. Continue **Execute Next Plan**.
4. When the issue is handled, mark the clarification as `resolved`.
5. Record the clarification in the checkpoint so future planning can reconstruct the decision.

## Execution Agent Workflow

Use when the agent executes an existing plan.

1. Resume first.
2. Treat `docs/plans/handoff.md` and `docs/plans/current-plan.md` as the source of truth.
3. Implement the task.
4. Verify with appropriate commands.
5. Checkpoint the result.

## Checkpoint

Use when ending a work segment, completing a task, or handing results back to the planning agent.

1. Run `snapshot`.
2. Create a permanent checkpoint file:
   - Run `checkpoint --task "<task name>"` to create a timestamped file under `docs/plans/checkpoints/`.
   - Name format: `YYYY-MM-DD-HHMMSS-<task>.md`.
   - This file is append-only history. Do not overwrite old checkpoint files.
   - Record errors, failed commands, root causes, attempted fixes, verification evidence, and lessons learned candidates.
3. Update factual current status:
   - `docs/plans/execution-log.md`
   - `docs/plans/current-plan.md`
   - `docs/plans/known-issues.md`
   - `docs/plans/next-steps.md`
   - `docs/tests/verification-log.md`
   - `docs/tests/evaluation-report.md` if an evaluation was performed
   - `.agent-state/last-checkpoint.json`
4. Preserve validation integrity:
   - Never claim tests pass without command output.
   - If tests were not run, write `not_run`.
   - Record failed, skipped, blocked, or partial verification explicitly.
5. Final response must include:

```text
Checkpoint Summary
- Project:
- Current goal:
- Completed this session:
- Files changed:
- Verification:
- Permanent checkpoint:
- Known issues:
- Next steps:
```

Checkpoint persistence rule:

- Permanent history lives in `docs/plans/checkpoints/` and `docs/tests/verification-log.md`.
- Plan/execution alignment history lives in `docs/plans/clarifications/`.
- Current fast-resume state lives in `docs/plans/current-plan.md`, `docs/plans/handoff.md`, `docs/plans/next-steps.md`, `.agent-state/handoff.json`, and `.agent-state/last-checkpoint.json`.
- Use checkpoint history later to write `docs/outcomes/achievements.md` and `docs/outcomes/lessons-learned.md`.

## Docs Impact Update

Use after code changes, feature planning, test runs, or bug fixes.

Classify each documentation update by primary purpose:

- `docs/system/`: architecture, modules, APIs, data model, workflows, decisions.
- `docs/plans/`: implementation plans, task breakdowns, handoffs, status, risks.
- `docs/tests/`: test strategy, test records, eval reports, failure analysis.
- `docs/outcomes/`: achievements, lessons, pitfalls, metrics, interview-ready writeups.

Prefer updating existing docs and indexes before creating new files. Update the nearest `README.md` index when a major doc is created or status changes.

## References

Load only when needed:

- `references/docs-structure.md`: file purposes, index rules, and status labels.
- `references/agent-workflows.md`: planning/execution agent handoff protocol.
- `references/checkpoint-schema.md`: recommended JSON fields for `.agent-state/`.
- `references/clarification-schema.md`: clarification file and state schema.

## Templates

Use templates from `assets/templates/` for new docs:

- `checkpoint-doc.md`
- `clarification-doc.md`
- `system-doc.md`
- `plan-doc.md`
- `test-doc.md`
- `outcome-doc.md`
