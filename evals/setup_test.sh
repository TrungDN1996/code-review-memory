#!/bin/bash
set -e

# Test: setup.sh creates correct vault structure
# Usage: bash evals/setup_test.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ONBOARDING="$REPO_ROOT/scripts/setup.sh"
TEST_DIR=$(mktemp -d)
TEST_VAULT="$TEST_DIR/test-vault"
PYTHON=$(command -v python3 || command -v python || echo python3)

cleanup() {
  rm -rf "$TEST_DIR"
}
trap cleanup EXIT

PASS=0
FAIL=0

assert_dir() {
  if [ -d "$1" ]; then
    echo "  PASS: directory exists — $1"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: directory missing — $1"
    FAIL=$((FAIL + 1))
  fi
}

assert_file() {
  if [ -f "$1" ]; then
    echo "  PASS: file exists — $1"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: file missing — $1"
    FAIL=$((FAIL + 1))
  fi
}

assert_contains() {
  if grep -q "$2" "$1" 2>/dev/null; then
    echo "  PASS: file contains '$2' — $1"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: file does not contain '$2' — $1"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Test: setup.sh ==="
echo ""

# Test 1: Script runs successfully on a new directory
echo "Test 1: Fresh vault scaffolding"
bash "$ONBOARDING" "$TEST_VAULT" 2>/dev/null

assert_dir "$TEST_VAULT/raw"
assert_dir "$TEST_VAULT/wiki"
assert_dir "$TEST_VAULT/wiki/sources"
assert_dir "$TEST_VAULT/wiki/entities"
assert_dir "$TEST_VAULT/wiki/concepts"
assert_dir "$TEST_VAULT/wiki/synthesis"
assert_dir "$TEST_VAULT/output"

echo ""

# Test 2: wiki/index.md created with correct scaffolding
echo "Test 2: wiki/index.md content"
assert_file "$TEST_VAULT/wiki/index.md"
assert_contains "$TEST_VAULT/wiki/index.md" "## Sources"
assert_contains "$TEST_VAULT/wiki/index.md" "## Entities"
assert_contains "$TEST_VAULT/wiki/index.md" "## Concepts"
assert_contains "$TEST_VAULT/wiki/index.md" "## Synthesis"

echo ""

# Test 3: wiki/log.md created with header
echo "Test 3: wiki/log.md content"
assert_file "$TEST_VAULT/wiki/log.md"
assert_contains "$TEST_VAULT/wiki/log.md" "# Log"

echo ""

# Test 4: Idempotent — running again doesn't overwrite existing files
echo "Test 4: Idempotency"
echo "# Custom content" >> "$TEST_VAULT/wiki/index.md"
bash "$ONBOARDING" "$TEST_VAULT" 2>/dev/null
assert_contains "$TEST_VAULT/wiki/index.md" "# Custom content"

echo ""

# Test 5: Script outputs valid JSON
echo "Test 5: JSON output"
OUTPUT=$(bash "$ONBOARDING" "$TEST_VAULT" 2>/dev/null)
if echo "$OUTPUT" | "$PYTHON" -m json.tool > /dev/null 2>&1; then
  echo "  PASS: output is valid JSON"
  PASS=$((PASS + 1))
else
  echo "  FAIL: output is not valid JSON"
  FAIL=$((FAIL + 1))
fi

echo ""

# Drop PATH entries holding a real markitdown so it looks uninstalled
CLEAN_PATH="$STUB_BIN"
IFS=':' read -ra PATH_DIRS <<< "$PATH"
for d in "${PATH_DIRS[@]}"; do
  if [ ! -x "$d/markitdown" ] && [ ! -x "$d/markitdown.exe" ]; then
    CLEAN_PATH="$CLEAN_PATH:$d"
  fi
done

# setup.sh only prompts when stderr is a tty; 2>/dev/null keeps the test non-interactive.
# HOME is faked so a real ~/.local/bin/markitdown (added to PATH by setup.sh) is not found.
if OUTPUT=$(HOME="$TEST_DIR/home" PATH="$CLEAN_PATH" bash "$ONBOARDING" "$NEW_VAULT" 2>/dev/null </dev/null); then
  echo "  PASS: script exits 0"
  PASS=$((PASS + 1))
else
  echo "  FAIL: script exited non-zero"
  FAIL=$((FAIL + 1))
fi
assert_dir "$NEW_VAULT/raw"
assert_file "$NEW_VAULT/wiki/index.md"
if [ ! -e "$UV_LOG" ]; then
  echo "  PASS: uv not invoked without tty consent"
  PASS=$((PASS + 1))
else
  echo "  FAIL: uv invoked without consent — $(cat "$UV_LOG")"
  FAIL=$((FAIL + 1))
fi
if echo "$OUTPUT" | "$PYTHON" -c "
import sys, json
tools = {t['name']: t['status'] for t in json.load(sys.stdin)['tools']}
sys.exit(0 if tools.get('markitdown') == 'missing' else 1)
" 2>/dev/null; then
  echo "  PASS: JSON reports markitdown missing"
  PASS=$((PASS + 1))
else
  echo "  FAIL: JSON does not report markitdown missing"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi