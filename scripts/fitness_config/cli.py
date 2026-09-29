"""Command-line shell: argparse wiring and the cmd_* verbs.

The only module that talks to the user: it composes the pure core with the
filesystem adapters, prints, and turns outcomes into exit codes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters import config_file_at, load_legacy_config, read_anchored_chain, read_chain_configs
from .audit import cmd_audit
from .model import CONFIG_FILENAME
from .render import render_canonical, render_show_output
from .resolution import (WALK_UP_DEPTH_CAP, build_effective_config, build_seed_config,
                         deep_merge_chain, merge_defaults, walk_up_chain_with_status)
from .validation import validate_config, validate_effective, validate_schema_versions
from .write_gate import GateOutcome, check_proposal, save_reviewed_proposal

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2


def _print_errors(errors: list[str]) -> None:
    for line in errors:
        print(line, file=sys.stderr)


def _write_json(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# ---------------------------------------------------------------------------
# Legacy single-file verbs: validate|init|show [path]
# ---------------------------------------------------------------------------

def cmd_validate(path: Path) -> int:
    """Legacy `validate [path]`: strict per-file rules; errors name the file (NFR-3)."""
    data = load_legacy_config(path)
    if data is None:
        print(f"Error: {path} not found or invalid JSON", file=sys.stderr)
        return EXIT_FAILED
    violations = validate_config(data)
    if violations:
        _print_errors([f"Error: {line}" for line in violations])
        print(f"Error: invalid config: {path}", file=sys.stderr)
        return EXIT_FAILED
    print("Valid:", path)
    return EXIT_OK


def cmd_init(path: Path) -> int:
    """Legacy `init [path]`: write the built-in defaults; never overwrite."""
    if path.exists():
        print(f"Error: {path} already exists", file=sys.stderr)
        return EXIT_FAILED
    _write_json(path, build_seed_config([]))
    print("Created:", path)
    return EXIT_OK


def cmd_show(path: Path) -> int:
    """Legacy `show [path]`: one file over the defaults, as JSON."""
    data = load_legacy_config(path) or {}
    print(json.dumps(merge_defaults(data), indent=2))
    return EXIT_OK


# ---------------------------------------------------------------------------
# Walk-up verbs: show|validate --path TARGET
# ---------------------------------------------------------------------------

def _check_target_exists(target: Path, base: Path) -> str | None:
    """ADR-006 fail-closed: an error when neither the target nor its parent exists
    (a not-yet-created file inside a real folder is fine)."""
    candidate = (base / target) if not target.is_absolute() else target
    if candidate.exists() or candidate.parent.exists():
        return None
    return (
        f"Error: target path does not exist: {target}\n"
        f"  Fix: create the directory at {target}, "
        f"or invoke validate from a path that exists."
    )


def _depth_cap_error_message(target: Path) -> str:
    """ADR-006: a walk that hit WALK_UP_DEPTH_CAP is a pathological tree, not a short chain."""
    return (
        f"Error: pathological-tree depth limit (>{WALK_UP_DEPTH_CAP} levels) "
        f"reached while resolving config from {target}.\n"
        f"  Fix: invoke from a path within a normal repo tree, "
        f"or place a fitness-config.json above the target so resolution can anchor."
    )


def _resolve_effective(target: Path, base: Path) -> tuple[list[Path], dict | None, list[str]]:
    """Walk up from target to base, read and version-check the chain, merge it.

    Returns (chain, effective, []) or (chain, None, errors): the depth cap,
    malformed JSON and a schema version mismatch each stop before merging.
    """
    walk = walk_up_chain_with_status(target, stop=base)
    if walk.depth_capped:
        return walk.chain, None, [_depth_cap_error_message(target)]
    raw_configs, unreadable = read_chain_configs(walk.chain)
    if unreadable is not None:
        return walk.chain, None, [unreadable]
    version_check = validate_schema_versions(raw_configs, source_chain=walk.chain)
    if not version_check.ok:
        return walk.chain, None, version_check.errors
    return walk.chain, build_effective_config(deep_merge_chain(raw_configs)), []


def cmd_show_path(target: Path, base: Path) -> int:
    """`show --path T`: render T's effective config. Fails closed before rendering,
    so no JSON block is printed from a partial chain. A target that does not
    exist yet is allowed: show is a preview; validate is the gate."""
    chain, effective, errors = _resolve_effective(target, base)
    if errors:
        _print_errors(errors)
        return EXIT_FAILED
    sys.stdout.write(render_show_output(target, chain, effective, base=base))
    return EXIT_OK


def cmd_validate_path(target: Path, base: Path) -> int:
    """`validate --path T`: fail closed, in order, on a missing target, the depth
    cap, malformed JSON, a schema version mismatch, then invalid effective weights."""
    missing = _check_target_exists(target, base)
    if missing is not None:
        print(missing, file=sys.stderr)
        return EXIT_FAILED
    chain, effective, errors = _resolve_effective(target, base)
    errors = errors or validate_effective(effective, source_chain=chain).errors
    if errors:
        _print_errors(errors)
        return EXIT_FAILED
    if chain:
        print(f"Valid: merged config from {chain[0]}")
    else:
        print("Valid: built-in defaults (no fitness-config.json found)")
    return EXIT_OK


# ---------------------------------------------------------------------------
# Seeding and the write gate: init --path TARGET [--dry-run | --from - ...]
# ---------------------------------------------------------------------------

def cmd_init_path(target: Path, base: Path) -> int:
    """`init --path T`: seed T/fitness-config.json from the anchored chain's
    effective config (or the defaults, said on stdout); never overwrite."""
    out_path = target / CONFIG_FILENAME
    if out_path.exists():
        print(f"Error: {out_path} already exists", file=sys.stderr)
        return EXIT_FAILED
    _, raw_configs, error, exit_code = read_anchored_chain(target, base)
    if error is not None:
        print(error, file=sys.stderr)
        return exit_code
    _write_json(out_path, build_seed_config(raw_configs))
    if not raw_configs:
        print("No root fitness-config.json found; seeded with documented default weights.")
    print("Created:", out_path)
    return EXIT_OK


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
    return EXIT_OK


_GATE_SUCCESS = {"would-create", "would-replace", "unchanged", "existing-malformed",
                 "created", "replaced"}


def _print_gate_outcome(outcome: GateOutcome, show_canonical: bool) -> int:
    print(f"STATUS: {outcome.status}")
    if outcome.fingerprint:
        print(f"Proposal: {outcome.fingerprint}")
    _print_errors(list(outcome.errors))
    for line in outcome.review:
        print(line)
    if show_canonical and outcome.canonical:
        sys.stdout.write(outcome.canonical)
    return EXIT_OK if outcome.status in _GATE_SUCCESS else EXIT_FAILED


def cmd_init_from(target: Path, base: Path, proposal_text: str,
                  dry_run: bool, expected_fingerprint: str | None, force: bool = False) -> int:
    """`init --path T --from - (--dry-run | --expect FP [--force])`: the write gate."""
    _, configs_above, error, exit_code = read_anchored_chain(target, base)
    if error is not None:
        print(error, file=sys.stderr)
        return exit_code
    config_file = config_file_at(target / CONFIG_FILENAME)
    if dry_run:
        return _print_gate_outcome(check_proposal(proposal_text, config_file.read()),
                                   show_canonical=True)
    outcome = save_reviewed_proposal(proposal_text, expected_fingerprint, config_file,
                                     configs_above, force)
    return _print_gate_outcome(outcome, show_canonical=False)


# ---------------------------------------------------------------------------
# Argument handling
# ---------------------------------------------------------------------------

def _gate_usage_error(args) -> str | None:
    """The first inconsistency among the write-gate flags, else None."""
    init_with_target = args.command == "init" and args.resolve_path is not None
    if args.proposal_source is None:
        rules = (
            (args.force, "Error: --force needs --from - and --expect <fingerprint>"),
            (bool(args.expect), "Error: --expect needs --from -"),
            (args.dry_run and not init_with_target, "Error: --dry-run only works with init --path"),
        )
    else:
        rules = (
            (not init_with_target, "Error: --from only works with init --path"),
            (args.proposal_source != "-", "Error: --from takes '-' (read the proposal from stdin)"),
            (args.force and args.dry_run, "Error: --force saves; it does not go with --dry-run"),
            (not args.dry_run and args.expect is None,
             "Error: saving needs --expect <fingerprint> of a reviewed proposal; "
             "run with --dry-run first to see it"),
        )
    return next((message for broken, message in rules if broken), None)


def _usage_error(args) -> str | None:
    """Argument combinations argparse cannot express, checked before any work."""
    if args.command == "audit":
        if args.resolve_path is not None or args.path is not None:
            return "Error: audit takes no path arguments — it scans cwd"
        return None
    gate_error = _gate_usage_error(args)
    if gate_error is not None:
        return gate_error
    if args.resolve_path is not None and args.path is not None:
        return "Error: positional path and --path are mutually exclusive"
    return None


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


def _run_with_target(args) -> int:
    target, base = Path(args.resolve_path), Path.cwd()
    if args.command == "show":
        return cmd_show_path(target, base)
    if args.command == "validate":
        return cmd_validate_path(target, base)
    if args.proposal_source is not None:
        return cmd_init_from(target, base, sys.stdin.read(), args.dry_run, args.expect, args.force)
    if args.dry_run:
        return cmd_init_baseline(target, base)
    return cmd_init_path(target, base)


_LEGACY_COMMANDS = {"validate": cmd_validate, "init": cmd_init, "show": cmd_show}


def main() -> int:
    args = _build_parser().parse_args()
    usage_error = _usage_error(args)
    if usage_error is not None:
        print(usage_error, file=sys.stderr)
        return EXIT_USAGE
    if args.command == "audit":
        # CI gate: scans the repo at cwd for inline weight tables and direct config loads.
        return cmd_audit(Path.cwd())
    if args.resolve_path is not None:
        return _run_with_target(args)
    legacy_path = Path(args.path) if args.path else Path(CONFIG_FILENAME)
    return _LEGACY_COMMANDS[args.command](legacy_path)
