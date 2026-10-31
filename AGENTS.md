# Agent Instructions

## Skill versioning

Any change inside a skill's directory under `skills/`, `references/` and `scripts/` included, raises that skill's version. Use the `version-skills` skill from the `jbb-skills` plugin (`jbb-skills:version-skills`) before committing; it covers the level, the bump, and the proof. Done means its `check` exits 0.

If that skill is unavailable, make the same change by hand:

- Raise the quoted `metadata.version` in each changed `SKILL.md`. A new skill starts at `1.0.0`.
- Raise `version` to the same value in `plugin.json` and `.claude-plugin/plugin.json`, or Claude Code will not deliver the update.
- Use **major** when a caller breaks, **minor** for a new capability, and **patch** for fixes and wording.

Skills in `.agents/` are vendored and pinned by hash in `skills-lock.json`. Leave them unversioned.
