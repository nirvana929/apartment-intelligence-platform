---
name: project-harness
description: Use when the user wants to initialize a default project, switch project context, save work progress, checkpoint engineering state, resume a project in a new context window, or inspect the current default project.
---

# Project Harness

## Purpose

Maintain project engineering state outside the chat context so future sessions can resume quickly.

Use this skill for four manual actions:

```text
project-harness init [project path]
project-harness checkpoint [optional project path]
project-harness resume [optional project path]
project-harness status
```

If the user gives a project path, switch the default project to that path before running the action. If no path is given, use the saved default project.

## Global State

Default project state lives at:

```text
~/.codex/project-harness/default-project.json
~/.codex/project-harness/recent-projects.json
```

Use the local `scripts/project_harness.py` for deterministic operations.

Codex path:

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py init --project "/path/to/project"
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py status
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Claude path:

```bash
python3 /home/chove/.claude/skills/project-harness/scripts/project_harness.py init --project "/path/to/project"
python3 /home/chove/.claude/skills/project-harness/scripts/project_harness.py status
python3 /home/chove/.claude/skills/project-harness/scripts/project_harness.py snapshot
```

## Project State Files

Initialize missing files only; do not overwrite existing project state.

```text
<project>/
├── project/
│   ├── feature-list.json
│   └── sprint-plan.json
├── progress/
│   ├── current-plan.md
│   ├── completed.md
│   ├── known-issues.md
│   └── next-steps.md
├── reports/
│   └── evaluation-report.md
└── traces/
```

## Action: init

Use when the user wants to initialize or switch the default project.

Steps:

1. Resolve the project path from the user message. If missing, use the current working directory only if the user clearly implies "this project"; otherwise ask for a path.
2. Run:

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py init --project "<project path>"
```

3. Report the default project path and initialized/missing-created files.

## Action: status

Use when the user asks what the current default project is.

Run:

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py status
```

Report the default project and recent projects.

## Action: checkpoint

Use when a work segment is ending and the user wants to preserve state.

Steps:

1. If the user gave a project path, run `init --project "<path>"` first to switch default and initialize missing files.
2. Run:

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

3. Read the snapshot output and inspect changed files as needed.
4. Update these project files with factual status:
   - `progress/current-plan.md`
   - `progress/completed.md`
   - `progress/known-issues.md`
   - `progress/next-steps.md`
   - `reports/evaluation-report.md`
   - `project/feature-list.json` only if feature status is clear
   - `project/sprint-plan.json` only if sprint contract changed
5. Preserve validation integrity:
   - Never set `passes=true` without test/eval evidence.
   - If tests were not run, write `test_status: "not_run"` or state "not run".
   - Record failed or skipped verification explicitly.
6. Final response must include:

```text
Checkpoint Summary
- Project:
- Current goal:
- Completed this session:
- Files changed:
- Verification:
- Known issues:
- Next steps:
```

## Action: resume

Use when starting a new context window or taking over a project.

Steps:

1. If the user gave a project path, run `init --project "<path>"` first to switch default and initialize missing files.
2. Run:

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

3. Read the listed state files. For large docs, read only the relevant sections.
4. Prefer project-specific onboarding docs in this order when present:
   - `AGENTS.md`
   - `README.md`
   - `docs/README.md`
   - `docs/00-start-here.md`
   - `docs/system/harness-method-selection.md`
   - `docs/system/enterprise-harness-architecture.md`
5. Output a concise resume brief:

```text
Resume Brief
- Project:
- Current phase:
- Current sprint/feature:
- Completed:
- In progress:
- Known issues:
- Latest verification:
- Git state:
- Recommended next step:
- Do not touch / constraints:
```

Do not modify project files during `resume` unless the user explicitly asks.

## Project-Specific Adaptation

For AptGuide 2.0, prioritize:

```text
docs/00-start-here.md
docs/system/harness-method-selection.md
docs/system/enterprise-harness-architecture.md
docs/plans/2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md
```

Core AptGuide rule: keep `aptguide2.rag` intact; default `/chat` behavior remains MVP unless `APTGUIDE_PIPELINE_VERSION=harness_v1`.

## Common Mistakes

- Do not rely on chat history as project state.
- Do not overwrite existing progress files during init.
- Do not mark features complete without evidence.
- Do not hide failed, skipped, or unrun tests.
- Do not run destructive git commands.
