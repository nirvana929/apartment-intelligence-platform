#!/usr/bin/env python3
"""Synchronize local agent skills between Codex and Claude directories."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_CODEX_DIR = Path.home() / ".codex" / "skills"
DEFAULT_CLAUDE_DIR = Path.home() / ".claude" / "skills"
BACKUP_ROOT = Path.home() / ".skill-sync-backups"
DEFAULT_EXCLUDES = {
    ".system",
    "__pycache__",
    ".git",
    ".DS_Store",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-dir", type=Path, default=DEFAULT_CODEX_DIR)
    parser.add_argument("--claude-dir", type=Path, default=DEFAULT_CLAUDE_DIR)
    parser.add_argument(
        "--direction",
        choices=("both", "codex-to-claude", "claude-to-codex"),
        default="both",
    )
    parser.add_argument(
        "--prefer",
        choices=("none", "codex", "claude"),
        default="none",
        help="Conflict resolution preference. Default refuses overwrites.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden skill directories. .system is still excluded unless --include-system is set.",
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help="Include Codex .system skills. Use only when you know the target supports them.",
    )
    return parser.parse_args()


def is_skill_dir(path: Path, include_hidden: bool, include_system: bool) -> bool:
    if not path.is_dir():
        return False
    name = path.name
    if name == ".system" and not include_system:
        return False
    if name.startswith(".") and not include_hidden and name != ".system":
        return False
    return (path / "SKILL.md").exists() or any(path.iterdir())


def iter_skills(root: Path, include_hidden: bool, include_system: bool) -> dict[str, Path]:
    if not root.exists():
        return {}
    return {
        child.name: child
        for child in sorted(root.iterdir())
        if is_skill_dir(child, include_hidden, include_system)
    }


def should_skip_part(part: str) -> bool:
    return part in DEFAULT_EXCLUDES


def dir_hash(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_symlink():
        digest.update(b"symlink:")
        digest.update(os.readlink(path).encode())
        return digest.hexdigest()

    for item in sorted(path.rglob("*")):
        rel = item.relative_to(path)
        if any(should_skip_part(part) for part in rel.parts):
            continue
        digest.update(str(rel).encode())
        if item.is_symlink():
            digest.update(b"symlink")
            digest.update(os.readlink(item).encode())
        elif item.is_file():
            digest.update(b"file")
            digest.update(item.read_bytes())
        elif item.is_dir():
            digest.update(b"dir")
    return digest.hexdigest()


def backup_existing(path: Path, dry_run: bool) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_ROOT / timestamp / path.name
    if dry_run:
        return backup
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(path, backup, symlinks=True)
    return backup


def copy_skill(src: Path, dst: Path, dry_run: bool) -> None:
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_symlink():
        target = os.readlink(src)
        dst.symlink_to(target)
    else:
        shutil.copytree(src, dst, symlinks=True)


def overwrite_skill(src: Path, dst: Path, dry_run: bool) -> Path:
    backup = backup_existing(dst, dry_run)
    if not dry_run:
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
        copy_skill(src, dst, dry_run=False)
    return backup


def sync_one_way(
    src_name: str,
    src_root: Path,
    dst_name: str,
    dst_root: Path,
    prefer: str,
    dry_run: bool,
    include_hidden: bool,
    include_system: bool,
) -> dict[str, list[str]]:
    report = {"copied": [], "identical": [], "conflicted": [], "overwritten": []}
    src_skills = iter_skills(src_root, include_hidden, include_system)
    dst_skills = iter_skills(dst_root, include_hidden, include_system)

    for name, src in src_skills.items():
        dst = dst_root / name
        if name not in dst_skills:
            copy_skill(src, dst, dry_run)
            report["copied"].append(f"{name}: {src_name} -> {dst_name}")
            continue

        if dir_hash(src) == dir_hash(dst):
            report["identical"].append(name)
            continue

        if prefer == src_name:
            backup = overwrite_skill(src, dst, dry_run)
            report["overwritten"].append(
                f"{name}: preferred {src_name}, backup {backup}"
            )
        else:
            report["conflicted"].append(f"{name}: differs in {src_name} and {dst_name}")

    return report


def merge_reports(base: dict[str, list[str]], extra: dict[str, list[str]]) -> None:
    for key, values in extra.items():
        base.setdefault(key, []).extend(values)


def print_report(report: dict[str, list[str]], dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "APPLIED"
    print(f"Skill sync report ({mode})")
    for key in ("copied", "overwritten", "conflicted", "identical"):
        values = list(dict.fromkeys(report.get(key, [])))
        if key == "conflicted":
            seen_names: set[str] = set()
            unique_values: list[str] = []
            for value in values:
                name = value.split(":", 1)[0]
                if name in seen_names:
                    continue
                seen_names.add(name)
                unique_values.append(value)
            values = unique_values
        print(f"\n{key}: {len(values)}")
        for value in values:
            print(f"  - {value}")

    if report.get("conflicted"):
        print("\nConflicts were not overwritten.")
        print("Resolve with --prefer codex or --prefer claude after reviewing.")


def main() -> int:
    args = parse_args()
    codex_dir = args.codex_dir.expanduser()
    claude_dir = args.claude_dir.expanduser()

    report: dict[str, list[str]] = {
        "copied": [],
        "identical": [],
        "conflicted": [],
        "overwritten": [],
    }

    if args.direction in ("both", "codex-to-claude"):
        merge_reports(
            report,
            sync_one_way(
                "codex",
                codex_dir,
                "claude",
                claude_dir,
                args.prefer,
                args.dry_run,
                args.include_hidden,
                args.include_system,
            ),
        )

    if args.direction in ("both", "claude-to-codex"):
        merge_reports(
            report,
            sync_one_way(
                "claude",
                claude_dir,
                "codex",
                codex_dir,
                args.prefer,
                args.dry_run,
                args.include_hidden,
                args.include_system,
            ),
        )

    print_report(report, args.dry_run)
    if args.dry_run:
        return 0
    return 1 if report.get("conflicted") and args.prefer == "none" else 0


if __name__ == "__main__":
    raise SystemExit(main())
