# Audit rubric

The principles (no-ops, context load, progressive disclosure, single source of truth, negation, sprawl, context pointers) come from `mattpocock-skills:writing-for-agents`. This file maps them to ledger actions and the evidence each finding needs. If that skill is not installed, the one-line tests below are enough to run the audit.

Use one category per finding. When a line fails more than one, record the one that decides its fate: cut beats move beats rewrite.

| Category | Test | Action | Evidence |
|---|---|---|---|
| **No-op** | Would behavior change if the sentence disappeared? | Cut the whole sentence. If the behavior matters but the wording is too weak to move the default, rewrite with a stronger, concrete instruction. | The default it restates. |
| **Duplicate** | Does the same meaning appear elsewhere (same file, `CLAUDE.md` vs `AGENTS.md`, parent vs nested file, instruction file vs skill)? | Keep the copy at the right tier, cut the rest. | `file:line` of every copy. |
| **Cache** | Does one command or one file already answer this (`package.json` scripts, directory tree, `--help`, `Makefile`)? | Cut, or rewrite to a pointer. Keep only the why, the unwritten convention, or the gotcha the environment cannot say. | The command or file that answers it. |
| **Stale** | Does the named path, command, tool, version, or process still exist and work? | Cut, or rewrite to the current truth. | The failing `ls`, the missing script, or the `git log` showing the removal. |
| **Negation** | Does it steer by prohibition where a positive target exists? | Rewrite to the target. Keep a prohibition only as a guardrail for destructive or secret-handling actions, paired with what to do instead. | The positive phrasing. |
| **Misplaced** | Do only some tasks need it? | Move to a disclosed file behind a pointer: coding and language rules to `CODING_STANDARDS.md`, workflow to `CONTRIBUTING.md` or `docs/agents/<topic>.md`, subtree rules to a nested `AGENTS.md`. | Which tasks need it. |
| **Weak pointer** | Does the pointer lead with the condition for reading its target? | Rewrite: "Before editing X, read Y." | The current wording. |
| **Scattered** | Are one topic's rule, exception, and caveat in different sections? | Rewrite to group them under one heading. | `file:line` of each fragment. |
| **Sprawl** | Is the file too long even though every line is live? | Move reference out, or split per subtree. | Line and token count. |

**Keep** a line when it changes behavior, most tasks need it, the agent cannot find it by looking, and it appears nowhere else.

A move without a pointer is a deletion in practice: the agent never reaches a disclosed file that nothing names.
