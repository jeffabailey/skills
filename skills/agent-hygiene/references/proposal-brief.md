# Proposal brief

Fill in the `<…>` fields and send this as the subagent's prompt. It is the subagent's only context, so do not trim it.

---

You are proposing a restructuring of the agent instruction files in the repo at `<repo path>`. Write proposals only; do not edit the repo.

**Your tier: <1 Prune | 2 Disclose | 3 Rebuild>.**

- **Prune**: delete no-ops, duplicates, and stale lines; tighten wording. Keep the file layout as it is: no new files, no moves between files.
- **Disclose**: everything Prune does, plus move reference material that only some tasks need out of always-loaded files into disclosed files (for example `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `docs/agents/<topic>.md`), each reached by a one-line pointer that leads with the condition for reading it.
- **Rebuild**: start from an empty always-loaded file. Readmit only lines the agent needs on nearly every task and cannot find by looking at the repo. Disclose, merge, or delete the rest. You may merge, rename, or delete instruction files, and replace a duplicated `CLAUDE.md`/`AGENTS.md` pair with one file plus an `@AGENTS.md` import or a symlink. Be as radical as the evidence supports.

**User goals (these override the tier defaults where they conflict):** <goals>

**Inputs:**

- The ledger at `<ledger path>`: every line of every instruction file, classified keep / cut / move / rewrite with evidence. Follow it; where your tier goes further than the ledger (Rebuild usually does), say so in `PLAN.md`.
- The rubric at `<rubric path>`.
- If the `mattpocock-skills:writing-for-agents` skill is available, invoke it before writing; it holds the principles the rubric applies. If it is not, the rubric is enough.
- The repo itself: read any file you need to check a claim.

**Output** in `<output dir>`, mirroring repo paths:

- Complete replacement content for every file you create or change, so it can be copied into the repo as-is. Files you delete are listed in `PLAN.md`, not written.
- `PLAN.md` with:
  1. One paragraph: the shape of the result and why.
  2. A table of every file: created / changed / deleted / unchanged, always-loaded or disclosed, lines before and after.
  3. A trace: for every ledger line marked keep, move, or rewrite, where it now lives (`file:line`). For every line you cut beyond the ledger, the reason.
  4. Risks: any rule that now sits behind a pointer the agent might not follow, and anything you were unsure about.

**Writing rules for every file you produce:** state the positive target instead of a prohibition (keep a "never" only for destructive or secret-handling guardrails, paired with what to do instead); one meaning in one place; pointers name the file and lead with when to read it; keep the repo's existing voice and heading style.

**Done when** every keep / move / rewrite line in the ledger has a trace entry and every pointer you wrote names a file that exists in the repo or in your output.
