---
name: sync-agent-skills
description: Use when the user wants to synchronize local agent skills between Claude/Claude Code and Codex, compare skill directories, copy missing skills, resolve skill conflicts, or keep ~/.claude/skills and ~/.codex/skills consistent.
---

# Sync Agent Skills

Synchronize local skills between Codex and Claude/Claude Code skill directories.

## Default Locations

- Codex global skills: `~/.codex/skills`
- Claude global skills: `~/.claude/skills`

Project-level Claude skills may also exist at `<repo>/.claude/skills`; only use them when the user explicitly asks for project-level sync.

## Workflow

1. Identify source and target:
   - `--direction both`: copy missing skills both ways.
   - `--direction codex-to-claude`: copy Codex skills to Claude.
   - `--direction claude-to-codex`: copy Claude skills to Codex.
2. Always run a dry-run first.
3. Do not sync Codex system skills by default. Skip `.system`.
4. Treat same-named but different skill directories as conflicts.
5. Do not overwrite conflicts unless the user explicitly chooses `--prefer codex` or `--prefer claude`.
6. After syncing, tell the user that new agent sessions may be needed before the other tool sees newly copied skills.

## Script

Use the bundled script:

```bash
python3 ~/.codex/skills/sync-agent-skills/scripts/sync_skills.py --dry-run
```

Common commands:

```bash
# Preview two-way sync
python3 ~/.codex/skills/sync-agent-skills/scripts/sync_skills.py --direction both --dry-run

# Copy missing skills both ways
python3 ~/.codex/skills/sync-agent-skills/scripts/sync_skills.py --direction both

# Copy only Codex skills into Claude
python3 ~/.codex/skills/sync-agent-skills/scripts/sync_skills.py --direction codex-to-claude

# Resolve conflicts by preferring Codex copies
python3 ~/.codex/skills/sync-agent-skills/scripts/sync_skills.py --direction both --prefer codex
```

## Safety Rules

- Never delete skills during sync.
- Back up overwritten skill directories under `~/.skill-sync-backups/`.
- Skip hidden/system directories unless the user explicitly asks otherwise.
- Preserve symlinks as symlinks.
- Report copied, skipped, identical, and conflicted skills separately.
