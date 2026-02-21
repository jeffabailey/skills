# Code Review Skills

Reusable skills for architectural fitness analysis, JIT test generation, and full code review. Use in **Cursor**, **Claude Code**, **GitHub Actions**, or anywhere you run AI-assisted code review.

## Skills

| Skill | Purpose |
|-------|---------|
| `review-arch-fitness` | Score codebase architecture (coupling, cohesion, testability, layering, etc.) |
| `review-jit-test-gen` | Suggest JIT catching tests for changed code |
| `review-full` | Orchestrator: runs arch-fitness + jit-test-gen + security review |

## Installation

### Cursor / Claude Code

Install into your project or personal skills directory:

**Option A: Clone and symlink**
```bash
git clone https://github.com/jeffabailey/skills.git
ln -s $(pwd)/skills/review-arch-fitness ~/.cursor/skills/review-arch-fitness
ln -s $(pwd)/skills/review-jit-test-gen ~/.cursor/skills/review-jit-test-gen
ln -s $(pwd)/skills/review-full ~/.cursor/skills/review-full
```

**Option B: Copy into project**
```bash
mkdir -p .cursor/skills
cp -r /path/to/skills/review-arch-fitness .cursor/skills/
cp -r /path/to/skills/review-jit-test-gen .cursor/skills/
cp -r /path/to/skills/review-full .cursor/skills/
```

**Option C: Codex skill installer** (if using Codex)
```bash
scripts/install-skill-from-github.py --repo jeffabailey/skills --path review-arch-fitness review-jit-test-gen review-full
```

### Slash Commands (Claude Code / Cursor)

To map slash commands to these skills, create `.claude/commands/review/` in your project:

```
.claude/commands/review/
├── arch-fitness.md   → points to /review:arch-fitness
├── jit-test-gen.md   → points to /review:jit-test-gen
└── full-review.md    → points to /review:full-review
```

Each command file can simply invoke the skill by referencing it, or copy the skill instructions. See [canzan-infrastructure](https://github.com/canzan/canzan-infrastructure) for an example.

### GitHub Actions (Reusable Workflow)

The [reusable-workflows](https://github.com/jeffabailey/reusable-workflows) repo provides `claude-code-review.yml` which runs these reviews on PRs. The `prompts/` folder in this repo contains CI-ready prompt text; workflows can checkout this repo and pass the file contents to the Claude Code Action. The reusable workflow keeps inline prompts in sync with these skills.

## License

Unlicense (public domain)
