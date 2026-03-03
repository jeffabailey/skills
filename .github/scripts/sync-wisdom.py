#!/usr/bin/env python3
"""Sync wisdom content from blog posts into skill reference files.

Reads skill-sources.json, fetches LLM-optimized content from each
blog post, and writes references/wisdom.md for each skill.

Usage:
    python3 .github/scripts/sync-wisdom.py [--dry-run] [--skill SKILL]
"""

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def fetch_llm_content(base_url: str, url_path: str) -> str:
    """Fetch the LLM-optimized content for a blog post."""
    url_path = url_path.rstrip("/")
    llm_url = f"{base_url}{url_path}/llm.txt"

    try:
        req = urllib.request.Request(
            llm_url,
            headers={"User-Agent": "skills-sync-wisdom/1.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  WARNING: Failed to fetch {llm_url}: {e}", file=sys.stderr)
        return ""


def generate_wisdom(
    fetch_base_url: str, canonical_base_url: str, posts: list
) -> str:
    """Generate wisdom.md content from a list of blog posts."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        "# Domain Knowledge Reference",
        "",
        "Auto-generated from blog posts. Do not edit manually.",
        f"Last updated: {now}",
    ]

    for post in posts:
        slug = post["slug"]
        url = post["url"]
        content = fetch_llm_content(fetch_base_url, url)
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## Source: {slug}")
        lines.append("")
        lines.append(f"URL: {canonical_base_url}{url}")
        lines.append("")
        if content:
            lines.append(content)
        else:
            lines.append("Failed to fetch content.")
        lines.append("")

    return "\n".join(lines)


def strip_date_line(text: str) -> str:
    """Remove the 'Last updated:' line for content comparison."""
    return "\n".join(
        line for line in text.splitlines() if not line.startswith("Last updated:")
    )


def main():
    parser = argparse.ArgumentParser(
        description="Sync wisdom content from blog posts into skill reference files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files.",
    )
    parser.add_argument(
        "--skill",
        help="Sync only this skill (e.g. review-maintainability).",
    )
    parser.add_argument(
        "--base-url",
        help="Override the base URL from skill-sources.json (e.g. http://localhost:8765).",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent.parent
    config_path = root / "skill-sources.json"

    with open(config_path) as f:
        config = json.load(f)

    canonical_base_url = config["baseUrl"]
    fetch_base_url = args.base_url or canonical_base_url
    changed = []
    skipped = []
    failed = []

    for skill_name, skill_config in config["skills"].items():
        if args.skill and skill_name != args.skill:
            continue

        posts = skill_config.get("posts", [])
        if not posts:
            print(f"  SKIP: {skill_name} (no posts configured)")
            skipped.append(skill_name)
            continue

        print(f"  SYNC: {skill_name} ({len(posts)} post(s))")

        wisdom_content = generate_wisdom(fetch_base_url, canonical_base_url, posts)
        wisdom_path = root / "src" / skill_name / "references" / "wisdom.md"

        # Check for fetch failures
        if "Failed to fetch content." in wisdom_content:
            failed.append(skill_name)

        # Compare ignoring the date line
        existing = ""
        if wisdom_path.exists():
            existing = wisdom_path.read_text()

        if strip_date_line(existing) == strip_date_line(wisdom_content):
            print(f"    No changes for {skill_name}")
            continue

        if args.dry_run:
            print(f"    Would update {wisdom_path}")
        else:
            wisdom_path.parent.mkdir(parents=True, exist_ok=True)
            wisdom_path.write_text(wisdom_content)
            print(f"    Updated {wisdom_path}")

        changed.append(skill_name)

    action = "Would change" if args.dry_run else "Changed"
    print(f"\n{action}: {len(changed)} skill(s)")
    if skipped:
        print(f"Skipped: {len(skipped)} skill(s) (no posts)")
    if failed:
        print(f"Fetch failures in: {', '.join(failed)}")

    # Exit 0 if no changes, 1 if changes were made (useful for CI)
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
