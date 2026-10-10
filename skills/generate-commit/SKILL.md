---
name: generate-commit
description: Writes a conventional commit message for what the user has staged, matching the types and scopes in the repo's own git log, runs the project's CI lint on the staged files only, shows the message for review, and commits only after the user confirms. Respects the user's staging, warns about secret-looking or scratch files, and suggests splitting diffs that mix unrelated changes. Use when the user says /generate-commit, "write a commit message", "commit what I staged", "commit this", or wants a reviewed conventional commit.
---

# Generate Commit

Write a commit message for the changes the user staged, in this repo's conventional commit style, and commit after they approve it.

The index is the user's decision about what goes into this commit. Treat it as input, not something to rebuild. Everything below follows from that: inspect what is staged, check only that, and leave the rest of the working tree exactly as you found it.

## Step 1: Snapshot and inspect the index

```bash
git status --short --untracked-files=all
git write-tree              # prints a tree hash: remember it as ORIG_TREE
git diff --cached --stat
git diff --cached
```

`ORIG_TREE` records the index exactly as the user left it. On abort, `git read-tree <ORIG_TREE>` puts it back without touching working-tree files. Shell variables do not survive between tool calls, so keep the hash itself in your notes.

**If something is staged**, use that and only that. Do not run `git add -A`, `git add .`, or `git commit -a`. Unstaged edits and untracked files stay out of the commit, even when they look related. Mention them in one line ("README.md is modified but not staged; leaving it out") so the user can add them if they meant to.

**If nothing is staged:**

- With a clean working tree, say there is nothing to commit and stop.
- Otherwise list the modified and untracked files and ask whether to stage all of them, a subset, or none. Stage only after the user agrees, and stage the paths they chose (`git add -- <paths>`). Do not fall back to `git add -A` silently.

## Step 2: Check for files that should not be committed

Before staging anything, and again over the staged file list, flag files that look like secrets or scratch work. Look at names, at the content of small untracked files, and at the diff (not the whole file) of modified tracked files, so a README that mentions `API_KEY` does not raise an alarm:

- Names: `.env*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `credentials*`, `secrets*`, `*scratch*`, `*notes*.txt`, `*.log`, `*.tmp`, `*.bak`, `.DS_Store`, large binaries.
- Contents (for example `git diff --cached | grep -nEi '...'`): `api[_-]?key`, `token`, `secret`, `password`, `BEGIN .*PRIVATE KEY`, `sk-[A-Za-z0-9-]+`, `AKIA[0-9A-Z]{16}`, `ghp_[A-Za-z0-9]+`, `xox[bp]-`.

If a staged file matches, stop and ask before going on, and offer to unstage it (`git restore --staged -- <path>`). If an unstaged or untracked file matches, warn in one line and keep it out of the commit. A false positive costs one question; a committed key costs a rotation.

## Step 3: Run the project's lint on the staged files

The goal is to catch problems in this commit, not to clean up the repo.

1. **Find the command CI actually runs.** Read `.github/workflows/*.yml` (or `.gitlab-ci.yml`, `.pre-commit-config.yaml`, a `Makefile`/`justfile` `lint` or `check` target, or the `scripts` in `package.json`). Use those commands with the project's runner (`uv run`, `npm run`, `pnpm`, and so on). Do not guess a formatter the project has not adopted. A repo that runs `ruff check` in CI has not opted into `ruff format`.
2. **Run it in check mode on the staged paths only:**

   ```bash
   git diff --cached --name-only --diff-filter=ACMR -- '*.py' | xargs uvx ruff check
   ```

   That example uses CI's ruff; substitute the project's own command and globs. Piping through `xargs` avoids shell word-splitting differences (zsh does not split `$FILES`). Filter that list to the file types the tool handles. When a tool cannot take a path list (for example `go vet ./...`), limit it to the affected packages or directories. When no lint is configured, say so and continue. Do not invent one.
3. **On failure, report it and ask.** Show the findings with file and line. Note any that sit on lines this diff did not touch, since those existed before. Then let the user choose: fix the staged files, commit anyway, or abort. Never reformat the whole repo, and never fix files outside the staged set.
4. **If the user asks you to fix,** edit only the staged files, then re-stage those paths. If a file is partly staged (it shows in both `git diff` and `git diff --cached`), re-staging also picks up its unstaged hunks. Say so and ask before you re-stage it.

Do not run the full test suite by default; it is slow and does not change the message. Run tests only when the user asks or the project's `CONTRIBUTING.md` requires them before every commit. Then run only the tests related to the staged files and report the results.

Do not write the lint command, or anything else, into `CLAUDE.md`, `AGENTS.md`, or any other tracked file. This skill changes nothing except the commit.

## Step 4: Learn the repo's conventions

```bash
git log --format=%s -30
```

Read the types and scopes this repo actually uses, for example `docs(adr):`, `ci:`, `test(fitness-config):`, `fix(fitness-config):`. Prefer them over any generic list. When the history is not conventional, use the standard types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`. Skim `CONTRIBUTING.md` for commit rules if it exists. Rules there override this skill.

**Scope:** reuse a scope the log already uses for these files (check `git log --format=%s -- <path>` for a staged path). If none fits, use the most specific module or directory that covers every staged file, or leave the scope out. Never join several scopes into one, such as `ci,docs,scripts`.

## Step 5: Check whether the diff is one change

When the staged files serve unrelated purposes (for example a CI timeout, a docs fix, and a new script feature), say so before writing the message. Propose a split: one commit per concern, with the files for each and a draft subject for each. Then ask whether to:

- **Split.** Unstage everything (`git restore --staged -- .`). For each group, stage that group's paths, confirm the message, and commit. When done, the index holds nothing the user had not staged. If a single file mixes concerns, say so; splitting it needs `git add -p`, which the user has to do themselves.
- **Commit together.** Write one message whose body lists every concern.

A change and its own tests, docs, or config are one concern, so do not suggest splitting those.

## Step 6: Write the message

```text
type(scope): imperative summary of the change

Optional body: what changed and why, wrapped at 72 columns.
Use bullets when there are several distinct points.
```

- Start the subject with an imperative verb ("add", "fix", "accept"), not "added" or "fixes". Keep it at 72 characters or fewer, and do not end it with a period.
- Add a body when the subject cannot say why the change was made, when it covers more than one point, or when the change is breaking. Leave it out for small, self-explanatory changes.
- Mark breaking changes with `!` after the type or scope and a `BREAKING CHANGE:` footer.
- Do not add `Co-Authored-By`, "Generated with", or any model or tool name. It adds noise to the history. If the user's own instructions require a trailer, follow them.

## Step 7: Present for review

Show the full message, the list of files it will commit, and any warnings from Steps 1-3. Then ask with AskUserQuestion:

1. **Use as-is**: commit with this message.
2. **Edit**: take the user's revised message and commit with it.
3. **Abort**: no commit, and the index is restored.

## Step 8: Commit or abort

Commit with a HEREDOC so the body and line breaks survive:

```bash
git commit -F - <<'EOF'
type(scope): subject

Body.
EOF
```

- Let hooks run. Never pass `--no-verify`. If a pre-commit hook fails or rewrites files, show its output and go back to Step 3. Do not retry blindly.
- After committing, run `git status --short` and confirm that the files the user left unstaged or untracked are still there and still uncommitted.
- **On abort:** run `git read-tree <ORIG_TREE>` to put the index back exactly as the user left it, including anything they had staged. Do not use `git reset HEAD`, which also unstages their own staging. Undo any lint fixes you made only if the user asks. Then print "Aborted: no commit created; staging restored."

## Constraints

- Never commit without explicit confirmation.
- Never stage files the user did not stage or approve.
- Never edit files outside the staged set, and never edit `CLAUDE.md` or other agent notes as a side effect.
- Never push.
