#!/usr/bin/env bash
# Install project fitness review skills by symlinking src/* into a destination
# directory (e.g. ~/.claude/skills or ~/.cursor/skills).
#
# Usage:
#   install-skills.sh SOURCE_DIR DEST_DIR
#     Symlink SOURCE_DIR/src/* into DEST_DIR. Use when the repo is already
#     present (e.g. after checkout in CI or existing clone).
#
#   install-skills.sh --clone CLONE_PATH DEST_DIR [REPO_URL]
#     If CLONE_PATH exists, remove it (so clone works when the repo was moved).
#     Clone REPO_URL into CLONE_PATH, then symlink CLONE_PATH/src/* into DEST_DIR.
#     Default REPO_URL: https://github.com/jeffabailey/skills.git
#
set -euo pipefail

REPO_URL_DEFAULT="https://github.com/jeffabailey/skills.git"

usage() {
  echo "Usage: $0 SOURCE_DIR DEST_DIR" >&2
  echo "   or: $0 --clone CLONE_PATH DEST_DIR [REPO_URL]" >&2
  echo "" >&2
  echo "  SOURCE_DIR   Repo root containing src/ (e.g. \$GITHUB_WORKSPACE or ~/Projects/skills)" >&2
  echo "  DEST_DIR     Where to create symlinks (e.g. ~/.claude/skills or ~/.cursor/skills)" >&2
  echo "  CLONE_PATH   Directory to clone into; removed first if it exists" >&2
  echo "  REPO_URL     Git URL (default: $REPO_URL_DEFAULT)" >&2
  exit 1
}

symlink_skills() {
  local source_dir dest_dir
  source_dir="$(cd "$1" && pwd)"
  dest_dir="$2"

  if [[ ! -d "$source_dir/src" ]]; then
    echo "Error: $source_dir/src not found" >&2
    exit 1
  fi

  mkdir -p "$dest_dir"
  for skill in "$source_dir/src"/*/; do
    [[ -d "$skill" ]] || continue
    name="$(basename "$skill")"
    ln -sf "$(cd "$skill" && pwd)" "$dest_dir/$name"
  done
  echo "Installed skills from $source_dir/src into $dest_dir"
}

if [[ $# -lt 2 ]]; then
  usage
fi

if [[ "$1" == "--clone" ]]; then
  if [[ $# -lt 3 ]]; then
    usage
  fi
  clone_path="$2"
  dest_dir="$3"
  repo_url="${4:-$REPO_URL_DEFAULT}"
  if [[ -d "$clone_path" ]]; then
    echo "Removing existing $clone_path (e.g. repo was moved)"
    rm -rf "$clone_path"
  fi
  git clone "$repo_url" "$clone_path"
  symlink_skills "$clone_path" "$dest_dir"
else
  symlink_skills "$1" "$2"
fi
