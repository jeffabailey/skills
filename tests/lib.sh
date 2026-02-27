#!/usr/bin/env bash
# Shared test harness for shell-based test scripts.
# Source this file at the top of each test script:
#   source "$(dirname "$0")/lib.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; if [ -n "${2:-}" ]; then echo "        got: $2"; fi; }

summarize() {
  echo ""
  echo "=== Results: $PASS passed, $FAIL failed ==="
  if [ "$FAIL" -gt 0 ]; then
    exit 1
  fi
}
