#!/usr/bin/env bash
# Install skills by symlinking src/* into detected AI tool config directories
#
# Usage:
#   install-skills.sh
#     Auto-detect installed tools and symlink skills to each
#
#   install-skills.sh SOURCE_DIR
#     Use SOURCE_DIR instead of script's parent directory
#
set -euo pipefail

detect_tool_configs() {
  local configs=()
  
  # Claude.app desktop
  [[ -d ~/.config/Claude ]] && configs+=("$HOME/.config/Claude/skills")
  
  # Cursor.app
  [[ -d ~/.config/Cursor ]] && configs+=("$HOME/.config/Cursor/skills")
  
  # opencode
  [[ -d ~/.config/opencode ]] && configs+=("$HOME/.config/opencode/skills")
  
  # Zed agents
  [[ -d ~/.agents ]] && configs+=("$HOME/.agents/skills")
  
  printf '%s\n' "${configs[@]}"
}

symlink_skills() {
  local source_dir="$1"
  local dest_dir="$2"
  
  if [[ ! -d "$source_dir/src" ]]; then
    echo "Error: $source_dir/src not found" >&2
    exit 1
  fi
  
  mkdir -p "$dest_dir"
  
  local count=0
  for skill in "$source_dir/src"/*/; do
    [[ -d "$skill" ]] || continue
    local name
    name="$(basename "$skill")"
    ln -sf "$(cd "$skill" && pwd)" "$dest_dir/$name"
    count=$((count + 1))
  done
  
  echo "✓ Installed $count skills to $dest_dir"
}

main() {
  local source_dir
  
  if [[ $# -eq 0 ]]; then
    # Default: use script's parent directory
    source_dir="$(cd "$(dirname "$0")/.." && pwd)"
  elif [[ $# -eq 1 ]]; then
    source_dir="$(cd "$1" && pwd)"
  else
    echo "Usage: $0 [SOURCE_DIR]" >&2
    echo "" >&2
    echo "  SOURCE_DIR   Repo root containing src/ (default: script's parent dir)" >&2
    exit 1
  fi
  
  # Store detected configs
  local configs_output
  configs_output="$(detect_tool_configs)"
  
  if [[ -z "$configs_output" ]]; then
    echo "No AI tool configs detected. Checked:" >&2
    echo "  ~/.config/Claude" >&2
    echo "  ~/.config/Cursor" >&2
    echo "  ~/.config/opencode" >&2
    echo "  ~/.agents (Zed)" >&2
    exit 1
  fi
  
  echo "Detected tools:"
  echo "$configs_output" | sed 's/^/  /'
  echo ""
  
  echo "$configs_output" | while IFS= read -r dest_dir; do
    [[ -n "$dest_dir" ]] || continue
    symlink_skills "$source_dir" "$dest_dir"
  done
}

main "$@"
