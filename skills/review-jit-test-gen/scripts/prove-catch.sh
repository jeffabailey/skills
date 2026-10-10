#!/usr/bin/env bash
# Prove that new tests catch a change: run the test command on the changed
# code, then on a broken version (the parent commit's copy of the changed
# files, or the change plus a mutant patch), then restore the working tree.
#
# Usage:
#   prove-catch.sh [--base REF | --mutant PATCH] --file PATH [--file PATH ...] -- TEST_CMD...
#
#   --file PATH    a changed source file (repeat per file). Never pass test files.
#   --base REF     broken version = PATH as it is at REF (default: HEAD).
#                  A PATH that does not exist at REF is removed for the run.
#   --mutant PATCH broken version = working tree with PATCH applied (git apply).
#
# Prints both exit codes and the log paths, then a verdict line:
#   VERDICT: CATCHES   tests pass on the change and fail on the broken version
#   VERDICT: NO-CATCH  tests pass on both (they do not detect the change)
#   VERDICT: RED       tests fail on the change itself (fix them, or treat them
#                      as catching tests that flag a possible bug in the diff)
# Exit status: 0 for CATCHES, 1 otherwise, 2 for usage errors.
#
# The working tree is always restored from a backup, including on Ctrl-C.
# If the script is killed with SIGKILL, the backup directory it printed holds
# the original files.

set -euo pipefail

usage() { sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

base="HEAD"
mutant=""
files=()
while [ $# -gt 0 ]; do
  case "$1" in
    --base) base="${2:?--base needs a ref}"; shift 2 ;;
    --mutant) mutant="${2:?--mutant needs a patch file}"; shift 2 ;;
    --file) files+=("${2:?--file needs a path}"); shift 2 ;;
    --) shift; break ;;
    -h|--help) usage ;;
    *) echo "unknown option: $1" >&2; usage ;;
  esac
done
[ $# -gt 0 ] || { echo "missing test command after --" >&2; usage; }
[ "${#files[@]}" -gt 0 ] || [ -n "$mutant" ] || { echo "need --file or --mutant" >&2; usage; }

top="$(git rev-parse --show-toplevel)"
cd "$top"
if [ -n "$mutant" ]; then
  mutant="$(cd "$(dirname "$mutant")" && pwd)/$(basename "$mutant")"
  # Back up every file the mutant touches as well as any --file paths.
  while IFS= read -r p; do files+=("$p"); done < <(git apply --numstat "$mutant" | cut -f3)
fi

tmp="${TMPDIR:-/tmp}"
work="$(mktemp -d "${tmp%/}/prove-catch.XXXXXX")"
echo "backup: $work/backup"
mkdir -p "$work/backup"
for f in "${files[@]}"; do
  if [ -e "$f" ]; then
    mkdir -p "$work/backup/$(dirname "$f")"
    cp -p "$f" "$work/backup/$f"
  else
    echo "$f" >> "$work/absent"
  fi
done

restore() {
  for f in "${files[@]}"; do
    if [ -e "$work/backup/$f" ]; then
      cp -p "$work/backup/$f" "$f"
    elif [ -f "$work/absent" ] && grep -qxF "$f" "$work/absent"; then
      rm -f "$f"
    fi
  done
}
trap restore EXIT INT TERM

set +e
"$@" > "$work/on-change.log" 2>&1
on_change=$?
set -e

if [ -n "$mutant" ]; then
  git apply "$mutant"
else
  for f in "${files[@]}"; do
    if git cat-file -e "$base:$f" 2>/dev/null; then
      git show "$base:$f" > "$f"
    else
      rm -f "$f"
    fi
  done
fi

set +e
"$@" > "$work/on-broken.log" 2>&1
on_broken=$?
set -e

restore
trap - EXIT INT TERM

echo "on change:  exit $on_change  log: $work/on-change.log"
echo "on broken:  exit $on_broken  log: $work/on-broken.log  ($([ -n "$mutant" ] && echo "mutant $mutant" || echo "files at $base"))"
if [ "$on_change" -ne 0 ]; then
  echo "VERDICT: RED"; exit 1
elif [ "$on_broken" -ne 0 ]; then
  echo "VERDICT: CATCHES"; exit 0
else
  echo "VERDICT: NO-CATCH"; exit 1
fi
