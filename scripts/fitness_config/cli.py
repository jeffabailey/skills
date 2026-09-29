"""Command-line shell: argparse wiring and the cmd_* verbs. The only place that prints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters import config_file_at, load, read_anchored_chain, read_chain_configs
from .audit import cmd_audit
from .resolution import (WALK_UP_DEPTH_CAP, build_effective_config, build_seed_config,
                    deep_merge_chain, merge_defaults, walk_up_chain_with_status)
from .model import (CONFIG_FILENAME, DEFAULT_SCORING, DEFAULT_SECURITY, DEFAULT_STATUS,
                    DEFAULT_WEIGHTS)
from .render import render_canonical, render_show_output
from .validation import validate_config, validate_effective, validate_schema_versions
from .write_gate import GateOutcome, check_proposal, save_new_proposal

def _print_validation_errors(errors: list[str]) -> None:
    """Adapter: print each error line on its own to stderr.

    Centralises the multi-line ValidationResult.errors -> stderr boundary
    so command verbs read as a flat pipeline of validation gates.
    """
    for line in errors:
        print(line, file=sys.stderr)

def cmd_validate(path: Path) -> int:
    """Validate config file.

    On failure, names the offending file in the error message so downstream
    consumers (CI, milestone-5 backward-compat) can identify the source. The
    successful "Valid: <path>" line is preserved verbatim from the legacy
    behavior to keep bare invocations byte-identical (NFR-3).
    """
    data = load(path)
    if data is None:
        print(f"Error: {path} not found or invalid JSON", file=sys.stderr)
        return 1
    violations = validate_config(data)
    if violations:
        _print_validation_errors([f"Error: {line}" for line in violations])
        print(f"Error: invalid config: {path}", file=sys.stderr)
        return 1
    print("Valid:", path)
    return 0


def cmd_init(path: Path) -> int:
    """Create default config."""
    if path.exists():
        print(f"Error: {path} already exists", file=sys.stderr)
        return 1
    cfg = {
        "version": 1,
        "weights": DEFAULT_WEIGHTS,
        "statusThresholds": DEFAULT_STATUS,
        "security": DEFAULT_SECURITY,
        "scoring": DEFAULT_SCORING,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("Created:", path)
    return 0


def cmd_init_path(target: Path, base: Path) -> int:
    """Seed a per-directory override at <target>/fitness-config.json.

    Resolution rule: walk up from <target>'s PARENT (so we don't read the
    file we're about to create) to <base>, collect any fitness-config.json
    files into a chain (nearest-first), and seed the new override from the
    deep-merged effective config. When no ancestor config is found, fall
    back to documented DEFAULT_WEIGHTS and note that on stdout so Devin
    knows the seed source.

    Refuses to overwrite an existing file (exit 1, names the file). The
    file-write boundary stays here; the seed builder above is pure.
    """
    out_path = target / CONFIG_FILENAME

    if out_path.exists():
        print(f"Error: {out_path} already exists", file=sys.stderr)
        return 1

    _, raw_configs, error, exit_code = read_anchored_chain(target, base)
    if error is not None:
        print(error, file=sys.stderr)
        return exit_code

    seed = build_seed_config(raw_configs)

    target.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(seed, f, indent=2)

    if not raw_configs:
        print(
            "No root fitness-config.json found; seeded with documented default weights."
        )
    print("Created:", out_path)
    return 0


_GATE_SUCCESS = {"would-create", "would-replace", "unchanged", "existing-malformed",
                 "created", "replaced"}


def _print_gate_outcome(outcome: GateOutcome, show_canonical: bool) -> int:
    print(f"STATUS: {outcome.status}")
    if outcome.fingerprint:
        print(f"Proposal: {outcome.fingerprint}")
    _print_validation_errors(list(outcome.errors))
    for line in outcome.review:
        print(line)
    if show_canonical and outcome.canonical:
        sys.stdout.write(outcome.canonical)
    return 0 if outcome.status in _GATE_SUCCESS else 1


def cmd_init_from(target: Path, base: Path, proposal_text: str,
                  dry_run: bool, expected_fingerprint: str | None, force: bool = False) -> int:
    """`init --path T --from - (--dry-run | --expect FP [--force])`: the write gate."""
    _, configs_above, error, exit_code = read_anchored_chain(target, base)
    if error is not None:
        print(error, file=sys.stderr)
        return exit_code
    config_file = config_file_at(target / CONFIG_FILENAME)
    if dry_run:
        current = config_file.read()
        return _print_gate_outcome(check_proposal(proposal_text, current is not None, current), True)
    outcome = save_new_proposal(proposal_text, expected_fingerprint, config_file,
                                configs_above, force)
    return _print_gate_outcome(outcome, False)


def cmd_init_baseline(target: Path, base: Path) -> int:
    """`init --path T --dry-run`: print the starting config; write nothing."""
    chain, raw_configs, error, exit_code = read_anchored_chain(target, base)
    if error is not None:
        print(error, file=sys.stderr)
        return exit_code
    print("STATUS: baseline")
    print(f"Baseline-Source: {'chain' if raw_configs else 'defaults'}")
    for config_path in chain:
        print(config_path)
    sys.stdout.write(render_canonical(build_seed_config(raw_configs)))
    return 0


def _gate_usage_error(args) -> str | None:
    """Return a usage error for inconsistent write-gate flags, else None."""
    if args.proposal_source is None:
        if args.force:
            return "Error: --force needs --from - and --expect <fingerprint>"
        if args.expect:
            return "Error: --expect needs --from -"
        if args.dry_run and (args.command != "init" or args.resolve_path is None):
            return "Error: --dry-run only works with init --path"
        return None
    if args.command != "init" or args.resolve_path is None:
        return "Error: --from only works with init --path"
    if args.proposal_source != "-":
        return "Error: --from takes '-' (read the proposal from stdin)"
    if args.force and args.dry_run:
        return "Error: --force saves; it does not go with --dry-run"
    if not args.dry_run and args.expect is None:
        return ("Error: saving needs --expect <fingerprint> of a reviewed proposal; "
                "run with --dry-run first to see it")
    return None


def cmd_show(path: Path) -> int:
    """Print effective config (legacy single-file mode)."""
    data = load(path) or {}
    effective = merge_defaults(data)
    print(json.dumps(effective, indent=2))
    return 0


def _check_target_exists(target: Path, base: Path) -> str | None:
    """Return an actionable error message iff the target path is missing.

    Adapter-level guard: walk-up resolution requires a real anchor for the
    chain. Missing-path is a hard error per ADR-006 (fail-closed): silent
    fallback to defaults would let downstream consumers receive an effective
    config from the wrong scope.

    A path is considered "missing" iff neither the path itself NOR its
    immediate parent directory exists under base. This preserves the prior
    contract for `show --path` invocations that name a file inside a real
    directory (the file may not exist yet, but the anchor directory does).
    """
    candidate = (base / target) if not target.is_absolute() else target
    if candidate.exists():
        return None
    if candidate.parent.exists():
        return None
    return (
        f"Error: target path does not exist: {target}\n"
        f"  Fix: create the directory at {target}, "
        f"or invoke validate from a path that exists."
    )


def _depth_cap_error_message(target: Path) -> str:
    """Build the pathological-tree depth-cap error message.

    The 64-level safety cap fires only when an ancestor walk traverses more
    than WALK_UP_DEPTH_CAP directories without reaching the stop boundary.
    That signals a pathological tree (no .git, no repo root, no fitness-config
    anywhere on the way up). Surfacing this as a hard error lets the CLI
    fail-closed instead of silently truncating.
    """
    return (
        f"Error: pathological-tree depth limit (>{WALK_UP_DEPTH_CAP} levels) "
        f"reached while resolving config from {target}.\n"
        f"  Fix: invoke from a path within a normal repo tree, "
        f"or place a fitness-config.json above the target so resolution can anchor."
    )


def cmd_show_path(target: Path, base: Path) -> int:
    """Resolve walk-up chain from target, deep-merge, render to stdout.

    Fail-closed: every IO/parse/depth-cap/version-mismatch error short-
    circuits BEFORE rendering so downstream consumers cannot read the JSON
    sentinel block from a partial chain.

    Note: `show` deliberately does NOT reject non-existent target paths —
    legacy preview behavior (milestone-5 backward-compat) renders the root
    chain when the target is a hypothetical/future path. `validate` is the
    fail-closed gate; `show` is a preview tool.
    """
    walk = walk_up_chain_with_status(target, stop=base)
    if walk.depth_capped:
        print(_depth_cap_error_message(target), file=sys.stderr)
        return 1

    chain = walk.chain
    raw_configs, error = read_chain_configs(chain)
    if error is not None:
        print(error, file=sys.stderr)
        return 1

    version_check = validate_schema_versions(raw_configs, source_chain=chain)
    if not version_check.ok:
        _print_validation_errors(version_check.errors)
        return 1

    merged = deep_merge_chain(raw_configs)
    effective = build_effective_config(merged)
    output = render_show_output(target, chain, effective, base=base)
    sys.stdout.write(output)
    return 0


def cmd_validate_path(target: Path, base: Path) -> int:
    """Resolve walk-up chain from target, deep-merge, validate effective config.

    On success: prints a confirmation that the merged config is valid.
    On failure: prints actionable error(s) to stderr and exits non-zero.
    Critical: on failure, the JSON sentinel block MUST NOT appear on stdout
    so downstream review skills cannot consume an invalid config.

    Fail-closed order (each step short-circuits before the next):
      1. Target path must exist
      2. Walk-up must complete within the depth cap
      3. Every chain file must parse as JSON
      4. Every chain file must declare the supported schema version
      5. The effective merged config must satisfy domain invariants
    """
    missing = _check_target_exists(target, base)
    if missing is not None:
        print(missing, file=sys.stderr)
        return 1

    walk = walk_up_chain_with_status(target, stop=base)
    if walk.depth_capped:
        print(_depth_cap_error_message(target), file=sys.stderr)
        return 1

    chain = walk.chain
    raw_configs, error = read_chain_configs(chain)
    if error is not None:
        print(error, file=sys.stderr)
        return 1

    version_check = validate_schema_versions(raw_configs, source_chain=chain)
    if not version_check.ok:
        _print_validation_errors(version_check.errors)
        return 1

    merged = deep_merge_chain(raw_configs)
    effective = build_effective_config(merged)
    result = validate_effective(effective, source_chain=chain)

    if result.ok:
        if chain:
            print(f"Valid: merged config from {chain[0]}")
        else:
            print("Valid: built-in defaults (no fitness-config.json found)")
        return 0

    _print_validation_errors(result.errors)
    return 1

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage fitness-config.json for project fitness review skills."
    )
    parser.add_argument(
        "command",
        choices=["validate", "init", "show", "audit"],
        help="Command to run",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Config file path (default: fitness-config.json) — legacy mode for show/validate/init",
    )
    parser.add_argument(
        "--path",
        dest="resolve_path",
        default=None,
        help="(show/validate/init) Resolve walk-up chain or seed override starting from this target path",
    )
    parser.add_argument("--from", dest="proposal_source", default=None,
                        help="(init --path) read a proposed config from stdin ('-')")
    parser.add_argument("--dry-run", action="store_true",
                        help="(init --path --from -) validate and show the proposal; write nothing")
    parser.add_argument("--expect", default=None,
                        help="(init --path --from -) fingerprint of the reviewed proposal to save")
    parser.add_argument("--force", action="store_true",
                        help="(init --path --from - --expect FP) replace an existing config")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    # `audit` is a special-case CI gate: it scans the repo for inline weight
    # tables and direct fitness-config.json loads in SKILL.md prose. It does
    # not accept --path or a positional config path; the scan root is cwd.
    if args.command == "audit":
        if args.resolve_path is not None or args.path is not None:
            print(
                "Error: audit takes no path arguments — it scans cwd",
                file=sys.stderr,
            )
            return 2
        return cmd_audit(Path.cwd())

    gate_error = _gate_usage_error(args)
    if gate_error is not None:
        print(gate_error, file=sys.stderr)
        return 2

    if args.resolve_path is not None:
        if args.path is not None:
            print(
                "Error: positional path and --path are mutually exclusive",
                file=sys.stderr,
            )
            return 2
        target = Path(args.resolve_path)
        if args.command == "show":
            return cmd_show_path(target, base=Path.cwd())
        if args.command == "validate":
            return cmd_validate_path(target, base=Path.cwd())
        if args.command == "init" and args.proposal_source is not None:
            return cmd_init_from(target, Path.cwd(), sys.stdin.read(),
                                 args.dry_run, args.expect, args.force)
        if args.command == "init" and args.dry_run:
            return cmd_init_baseline(target, Path.cwd())
        if args.command == "init":
            return cmd_init_path(target, base=Path.cwd())
        return 1

    legacy_path = Path(args.path) if args.path else Path(CONFIG_FILENAME)

    if args.command == "validate":
        return cmd_validate(legacy_path)
    if args.command == "init":
        return cmd_init(legacy_path)
    if args.command == "show":
        return cmd_show(legacy_path)
    return 1
