# Portable Codex config

This archive contains portable Codex configuration only.

It intentionally excludes:

- `auth.json`
- installation IDs
- logs, sessions, shell snapshots, cache, generated images
- SQLite state files

After importing on another machine:

1. Install Codex there.
2. Extract this archive.
3. Run `scripts/import-codex-config.sh`.
4. Run `codex login`.
5. Replace any `__REPLACE_ON_TARGET__` values in `~/.codex/config.toml`.

Review MCP server settings, hooks, skills, and plugins before relying on them.
