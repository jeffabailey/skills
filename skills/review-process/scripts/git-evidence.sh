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
  # Exact-case match: on case-insensitive filesystems (macOS) [ -e ] would report
  # PULL_REQUEST_TEMPLATE.md present when only pull_request_template.md exists.
  if git ls-files | grep -qxF "$f"; then
    echo "present: $f"
  elif [ -e "$f" ]; then
    for g in "$(dirname "$f")"/.[!.]* "$(dirname "$f")"/*; do
      [ "${g#./}" = "$f" ] && { echo "present (untracked): $f"; break; }
    done
  fi
done
echo "license_mentions_in_readme:"
git ls-files | grep -iE '(^|/)readme(\.md|\.rst|\.txt)?$' | while read -r r; do
  grep -niE 'licen[cs]e' "$r" | head -3 | sed "s#^#  $r:#"
done
# Classify a backticked or linked token from README/CONTRIBUTING.
# Prints "<class>\t<detail>"; class is ok|skip|missing|elsewhere|ignored.
# A token counts as a path only if it looks like one in THIS repo: its first
# segment is (or was) a tracked directory, the exact path was ever tracked, or
# its last segment has a file extension. That drops model IDs (org/model),
# package names, owner/repo refs, MIME types, domains, and version strings.
classify_ref() {
  local p="$1" first last hit n
  case "$p" in
    *://*|~*|/*|-*|@*|\$*|*@*|*:*|*'*'*|*'{'*|*'<'*) echo "skip	not a repo path"; return ;;
  esac
  [ -e "$p" ] && { echo "ok	"; return; }
  first="${p%%/*}"; last="${p##*/}"
  if printf '%s' "$first" | grep -qiE '^[a-z0-9-]+(\.[a-z0-9-]+)*\.(com|org|net|io|dev|ai|co|app|sh|me|gov|edu|cloud|xyz)$'; then
    echo "skip	domain"; return
  fi
  if printf '%s' "$last" | grep -qiE '^v?[0-9]+(\.[0-9x]+)*$'; then
    echo "skip	version"; return
  fi
  local was_tracked dir_known has_ext
  was_tracked="$(git log --all -1 --format=%h -- "$p" 2>/dev/null)"
  dir_known=""
  if [ "$first" != "$p" ] && { [ -d "$first" ] || [ -n "$(git log --all -1 --format=%h -- "$first" 2>/dev/null)" ]; }; then
    dir_known=1
  fi
  has_ext=""
  printf '%s' "$last" | grep -qE '^[^.].*\.[A-Za-z][A-Za-z0-9]{0,7}$' && has_ext=1
  if [ -z "$was_tracked" ] && [ -z "$dir_known" ] && [ -z "$has_ext" ]; then
    echo "skip	not path-like (model ID, package, owner/repo, MIME type?)"; return
  fi
  if git check-ignore -q "$p" 2>/dev/null; then
    echo "ignored	gitignored (generated or runtime output, not a defect)"; return
  fi
  hit="$(git ls-files | grep -E "/$(printf '%s' "$p" | sed 's/[.[\*^$()+?{|]/\\&/g')$")"
  if [ -n "$hit" ]; then
    n="$(printf '%s\n' "$hit" | grep -c .)"
    if [ "$n" -gt 1 ]; then
      echo "elsewhere	-> $(printf '%s\n' "$hit" | head -1) (+$((n-1)) more; likely relative to each subdirectory)"
    else
      echo "elsewhere	-> $hit (moved, or relative to a subdirectory)"
    fi
    return
  fi
  if [ -n "$was_tracked" ]; then
    echo "missing	deleted or renamed in $(git log --all -1 --diff-filter=DR --format=%h -- "$p" 2>/dev/null || echo "$was_tracked")"
  else
    echo "missing	never tracked"
  fi
}
tracked_ending() {  # tracked files whose path is $1 or ends with /$1 (case-exact)
  git ls-files | awk -v n="$1" '$0==n || substr($0, length($0)-length(n)) == "/" n'
}
# Emit "<line>\t<file>\t<command>\t<cwd>" for each `python|uv run|bash|... X.ext`.
# cwd is "" when no cd precedes it in the block, a repo-relative dir after a
# resolvable cd, or "?<target>" when the cd is a placeholder or leaves the repo.
cmd_cwds() {
  awk -v base="$2" '
    function norm(cur, t,   n, a, i, out, k, j) {
      if (t ~ /^[\/~$<{]/ || t ~ /[<>$*{}]/) return "?" t
      if (cur ~ /^\?/) return cur
      n = split((cur == "." ? "" : cur "/") t, a, "/"); k = 0
      for (i = 1; i <= n; i++) {
        if (a[i] == "" || a[i] == ".") continue
        if (a[i] == "..") { if (k == 0) return "?" t; k--; continue }
        out[++k] = a[i]
      }
      s = ""; for (j = 1; j <= k; j++) s = s (j > 1 ? "/" : "") out[j]
      return s == "" ? "." : s
    }
    /^[ \t]*(```|~~~)/ { fence = !fence; cwd = ""; next }
    {
      if (!fence && $0 !~ /^(    |\t)/) cwd = ""
      line = $0
      while (1) {
        cdp = match(line, /(^|[^A-Za-z0-9_-])cd [^ \t;&|)`]+/); cdl = RLENGTH
        cmp = match(line, /(^|[^A-Za-z0-9_-])(python3?|uv run|bash|sh|node|ruby|go run) [A-Za-z0-9_.\/-]+\.(py|sh|js|ts|rb|go)/); cml = RLENGTH
        if (!cdp && !cmp) break
        if (cdp && (!cmp || cdp < cmp)) {
          tok = substr(line, cdp, cdl); sub(/^.*cd /, "", tok); sub(/\/$/, "", tok)
          cwd = norm(cwd == "" ? base : cwd, tok)
          line = substr(line, cdp + cdl)
        } else {
          tok = substr(line, cmp, cml); sub(/^[^A-Za-z]/, "", tok)
          f = tok; sub(/^.* /, "", f)
          print NR "\t" f "\t" tok "\t" cwd
          line = substr(line, cmp + cml)
        }
      }
    }' "$1"
}
classify_cmd_file() {  # $1 file, $2 cwd from cmd_cwds, $3 doc dir
  local f="$1" cwd="$2" d="$3" hits n where
  case "$f" in /*|~*) echo "skip	absolute"; return ;; esac
  hits="$(tracked_ending "${f#./}")"
  # `bash skills/scripts/x.sh` run from a checkout's parent: drop a leading segment.
  [ -z "$hits" ] && case "$f" in */*) hits="$(tracked_ending "${f#*/}")" ;; esac
  n="$(printf '%s' "$hits" | grep -c .)"
  where="$(printf '%s\n' "$hits" | head -3 | paste -sd, - | sed 's/,/, /g')"
  [ "$n" -gt 3 ] && where="$where (+$((n-3)) more)"
  case "$cwd" in
    '')
      { [ -e "$d/$f" ] || [ -e "$f" ]; } && { echo "ok	"; return; }
      [ "$n" -gt 0 ] && { echo "elsewhere	-> no cd in this block, so it runs from $d; $f exists only at $where"; return; }
      echo "missing	no such script anywhere"; return ;;
    \?*)
      [ -e "$d/$f" ] && { echo "ok	"; return; }
      [ "$n" -gt 0 ] && { echo "elsewhere	-> runs from unresolvable cd ${cwd#?}; $f exists at $where (check it holds for every directory the doc means)"; return; }
      echo "missing	no such script anywhere"; return ;;
  esac
  [ -e "$cwd/$f" ] && { echo "ok	"; return; }
  if [ ! -d "$cwd" ]; then
    # The stale cd itself is reported; only flag the file if it exists nowhere.
    [ "$n" -gt 0 ] && { echo "ok	"; return; }
    echo "missing	no such script anywhere"; return
  fi
  [ "$n" -gt 0 ] && { echo "elsewhere	-> runs from $cwd/ (preceding cd) but $f is not there; it exists at $where"; return; }
  echo "missing	not in $cwd/ (preceding cd) or anywhere else"
}
# Bare doc/config filenames, one "<line>:<name>" per distinct mention.
bare_names() {
  {
    grep -noE '[A-Za-z0-9_./-]*[A-Z][A-Z0-9_-]*\.(md|rst|txt|adoc)[A-Za-z0-9_/-]*' "$1" \
      | grep -E ':[A-Z][A-Z0-9_-]*\.(md|rst|txt|adoc)$'
    grep -noE '`[A-Za-z0-9_][A-Za-z0-9_.-]*`' "$1" | tr -d '`' \
      | grep -E ':([A-Za-z0-9_][A-Za-z0-9_.-]*\.(md|rst|txt|adoc|ya?ml|toml|json|jsonc|ini|cfg|conf|lock)|Makefile|Dockerfile|Containerfile|Justfile|justfile|Procfile|Gemfile|Brewfile|Vagrantfile|\.editorconfig|\.gitattributes|\.gitignore|\.dockerignore)$'
  } | sort -t: -k1,1n -k2 -u
}
classify_bare() {  # $1 bare filename, $2 doc dir
  local b="$1" d="$2" hits n gone
  if git ls-files | grep -qxF -e "$b" -e "${d#./}/$b"; then echo "ok	"; return; fi
  if git check-ignore -q "$b" 2>/dev/null; then echo "ignored	gitignored"; return; fi
  if printf '%s' "$b" | grep -qiE '^v?[0-9]+(\.[0-9x]+)*\.[a-z]+$'; then echo "skip	version"; return; fi
  hits="$(tracked_ending "$b")"
  n="$(printf '%s' "$hits" | grep -c .)"
  if [ "$n" -ge 3 ]; then echo "skip	generic name; $n tracked copies"; return; fi
  if [ "$n" -gt 0 ]; then
    echo "elsewhere	-> $(printf '%s\n' "$hits" | paste -sd, - | sed 's/,/, /g') (bare name; not in the doc's directory or the repo root)"; return
  fi
  gone="$(git log --all -1 --diff-filter=DR --format=%h -- "$b" ":(glob)**/$b" 2>/dev/null)"
  if [ -n "$gone" ]; then echo "missing	bare name; deleted or renamed in $gone"; return; fi
  echo "missing	bare name; no tracked file has this name"
}
miss=""; elsew=""; ign=""; skipped=""
for r in README.md CONTRIBUTING.md; do
  [ -f "$r" ] || continue
  while IFS=: read -r ln tok; do
    p="$(printf '%s' "$tok" | sed -E 's/^`//; s/`$//; s/^\]\(//; s/\)$//; s/#.*$//; s#/$##')"
    [ -n "$p" ] || continue
    res="$(classify_ref "$p")"; cls="${res%%	*}"; det="${res#*	}"
    case "$cls" in
      missing)   miss="$miss  $r:$ln $p ($det)"$'\n' ;;
      elsewhere) elsew="$elsew  $r:$ln $p $det"$'\n' ;;
      ignored)   ign="$ign  $r:$ln $p"$'\n' ;;
      skip)      skipped="$skipped  $r:$ln $p ($det)"$'\n' ;;
    esac
  done < <(grep -noE '(`[A-Za-z0-9_.@~$-][A-Za-z0-9_./@:*{}<>$-]*/[A-Za-z0-9_./@:*{}<>$-]+`|\]\([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+(#[^)]*)?\))' "$r")
  # Command file arguments resolve against the working directory the doc implies:
  # the last `cd` earlier in the same code block (or the same line), else the doc's
  # own directory, else the repo root.
  rdir="$(dirname "$r")"
  while IFS=$'\t' read -r ln f cmd cwd; do
    res="$(classify_cmd_file "$f" "$cwd" "$rdir")"; cls="${res%%	*}"; det="${res#*	}"
    case "$cls" in
      missing)   miss="$miss  $r:$ln $cmd ($det)"$'\n' ;;
      elsewhere) elsew="$elsew  $r:$ln $cmd $det"$'\n' ;;
    esac
  done < <(cmd_cwds "$r" "$rdir")
  # Bare filenames (no slash): uppercase doc names anywhere in the text (RUN.md,
  # SETUP.md) and backticked doc/config names (`mkdocs.yml`, `Makefile`).
  while IFS=: read -r ln name; do
    res="$(classify_bare "$name" "$rdir")"; cls="${res%%	*}"; det="${res#*	}"
    case "$cls" in
      missing)   miss="$miss  $r:$ln $name ($det)"$'\n' ;;
      elsewhere) elsew="$elsew  $r:$ln $name $det"$'\n' ;;
      ignored)   ign="$ign  $r:$ln $name"$'\n' ;;
      skip)      skipped="$skipped  $r:$ln $name ($det)"$'\n' ;;
    esac
  done < <(bare_names "$r")
  # cd targets: the directory (after stripping ./ and ../) must exist somewhere in the tracked tree.
  while IFS=: read -r ln tok; do
    d="$(printf '%s' "${tok#cd }" | sed -E 's#^(\.\.?/)+##; s#/$##')"
    case "$d" in ''|.|..|-*|/*|~*) continue ;; esac
    [ -d "$d" ] && continue
    git ls-files | grep -qE "(^|/)$(printf '%s' "$d" | sed 's/[.[\*^$()+?{|]/\\&/g')/" \
      || miss="$miss  $r:$ln $tok (no such directory anywhere in the repo)"$'\n'
  done < <(grep -noE '(^|[[:space:]`;&(])cd [A-Za-z0-9_./-]+' "$r" | sed -E 's/:[^c]*cd /:cd /')
done
echo "readme_paths_missing (path-like refs in README/CONTRIBUTING that resolve nowhere; strongest stale-doc evidence):"
printf '%s' "$miss" | head -15
echo "readme_paths_elsewhere (not at the literal path, but a tracked file ends with it; check whether the doc means a subdirectory before citing):"
printf '%s' "$elsew" | head -10
echo "readme_paths_ignored (gitignored generated/runtime outputs; not defects):"
printf '%s' "$ign" | head -10
echo "readme_tokens_skipped (slash tokens judged not to be repo paths: model IDs, packages, domains, versions; first 5):"
printf '%s' "$skipped" | head -5
echo "lockfiles:"
git ls-files | grep -E '(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock|go\.sum|poetry\.lock|uv\.lock|Pipfile\.lock|Gemfile\.lock|composer\.lock|bun\.lockb?)$' | sed 's/^/  /'
echo "absolute_paths_in_tracked_text (first 10):"
git grep -nIE '(/Users/[A-Za-z]|/home/[a-z][a-z0-9_-]+/|[A-Z]:\\\\Users\\\\)' -- ':!*.lock' ':!*lock.json' 2>/dev/null | head -10 | cut -c1-160 | sed 's/^/  /'
