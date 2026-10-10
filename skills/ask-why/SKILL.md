---
name: ask-why
description: "Investigates a question about a codebase or system and answers it from evidence, without changing anything. Gathers evidence first (git history and blame, CI run logs, tests, ADRs and docs), then uses Five Whys for 'why is X failing / why did X break', a scored placement analysis for 'where should Y live' (module, layer, script, package, CI job, or bounded context), and structured explanation, description, or a decision matrix for how/what/which questions. Checks the question's premise and says what evidence it could not reach. Use when the user says /ask-why, asks 'why is this failing', 'why did this break', 'what was the root cause', 'where does this belong', 'where should this check/code live', or wants a root cause explained for a bug that is already fixed. Read-only: no code is written or changed."
user-invocable: true
argument-hint: '[question] - The question you want to investigate'
---

# ASK-WHY: Structured Question Investigation

**Mode**: read-only on the project. Read files, run read-only commands, and answer. Do not edit, create, commit, push, or comment on anything in the project or its remote. (If the user or a harness asks you to save the answer to a file outside the project, that is fine.)

**Standards**:
- **Evidence first.** Every claim points to something checkable: a `file:line`, a commit hash, a CI run ID and log line, a test name, an ADR.
- **Symptom is not cause.** Keep asking why until you reach something a person could change.
- **Name uncertainty.** Say "likely" or "unknown" instead of guessing silently, and say what evidence would settle it.
- **Falsifiable conclusions.** Phrase the answer so the reader can verify or disprove it.

---

## Step 1: Classify and check the premise

| Signal words | Question type | Method |
|---|---|---|
| why, why is, why did, what broke, root cause | **Causal** | Five Whys |
| where, where should, where does, belongs | **Placement** | Placement analysis |
| how, how does, how should | **Mechanism** | Structured explanation |
| what, what is, what causes | **Definition / discovery** | Evidence-based description |
| which, which is better, which should | **Decision / trade-off** | Decision matrix |

A question can be mixed ("why did this break and where should the guard go"). Answer the main question with its method and handle the rest in Next Steps.

Then check the premise. Questions often carry facts that are wrong or incomplete: the wrong date, the wrong file, "it got fixed" when it did not, "it started failing on Tuesday" when it had failed for weeks, candidates that leave out the obvious home. Verify each stated fact against evidence while you investigate. Report the result in the **Premise check** line of the output; correcting a false premise is often the most useful part of the answer.

## Step 2: Gather evidence

Look before you reason. The user rarely pastes the logs, so go get them. Pick the sources that fit the question; you do not need all of them.

| Source | Read-only commands | Good for |
|---|---|---|
| Git history | `git log --oneline -- <path>`, `git log -S '<string>'`, `git log -L <start>,<end>:<file>`, `git blame -L <range> <file>`, `git show <sha> [--stat] [-- <path>]` | When something changed, who changed what, the fixing commit, the breaking commit |
| CI runs | `gh run list --workflow <file> --limit 20`, `gh run view <id>`, `gh run view <id> --log-failed` | Exact error text, onset (first failing run), whether the fix has run green since |
| Issues and PRs | `gh pr view <n>`, `gh issue view <n>`, `gh pr list --search <sha>` | Intent behind a change, discussion of the failure |
| Tests | Read the tests that cover the code; run them only if they are side-effect free | Whether the behaviour is pinned, whether a regression guard exists |
| Decisions and docs | ADRs (`docs/adr*`, `docs/decisions`), README, CONTRIBUTING, architecture notes | Intended design, ownership, rules the answer must respect |
| Runtime config | CI workflow YAML, Makefiles, scripts, package manifests | Who calls what, with which arguments |

In long CI logs, find the first failing step and its first error line; later errors are often knock-on effects of the early exit, so name them as such rather than as separate causes.

For a causal question about something that "got fixed", find both ends: the fixing commit, and the breaking change plus the first failing run. The span between them often explains why nobody noticed (a weekly-only job, a second failure masking the first).

Keep a short list of what you checked and what you could not reach (no `gh` auth, logs expired, no network, file outside the repo). It goes in the **Evidence checked** section, so the reader knows how far to trust the answer.

## Step 3: Apply the method

### Method 1: Five Whys (causal)

State the symptom: what fails, when, under what conditions, expected vs actual, and the exact error text.

Then build a WHY tree. Follow each branch until you reach a cause that someone can act on (a decision, a missing guard, a contract nobody owns). That is usually 3 to 5 levels. Stop a branch early if the evidence ends there, and do not pad a branch to reach five. Open a second branch only for a separate symptom or a contributing cause, such as an earlier failure that hid this one.

```
PROBLEM: [falsifiable problem statement, with corrected facts if the premise was wrong]

WHY 1A: [first observable cause]     [Evidence: ...]
  WHY 2A: [why 1A happened]          [Evidence: ...]
    ...                              (as many levels as the evidence supports)
    -> ROOT CAUSE A: [one sentence]
    -> IMPLICATION A: [what this means for a fix or a guard]

WHY 1B: [separate or contributing cause, if any]
  ...

CROSS-VALIDATION:
- Every symptom explained: [yes / partial: gaps]
- Timeline consistent (cause precedes onset, fix precedes recovery): [yes / no / unverified]
```

### Method 2: Placement analysis (where)

Works for any kind of home: a function's module, a check's script, a package, a layer, a service, a CI job, or a bounded context.

**Characterise the thing being placed**: what it does, what it reads or owns, what triggers it to change, and what it depends on.

**List the candidates.** Use the user's list, and add an obvious candidate they missed if the evidence points to one (say you added it). Separate a *home* (where the code or rule lives) from *wiring* (where it is invoked, such as a CI job that only calls a script). If a candidate is wiring, say so: the answer may be "lives in A, runs from B". Still score a wiring-only candidate, judging it by where its logic would have to go (inline YAML, a new script), so the table compares like with like.

**Score each candidate from 1 to 5 (higher is better)**, citing evidence for each score:

| Criterion | Question |
|---|---|
| Responsibility fit | Does this home already describe itself as doing this kind of thing (its header, README, ADR, naming)? |
| Dependency direction | Does placing it here keep dependencies pointing the way they already point (tests depend on code, not code on tests; shipped code not on repo-only files)? |
| Existing analogues | Does this home already hold similar things you could copy the pattern from? |
| Wiring cost | How much new plumbing is needed: new jobs, CLI verbs, imports, duplicated discovery logic? Less is better. |
| Change alignment | Does it change for the same reasons and get maintained by the same people as this home? |

Total the five scores (out of 25) unweighted, unless the user named a priority; then say which criterion you weighted and why. If the top two are within 2 points, treat it as a tie and decide on the criterion that matters most for this case, defaulting to lower wiring cost, then to the stronger existing analogue. Name the deciding criterion either way.

State the recommendation, the main risk, and anything that would change it.

### Method 3: Structured explanation (how)

1. **Mechanism**: the steps and components involved, with `file:line` for each.
2. **Key invariants**: what must hold for it to work.
3. **Failure modes**: when it breaks and why.
4. **Diagram** if it helps: ASCII or Mermaid.

### Method 4: Evidence-based description (what)

1. **Definition**: one sentence.
2. **Scope**: what it includes and excludes.
3. **Evidence**: where it is observable in code, config, or docs.
4. **Common confusions**: what it gets mistaken for.

### Method 5: Decision matrix (which)

| Option | Pros | Cons | Fit (1-5) |
|---|---|---|---|

State the winner and the deciding criterion.

---

## Output format

```
## Question
[the question as asked]
**Premise check:** [confirmed | corrected: what was wrong and the evidence | unverifiable: why] (list each stated fact separately if they differ)

## Classification
[question type] → [method]

## Evidence checked
- [source]: [what you looked at, e.g. `git log -- scripts/x.sh`, run 123 --log-failed]
- Not reachable: [source and reason, or "none"]

## Investigation
[method output: WHY tree, placement table, explanation, etc.]

## Answer
[2-5 sentences, written once: the direct answer, the key evidence behind it, and your confidence. Do not repeat it elsewhere as a summary.]

## Next Steps (optional)
[up to 3 bullets, routed as below]
```

### Routing next steps

This skill stops at the answer. Point to the right follow-up instead of fixing anything:

| Finding | Next step |
|---|---|
| Open bug | Suggest `/nw-bugfix` with the root cause |
| Bug already fixed | Name the fixing commit or PR. Say whether a run since the fix proves it (cite the run) or not yet. If no test or check would catch a repeat, suggest a regression guard and where it belongs |
| Design gap or missing guard | Suggest `/nw-design`, or name the small change and where it goes |
| Stale or wrong docs | Name the `file:line` and what it should say |
| Missing test coverage | Name the behaviour and the test file that should hold it |
| Nothing actionable | Omit Next Steps |

---

## Examples

- `/ask-why "Why did the nightly deploy start failing last week?"`: causal. Pulls `gh run list` for the workflow to find the first failing run, reads its `--log-failed`, uses `git log` between the last green and first red run to find the breaking change, and may correct "last week" if failures began earlier.
- `/ask-why "Where should the retry policy live: the HTTP client wrapper or each service caller?"`: placement. Characterises the policy, scores both candidates on the five criteria with evidence, and recommends one with the deciding criterion named.
- `/ask-why "How does the token refresh cycle work here?"`: mechanism. Steps with `file:line`, invariants, failure modes, and a sequence diagram.

## Constraints

- **No code generation and no fixes.** Describe the change; do not make it.
- **No project writes or outward actions.** No edits, commits, pushes, issue or PR comments, or workflow dispatches.
- **Cite sources.** Every factual claim references a file and line, commit, CI run, log excerpt, test, or named design principle.
