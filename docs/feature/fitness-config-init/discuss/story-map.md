# Story Map: fitness-config-init

**User**: A maintainer adopting fitness reviews on a project (Priya Raman / `ledgerd`; Jeff Bailey / `jeffbaileyblog`; Tomas Okafor / `homelab-cli`)
**Goal**: A valid `fitness-config.json` tuned to the project's purpose, with the reasoning visible

## Backbone

| Invoke & choose mode | Gather evidence | Classify purpose | Propose & explain | Protect existing | Validate & write |
|---|---|---|---|---|---|
| Invoke; fast by default (US-01) | Fast scan of README, manifests, dirs, deploy (US-01) | Purpose + confidence + evidence (US-01) | Tuned weights, each change explained (US-02) | Refuse to overwrite silently (US-03) | Schema + resolver gate, then write (US-03) |
| | | | | Diff + confirm y/N (US-04) | |
| Opt into full review (US-05) | review-full scores + findings (US-05) | Purpose refined by findings (US-05) | Rationale cites review findings (US-05) | | |
| | | | Tune thresholds and confidence cutoff (US-06) | | |

---

### Walking Skeleton: US-01, US-02, US-03

This is brownfield: the schema, the example config, and the resolver `validate`/`show` already exist. The skeleton is the thinnest pass of the new skill across all six activities. It invokes the skill, fast-scans the folder, classifies the purpose, proposes explained weights, and writes a validated file. When a config already exists, the skeleton refuses to overwrite it and shows the proposal instead, so nothing is ever destroyed. The skeleton is demoable on `ledgerd` with no prior config.

### Release 1: Existing configs can be re-tuned safely (US-04)

Outcome: maintainers with an existing config adopt proposals without losing their edits. KPI-3.

### Release 2: Deeper evidence when the maintainer wants it (US-05)

Outcome: a full-review run produces proposals the maintainer accepts with fewer manual edits than a fast scan. KPI-4.

### Release 3: Purpose-tuned thresholds (US-06)

Outcome: security-critical projects get a stricter confidence cutoff without hand edits. KPI-1 guardrail.

## Priority Rationale

1. **Walking skeleton first.** It proves the riskiest assumption: that a fast scan is enough to propose weights a maintainer accepts (KPI-1). It also proves that the output always passes the existing resolver (KPI-2).
2. **US-04 next.** Existing configs are the main data-loss risk. The skeleton's "refuse" behaviour is safe but blocks re-tuning, which is the most common repeat use.
3. **US-05 after that.** Its value is high but so is its cost (a full ten-domain review), and it depends on the skeleton's proposal format.
4. **US-06 last.** Weights carry most of the purpose signal. Thresholds already have sensible defaults.
