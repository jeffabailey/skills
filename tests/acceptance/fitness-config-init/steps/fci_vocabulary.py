"""Shared journey vocabulary for fitness-config-init.

The step methods every milestone reuses: setting up persona projects,
checking a proposal, saving it, replacing a config, asking for starting
weights, validating a config, and the observable outcomes of those actions.

Pillar 2 (chained narrative): each "has checked" / "has asked" / "has saved"
Given is the SAME function as the matching When, so a scenario's Given replays
the previous scenario's action instead of copying its setup.

Pillar 3 (app as in production): every action runs the real resolver CLI as a
subprocess with cwd = the project folder (the anchor the skill uses).

Mandate 8: actions that could change files capture workspace snapshots, and
outcomes assert with assert_state_delta over the full file universe.

Step modules import this with `from fci_vocabulary import *`; pytest-bdd step
fixtures registered here become visible to the importing module.
"""

from __future__ import annotations

import json

from pytest_bdd import given, parsers, then, when

from fci_state_delta import anything, assert_state_delta, set_to_content, universe_of  # noqa: E402
from fci_support import (  # noqa: E402
    CONFIG,
    DEFAULT_SCORING,
    DEFAULT_SECURITY,
    DEFAULT_STATUS,
    DEFAULT_WEIGHTS,
    FIELDNOTES_ROOT,
    JUNE_LEDGERD,
    REPO_ROOT,
    EXAMPLE_CONFIG,
    fingerprint_of,
    parse_gate_report,
    proposal,
    require_status,
    run_resolver,
    sha256_of_bytes,
    to_stdin,
)

SAVE_OK = {"created", "replaced", "unchanged"}
CHECK_OK = {"would-create", "would-replace", "unchanged", "existing-malformed"}


def _mark_initial(workspace, context) -> None:
    """Snapshot after the Givens that shape the file tree."""
    context["initial"] = workspace.snapshot()


# ---------------------------------------------------------------------------
# Given: persona projects
# ---------------------------------------------------------------------------

@given(parsers.parse("{person}'s project \"{project}\" has no fitness config"))
def project_without_config(workspace, context, person, project):
    anchor = workspace.create_project(project)
    assert not list(anchor.rglob(CONFIG)), f"{project} unexpectedly has a fitness config"
    _mark_initial(workspace, context)


@given(parsers.parse("{person}'s project \"{project}\" has a root fitness config"))
def project_with_root_config(workspace, context, person, project):
    workspace.write_config(workspace.create_project(project), FIELDNOTES_ROOT)
    _mark_initial(workspace, context)


@given(parsers.parse("{person}'s project \"{project}\" already has the fitness config she tuned in June"))
def project_with_june_config(workspace, context, person, project):
    workspace.write_config(workspace.create_project(project), JUNE_LEDGERD)
    _mark_initial(workspace, context)


@given(parsers.parse(
    "{person}'s project \"{project}\" already has a fitness config equal to the {name} proposal"))
def project_with_matching_config(workspace, context, person, project, name):
    # Written with non-canonical formatting on purpose: "equal" is by value.
    workspace.write_config(workspace.create_project(project), proposal(name))
    _mark_initial(workspace, context)


@given(parsers.parse("a stray fitness config favouring accessibility sits in the folder above \"{project}\""))
def stray_config_above(workspace, context, project):
    from fci_support import STRAY_ABOVE_ANCHOR
    workspace.write_config(workspace.root, STRAY_ABOVE_ANCHOR)
    _mark_initial(workspace, context)


# ---------------------------------------------------------------------------
# Actions (When) that double as chained Givens
# ---------------------------------------------------------------------------

def check_proposal(workspace, context, target: str, config) -> None:
    """`init --path T --from - --dry-run`: validate, render, diff, fingerprint."""
    anchor, rel = workspace.split_target(target)
    before = workspace.snapshot()
    run = run_resolver(anchor, "init", "--path", rel, "--from", "-", "--dry-run",
                       stdin_text=to_stdin(config))
    after = workspace.snapshot()
    context.update(report=parse_gate_report(run), proposal=config, target=target)
    # A check never touches the project, whatever its verdict.
    assert_state_delta(before, after, universe_of(before, after), {})


@when(parsers.parse("{person} checks the {name} proposal for \"{target}\""))
def checks_named_proposal(workspace, context, person, name, target):
    check_proposal(workspace, context, target, proposal(name))


@given(parsers.parse("{person} has checked the {name} proposal for \"{target}\""))
def has_checked_named_proposal(workspace, context, person, name, target):
    checks_named_proposal(workspace, context, person, name, target)
    report = context["report"]
    require_status(report, *sorted(CHECK_OK))
    assert report.fingerprint, f"check showed no proposal fingerprint\n{report.run.describe()}"
    context["reviewed"] = {
        "target": target,
        "proposal": proposal(name),
        "fingerprint": report.fingerprint,
        "canonical": report.canonical_text,
    }


def save_proposal(workspace, context, target: str, config, fingerprint: str | None,
                  *, force: bool = False) -> None:
    """`init --path T --from - --expect FP [--force]`: the gated write."""
    anchor, rel = workspace.split_target(target)
    args = ["init", "--path", rel, "--from", "-"]
    if fingerprint is not None:
        args += ["--expect", fingerprint]
    if force:
        args.append("--force")
    run = run_resolver(anchor, *args, stdin_text=to_stdin(config))
    context["save"] = parse_gate_report(run)


def _reviewed(context, target):
    reviewed = context.get("reviewed")
    assert reviewed and reviewed["target"] == target, f"no reviewed proposal for {target}"
    return reviewed


@when(parsers.parse("{person} saves the reviewed proposal for \"{target}\""))
def saves_reviewed_proposal(workspace, context, person, target):
    reviewed = _reviewed(context, target)
    save_proposal(workspace, context, target, reviewed["proposal"], reviewed["fingerprint"])


@given(parsers.parse("{person} has saved the reviewed proposal for \"{target}\""))
def has_saved_reviewed_proposal(workspace, context, person, target):
    saves_reviewed_proposal(workspace, context, person, target)
    require_status(context["save"], "created")


@when(parsers.parse("{person} confirms replacing the config for \"{target}\" with the reviewed proposal"))
def confirms_replacing(workspace, context, person, target):
    reviewed = _reviewed(context, target)
    save_proposal(workspace, context, target, reviewed["proposal"], reviewed["fingerprint"], force=True)


@when(parsers.parse("the {name} proposal is saved for \"{target}\" against {person}'s reviewed fingerprint"))
def other_proposal_saved(workspace, context, name, target, person):
    save_proposal(workspace, context, target, proposal(name), _reviewed(context, target)["fingerprint"])


@when(parsers.parse(
    "the {name} proposal replaces the config for \"{target}\" against {person}'s reviewed fingerprint"))
def other_proposal_replaces(workspace, context, name, target, person):
    save_proposal(workspace, context, target, proposal(name),
                  _reviewed(context, target)["fingerprint"], force=True)


@when(parsers.parse("{person} saves the {name} proposal for \"{target}\" without a reviewed fingerprint"))
def saves_without_fingerprint(workspace, context, person, name, target):
    save_proposal(workspace, context, target, proposal(name), None)


def ask_starting_weights(workspace, context, target: str) -> None:
    anchor, rel = workspace.split_target(target)
    before = workspace.snapshot()
    run = run_resolver(anchor, "init", "--path", rel, "--dry-run")
    after = workspace.snapshot()
    context["starting"] = parse_gate_report(run)
    assert_state_delta(before, after, universe_of(before, after), {})


@when(parsers.parse("{person} asks for the starting weights for \"{target}\""))
def asks_starting_weights(workspace, context, person, target):
    ask_starting_weights(workspace, context, target)


@given(parsers.parse("{person} has asked for the starting weights for \"{target}\""))
def has_asked_starting_weights(workspace, context, person, target):
    ask_starting_weights(workspace, context, target)
    require_status(context["starting"], "baseline")
    assert context["starting"].canonical_text, context["starting"].run.describe()


@when(parsers.parse("{person} validates the fitness config file in \"{target}\""))
def validates_config_file(workspace, context, person, target):
    anchor, rel = workspace.split_target(target)
    file_arg = CONFIG if rel == "." else f"{rel}/{CONFIG}"
    context["validation"] = run_resolver(anchor, "validate", file_arg)


@when("the maintainer validates the published example config")
def validates_example(context):
    context["validation"] = run_resolver(REPO_ROOT, "validate", str(EXAMPLE_CONFIG))


# ---------------------------------------------------------------------------
# Then: outcomes of a check
# ---------------------------------------------------------------------------

@then("the check reports the proposal would create a new config")
def check_would_create(context):
    require_status(context["report"], "would-create")
    assert context["report"].run.exit_code == 0, context["report"].run.describe()


@then("the check reports the proposal would replace the current config")
def check_would_replace(context):
    require_status(context["report"], "would-replace")
    assert context["report"].run.exit_code == 0, context["report"].run.describe()


@then("the check reports no changes")
def check_unchanged(context):
    require_status(context["report"], "unchanged")
    assert context["report"].run.exit_code == 0, context["report"].run.describe()


@then(parsers.parse("the proposal is rejected with a reason naming \"{word}\""))
def rejected_naming(context, word):
    report = context.get("save") if context.get("rejection_from_save") else context["report"]
    require_status(report, "invalid")
    assert report.run.exit_code == 1, report.run.describe()
    assert word.lower() in report.run.output.lower(), (
        f"reason does not name {word!r}\n{report.run.describe()}")


# ---------------------------------------------------------------------------
# Then: outcomes of a save
# ---------------------------------------------------------------------------

@then(parsers.parse("the save reports the config was {outcome}"))
def save_outcome(context, outcome):
    save = context["save"]
    if outcome == "not written":
        assert save.run.exit_code != 0, save.run.describe()
        assert save.status not in SAVE_OK, save.run.describe()
        assert "Traceback" not in save.run.stderr, save.run.describe()
        return
    require_status(save, outcome)
    assert save.run.exit_code == 0, save.run.describe()


@then("the save is refused because a config already exists")
def save_refused_exists(context):
    require_status(context["save"], "refused-exists")
    assert context["save"].run.exit_code == 1, context["save"].run.describe()


@then(parsers.parse("the save is refused because it is not the proposal {person} reviewed"))
def save_refused_mismatch(context, person):
    require_status(context["save"], "fingerprint-mismatch")
    assert context["save"].run.exit_code == 1, context["save"].run.describe()


@then("the save is refused")
def save_refused(context):
    save = context["save"]
    assert save.run.exit_code != 0, save.run.describe()
    assert save.status not in SAVE_OK, save.run.describe()


# ---------------------------------------------------------------------------
# Then: the files Priya can see
# ---------------------------------------------------------------------------

@then(parsers.parse("the fitness config in \"{target}\" is identical to the reviewed proposal"))
def config_identical_to_reviewed(workspace, context, target):
    reviewed = _reviewed(context, target)
    path = workspace.config_path(target)
    assert path.is_file(), f"no fitness config at {path}"
    saved = path.read_bytes()
    assert reviewed["canonical"] is not None, "the check showed no config to compare with"
    assert saved.decode("utf-8") == reviewed["canonical"], "saved bytes differ from the reviewed proposal"
    assert json.loads(saved) == reviewed["proposal"]
    assert fingerprint_of(saved.decode("utf-8")) == reviewed["fingerprint"]
    now = workspace.snapshot()
    assert_state_delta(context["initial"], now, universe_of(context["initial"], now),
                       {workspace.key(path): set_to_content(sha256_of_bytes(saved))})


@then(parsers.parse("the fitness config in \"{target}\" passes the resolver's validation"))
def config_passes_validation(workspace, target):
    anchor, rel = workspace.split_target(target)
    chain_check = run_resolver(anchor, "validate", "--path", rel)
    assert chain_check.exit_code == 0, chain_check.describe()
    file_arg = CONFIG if rel == "." else f"{rel}/{CONFIG}"
    strict_check = run_resolver(anchor, "validate", file_arg)
    assert strict_check.exit_code == 0, strict_check.describe()


@then(parsers.parse("reviews of \"{target}\" will use its own fitness config"))
def reviews_use_own_config(workspace, target):
    anchor, rel = workspace.split_target(target)
    shown = run_resolver(anchor, "show", "--path", rel)
    assert shown.exit_code == 0, shown.describe()
    expected = CONFIG if rel == "." else f"{rel}/{CONFIG}"
    assert f"Config: {expected}" in shown.stdout.splitlines(), shown.describe()


@then(parsers.parse("nothing else in \"{project}\" changed"))
def nothing_else_changed(workspace, context, project):
    now = workspace.snapshot()
    config_key = workspace.key(workspace.config_path(project))
    assert_state_delta(context["initial"], now, universe_of(context["initial"], now),
                       {config_key: anything()})


@then(parsers.parse("nothing has been saved in \"{project}\""))
def nothing_saved(workspace, context, project):
    now = workspace.snapshot()
    assert_state_delta(context["initial"], now, universe_of(context["initial"], now), {})


@then(parsers.parse("the fitness config in \"{target}\" is byte-for-byte unchanged"))
def config_unchanged(workspace, context, target):
    key = workspace.key(workspace.config_path(target))
    assert key in context["initial"], f"{key} did not exist before"
    assert_state_delta(context["initial"], workspace.snapshot(), {key}, {})


@then(parsers.parse("the {project} root config is byte-for-byte unchanged"))
def root_config_unchanged(workspace, context, project):
    key = f"{project}/{CONFIG}"
    assert key in context["initial"], f"{key} did not exist before"
    assert_state_delta(context["initial"], workspace.snapshot(), {key}, {})


# ---------------------------------------------------------------------------
# Then: starting weights and validation
# ---------------------------------------------------------------------------

def _starting_config(context) -> dict:
    starting = context["starting"]
    require_status(starting, "baseline")
    assert starting.run.exit_code == 0, starting.run.describe()
    assert starting.canonical_text, starting.run.describe()
    return json.loads(starting.canonical_text)


@then("the starting weights are the built-in defaults")
def starting_is_defaults(context):
    config = _starting_config(context)
    assert context["starting"].header_value("Baseline-Source") == "defaults", context["starting"].run.describe()
    assert config == {"version": 1, "weights": DEFAULT_WEIGHTS, "statusThresholds": DEFAULT_STATUS,
                      "security": DEFAULT_SECURITY, "scoring": DEFAULT_SCORING}, config


@then("the validation passes")
def validation_passes(context):
    run = context["validation"]
    assert run.exit_code == 0, run.describe()


@then("the validation fails")
def validation_fails(context):
    run = context["validation"]
    assert run.exit_code != 0, run.describe()
