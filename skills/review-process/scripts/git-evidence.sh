#!/usr/bin/env bash
# Read-only git and layout evidence for review-process.
# Usage: git-evidence.sh [repo-path] [sample-size]
#        git-evidence.sh [repo-path] --verify <sha>...
# Prints counts the rubric uses; never writes, fetches, or calls a network API.
# --verify prints one line per sha (ok or UNRESOLVED) and exits 1 if any is unresolved.
set -u
# No pipefail: several pipelines end in head, which would turn complete output into exit 141.

repo=""; n=""; verify=0
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --verify) verify=1; shift; break ;;
    -*) echo "error: unknown option $1 (see --help)" >&2; exit 2 ;;
    *)
      if [ -z "$repo" ]; then repo="$1"
      elif [ -z "$n" ]; then n="$1"
      else echo "error: unexpected argument $1 (see --help)" >&2; exit 2
      fi
      shift ;;
  esac
done
repo="${repo:-.}"; n="${n:-100}"
case "$n" in ''|*[!0-9]*|0) echo "error: sample-size must be a positive integer, got $n" >&2; exit 2 ;; esac
cd "$repo" 2>/dev/null || { echo "error: cannot cd to $repo" >&2; exit 1; }

# Print stdin, at most $1 lines, then how many were left out.
cap() { awk -v n="$1" 'NR<=n {print} END {if (NR>n) print "  (+" NR-n " more)"}'; }

if [ "$verify" = 1 ]; then
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "error: $repo is not a git repository" >&2; exit 1; }
  [ $# -gt 0 ] || { echo "error: --verify needs at least one sha" >&2; exit 2; }
  bad=0; lines=""
  for s in "$@"; do
    if printf '%s' "$s" | grep -qE '^[0-9a-fA-F]{4,40}$' \
       && git rev-parse --verify --quiet "$s^{commit}" >/dev/null 2>&1; then
      lines="$lines  ok $s $(git log -1 --format='%cs %s' "$s" | cut -c1-80)"$'\n'
    else
      bad=$((bad + 1)); lines="$lines  UNRESOLVED $s"$'\n'
    fi
  done
  echo "verify: $# checked, $bad unresolved"
  printf '%s' "$lines"
  if [ "$bad" -gt 0 ] && [ "$(git rev-parse --is-shallow-repository 2>/dev/null)" = true ]; then
    echo "note: shallow clone; a sha older than the fetched history cannot resolve"
  fi
  [ "$bad" -eq 0 ]; exit $?
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "git: not a git repository (history-based items are N/A)"
  exit 0
fi

root="$(git rev-parse --show-toplevel)"
cd "$root" || exit 1
echo "repo_root: $root"
if ! git rev-parse --verify --quiet HEAD >/dev/null; then
  echo "git: repository has no commits (history-based items are N/A)"
  exit 0
fi
shallow="$(git rev-parse --is-shallow-repository 2>/dev/null || echo unknown)"
echo "shallow: $shallow"
[ "$shallow" = true ] && echo "note: shallow clone; history, tag, and PR counts cover fetched commits only (treat as N/A)"

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
# One window of $n first-parent commits; a merge has more than one parent.
fp_window="$(git log --first-parent -n "$n" --format='%P%x09%s' "$default")"
fp_merges="$(printf '%s\n' "$fp_window" | awk -F'\t' '$1 ~ / / {sub(/^[^\t]*\t/, ""); print}')"
fp_direct="$(printf '%s\n' "$fp_window" | awk -F'\t' 'NF && $1 !~ / / {sub(/^[^\t]*\t/, ""); print}')"
pr_merges="$(printf '%s\n' "$fp_merges" | grep -cE '^Merge (pull request|branch .* into)|^Merge .*#[0-9]+')"
squash_prs="$(printf '%s\n' "$fp_direct" | grep -cE '\(#[0-9]+\)$')"
direct_total="$(printf '%s\n' "$fp_direct" | grep -c .)"
fp_total="$(printf '%s\n' "$fp_window" | grep -c .)"
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
echo "== releases =="
tags="$(git tag --list)"
tag_n="$(printf '%s\n' "$tags" | grep -c .)"
echo "tags: $tag_n"
if [ "$tag_n" -gt 0 ]; then
  newest="$(git for-each-ref --sort=-version:refname --sort=-creatordate --count=1 --format='%(refname:short)' refs/tags)"
  echo "newest_tag: $newest $(git for-each-ref --format='%(creatordate:short)' "refs/tags/$newest")"
  echo "commits_since_newest_tag: $(git rev-list --count "refs/tags/$newest..$default" 2>/dev/null || echo unknown)"
  sem='[0-9]+\.[0-9]+\.[0-9]+'
  t_v="$(printf '%s\n' "$tags" | grep -cE "^v$sem")"
  t_bare="$(printf '%s\n' "$tags" | grep -cE "^$sem")"
  t_any="$(printf '%s\n' "$tags" | grep -cE "$sem")"
  echo "tag_style: v_semver $t_v, bare_semver $t_bare, prefixed_semver $(( t_any - t_v - t_bare )), other $(( tag_n - t_any ))"
fi
changelogs="$(git -c core.quotePath=false ls-files \
  | grep -iE '(^|/)(changelog|changes|history|releases|release[-_]notes|news)(\.(md|rst|txt|adoc))?$' \
  | awk -F/ '{print NF "\t" $0}' | LC_ALL=C sort -t"$(printf '\t')" -k1,1n -k2,2 | cut -f2-)"
echo "changelogs: $(printf '%s\n' "$changelogs" | grep -c .) (shallowest 3; newest version heading)"
printf '%s\n' "$changelogs" | grep . | head -3 | while IFS= read -r c; do
  awk -v f="$c" '
    /^##[ \t]/ { if (!fb) { fb = NR; fbt = $0 } if ($0 ~ /[0-9]/) { hit = NR; hitt = $0; exit } }
    END {
      if (hit) printf "  %s:%d %s\n", f, hit, substr(hitt, 1, 80)
      else if (fb) printf "  %s:%d %s (no version heading)\n", f, fb, substr(fbt, 1, 80)
      else printf "  %s (no ## heading)\n", f
    }' "$c"
done

echo
echo "== top level (type name) =="
{
  git -c core.quotePath=false ls-files -s | awk -F'\t' '
    { split($1, m, " "); k = split($2, p, "/")
      if (k > 1) d[p[1]]++
      else t[p[1]] = (m[1] == "120000" ? "link" : (m[1] == "160000" ? "submodule" : "file")) }
    END { for (x in d) print x "/\tdir\t" d[x]; for (x in t) print x "\t" t[x] "\t" }'
  git -c core.quotePath=false ls-files --others --exclude-standard --directory \
    | awk -F/ '{print $1 (NF > 1 ? "/" : "") "\tuntracked\t"}'
} | LC_ALL=C sort -u | awk -F'\t' '!seen[$1]++ {printf "  %s %s%s\n", $2, $1, ($3 != "" ? " (" $3 " tracked files)" : "")}' | cap 40

echo
manifests="$(git -c core.quotePath=false ls-files | awk '
  function base(p,   a, k) { k = split(p, a, "/"); return a[k] }
  function dirof(p) { return (p ~ /\//) ? substr(p, 1, length(p) - length(base(p)) - 1) : "." }
  function locks_for(b) {
    if (b == "package.json") return "package-lock.json yarn.lock pnpm-lock.yaml bun.lock bun.lockb npm-shrinkwrap.json"
    if (b == "pyproject.toml") return "uv.lock poetry.lock pdm.lock"
    if (b == "Pipfile") return "Pipfile.lock"
    if (b == "Cargo.toml") return "Cargo.lock"
    if (b == "go.mod") return "go.sum"
    if (b == "Gemfile") return "Gemfile.lock"
    if (b == "composer.json") return "composer.lock"
    if (b == "mix.exs") return "mix.lock"
    if (b == "pubspec.yaml") return "pubspec.lock"
    if (b == "build.gradle" || b == "build.gradle.kts") return "gradle.lockfile"
    return ""
  }
  { have[$0] = 1
    if ($0 ~ /(^|\/)(node_modules|vendor|third_party)\//) next
    b = base($0)
    if (locks_for(b) != "") man[$0] = b
    else if (b ~ /^requirements.*\.txt$/) req[$0] = 1 }
  END {
    for (m in man) {
      k = split(locks_for(man[m]), L, " "); d = dirof(m); found = ""; where = d
      while (1) {
        for (i = 1; i <= k; i++) {
          cand = (where == "." ? "" : where "/") L[i]
          if (cand in have) { found = cand; break }
        }
        if (found != "" || where == ".") break
        where = dirof(where)
      }
      if (found == "") print "0\t" m "\tNO LOCKFILE"
      else if (where == d) print "1\t" m "\t" base(found)
      else print "1\t" m "\t" found " (ancestor directory)"
    }
    for (r in req) {
      tot = 0; pin = 0
      while ((getline line < r) > 0) {
        if (line ~ /^[ \t]*($|#|-)/) continue
        tot++; if (line ~ /==|@ /) pin++
      }
      close(r)
      print "1\t" r "\tpinned " pin " of " tot " requirements"
    }
  }' | LC_ALL=C sort)"
echo "== manifests ($(printf '%s\n' "$manifests" | grep -c .) tracked; without_lockfile $(printf '%s\n' "$manifests" | grep -c '^0') listed first) =="
printf '%s\n' "$manifests" | grep . | awk -F'\t' '{print "  " $2 ": " $3}' | cap 20

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
echo "absolute_paths_in_tracked_text (first 10):"
git grep -nIE '(/Users/[A-Za-z]|/home/[a-z][a-z0-9_-]+/|[A-Z]:\\\\Users\\\\)' -- ':!*.lock' ':!*lock.json' 2>/dev/null | head -10 | cut -c1-160 | sed 's/^/  /'
