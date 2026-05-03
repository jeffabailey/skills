#!/usr/bin/env bash
# Workflow validation tests using act (dry-run mode)
# Tests that the fitness-review workflow is valid and properly configured.
set -euo pipefail
source "$(dirname "$0")/lib.sh"

PLATFORM_ARGS="-P ubuntu-slim=catthehacker/ubuntu:act-latest -P ubuntu-latest=catthehacker/ubuntu:act-latest"

echo "=== Workflow Validation Tests ==="
echo ""

# ---- File structure ----
echo "--- File structure ---"
if [ -f .github/workflows/fitness-review.yml ]; then
  pass "fitness-review.yml exists"
else
  fail "fitness-review.yml missing"
fi

if [ ! -f .github/workflows/fitness-review-copilot.yml ]; then
  pass "No separate Copilot workflow (single engine)"
else
  fail "fitness-review-copilot.yml should not exist"
fi

if [ ! -f .github/workflows/fitness-review.lock.yml ]; then
  pass "No .lock.yml file"
else
  fail "fitness-review.lock.yml still exists"
fi

if [ ! -f .github/workflows/fitness-review.md ]; then
  pass "No .md source file"
else
  fail "fitness-review.md still exists"
fi

if [ ! -d .github/aw ]; then
  pass "No .github/aw directory"
else
  fail ".github/aw directory still exists"
fi

if [ -f .github/fitness-review-prompt.md ]; then
  pass "Standalone prompt file exists"
else
  fail "fitness-review-prompt.md missing"
fi

# ---- Engine config script ----
echo "--- Engine config script ---"
if [ -f .github/scripts/engine-config.py ]; then
  pass "engine-config.py exists"
else
  fail "engine-config.py missing"
fi

if [ -x .github/scripts/engine-config.py ]; then
  pass "engine-config.py is executable"
else
  fail "engine-config.py is not executable"
fi

# Validate engine-config.py outputs for each engine
# Unset GITHUB_OUTPUT so the script writes to stdout instead of the GH Actions file
unset GITHUB_OUTPUT
for ENGINE in claude copilot codex; do
  ENGINE_OUTPUT=$(python3 .github/scripts/engine-config.py --engine "$ENGINE")
  if echo "$ENGINE_OUTPUT" | grep -q "^engine_id=$ENGINE"; then
    pass "engine-config.py outputs engine_id=$ENGINE"
  else
    actual_id=$(echo "$ENGINE_OUTPUT" | grep "^engine_id=" | head -1)
    fail "engine-config.py missing engine_id for $ENGINE" "${actual_id:-<no engine_id line found>}"
  fi
  for KEY in engine_name secret_name concurrency_prefix; do
    if echo "$ENGINE_OUTPUT" | grep -q "^${KEY}="; then
      pass "engine-config.py outputs $KEY for $ENGINE"
    else
      fail "engine-config.py missing $KEY for $ENGINE"
    fi
  done
  # install_cmd may use heredoc delimiter for long values
  if echo "$ENGINE_OUTPUT" | grep -q "^install_cmd=\|^install_cmd<<"; then
    pass "engine-config.py outputs install_cmd for $ENGINE"
  else
    fail "engine-config.py missing install_cmd for $ENGINE"
  fi
done

# ---- Clean headers ----
echo ""
echo "--- Clean headers ---"
if ! grep -q "gh-aw-metadata" .github/workflows/fitness-review.yml; then
  pass "No gh-aw-metadata"
else
  fail "gh-aw-metadata still present"
fi

if ! grep -q "DO NOT EDIT" .github/workflows/fitness-review.yml; then
  pass "No DO NOT EDIT header"
else
  fail "DO NOT EDIT still present"
fi

# ---- Multi-engine support ----
echo "--- Multi-engine support ---"
if grep -q "engine:" .github/workflows/fitness-review.yml && grep -q "claude" .github/workflows/fitness-review.yml && grep -q "copilot" .github/workflows/fitness-review.yml && grep -q "codex" .github/workflows/fitness-review.yml; then
  pass "Engine dropdown with claude, copilot, codex"
else
  fail "Missing engine dropdown or engine choices"
fi

if grep -q "engine-config.py" .github/workflows/fitness-review.yml; then
  pass "Workflow references engine-config.py"
else
  fail "Workflow does not reference engine-config.py"
fi

if grep -q "steps.engine-config.outputs" .github/workflows/fitness-review.yml; then
  pass "Workflow uses engine-config step outputs"
else
  fail "Workflow does not use engine-config step outputs"
fi

# Engine-specific secrets should be in the script, not hardcoded as the sole option in YAML
if ! grep -q 'engine_id: "claude"' .github/workflows/fitness-review.yml; then
  pass "No hardcoded engine_id in YAML"
else
  fail "Hardcoded engine_id still in YAML"
fi

# ---- No agent_type or cursor ----
echo "--- No legacy patterns ---"
if ! grep -q "cursor" .github/workflows/fitness-review.yml; then
  pass "No cursor in workflow"
else
  fail "cursor still in workflow"
fi

if ! grep -q "agent_type" .github/workflows/fitness-review.yml; then
  pass "No agent_type dropdown"
else
  fail "agent_type dropdown still present"
fi

# Regression guard: this repo uses frozen hand-edited YAML (not gh aw compile).
# check_workflow_timestamp_api is therefore forbidden unconditionally — the lock-file
# model it depends on was abandoned in commit 01dc4cf. See GH Actions run 25275707144.
if ! grep -rq "check_workflow_timestamp_api" .github/workflows/; then
  pass "No orphaned gh-aw lock-file staleness check"
else
  offenders=$(grep -lr "check_workflow_timestamp_api" .github/workflows/ | tr '\n' ' ')
  fail "check_workflow_timestamp_api is forbidden: repo uses frozen YAML, not gh aw compile" "$offenders"
fi

# Regression guard: gh-aw v0.62.0 moved PROMPTS_DEST and SAFEOUTPUTS_DEST from
# /opt/gh-aw/{prompts,safeoutputs} to ${RUNNER_TEMP}/gh-aw/{prompts,safeoutputs}.
# The hand-frozen YAML hardcodes the old /opt/gh-aw/* paths, so any gh-aw bump
# past v0.58.1 breaks `cat /opt/gh-aw/prompts/xpia.md` etc. — see run 25287248940.
# Pin gh-aw to v0.58.1 until the workflow is regenerated via `gh aw compile`.
GH_AW_PINNED_SHA="fa061e89469ef007881d22d3af5a8c9e62363a0d"
GH_AW_PINNED_VERSION="v0.58.1"
unpinned=$(grep -E "github/gh-aw/actions/setup@" .github/workflows/*.yml \
           | grep -v "$GH_AW_PINNED_SHA" || true)
if [ -z "$unpinned" ]; then
  pass "gh-aw pinned to $GH_AW_PINNED_VERSION (last YAML-compatible version)"
else
  fail "gh-aw not pinned to $GH_AW_PINNED_VERSION" "$unpinned"
fi

# Regression guard: dependabot must ignore github-actions bumps until the
# workflow YAML is regenerated. Without this, the next bump silently
# reintroduces path drift.
if grep -q 'dependency-name: "\*"' .github/dependabot.yml; then
  pass "dependabot ignores all github-actions bumps"
else
  fail "dependabot.yml missing 'dependency-name: \"*\"' ignore rule"
fi

# ---- act parsing (skipped if act is not installed) ----
echo "--- act workflow parsing ---"
if command -v act &>/dev/null; then
  JOB_LIST=$(act --list -W .github/workflows/fitness-review.yml $PLATFORM_ARGS 2>&1)

  for JOB in activation agent detection safe_outputs conclusion; do
    if echo "$JOB_LIST" | grep -q "$JOB"; then
      pass "Has $JOB job"
    else
      fail "Missing $JOB job"
    fi
  done
else
  echo "  SKIP: act not installed — skipping job list validation"
fi

# ---- Triggers ----
echo "--- Triggers ---"
if grep -q "schedule:" .github/workflows/fitness-review.yml; then
  pass "Has schedule trigger"
else
  fail "Missing schedule trigger"
fi

if grep -q "workflow_dispatch:" .github/workflows/fitness-review.yml; then
  pass "Has workflow_dispatch trigger"
else
  fail "Missing workflow_dispatch trigger"
fi

# ---- Prompt reference ----
echo "--- Prompt ---"
if grep -q "runtime-import .github/fitness-review-prompt.md" .github/workflows/fitness-review.yml; then
  pass "Runtime-import points to canonical prompt"
else
  fail "Runtime-import path is wrong"
fi

if ! grep -q "Cursor" .github/fitness-review-prompt.md; then
  pass "No Cursor reference in prompt"
else
  fail "Cursor still referenced in prompt"
fi

# ---- Summary ----
summarize
