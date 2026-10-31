#!/usr/bin/env python3
"""Keep each skill's metadata.version and the plugin version moving together.

Run from inside the repo that holds the skills:

  skill_version.py bump {patch,minor,major} [SKILL ...] [--all]
  skill_version.py check [--base REF]

bump works on the named skills, on every skill with --all, or by default on the
skills that differ from HEAD. It computes from the version at HEAD, so rerunning
it before a commit does not bump twice. A skill with no version at HEAD starts at
1.0.0. The version in each plugin manifest rises by the same level, once per run.
Name a deleted skill to raise the plugin version for its removal.

check fails when a skill or manifest has no valid version, when the manifests
disagree, or when anything under the skills directory differs from REF without a
matching rise in that skill's version and the plugin version.

Standard library only. It edits text in place so frontmatter keeps its layout.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

INITIAL_VERSION = "1.0.0"
MANIFEST_NAMES = ("plugin.json", ".claude-plugin/plugin.json")

SEMVER = re.compile(r"\d+\.\d+\.\d+")
FRONTMATTER = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)
METADATA_VERSION = re.compile(r'^(metadata:\n(?:  .*\n)*?  version: )"?([^"\n]*)"?$', re.MULTILINE)
MANIFEST_VERSION = re.compile(r'("version":\s*")[^"]*(")')


def semver_key(version):
    if not SEMVER.fullmatch(version):
        raise ValueError(f"not a MAJOR.MINOR.PATCH version: {version!r}")
    return tuple(int(part) for part in version.split("."))


def bumped(version, level):
    major, minor, patch = semver_key(version)
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def skill_version(text):
    frontmatter = FRONTMATTER.match(text or "")
    found = frontmatter and METADATA_VERSION.search(frontmatter.group(1))
    return found.group(2) if found else None


def with_skill_version(text, version):
    frontmatter = FRONTMATTER.match(text)
    if not frontmatter:
        raise ValueError("SKILL.md has no YAML frontmatter")
    head, end = frontmatter.group(1), frontmatter.end(1)
    line = f'  version: "{version}"\n'
    if METADATA_VERSION.search(head):
        head = METADATA_VERSION.sub(lambda m: f'{m.group(1)}"{version}"', head, count=1)
    elif re.search(r"^metadata:\n", head, re.MULTILINE):
        head = re.sub(r"^metadata:\n", lambda m: m.group(0) + line, head, count=1, flags=re.MULTILINE)
    else:
        head += f"metadata:\n{line}"
    return f"---\n{head}{text[end:]}"


def manifest_version(text):
    return json.loads(text)["version"]


def write_if_changed(path, old, new):
    if new != old:
        path.write_text(new)


class Repo:
    def __init__(self, skills_dir):
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if result.returncode != 0:
            raise ValueError("run this inside a git repository")
        self.root = Path(result.stdout.strip())
        self.skills = self.root / skills_dir
        self.manifests = [self.root / name for name in MANIFEST_NAMES if (self.root / name).is_file()]
        if not self.skills.is_dir():
            raise ValueError(f"no skills directory at {self.skills}")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)

    def show(self, ref, path):
        """Return the file's text at ref, or None if it does not exist there."""
        result = self.git("cat-file", "blob", f"{ref}:{path.relative_to(self.root).as_posix()}")
        return result.stdout if result.returncode == 0 else None

    def changed_paths(self, base):
        """Return changed paths relative to the skills directory."""
        skills = self.skills.relative_to(self.root).as_posix()
        result = self.git("diff", "--name-only", "--no-renames", base, "--", skills)
        if result.returncode != 0:
            raise ValueError(result.stderr.strip())
        untracked = self.git("ls-files", "--others", "--exclude-standard", "--", skills).stdout
        return {Path(line).relative_to(skills) for line in (result.stdout + untracked).splitlines()}


def changed_skills(paths):
    return sorted({path.parts[0] for path in paths if len(path.parts) > 1})


def bump(repo, level, names, every):
    if every:
        names = sorted(path.parent.name for path in repo.skills.glob("*/SKILL.md"))
    elif not names:
        names = changed_skills(repo.changed_paths("HEAD"))
    if not names:
        print("nothing to bump: no skill differs from HEAD")
        return

    targets = []
    for name in names:
        path = repo.skills / name / "SKILL.md"
        if path.is_file():
            targets.append((name, path))
        elif repo.show("HEAD", path) is None:
            raise ValueError(f"no such skill: {name}")

    for name, path in targets:
        text = path.read_text()
        current = skill_version(text)
        base = skill_version(repo.show("HEAD", path))
        if base is None:
            target = current or INITIAL_VERSION
        else:
            target = max(current or base, bumped(base, level), key=semver_key)
        write_if_changed(path, text, with_skill_version(text, target))
        print(f"{name}: {target}")

    if repo.manifests:
        texts = {path: path.read_text() for path in repo.manifests}
        target = "0.0.0"
        for path, text in texts.items():
            base = manifest_version(repo.show("HEAD", path) or text)
            target = max(target, manifest_version(text), bumped(base, level), key=semver_key)
        for path, text in texts.items():
            write_if_changed(path, text, MANIFEST_VERSION.sub(rf"\g<1>{target}\g<2>", text, count=1))
        print(f"plugin: {target}")


def check(repo, base):
    errors = []

    plugin_versions = {manifest_version(path.read_text()) for path in repo.manifests}
    if len(plugin_versions) > 1:
        errors.append(f"manifests disagree: {sorted(plugin_versions)}")

    for path in sorted(repo.skills.glob("*/SKILL.md")):
        version = skill_version(path.read_text())
        if version is None or not SEMVER.fullmatch(version):
            errors.append(f"{path.parent.name}: metadata.version is {version!r}, want MAJOR.MINOR.PATCH")

    changed = repo.changed_paths(base)
    for name in changed_skills(changed):
        path = repo.skills / name / "SKILL.md"
        now = skill_version(path.read_text()) if path.is_file() else None
        before = skill_version(repo.show(base, path))
        if now and before and SEMVER.fullmatch(now) and semver_key(now) <= semver_key(before):
            errors.append(f"{name}: changed since {base} but still at {now}")

    if changed and len(plugin_versions) == 1:
        plugin = next(iter(plugin_versions))
        before = repo.show(base, repo.manifests[0])
        if before and semver_key(plugin) <= semver_key(manifest_version(before)):
            errors.append(f"plugin: skills changed since {base} but still at {plugin}")

    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print(f"ok: {len(changed)} changed file(s) under {repo.skills.name}/ since {base}")
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description="Bump or check skill and plugin versions.")
    parser.add_argument("--skills-dir", default="skills", help="skills directory, relative to the repo root")
    commands = parser.add_subparsers(dest="command", required=True)
    bump_parser = commands.add_parser("bump", help="raise skill versions and the plugin version")
    bump_parser.add_argument("level", choices=("patch", "minor", "major"))
    bump_parser.add_argument("skills", nargs="*", metavar="SKILL", help="default: skills that differ from HEAD")
    bump_parser.add_argument("--all", action="store_true", help="every skill, for first-time adoption")
    check_parser = commands.add_parser("check", help="fail when versions are missing or did not rise")
    check_parser.add_argument("--base", default="HEAD", help="git ref to compare against (default: HEAD)")
    args = parser.parse_args()

    try:
        repo = Repo(args.skills_dir)
        if args.command == "bump":
            bump(repo, args.level, args.skills, args.all)
            return 0
        return check(repo, args.base)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
