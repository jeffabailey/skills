---
name: version-skills
description: Versions agent skills. Raises metadata.version in each changed SKILL.md and the plugin version in plugin.json and .claude-plugin/plugin.json together, using a bundled script, then proves that nothing changed without a version rise. Use when the user says /version-skills, asks to bump, add, or check skill versions, when a repo's AGENTS.md or CLAUDE.md asks for skill versions to rise, or before committing a change to a repo of skills. For tagging a release of an application, use a release skill instead.
metadata:
  version: "1.0.0"
---

# Version Skills

A skill's version lives in its frontmatter, quoted, under `metadata`. The Agent Skills spec has no top-level `version` key, and `metadata` values are strings.

```yaml
metadata:
  version: "1.0.0"
```

Any change inside a skill's directory, `references/` and `scripts/` included, raises its version. Claude Code delivers a plugin update only when the plugin's `version` rises, so the plugin version rises with it. When a repo has both `plugin.json` and `.claude-plugin/plugin.json`, both must match.

## Workflow

Run these from the repo that holds the skills, after the edits are finished. Commit only if the user asks.

1. **See what changed.** Run `check` and read `git diff --stat -- skills`:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/skill_version.py" check
   ```

   On a branch, add `--base main`. A repo adopting versions for the first time reports every skill as missing one; go to step 3 and use `--all`.

2. **Pick one level** from the table, the highest that any changed skill needs.

   | Level | The caller sees | Examples |
   |-------|-----------------|----------|
   | `major` | Something breaks | Skill renamed or removed, a mode dropped, a contract another skill or command depends on changed |
   | `minor` | Something new | New mode, framework, rubric, or trigger |
   | `patch` | Same or fixed behavior | Wording, reference update, bug fix |

3. **Bump.** With no names it takes every skill that differs from HEAD. Name skills to narrow it, or name a deleted skill to record its removal:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/skill_version.py" bump <level>
   python3 "${CLAUDE_SKILL_DIR}/scripts/skill_version.py" bump <level> <skill> [<skill> ...]
   python3 "${CLAUDE_SKILL_DIR}/scripts/skill_version.py" bump minor --all
   ```

   Skills new to versioning start at `1.0.0`. Reruns before a commit compute from HEAD, so they land on the same version. Raising a level is safe too: the highest result wins. Pass `--skills-dir <path>` before the subcommand when skills live somewhere other than `skills/`.

4. **Verify.** Run `check` again. The step is done when it exits 0 and every skill and manifest it covers carries a valid version.

5. **Report** each new version and the level, with one line on why that level fit.

Vendored skills stay as their upstream shipped them. They normally live outside `skills/`, such as in `.agents/`, where neither command reaches them.
