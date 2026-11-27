#!/bin/bash
set -e

# Code Review Memory — Setup Script
# Scaffolds vault directory structure and verifies CLI tooling.
#
# Usage: bash setup.sh <vault-path>
# Output: JSON summary to stdout. Progress messages to stderr.

VAULT_ROOT="${1:-.}"

echo "=== LLM Wiki Setup ===" >&2

# 1. Create directory structure
echo "Creating directory structure..." >&2
mkdir -p "$VAULT_ROOT/raw"
mkdir -p "$VAULT_ROOT/wiki/sources"
mkdir -p "$VAULT_ROOT/wiki/entities"
mkdir -p "$VAULT_ROOT/wiki/concepts"
mkdir -p "$VAULT_ROOT/wiki/synthesis"
mkdir -p "$VAULT_ROOT/output"

# 2. Create wiki/index.md if it doesn't exist
if [ ! -f "$VAULT_ROOT/wiki/index.md" ]; then
  cat > "$VAULT_ROOT/wiki/index.md" << 'EOF'
# Index

Master catalog of all wiki pages. Updated on every ingest.

## Sources

## Entities

## Concepts

## Synthesis
EOF
  echo "Created wiki/index.md" >&2
else
  echo "wiki/index.md already exists, skipping" >&2
fi

# 3. Create wiki/log.md if it doesn't exist
if [ ! -f "$VAULT_ROOT/wiki/log.md" ]; then
  cat > "$VAULT_ROOT/wiki/log.md" << 'EOF'
# Log

Chronological record of all operations.

EOF
  echo "Created wiki/log.md" >&2
else
  echo "wiki/log.md already exists, skipping" >&2
fi

# 4. Check tooling
echo "" >&2
echo "Checking tooling..." >&2

TOOLS_JSON="[]"
# uv tool installs here; often missing from PATH in non-login shells
export PATH="$HOME/.local/bin:$PATH"

check_tool() {
  local name="$1"
  local cmd="$2"
  local install_cmd="$3"
  local status="missing"

  if command -v "$cmd" &> /dev/null; then
    status="installed"
    echo "  [ok] $name" >&2
  else
    echo "  [missing] $name" >&2
    # prompt via /dev/tty (stdout is JSON); no tty (CI/agent) = skip install
    local reply="" installer="${install_cmd%% *}"
    if ! command -v "$installer" &> /dev/null; then
      echo "  '$installer' not found; install it first" >&2
    elif [ -t 2 ] && [ -r /dev/tty ]; then
      # read -p writes its prompt to stderr, so print it ourselves
      printf "  Install %s with '%s'? [y/N] " "$name" "$install_cmd" >&2
      { read -r reply < /dev/tty; } 2>/dev/null || reply=""
    fi
    if [[ "$reply" =~ ^[Yy]([Ee][Ss])?$ ]]; then
      # install output to stderr so stdout stays pure JSON
      if eval "$install_cmd" >&2 && command -v "$cmd" &> /dev/null; then
        status="installed"
        echo "  [ok] $name (installed)" >&2
      else
        echo "  [failed] $name — install manually: $install_cmd" >&2
      fi
    else
      echo "  [skipped] install manually: $install_cmd" >&2
    fi
  fi

  # install cmds contain no quotes/backslashes, so no JSON escaping needed
  local entry="{\"name\": \"$name\", \"status\": \"$status\", \"install\": \"$install_cmd\"}"
  if [ "$TOOLS_JSON" = "[]" ]; then TOOLS_JSON="[$entry]"; else TOOLS_JSON="${TOOLS_JSON%]}, $entry]"; fi
}

check_tool "markitdown" "markitdown" "uv tool install markitdown[all]"
check_tool "qmd" "qmd" "npm i -g @tobilu/qmd"

echo "" >&2
echo "Setup complete." >&2

# 5. Output JSON result to stdout
VAULT_ABS=$(cd "$VAULT_ROOT" && pwd)
cat << JSONEOF
{
  "status": "complete",
  "vault_root": "$VAULT_ABS",
  "directories": [
    "raw/",
    "wiki/",
    "wiki/sources/",
    "wiki/entities/",
    "wiki/concepts/",
    "wiki/synthesis/",
    "output/"
  ],
  "files": [
    "wiki/index.md",
    "wiki/log.md"
  ],
  "tools": $TOOLS_JSON
}
JSONEOF