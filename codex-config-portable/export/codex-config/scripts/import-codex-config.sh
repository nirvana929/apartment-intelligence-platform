#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP="$HOME/.codex.backup.$(date +%Y%m%d-%H%M%S)"

mkdir -p "$CODEX_HOME"

if [[ -n "$(find "$CODEX_HOME" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
  mkdir -p "$BACKUP"
  cp -a "$CODEX_HOME"/. "$BACKUP"/
  echo "Backed up existing Codex config to: $BACKUP"
fi

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
  if [[ -d "$SRC/$name" ]]; then
    rm -rf "$CODEX_HOME/$name"
    cp -a "$SRC/$name" "$CODEX_HOME/$name"
  fi
}

copy_if_exists "$SRC/AGENTS.md" "$CODEX_HOME/AGENTS.md"
copy_if_exists "$SRC/config.toml" "$CODEX_HOME/config.toml"
copy_if_exists "$SRC/.personality_migration" "$CODEX_HOME/.personality_migration"

copy_dir_if_exists "skills"
copy_dir_if_exists "rules"
copy_dir_if_exists "plugins"
copy_dir_if_exists "memories"
copy_dir_if_exists "agent-project-harness"
copy_dir_if_exists "project-harness"

chmod 700 "$CODEX_HOME"
find "$CODEX_HOME" -type d -exec chmod 755 {} +
find "$CODEX_HOME" -type f -exec chmod u+rw,go-rwx {} +

echo "Imported portable Codex config into: $CODEX_HOME"
echo "Next: run 'codex login' and replace any __REPLACE_ON_TARGET__ values in config.toml."
