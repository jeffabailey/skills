# Algorithm Review Scoring Rubric

Hand-maintained scoring rubric. sync-wisdom does not regenerate this file.

This is the scoring source for review-algorithms. `checklist.md` lists what to look for; this file says how bad a finding is and what score a dimension earns.

## Severity

A finding's severity comes from what a user of the code would see when the defect fires on input the code is meant to accept. HIGH and CRITICAL require a reproduction (see "Proof for HIGH and CRITICAL" below).

| Severity | Definition | Examples |
|---|---|---|
| CRITICAL | Silent wrong result, data loss, or corruption on common input, or a hang/crash on the main path. | A dedupe keyed on a non-unique field drops records; a retry loop with no exit condition hangs on the first transient error. |
| HIGH | Wrong result, crash, or nondeterminism on valid input that is reachable without unusual setup, but not the common case. | An off-by-one slice drops the first or last element of a chain; iterating a `set` makes output order depend on the hash seed, so a "no change" check flaps. |
| MEDIUM | Validation or data structure gap that lets bad input through or fails loudly instead of cleanly; quadratic path on inputs that can realistically grow. | `validate` accepts a value that `show` later crashes on; `list.index` inside a loop over all files. |
| LOW | Fragile but currently correct: undocumented invariant, missing guard on a value callers never pass today, unclear inclusive/exclusive bounds. | A comparator relies on all keys being present; a division guarded only by an upstream caller. |

### Proof for HIGH and CRITICAL

Before rating a finding HIGH or CRITICAL, run a minimal reproduction: call the function from a one-off script, or run the CLI on an edge input (empty file, empty list, one element, boundary value, unknown key, different `PYTHONHASHSEED`). Put the command and its observed output in the finding's **Reproduction** field. Run it in a scratch copy or with temp files; never modify the user's files to reproduce.

If you cannot reproduce it, downgrade to MEDIUM or lower and say why, or drop it.

### Not a finding

Drop it, rather than reporting it at LOW, when triggering it needs a setup the code does not support or document: two copies of a single-user CLI or CI job running at once in the same checkout, a process killed between two writes, a hand-edited corrupt cache, an attacker-controlled input the tool never receives. Report these only if the user asked about that scenario. Security exploitability belongs to review-security, and "is it fast enough" belongs to review-performance.

## Dimension anchors

Score each applicable dimension from the findings in it and from what you checked and found sound. Pick the band whose description fits, then move one point within the band for strength or weakness of the evidence.

### 1. Algorithm Choice
- **9-10:** Every hotspot uses an algorithm whose preconditions hold (sorted input for binary search, acyclic or visited-set for traversal, greedy-choice property argued). Standard library used for sort/search.
- **7-8:** Choices fit; one LOW (e.g. undocumented precondition, hand-rolled helper where stdlib exists).
- **5-6:** One MEDIUM: an algorithm that is wrong for some realistic input shape (linear scan used as an index, recursion without depth bound on user data).
- **3-4:** One HIGH: an algorithm produces wrong output for valid input (BFS/DFS swapped for shortest path, greedy where it fails).
- **1-2:** CRITICAL, or multiple HIGH: the core algorithm is wrong on common input.

### 2. Data Structure Selection
- **9-10:** Collections match access patterns: sets/dicts for membership and lookup, ordered structures wherever order affects output, bounded caches and queues on long-lived paths.
- **7-8:** One LOW (list used for membership on small, fixed-size data; missing defensive copy at an internal boundary).
- **5-6:** One MEDIUM: unbounded cache or buffer on a long-lived path, `list.pop(0)` queue on input that grows, shared mutable default.
- **3-4:** One HIGH: unordered structure where order determines output, or aliasing that corrupts state on valid input.
- **1-2:** CRITICAL: structure choice silently loses or corrupts data on common input.

### 3. Complexity Awareness
- **9-10:** No nested loops over unbounded input; indexes built once; string building uses join/builder.
- **7-8:** One LOW: quadratic over a collection that is small by construction (skills in a repo, dimensions in a config).
- **5-6:** One MEDIUM: O(n^2) or repeated sort over input that can realistically reach thousands of items.
- **3-4:** HIGH: exponential recursion without memoization, or unbounded growth on a long-lived process.
- **1-2:** CRITICAL: a main path that cannot finish on normal production volumes.

### 4. Concurrency Safety
Score only when the target runs threads, async tasks, goroutines, multiple processes on shared state, or signal handlers. Otherwise mark it N/A (see below); do not invent inter-process races.
- **9-10:** Shared mutable state identified and protected; consistent lock order; no lock held across await; atomic writes where readers can see partial files.
- **7-8:** One LOW (lock scope wider than needed, flag not marked atomic but only set once).
- **5-6:** One MEDIUM: check-then-act on shared state that a supported concurrent caller can hit.
- **3-4:** HIGH: reproducible lost update or torn read under the documented concurrency model.
- **1-2:** CRITICAL: deadlock or data corruption under normal concurrent load.

### 5. Edge Case Handling
Edge inputs to try: empty, single element, boundary index, zero, negative, NaN/inf, unknown keys, missing optional fields, Unicode.
- **9-10:** Edge inputs tried during the review either work or are rejected with a clear error at the boundary; validation and use agree on what is valid.
- **7-8:** One LOW: an unguarded edge that no current caller produces.
- **5-6:** One MEDIUM: validator accepts input that a later step crashes on, or an edge input gives an unclear traceback instead of an error message.
- **3-4:** HIGH: an off-by-one or boundary bug that gives wrong output on valid input (reproduced).
- **1-2:** CRITICAL: common input (empty file, first run) gives wrong output or corrupts data.

### 6. Correctness Patterns
- **9-10:** Deterministic output for the same input; invariants documented or asserted; errors propagate with context; loops and recursion provably terminate; writes are idempotent where re-run is expected.
- **7-8:** One LOW: broad `except` that logs and continues where partial results are acceptable; undocumented invariant.
- **5-6:** One MEDIUM: an error swallowed so the caller cannot tell success from failure; a re-run that is not idempotent.
- **3-4:** HIGH: nondeterministic output (hash-order, wall clock) that affects a stored or compared result, reproduced.
- **1-2:** CRITICAL: silently wrong results on the main path.

## N/A

Mark a dimension `N/A — <reason>` when nothing in scope can be evaluated for it, for example Concurrency Safety for a single-threaded CLI with no threads, async, subprocess fan-out, or shared files written by concurrent callers. Cite the evidence for the absence, such as `sync-wisdom.py (no threading/asyncio/multiprocessing imports)`. An N/A dimension gets no score and is left out of the average. Do not use N/A for a dimension that applies but where you found nothing wrong; that scores 9-10.

## Overall score

- Overall = mean of the scored (non-N/A) dimensions, rounded to one decimal. Name the averaged dimensions on the overall line.
- If any CRITICAL finding exists, cap the overall at 4.0.
- Status bands: a score at or above `statusThresholds.healthy[0]` is Healthy, at or above `statusThresholds.needsAttention[0]` is Needs Attention, anything lower is Critical (defaults 8 / 5 when the resolver gives none). Only the lower bounds count, so a fractional score such as 7.5 is Needs Attention, never a gap; review-full uses the same rule.
