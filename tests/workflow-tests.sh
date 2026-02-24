#!/usr/bin/env bash
# Workflow validation tests using act (dry-run mode)
# Tests that both fitness-review workflows are valid and parseable.
set -euo pipefail

PASS=0
FAIL=0
PLATFORM_ARGS="-P ubuntu-slim=catthehacker/ubuntu:act-latest -P ubuntu-latest=catthehacker/ubuntu:act-latest"

pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

echo "=== Workflow Validation Tests ==="
echo ""

# ---- Test 1: Both workflow files exist ----
echo "--- File existence ---"
if [ -f .github/workflows/fitness-review.yml ]; then
  pass "fitness-review.yml exists"
else
  fail "fitness-review.yml missing"
fi

if [ -f .github/workflows/fitness-review-copilot.yml ]; then
  pass "fitness-review-copilot.yml exists"
else
  fail "fitness-review-copilot.yml missing"
fi

# ---- Test 2: Lock files removed ----
echo "--- Lock files removed ---"
if [ ! -f .github/workflows/fitness-review.lock.yml ]; then
  pass "No .lock.yml for Claude workflow"
else
  fail "fitness-review.lock.yml still exists"
fi

if [ ! -f .github/workflows/fitness-review-copilot.lock.yml ]; then
  pass "No .lock.yml for Copilot workflow"
else
  fail "fitness-review-copilot.lock.yml still exists"
fi

# ---- Test 3: .md source files removed ----
echo "--- Source .md files removed ---"
if [ ! -f .github/workflows/fitness-review.md ]; then
  pass "No .md source for Claude workflow"
else
  fail "fitness-review.md still exists"
fi

if [ ! -f .github/workflows/fitness-review-copilot.md ]; then
  pass "No .md source for Copilot workflow"
else
  fail "fitness-review-copilot.md still exists"
fi

# ---- Test 4: aw lock directory removed ----
echo "--- aw directory removed ---"
if [ ! -d .github/aw ]; then
  pass "No .github/aw directory"
else
  fail ".github/aw directory still exists"
fi

# ---- Test 5: No auto-generated header ----
echo "--- No auto-generated metadata ---"
if ! grep -q "gh-aw-metadata" .github/workflows/fitness-review.yml; then
  pass "No gh-aw-metadata in Claude workflow"
else
  fail "gh-aw-metadata still present in Claude workflow"
fi

if ! grep -q "gh-aw-metadata" .github/workflows/fitness-review-copilot.yml; then
  pass "No gh-aw-metadata in Copilot workflow"
else
  fail "gh-aw-metadata still present in Copilot workflow"
fi

if ! grep -q "DO NOT EDIT" .github/workflows/fitness-review.yml; then
  pass "No DO NOT EDIT in Claude workflow"
else
  fail "DO NOT EDIT still in Claude workflow"
fi

if ! grep -q "DO NOT EDIT" .github/workflows/fitness-review-copilot.yml; then
  pass "No DO NOT EDIT in Copilot workflow"
else
  fail "DO NOT EDIT still in Copilot workflow"
fi

# ---- Test 6: Cursor removed from agent options ----
echo "--- Cursor removed ---"
if ! grep -q "cursor" .github/workflows/fitness-review.yml; then
  pass "No cursor option in Claude workflow"
else
  fail "cursor option still in Claude workflow"
fi

if ! grep -q "cursor" .github/workflows/fitness-review-copilot.yml; then
  pass "No cursor option in Copilot workflow"
else
  fail "cursor option still in Copilot workflow"
fi

# ---- Test 7: act can list jobs for both workflows ----
echo "--- act workflow parsing ---"
CLAUDE_LIST=$(act --list -W .github/workflows/fitness-review.yml $PLATFORM_ARGS 2>&1)
if echo "$CLAUDE_LIST" | grep -q "agent"; then
  pass "act lists agent job in Claude workflow"
else
  fail "act cannot list agent job in Claude workflow"
fi

if echo "$CLAUDE_LIST" | grep -q "activation"; then
  pass "act lists activation job in Claude workflow"
else
  fail "act cannot list activation job in Claude workflow"
fi

COPILOT_LIST=$(act --list -W .github/workflows/fitness-review-copilot.yml $PLATFORM_ARGS 2>&1)
if echo "$COPILOT_LIST" | grep -q "agent"; then
  pass "act lists agent job in Copilot workflow"
else
  fail "act cannot list agent job in Copilot workflow"
fi

# ---- Test 8: Both workflows have expected jobs ----
echo "--- Expected jobs present ---"
for JOB in activation agent detection safe_outputs conclusion; do
  if echo "$CLAUDE_LIST" | grep -q "$JOB"; then
    pass "Claude workflow has $JOB job"
  else
    fail "Claude workflow missing $JOB job"
  fi
done

for JOB in activation agent detection safe_outputs conclusion; do
  if echo "$COPILOT_LIST" | grep -q "$JOB"; then
    pass "Copilot workflow has $JOB job"
  else
    fail "Copilot workflow missing $JOB job"
  fi
done

# ---- Test 9: Claude workflow has schedule trigger ----
echo "--- Triggers ---"
if grep -q "schedule:" .github/workflows/fitness-review.yml; then
  pass "Claude workflow has schedule trigger"
else
  fail "Claude workflow missing schedule trigger"
fi

if grep -q "workflow_dispatch:" .github/workflows/fitness-review.yml; then
  pass "Claude workflow has workflow_dispatch trigger"
else
  fail "Claude workflow missing workflow_dispatch trigger"
fi

if grep -q "workflow_dispatch:" .github/workflows/fitness-review-copilot.yml; then
  pass "Copilot workflow has workflow_dispatch trigger"
else
  fail "Copilot workflow missing workflow_dispatch trigger"
fi

# ---- Test 10: Engine IDs correct ----
echo "--- Engine configuration ---"
if grep -q 'engine_id: "claude"' .github/workflows/fitness-review.yml; then
  pass "Claude workflow engine_id is claude"
else
  fail "Claude workflow engine_id is wrong"
fi

if grep -q 'engine_id: "copilot"' .github/workflows/fitness-review-copilot.yml; then
  pass "Copilot workflow engine_id is copilot"
else
  fail "Copilot workflow engine_id is wrong"
fi

# ---- Test 11: Secrets referenced correctly ----
echo "--- Secret references ---"
if grep -q "ANTHROPIC_API_KEY" .github/workflows/fitness-review.yml; then
  pass "Claude workflow references ANTHROPIC_API_KEY"
else
  fail "Claude workflow missing ANTHROPIC_API_KEY"
fi

if grep -q "COPILOT_GITHUB_TOKEN" .github/workflows/fitness-review-copilot.yml; then
  pass "Copilot workflow references COPILOT_GITHUB_TOKEN"
else
  fail "Copilot workflow missing COPILOT_GITHUB_TOKEN"
fi

# ---- Test 12: Prompt file still exists ----
echo "--- Prompt file ---"
if [ -f .github/fitness-review-prompt.md ]; then
  pass "Standalone prompt file exists"
else
  fail "fitness-review-prompt.md missing"
fi

if ! grep -q "Cursor" .github/fitness-review-prompt.md; then
  pass "No Cursor reference in prompt"
else
  fail "Cursor still referenced in prompt"
fi

# ---- Summary ----
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
