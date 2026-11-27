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

# 4. Install markitdown (optional; failure must not abort setup)
if ! command -v markitdown &> /dev/null; then
  echo "" >&2
  echo "Installing markitdown..." >&2
  if command -v uv &> /dev/null; then
    uv tool install 'markitdown[all]' >&2 || echo "  markitdown install failed" >&2
  elif command -v pipx &> /dev/null; then
    pipx install 'markitdown[all]' >&2 || echo "  markitdown install failed" >&2
  elif command -v pip3 &> /dev/null; then
    pip3 install --user 'markitdown[all]' >&2 || echo "  markitdown install failed" >&2
  else
    echo "  no uv/pipx/pip3 found, skipping markitdown install" >&2
  fi
fi

# 5. Check tooling
echo "" >&2
echo "Checking tooling..." >&2

TOOLS_JSON="[]"
PYTHON=$(command -v python3 || command -v python || echo python3)

check_tool() {
  local name="$1"
  local cmd="$2"
  local install_cmd="$3"
  local status="missing"

  if command -v "$cmd" &> /dev/null; then
    status="installed"
    echo "  [ok] $name" >&2
  else
    echo "  [missing] $name — install with: $install_cmd" >&2
  fi

  TOOLS_JSON=$(echo "$TOOLS_JSON" | "$PYTHON" -c "
import sys, json
tools = json.load(sys.stdin)
tools.append({'name': '$name', 'status': '$status', 'install': '$install_cmd'})
print(json.dumps(tools))
" 2>/dev/null || echo "$TOOLS_JSON")
}

check_tool "markitdown" "markitdown" "uv tool install markitdown[all]"
check_tool "qmd" "qmd" "npm i -g @tobilu/qmd"

echo "" >&2
echo "Setup complete." >&2

# 6. Output JSON result to stdout
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