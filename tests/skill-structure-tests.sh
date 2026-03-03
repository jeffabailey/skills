#!/usr/bin/env bash
# Validates skill directory structure and conventions.
# Runs without external dependencies (no act required).
# Discovers all skills under src/ dynamically; no hardcoded skill names.
set -euo pipefail
source "$(dirname "$0")/lib.sh"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_ROOT="$ROOT/src"

# Discover skills: directories under src/ that contain SKILL.md
SKILLS=()
for d in "$SKILLS_ROOT"/*/; do
  [ -d "$d" ] || continue
  [ -f "${d}SKILL.md" ] || continue
  name="${d%/}"
  name="${name##*/}"
  SKILLS+=("$name")
done

echo "=== Skill Structure Tests ==="
echo "Found ${#SKILLS[@]} skills under $SKILLS_ROOT"
echo ""

# ---- Directories ----
echo "--- Directories ---"
for skill in "${SKILLS[@]}"; do
  dir="$SKILLS_ROOT/$skill"
  if [ -d "$dir" ]; then
    pass "$skill/ exists"
  else
    fail "$skill/ missing"
  fi
done

# ---- SKILL.md with frontmatter ----
echo "--- SKILL.md ---"
for skill in "${SKILLS[@]}"; do
  skill_md="$SKILLS_ROOT/$skill/SKILL.md"
  if [ -f "$skill_md" ]; then
    pass "$skill/SKILL.md exists"
    if head -1 "$skill_md" | grep -q "^---"; then
      pass "$skill/SKILL.md has frontmatter"
    else
      fail "$skill/SKILL.md missing frontmatter"
    fi
  else
    fail "$skill/SKILL.md missing"
  fi
done

# ---- Checklists: domain skills (with Scoring Dimensions) must have references/checklist.md ----
echo "--- Checklists ---"
for skill in "${SKILLS[@]}"; do
  skill_md="$SKILLS_ROOT/$skill/SKILL.md"
  checklist="$SKILLS_ROOT/$skill/references/checklist.md"
  # Only require checklist for domain review skills (those with scoring dimensions)
  if grep -q "## Scoring Dimensions" "$skill_md"; then
    if [ -f "$checklist" ]; then
      pass "$skill/references/checklist.md exists"
    else
      fail "$skill missing references/checklist.md (has Scoring Dimensions)"
    fi
  fi
done

# ---- Report path and standardized sections: only for skills that have a checklist (domain convention) ----
echo "--- Report paths ---"
for skill in "${SKILLS[@]}"; do
  checklist="$SKILLS_ROOT/$skill/references/checklist.md"
  [ -f "$checklist" ] || continue
  # domain = skill name with any prefix stripped (e.g. review-architecture -> architecture)
  domain="${skill#*-}"
  expected="docs/${domain}-review.md"
  skill_md="$SKILLS_ROOT/$skill/SKILL.md"
  if grep -q "$expected" "$skill_md"; then
    pass "$skill -> $expected"
  else
    fail "$skill does not reference $expected"
  fi
done

# ---- Standardized sections (domain skills only) ----
echo "--- Standardized sections ---"
for skill in "${SKILLS[@]}"; do
  checklist="$SKILLS_ROOT/$skill/references/checklist.md"
  [ -f "$checklist" ] || continue
  skill_md="$SKILLS_ROOT/$skill/SKILL.md"
  if grep -q "## Confidence and Severity" "$skill_md"; then
    pass "$skill has Confidence and Severity section"
  else
    fail "$skill missing Confidence and Severity section"
  fi
  if grep -q "## Scoring Dimensions (1-10 each)" "$skill_md"; then
    pass "$skill has standard Scoring Dimensions header"
  else
    fail "$skill has non-standard Scoring header"
  fi
done

# ---- Wisdom references: skills with posts in skill-sources.json must have references/wisdom.md ----
echo "--- Wisdom references ---"
if command -v python3 &>/dev/null && [ -f "$ROOT/skill-sources.json" ]; then
  while IFS= read -r skill; do
    wisdom="$SKILLS_ROOT/$skill/references/wisdom.md"
    if [ -f "$wisdom" ]; then
      pass "$skill/references/wisdom.md exists"
      if head -1 "$wisdom" | grep -q "^# Domain Knowledge Reference"; then
        pass "$skill/references/wisdom.md has expected header"
      else
        fail "$skill/references/wisdom.md missing expected header"
      fi
    else
      fail "$skill/references/wisdom.md missing (has posts in skill-sources.json)"
    fi
  done < <(python3 -c "
import json, sys
with open('$ROOT/skill-sources.json') as f:
    data = json.load(f)
for skill, cfg in data['skills'].items():
    if cfg.get('posts'):
        print(skill)
")
else
  echo "SKIP: python3 or skill-sources.json not available"
fi

# ---- Summary ----
summarize
