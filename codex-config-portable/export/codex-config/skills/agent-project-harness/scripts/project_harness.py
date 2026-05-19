#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DIR = Path.home() / ".codex" / "agent-project-harness"
DEFAULT_PROJECT = STATE_DIR / "default-project.json"
RECENT_PROJECTS = STATE_DIR / "recent-projects.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def now_stamp() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d-%H%M%S")


def slugify_task(task: str) -> str:
    value = task.strip().lower().replace("/", "-").replace("\\", "-")
    value = re.sub(r"\s+", "-", value)
    value = "".join(char for char in value if char.isalnum() or char in "-_")
    value = re.sub(r"-+", "-", value).strip("-_")
    return value[:80] or "checkpoint"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text_if_missing(path: Path, text: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def resolve_project(path: str | None) -> Path:
    if path:
        project = Path(path).expanduser().resolve()
    else:
        saved = read_json(DEFAULT_PROJECT, {}).get("default_project_path")
        if not saved:
            raise SystemExit("No default project set. Run init --project <path> first.")
        project = Path(saved).expanduser().resolve()
    if not project.exists() or not project.is_dir():
        raise SystemExit(f"Project path does not exist or is not a directory: {project}")
    return project


def update_recent(project: Path) -> None:
    recent = read_json(RECENT_PROJECTS, [])
    recent = [item for item in recent if item.get("path") != str(project)]
    recent.insert(0, {"path": str(project), "last_used_at": now_iso()})
    write_json(RECENT_PROJECTS, recent[:10])


def project_text_files() -> dict[str, str]:
    return {
        "docs/README.md": """# Project Documentation

## Reading Order

1. [System](system/README.md)
2. [Plans](plans/README.md)
3. [Tests](tests/README.md)
4. [Outcomes](outcomes/README.md)

## Current State

- Current plan: [plans/current-plan.md](plans/current-plan.md)
- Handoff: [plans/handoff.md](plans/handoff.md)
- Verification: [tests/verification-log.md](tests/verification-log.md)
- Checkpoints: [plans/checkpoints/](plans/checkpoints/)
- Clarifications: [plans/clarifications/](plans/clarifications/)
""",
        "docs/system/README.md": """# System Docs

| Document | Purpose | Status |
| --- | --- | --- |
| [agent-workflow.md](agent-workflow.md) | Planning/execution agent workflow | active |
| [feature-list.md](feature-list.md) | Feature inventory and status | draft |
""",
        "docs/system/agent-workflow.md": """# Agent Workflow

## Roles

- Planning agent: reads execution results and writes executable plans.
- Execution agent: reads the handoff, implements work, verifies results, and checkpoints status.

## Handoff Files

- `docs/plans/current-plan.md`
- `docs/plans/handoff.md`
- `docs/plans/execution-log.md`
- `docs/plans/clarifications/`
- `docs/tests/verification-log.md`
- `.agent-state/handoff.json`
- `.agent-state/last-checkpoint.json`
""",
        "docs/system/feature-list.md": """# Feature List

| Feature | Status | Notes |
| --- | --- | --- |
| _No features recorded yet._ | draft | Add features as work becomes clear. |
""",
        "docs/plans/README.md": """# Plans

| Document | Purpose | Status |
| --- | --- | --- |
| [current-plan.md](current-plan.md) | Current executable plan | active |
| [sprint-plan.md](sprint-plan.md) | Sprint or phase scope | draft |
| [handoff.md](handoff.md) | Next execution-agent task brief | active |
| [execution-log.md](execution-log.md) | Completed work history | active |
| [known-issues.md](known-issues.md) | Open blockers, risks, and defects | active |
| [next-steps.md](next-steps.md) | Recommended follow-up work | active |
| [checkpoints/](checkpoints/) | Permanent per-task checkpoint archive | active |
| [clarifications/](clarifications/) | Plan/execution alignment questions | active |
""",
        "docs/plans/current-plan.md": """# Current Plan

## Goal

No current goal recorded yet.

## Context

No context recorded yet.

## Steps

1. Define the next executable task.

## Acceptance Criteria

- The task has clear completion evidence.

## Verification

- `not_run`
""",
        "docs/plans/sprint-plan.md": """# Sprint Plan

## Scope

No sprint scope recorded yet.

## Commitments

- No commitments recorded yet.
""",
        "docs/plans/handoff.md": """# Handoff

## For Execution Agent

No handoff recorded yet.

## Source Of Truth

- `docs/plans/current-plan.md`
- `docs/plans/known-issues.md`
- `docs/tests/verification-log.md`
""",
        "docs/plans/execution-log.md": """# Execution Log

No completed work recorded yet.
""",
        "docs/plans/known-issues.md": """# Known Issues

No known issues recorded yet.
""",
        "docs/plans/next-steps.md": """# Next Steps

No next steps recorded yet.
""",
        "docs/plans/checkpoints/README.md": """# Checkpoints

Each checkpoint is a permanent task record named with time and task:

```text
YYYY-MM-DD-HHMMSS-task-name.md
```

Use these records to reconstruct project history, debug recurring problems, and write outcomes.
""",
        "docs/plans/clarifications/README.md": """# Clarifications

Each clarification records a plan/execution mismatch, open question, or blocking decision.

```text
YYYY-MM-DD-HHMMSS-task-question.md
```

Use these records to align planning-agent intent with execution-agent reality.
""",
        "docs/tests/README.md": """# Tests

| Document | Purpose | Status |
| --- | --- | --- |
| [verification-log.md](verification-log.md) | Test and verification command history | active |
| [evaluation-report.md](evaluation-report.md) | Evaluation summaries | draft |
| [failure-analysis.md](failure-analysis.md) | Failure and regression analysis | draft |
""",
        "docs/tests/verification-log.md": """# Verification Log

No verification has been recorded yet.
""",
        "docs/tests/evaluation-report.md": """# Evaluation Report

No evaluation has been recorded yet.
""",
        "docs/tests/failure-analysis.md": """# Failure Analysis

No failures have been analyzed yet.
""",
        "docs/outcomes/README.md": """# Outcomes

| Document | Purpose | Status |
| --- | --- | --- |
| [achievements.md](achievements.md) | Project achievements and metrics | draft |
| [lessons-learned.md](lessons-learned.md) | Lessons, pitfalls, and durable knowledge | draft |
""",
        "docs/outcomes/achievements.md": """# Achievements

No achievements recorded yet.
""",
        "docs/outcomes/lessons-learned.md": """# Lessons Learned

No lessons recorded yet.
""",
    }


def project_json_files(project: Path) -> dict[str, Any]:
    return {
        ".agent-state/project.json": {
            "project_path": str(project),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "docs_model": "docs-first",
        },
        ".agent-state/handoff.json": {
            "status": "empty",
            "role": "execution_agent",
            "task": None,
            "source_docs": [
                "docs/plans/current-plan.md",
                "docs/plans/handoff.md",
            ],
            "updated_at": now_iso(),
        },
        ".agent-state/feature-list.json": [],
        ".agent-state/sprint-plan.json": {"sprints": []},
        ".agent-state/last-checkpoint.json": {
            "status": "empty",
            "test_status": "not_run",
            "updated_at": now_iso(),
        },
        ".agent-state/clarifications/open.json": [],
    }


def init_project(path: str) -> dict[str, Any]:
    project = resolve_project(path)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(DEFAULT_PROJECT, {"default_project_path": str(project), "updated_at": now_iso()})
    update_recent(project)

    created: list[str] = []
    existing: list[str] = []
    for dirname in [
        "docs",
        "docs/system",
        "docs/plans",
        "docs/plans/checkpoints",
        "docs/plans/clarifications",
        "docs/plans/archive",
        "docs/tests",
        "docs/outcomes",
        ".agent-state",
        ".agent-state/checkpoints",
        ".agent-state/clarifications",
    ]:
        target = project / dirname
        if target.exists():
            existing.append(dirname + "/")
        else:
            target.mkdir(parents=True, exist_ok=True)
            created.append(dirname + "/")

    for rel, text in project_text_files().items():
        if write_text_if_missing(project / rel, text):
            created.append(rel)
        else:
            existing.append(rel)

    for rel, data in project_json_files(project).items():
        target = project / rel
        if target.exists():
            existing.append(rel)
        else:
            write_json(target, data)
            created.append(rel)

    return {"project": str(project), "created": created, "existing": existing}


def clarification_template(task: str, question: str, created_at: str, blocking_level: str) -> str:
    return f"""# Clarification: {question}

## Metadata

- Created at: {created_at}
- Task: {task}
- Status: open
- Blocking level: {blocking_level}
- Raised by: execution-agent
- Assigned to: planning-agent

## Original Plan Reference

Quote or link the relevant part of `docs/plans/current-plan.md` or `docs/plans/handoff.md`.

## Observed Mismatch

Describe what the execution agent found that does not match the plan or is unclear.

## Evidence

List code paths, command output summaries, errors, or repository facts.

## Question

{question}

## Options Considered

- 

## Execution Agent Recommendation

State the safest recommended path if one is clear.

## Planning Agent Response

Pending.

## Updated Plan Impact

- `docs/plans/current-plan.md`:
- `docs/plans/handoff.md`:
- `docs/plans/known-issues.md`:
- `docs/plans/next-steps.md`:
- `docs/tests/verification-log.md`:

## Resolution

Pending.
"""


def append_open_clarification(project: Path, payload: dict[str, Any]) -> None:
    open_path = project / ".agent-state/clarifications/open.json"
    open_items = read_json(open_path, [])
    if not isinstance(open_items, list):
        open_items = []
    open_items.append(payload)
    write_json(open_path, open_items)


def create_clarification(
    path: str | None,
    task: str,
    question: str,
    blocking_level: str,
) -> dict[str, Any]:
    project = resolve_project(path)
    update_recent(project)

    created_at = now_iso()
    stem = f"{now_stamp()}-{slugify_task(task)}-{slugify_task(question)}"
    md_rel = f"docs/plans/clarifications/{stem}.md"
    json_rel = f".agent-state/clarifications/{stem}.json"
    md_path = project / md_rel
    json_path = project / json_rel
    suffix = 2
    while md_path.exists() or json_path.exists():
        next_stem = f"{stem}-{suffix}"
        md_rel = f"docs/plans/clarifications/{next_stem}.md"
        json_rel = f".agent-state/clarifications/{next_stem}.json"
        md_path = project / md_rel
        json_path = project / json_rel
        suffix += 1

    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        clarification_template(task, question, created_at, blocking_level),
        encoding="utf-8",
    )

    payload = {
        "status": "open",
        "task": task,
        "question": question,
        "blocking_level": blocking_level,
        "clarification_doc": md_rel,
        "created_at": created_at,
        "updated_at": created_at,
        "raised_by": "execution-agent",
        "assigned_to": "planning-agent",
    }
    write_json(json_path, payload)
    append_open_clarification(project, payload | {"clarification_state": json_rel})

    return {
        "project": str(project),
        "task": task,
        "question": question,
        "blocking_level": blocking_level,
        "clarification_doc": md_rel,
        "clarification_state": json_rel,
        "created_at": created_at,
    }


def checkpoint_template(task: str, created_at: str) -> str:
    return f"""# Checkpoint: {task}

## Metadata

- Created at: {created_at}
- Task: {task}
- Status: draft
- Test status: not_run

## Goal

Describe the goal for this work segment.

## Context

Record the relevant plan, handoff, issue, or code context.

## Completed Work

- 

## Files Changed

- 

## Errors And Failures

Record every meaningful error, failed command, exception, broken assumption, and dead end.

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| _No errors recorded yet._ |  |  |  |  |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `not_run` | not_run | Verification has not been run yet. |

## Known Issues

- 

## Next Steps

- 

## Outcome Notes

Capture achievement, metric, lesson, or interview material that should later move into `docs/outcomes/`.
"""


def append_execution_log(project: Path, rel_path: str, task: str, created_at: str) -> None:
    log_path = project / "docs/plans/execution-log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text("# Execution Log\n", encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## {created_at} - {task}\n\n"
            f"- Checkpoint: [{rel_path}]({rel_path})\n"
            "- Status: draft\n"
            "- Verification: not_run\n"
        )


def create_checkpoint(path: str | None, task: str) -> dict[str, Any]:
    project = resolve_project(path)
    update_recent(project)

    created_at = now_iso()
    stem = f"{now_stamp()}-{slugify_task(task)}"
    md_rel = f"docs/plans/checkpoints/{stem}.md"
    json_rel = f".agent-state/checkpoints/{stem}.json"
    md_path = project / md_rel
    json_path = project / json_rel
    suffix = 2
    while md_path.exists() or json_path.exists():
        next_stem = f"{stem}-{suffix}"
        md_rel = f"docs/plans/checkpoints/{next_stem}.md"
        json_rel = f".agent-state/checkpoints/{next_stem}.json"
        md_path = project / md_rel
        json_path = project / json_rel
        suffix += 1

    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(checkpoint_template(task, created_at), encoding="utf-8")

    payload = {
        "status": "draft",
        "task": task,
        "checkpoint_doc": md_rel,
        "test_status": "not_run",
        "created_at": created_at,
        "updated_at": created_at,
        "errors_recorded": [],
        "verification": [],
        "next_steps": [],
    }
    write_json(json_path, payload)
    write_json(project / ".agent-state/last-checkpoint.json", payload | {"checkpoint_state": json_rel})
    append_execution_log(project, md_rel, task, created_at)

    return {
        "project": str(project),
        "task": task,
        "checkpoint_doc": md_rel,
        "checkpoint_state": json_rel,
        "created_at": created_at,
    }


def git(args: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except FileNotFoundError:
        return "git not found"
    return result.stdout.strip()


def has_git(project: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(project),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def file_head(path: Path, max_chars: int = 1800) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:max_chars]


def snapshot(path: str | None = None) -> dict[str, Any]:
    project = resolve_project(path)
    update_recent(project)

    state_files = [
        "AGENTS.md",
        "README.md",
        "docs/README.md",
        "docs/system/agent-workflow.md",
        "docs/system/feature-list.md",
        "docs/plans/current-plan.md",
        "docs/plans/sprint-plan.md",
        "docs/plans/handoff.md",
        "docs/plans/execution-log.md",
        "docs/plans/known-issues.md",
        "docs/plans/next-steps.md",
        "docs/plans/checkpoints/README.md",
        "docs/plans/clarifications/README.md",
        "docs/tests/verification-log.md",
        "docs/tests/evaluation-report.md",
        "docs/tests/failure-analysis.md",
        "docs/outcomes/achievements.md",
        "docs/outcomes/lessons-learned.md",
        ".agent-state/project.json",
        ".agent-state/handoff.json",
        ".agent-state/last-checkpoint.json",
        ".agent-state/clarifications/open.json",
    ]
    present = [rel for rel in state_files if (project / rel).exists()]
    missing = [rel for rel in state_files if not (project / rel).exists()]
    git_available = has_git(project)

    return {
        "project": str(project),
        "branch": git(["branch", "--show-current"], project) if git_available else "",
        "git_status_short": git(["status", "--short"], project) if git_available else "not a git repository",
        "present_state_files": present,
        "missing_state_files": missing,
        "current_plan_preview": file_head(project / "docs/plans/current-plan.md"),
        "handoff_preview": file_head(project / "docs/plans/handoff.md"),
        "known_issues_preview": file_head(project / "docs/plans/known-issues.md"),
        "next_steps_preview": file_head(project / "docs/plans/next-steps.md"),
        "verification_preview": file_head(project / "docs/tests/verification-log.md"),
        "last_checkpoint": read_json(project / ".agent-state/last-checkpoint.json", None),
        "open_clarifications": read_json(project / ".agent-state/clarifications/open.json", []),
    }


def status() -> dict[str, Any]:
    return {
        "default_project": read_json(DEFAULT_PROJECT, None),
        "recent_projects": read_json(RECENT_PROJECTS, []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init")
    init_parser.add_argument("--project", required=True)

    snapshot_parser = sub.add_parser("snapshot")
    snapshot_parser.add_argument("--project")

    checkpoint_parser = sub.add_parser("checkpoint")
    checkpoint_parser.add_argument("--project")
    checkpoint_parser.add_argument("--task", default="checkpoint")

    clarification_parser = sub.add_parser("clarification")
    clarification_parser.add_argument("--project")
    clarification_parser.add_argument("--task", default="clarification")
    clarification_parser.add_argument("--question", required=True)
    clarification_parser.add_argument(
        "--blocking-level",
        choices=("blocking", "non-blocking"),
        default="blocking",
    )

    sub.add_parser("status")

    args = parser.parse_args()
    if args.command == "init":
        payload = init_project(args.project)
    elif args.command == "snapshot":
        payload = snapshot(args.project)
    elif args.command == "checkpoint":
        payload = create_checkpoint(args.project, args.task)
    elif args.command == "clarification":
        payload = create_clarification(
            args.project,
            args.task,
            args.question,
            args.blocking_level,
        )
    else:
        payload = status()

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
