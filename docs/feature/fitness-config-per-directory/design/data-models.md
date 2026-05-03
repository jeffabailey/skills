# Data Models — fitness-config-per-directory

**Wave**: DESIGN
**Date**: 2026-04-25

Defines (1) the JSON shape of override config files, (2) the in-memory `ResolutionResult` record produced by the resolver, and (3) the stdout contract format for CLI subcommands.

---

## 1. Schema delta

The existing `fitness-config.schema.json` is unchanged for v1. The same schema applies to root and override files.

Key implications:

- `version` is still `const: 1`. Override files MUST also declare `"version": 1`. Mismatched versions across the chain are a hard error (ADR-003).
- All four top-level keys (`weights`, `statusThresholds`, `security`, `scoring`) are optional in the schema. An override file may contain only `weights`, only `security`, etc.
- `additionalProperties: false` on the root means override files cannot introduce new top-level keys. (We do NOT add a `mergeMode` property in v1 — see ADR-002.)
- `additionalProperties: false` on `weights` means override files cannot introduce new domain names. The 10-domain list is fixed.

### 1.1 Example: minimal partial override

```json
{
  "version": 1,
  "weights": {
    "data": 30,
    "reliability": 20,
    "performance": 6,
    "algorithms": 4,
    "accessibility": 0,
    "process": 1,
    "maintainability": 1
  }
}
```

When merged with a root config defining `architecture=14, security=14, testing=10` (sum=38), the effective weights sum to `38 + 30 + 20 + 6 + 4 + 0 + 1 + 1 = 100`. Valid.

### 1.2 Example: full override

```json
{
  "version": 1,
  "weights": {
    "architecture": 10,
    "security": 10,
    "reliability": 25,
    "testing": 10,
    "performance": 5,
    "algorithms": 5,
    "data": 30,
    "accessibility": 0,
    "process": 3,
    "maintainability": 2
  }
}
```

Override defines all 10 weights; merge result equals override exactly. Valid.

---

## 2. In-memory record types (resolver outputs)

The resolver produces a single `ResolutionResult` record. Software-crafter chooses the concrete representation (`@dataclass`, `NamedTuple`, or `TypedDict`); the contract is the field set.

### 2.1 `ResolutionResult`

| Field | Type | Description |
|-------|------|-------------|
| `target_path` | `Path` | Canonicalized input path (after `resolve(strict=False)`) |
| `source_chain` | `list[Path]` | Ordered list of `fitness-config.json` paths in precedence order (highest first). Empty if none found. |
| `raw_configs` | `list[dict]` | Parsed JSON of each chain entry, same order as `source_chain`. |
| `effective` | `dict` | Final merged config: `{weights: {...}, statusThresholds: {...}, security: {...}, scoring: {...}, version: int}` |
| `valid` | `bool` | True if validation passed. |
| `errors` | `list[str]` | Human-readable error messages (may include remediation hints). Empty if `valid` is True. |

### 2.2 Provenance per weight (optional)

For richer rendering of `show --path` output (the TUI mockup in `journey-fitness-config-per-directory-visual.md` annotates each weight with its source: "override" / "root" / "default"), the resolver may also produce:

| Field | Type | Description |
|-------|------|-------------|
| `weight_provenance` | `dict[str, str]` | `{"data": "override", "architecture": "root", ...}` — which entry in the chain (or "default") supplied each effective weight |

This is a derived field; it is not required for v1 AC compliance, but it makes the `show` table prettier. Software-crafter may include or omit at their discretion in DELIVER.

---

## 3. CLI stdout contract

### 3.1 `show --path <target>` output

The `show` subcommand prints two sections:

1. **Human-readable rendering** (matches the TUI mockup in `journey-fitness-config-per-directory-visual.md`).
2. **Embedded JSON block** (delimited by sentinels) so an LLM agent or downstream tool can parse the effective config without re-parsing the human text.

Format:

```text
Resolved config for: <target_path>

  config sources (in precedence order):
    1. <chain[0]>   (override)        # only if chain has 2+ entries
    2. <chain[1]>   (root)            # only if chain has 1+ entries
                                      # if chain is empty: "  (no fitness-config.json found — using built-in defaults)"

  effective weights (merged):
    <domain>      <value>   (<provenance>)
    ...
    -------------------
    total          <sum>   <OK|ERROR>

  effective thresholds, security, scoring: <"from <path>" | "from root (no override)">

<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->
{
  "version": 1,
  "source_chain": ["<chain[0]>", "<chain[1]>"],
  "effective": {
    "weights": {...},
    "statusThresholds": {...},
    "security": {...},
    "scoring": {...},
    "version": 1
  }
}
<!-- END_EFFECTIVE_CONFIG_JSON -->
```

The sentinels are HTML-comment-style so the output is also valid as an embedded fragment in a markdown report.

### 3.2 `validate --path <dir>` output

Success:
```text
Effective merged config valid: total <sum> OK
  Source: <chain[0]>
          merged with: <chain[1]> (root)    # if chain length >= 2
```

Failure (sum != 100):
```text
Error: Effective config has invalid weights

  Source: <chain[0]>
          merged with: <chain[1]> (root)    # if chain length >= 2

  Effective weights sum to <X>, must sum to 100.

  The override redefined: <list of domains in chain[0].weights>.
  The override left from root: <list of domains contributed by chain[1] (or default)>.

  To fix:
    1. Adjust override weights so the merged total is 100, OR
    2. Set "weights": { ... } with all 10 domains in the override
       (full replacement, no merge with root weights).

  See: fitness-config.example.json
```

Failure (schema version mismatch):
```text
Error: Cannot merge configs with different schema versions

  <chain[0]> declares version <Vchild>
  <chain[1]> declares version <Vroot>

  Supported version: 1.

  Update both files to the same version, or remove the override.
```

### 3.3 Report header lines (per US-03)

The skill prompt instructs the agent to extract these two lines from `show --path` output and embed them in the first 10 lines of the generated report:

- `Config: <chain[0]>` (when chain length is 1) OR
- `Config: <chain[0]> (merged with root)` (when chain length is 2+) OR
- `Config: built-in defaults (no fitness-config.json found)` (when chain is empty)
- `Effective weights: <domain>=<value> ... <domain>=<value>` (all 10 domains, descending by value, ties alphabetical)

The agent never recomputes weights; it copies them verbatim from the resolver output.

---

## 4. Error model

| Error condition | Where detected | Reported by |
|----------------|----------------|-------------|
| Malformed JSON in any chain entry | Resolver (in `_read_config`) | Resolver returns `valid=False`, errors list names the malformed file |
| Missing version field in any chain entry | Validator | `errors` includes "Config X is missing 'version' field" |
| Mismatched versions across chain | Validator | `errors` includes "Cannot merge: <a> has version V1, <b> has version V2. Supported: 1." |
| Effective weights sum != 100 | Validator | `errors` includes "Effective weights sum to N, must sum to 100" + remediation |
| Weight value out of [0, 100] | Validator | `errors` includes "Weight <domain> in <file> is out of range [0,100]" |
| `confidenceThreshold` out of [1, 10] | Validator | `errors` includes "confidenceThreshold in <file> must be 1-10" |
| Walk-up exceeds 64 levels | Resolver | `errors` includes "Walk-up exceeded 64 levels — pathological tree?" |
| Target path does not exist | Resolver | `errors` includes "Target path <X> does not exist" |

All errors are returned as data (`ResolutionResult.errors`); exceptions are reserved for programmer errors (e.g., calling resolver with `None`).

---

## 5. Backward compatibility (NFR-3)

When CLI subcommands are invoked WITHOUT `--path`:

- `validate [path]`: behavior unchanged. Loads single file, validates in isolation, exits 0/1.
- `init [path]`: behavior unchanged. Writes DEFAULT_* to `path` if it does not exist.
- `show [path]`: behavior unchanged. Loads single file, merges with `DEFAULT_*` constants, prints JSON.

When `--path` is supplied, the new resolver-driven behavior applies. The two modes are mutually exclusive (argparse rejects supplying both).

Existing functional tests that exercise the no-`--path` mode continue to pass.
