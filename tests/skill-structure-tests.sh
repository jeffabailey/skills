#!/usr/bin/env bash
# Validates skill directory structure and conventions.
# Runs without external dependencies (no act required).
set -euo pipefail

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

SKILLS=(review-architecture review-security review-reliability review-testing
        review-performance review-algorithms review-data review-accessibility
        review-process review-maintainability review-full review-jit-test-gen)

echo "=== Skill Structure Tests ==="
echo ""

# ---- Directories ----
echo "--- Directories ---"
for skill in "${SKILLS[@]}"; do
  if [ -d "$skill" ]; then
    pass "$skill/ exists"
  else
    fail "$skill/ missing"
  fi
done

# ---- SKILL.md with frontmatter ----
echo "--- SKILL.md ---"
for skill in "${SKILLS[@]}"; do
  if [ -f "$skill/SKILL.md" ]; then
    pass "$skill/SKILL.md exists"
    if head -1 "$skill/SKILL.md" | grep -q "^---"; then
      pass "$skill/SKILL.md has frontmatter"
    else
      fail "$skill/SKILL.md missing frontmatter"
    fi
  else
    fail "$skill/SKILL.md missing"
  fi
done

# ---- Checklists (domain skills only) ----
echo "--- Checklists ---"
for skill in "${SKILLS[@]}"; do
  if [ "$skill" = "review-full" ] || [ "$skill" = "review-jit-test-gen" ]; then
    continue
  fi
  if [ -f "$skill/references/checklist.md" ]; then
    pass "$skill/references/checklist.md exists"
  else
    fail "$skill/references/checklist.md missing"
  fi
done

# ---- Report path convention ----
echo "--- Report paths ---"
for skill in "${SKILLS[@]}"; do
  domain="${skill#review-}"
  if [ "$domain" = "full" ] || [ "$domain" = "jit-test-gen" ]; then
    continue
  fi
  expected="docs/${domain}-review.md"
  if grep -q "$expected" "$skill/SKILL.md"; then
    pass "$skill -> $expected"
  else
    fail "$skill does not reference $expected"
  fi
done

# ---- Summary ----
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
