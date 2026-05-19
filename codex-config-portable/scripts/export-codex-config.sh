#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="$ROOT/export/codex-config"
ARCHIVE="$ROOT/export/codex-config-portable.tar.gz"

if [[ ! -d "$CODEX_HOME" ]]; then
  echo "Codex home not found: $CODEX_HOME" >&2
  exit 1
fi

rm -rf "$STAGE" "$ARCHIVE"
mkdir -p "$STAGE"

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [[ -e "$src" ]]; then
    mkdir -p "$(dirname "$dst")"
    cp -a "$src" "$dst"
  fi
}

copy_dir_if_exists() {
  local name="$1"
  if [[ -d "$CODEX_HOME/$name" ]]; then
    cp -a "$CODEX_HOME/$name" "$STAGE/$name"
  fi
}

copy_if_exists "$CODEX_HOME/AGENTS.md" "$STAGE/AGENTS.md"
copy_if_exists "$CODEX_HOME/config.toml" "$STAGE/config.toml"
copy_if_exists "$CODEX_HOME/.personality_migration" "$STAGE/.personality_migration"

copy_dir_if_exists "skills"
copy_dir_if_exists "rules"
copy_dir_if_exists "plugins"
rm -rf "$STAGE/plugins/cache"
copy_dir_if_exists "memories"
copy_dir_if_exists "agent-project-harness"
copy_dir_if_exists "project-harness"

if [[ -f "$STAGE/config.toml" ]]; then
  perl -0pi -e 's/((?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|AUTH)[A-Z0-9_-]*\s*=\s*)"[^"]*"/$1"__REPLACE_ON_TARGET__"/ig' "$STAGE/config.toml"
fi

cat > "$STAGE/README.md" <<'README'
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
README

mkdir -p "$STAGE/scripts"
cp "$ROOT/scripts/import-codex-config.sh" "$STAGE/scripts/import-codex-config.sh"
chmod +x "$STAGE/scripts/import-codex-config.sh"

tar -C "$ROOT/export" -czf "$ARCHIVE" codex-config
echo "$ARCHIVE"
