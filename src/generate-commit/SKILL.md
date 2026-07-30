---
name: generate-commit
description: Generate a conventional commit message from staged changes, review before committing
---

# Generate Commit

Generate a commit message for staged changes following this project's conventional commit style.

## Workflow

### Step 1: Discover and apply the project's style guidance

Style tooling is language-specific, so **do not assume any particular formatter**. Instead, discover what this project uses:

1. **Detect the project's language and formatter/linter** by inspecting the repository root for its manifest and tooling config. Common signals:
   - Python: `pyproject.toml` / `ruff.toml` / `setup.cfg` → `ruff format --check .`, `black --check .`, or `flake8`
   - JavaScript/TypeScript: `package.json`, `.prettierrc`, `eslint.config.*` → `npx prettier --check .`, `npm run lint`
   - Go: `go.mod` → `gofmt -l .`, `go vet ./...`
   - Rust: `Cargo.toml` → `cargo fmt --check`, `cargo clippy`
   - Java/Kotlin: `pom.xml` / `build.gradle` → `mvn spotless:check`, `./gradlew spotlessCheck`
   - Ruby: `Gemfile` / `.rubocop.yml` → `rubocop`
   - If a `Makefile`/`justfile` exposes a `format`, `lint`, or `check` target, prefer that.
   - Respect a project-specific runner if present (e.g. `uv run`, `poetry run`, `pdm run`, `npm run`, `pnpm`, `yarn`).

2. **Run the discovered format/lint check** (the check-only variant). If it fails, fix formatting before proceeding. If **no** style tooling can be found, note that and continue without it — do not invent a command.

3. **Hold the resolved style command in memory for this directory** so you reuse the same command for the rest of this session instead of re-detecting it. If the project has a memory/notes file for agent conventions (e.g. `CLAUDE.md`, `AGENTS.md`, or an existing project memory), record the detected style command there under this working directory for future runs.

Read `CONTRIBUTING.md` (or equivalent contributor docs) at the project root, if present, to understand the Definition of Done and any commit-related conventions. Also run:

```bash
git log --oneline -10
```

to observe the established format: `type(scope): description`

**Types**: `feat`, `fix`, `chore`, `refactor`
**Scopes**: bounded context or directory affected (e.g., `ontology`, `scripts`, `contexts`, `tests`, or a file path)

### Step 2: Stage and inspect changes

Run:

```bash
git add -A
git diff --cached --stat
git diff --cached
```

Run all tests first, stage all changes, then inspect the diff. If the working tree is clean (nothing to stage), inform the user and stop.

### Step 3: Generate the commit message

Based on the diff, produce a single-line commit message matching the pattern:

```
type(scope): imperative description of the change
```

Rules:
- Use **imperative mood** ("add", "fix", "remove" — not "added", "fixes")
- Keep the subject line under 72 characters
- Pick the most specific scope that covers all changed files
- If changes span multiple scopes, use the parent directory or omit scope
- If the change is breaking, append `!` after the scope: `feat(ontology)!: remove deprecated field`

### Step 4: Present for review

Show the proposed message to the user using AskUserQuestion with options:
1. **Use as-is** — commit with this message
2. **Edit** — let the user provide a modified version
3. **Abort** — exit with zero side effects

### Step 5: Commit or abort

- If **Use as-is**: run `git commit -m "<message>"`
- If **Edit**: ask for the edited message, then run `git commit -m "<edited message>"`
- If **Abort**: print "Aborted — no commit created." and stop

### Important constraints

- **Never commit without explicit user confirmation**
- **Never tag the commit with the name of the model, e.g. Co-Authored by Claude Opus. It generates useless noise.**
- **Always stage all changes** (`git add -A`) before generating the commit message
- **On abort, unstage changes** — run `git reset HEAD` to restore the working tree
- Pass the commit message via HEREDOC to preserve formatting:
  ```bash
  git commit -m "$(cat <<'EOF'
  the message here
  EOF
  )"
  ```
