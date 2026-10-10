#!/usr/bin/env bash
# Read-only git and layout evidence for review-process.
# Usage: git-evidence.sh [repo-path] [sample-size]
# Prints counts the rubric uses; never writes, fetches, or calls a network API.
set -u
# No pipefail: several pipelines end in head, which would turn complete output into exit 141.

repo="${1:-.}"
n="${2:-100}"
cd "$repo" 2>/dev/null || { echo "error: cannot cd to $repo" >&2; exit 1; }

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "git: not a git repository (history-based items are N/A)"
  exit 0
fi

root="$(git rev-parse --show-toplevel)"
cd "$root" || exit 1
echo "repo_root: $root"
echo "shallow: $(git rev-parse --is-shallow-repository 2>/dev/null || echo unknown)"

# Default branch: origin/HEAD if known, else main, else master, else current.
default="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
for b in "$default" main master; do
  if [ -n "$b" ] && git rev-parse --verify --quiet "$b" >/dev/null; then default="$b"; break; fi
done
[ -z "$default" ] && default="$(git rev-parse --abbrev-ref HEAD)"
echo "default_branch: $default"

echo
echo "== history =="
echo "commits_total: $(git rev-list --count "$default")"
echo "commits_non_merge: $(git rev-list --count --no-merges "$default")"
echo "first_commit: $(git log --reverse --format=%cs "$default" | head -1)"
echo "last_commit: $(git log -1 --format=%cs "$default")"
echo "authors (top 5):"
git shortlog -sn --no-merges "$default" | head -5

echo
echo "== commit messages (last $n non-merge commits on $default) =="
subjects="$(git log --no-merges -n "$n" --format=%s "$default")"
sampled="$(printf '%s\n' "$subjects" | grep -c . )"
cc_re='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]*\))?!?: .+'
cc="$(printf '%s\n' "$subjects" | grep -cE "$cc_re")"
echo "sampled: $sampled"
echo "conventional_commits: $cc"
[ "$sampled" -gt 0 ] && echo "conventional_rate_pct: $(( cc * 100 / sampled ))"
vague_re='^(wip|fix|fixes|fixed|update|updates|updated|changes?|stuff|misc|tmp|temp|test|minor|cleanup|\.+)\.?$'
echo "vague_subjects (sha subject):"
git log --no-merges -n "$n" --format='%h %s' "$default" \
  | awk '{sha=$1; $1=""; sub(/^ /,""); print sha "\t" $0}' \
  | while IFS=$'\t' read -r sha s; do
      printf '%s\n' "$s" | grep -qiE "$vague_re" && echo "  $sha $s"
    done
echo "repeated_subjects (3+ identical; placeholders count as vague):"
printf '%s\n' "$subjects" | sort | uniq -c | sort -rn | awk '$1>=3' | head -5 | sed 's/^ */  /'
echo "short_subjects_lt_12_chars: $(printf '%s\n' "$subjects" | awk 'length($0)<12' | grep -c .)"

echo
echo "== integration path on $default (first-parent, last $n) =="
fp_merges="$(git log --first-parent --merges -n "$n" --format=%s "$default")"
fp_direct="$(git log --first-parent --no-merges -n "$n" --format=%s "$default")"
pr_merges="$(printf '%s\n' "$fp_merges" | grep -cE '^Merge (pull request|branch .* into)|^Merge .*#[0-9]+')"
squash_prs="$(printf '%s\n' "$fp_direct" | grep -cE '\(#[0-9]+\)$')"
direct_total="$(printf '%s\n' "$fp_direct" | grep -c .)"
fp_total="$(git log --first-parent -n "$n" --format=%h "$default" | grep -c .)"
echo "first_parent_sampled: $fp_total"
echo "merge_commits: $(printf '%s\n' "$fp_merges" | grep -c .)"
echo "pr_merge_commits: $pr_merges"
echo "squash_merged_prs (subject ends in (#N)): $squash_prs"
echo "direct_commits (no PR marker): $(( direct_total - squash_prs ))"
[ "$fp_total" -gt 0 ] && echo "via_pr_pct: $(( (pr_merges + squash_prs) * 100 / fp_total ))"
bot_prs="$(git log --first-parent -n "$n" --format='%an|%s' "$default" | grep -E '^Merge pull request|\(#[0-9]+\)$' | grep -ciE 'dependabot|renovate|github-actions|\[bot\]|/dependabot/|/renovate/')"
echo "bot_prs (dependabot/renovate/actions; exclude from human review rate): $bot_prs"
echo "sample direct commits:"
git log --first-parent --no-merges -n "$n" --format='%h %cs %s' "$default" | grep -vE '\(#[0-9]+\)$' | head -5 | sed 's/^/  /'

echo
echo "== branches =="
echo "local: $(git for-each-ref --format=x refs/heads | grep -c .)  remote: $(git for-each-ref --format=x refs/remotes | grep -c .)"
echo "stale (no commit in 90+ days):"
cutoff=$(( $(date +%s) - 90*86400 ))
git for-each-ref --format='%(committerdate:unix) %(refname:short)' refs/heads refs/remotes \
  | awk -v c="$cutoff" '$1<c {print "  " $2}' | grep -v 'HEAD' | head -10

echo
echo "== layout pitfalls =="
echo "root_workflows:"
git ls-files '.github/workflows/*' | sed 's/^/  /'
nested="$(git ls-files | grep -E '/\.github/workflows/' | grep -vE '^\.github/')"
if [ -n "$nested" ]; then
  echo "nested_workflows (GitHub Actions ignores these):"
  printf '%s\n' "$nested" | sed 's/^/  /'
fi
for f in LICENSE LICENSE.md LICENSE.txt COPYING CONTRIBUTING.md .github/CONTRIBUTING.md docs/CONTRIBUTING.md \
         CODEOWNERS .github/CODEOWNERS docs/CODEOWNERS .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE.md \
         .github/dependabot.yml renovate.json .github/renovate.json .editorconfig .gitattributes .devcontainer/devcontainer.json; do
  [ -e "$f" ] && echo "present: $f"
done
echo "license_mentions_in_readme:"
git ls-files | grep -iE '(^|/)readme(\.md|\.rst|\.txt)?$' | while read -r r; do
  grep -niE 'licen[cs]e' "$r" | head -3 | sed "s#^#  $r:#"
done
echo "readme_paths_missing (relative paths in backticks or links that do not exist; verify before citing; model IDs and generated outputs are false positives):"
for r in README.md CONTRIBUTING.md; do
  [ -f "$r" ] || continue
  grep -noE '(`[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+`|\]\([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+\))' "$r" \
    | while IFS=: read -r ln tok; do
        p="$(printf '%s' "$tok" | sed -E 's/^`//; s/`$//; s/^\]\(//; s/\)$//; s#/$##')"
        case "$p" in http*|*://*|~*|/*) continue ;; esac
        [ -e "$p" ] || echo "  $r:$ln $p"
      done | head -10
  grep -noE '(python3?|uv run|bash|sh|node|ruby|go run) [A-Za-z0-9_./-]+\.(py|sh|js|ts|rb|go)' "$r" \
    | while IFS=: read -r ln tok; do
        p="${tok##* }"
        [ -e "$p" ] || git ls-files | grep -qE "(^|/)${p##*/}$" || echo "  $r:$ln $tok (no such script anywhere)"
      done | head -10
done
echo "lockfiles:"
git ls-files | grep -E '(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock|go\.sum|poetry\.lock|uv\.lock|Pipfile\.lock|Gemfile\.lock|composer\.lock|bun\.lockb?)$' | sed 's/^/  /'
echo "absolute_paths_in_tracked_text (first 10):"
git grep -nIE '(/Users/[A-Za-z]|/home/[a-z][a-z0-9_-]+/|[A-Z]:\\\\Users\\\\)' -- ':!*.lock' ':!*lock.json' 2>/dev/null | head -10 | cut -c1-160 | sed 's/^/  /'
