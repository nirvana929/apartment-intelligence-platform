#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DIR = Path.home() / ".codex" / "project-harness"
DEFAULT_PROJECT = STATE_DIR / "default-project.json"
RECENT_PROJECTS = STATE_DIR / "recent-projects.json"


PROJECT_FILES: dict[str, Any] = {
    "project/feature-list.json": [],
    "project/sprint-plan.json": {
        "sprints": []
    },
    "progress/current-plan.md": "# Current Plan\n\nNo current plan recorded yet.\n",
    "progress/completed.md": "# Completed\n\nNo completed work recorded yet.\n",
    "progress/known-issues.md": "# Known Issues\n\nNo known issues recorded yet.\n",
    "progress/next-steps.md": "# Next Steps\n\nNo next steps recorded yet.\n",
    "reports/evaluation-report.md": "# Evaluation Report\n\nNo evaluation has been recorded yet.\n",
}

PROJECT_DIRS = ["project", "progress", "reports", "traces"]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


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


def resolve_project(path: str | None) -> Path:
    if path:
        project = Path(path).expanduser().resolve()
    else:
        state = read_json(DEFAULT_PROJECT, {})
        saved = state.get("default_project_path")
        if not saved:
            raise SystemExit("No default project set. Run: project_harness.py init --project <path>")
        project = Path(saved).expanduser().resolve()
    if not project.exists() or not project.is_dir():
        raise SystemExit(f"Project path does not exist or is not a directory: {project}")
    return project


def update_recent(project: Path) -> None:
    recent = read_json(RECENT_PROJECTS, [])
    recent = [item for item in recent if item.get("path") != str(project)]
    recent.insert(0, {"path": str(project), "last_used_at": now_iso()})
    write_json(RECENT_PROJECTS, recent[:10])


def init_project(path: str) -> dict[str, Any]:
    project = resolve_project(path)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(DEFAULT_PROJECT, {"default_project_path": str(project), "updated_at": now_iso()})
    update_recent(project)

    created: list[str] = []
    existing: list[str] = []
    for dirname in PROJECT_DIRS:
        directory = project / dirname
        if directory.exists():
            existing.append(dirname + "/")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            created.append(dirname + "/")

    for rel, content in PROJECT_FILES.items():
        target = project / rel
        if target.exists():
            existing.append(rel)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            write_json(target, content)
        created.append(rel)

    return {"project": str(project), "created": created, "existing": existing}


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
    return (project / ".git").exists() or git(["rev-parse", "--show-toplevel"], project)


def file_head(path: Path, max_chars: int = 1600) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:max_chars]


def snapshot(path: str | None = None) -> dict[str, Any]:
    project = resolve_project(path)
    update_recent(project)

    state_files = [
        "AGENTS.md",
        "README.md",
        "docs/README.md",
        "docs/00-start-here.md",
        "docs/system/harness-method-selection.md",
        "docs/system/enterprise-harness-architecture.md",
        "project/feature-list.json",
        "project/sprint-plan.json",
        "progress/current-plan.md",
        "progress/completed.md",
        "progress/known-issues.md",
        "progress/next-steps.md",
        "reports/evaluation-report.md",
    ]
    present = [rel for rel in state_files if (project / rel).exists()]
    missing = [rel for rel in state_files if not (project / rel).exists()]

    git_status = git(["status", "--short"], project) if has_git(project) else "not a git repository"
    branch = git(["branch", "--show-current"], project) if has_git(project) else ""

    return {
        "project": str(project),
        "branch": branch,
        "git_status_short": git_status,
        "present_state_files": present,
        "missing_state_files": missing,
        "current_plan_preview": file_head(project / "progress/current-plan.md"),
        "known_issues_preview": file_head(project / "progress/known-issues.md"),
        "next_steps_preview": file_head(project / "progress/next-steps.md"),
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

    sub.add_parser("status")

    args = parser.parse_args()
    if args.command == "init":
        payload = init_project(args.project)
    elif args.command == "snapshot":
        payload = snapshot(args.project)
    else:
        payload = status()

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
