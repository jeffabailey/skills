"""Steps: the reviewed-save gate, strict validation, the anchor rule,
replacing an existing config, and purpose-tuned thresholds.

Binds walking-skeleton, milestone-2, milestone-3 and milestone-5. Shared
journey vocabulary comes from fci_vocabulary (star import registers its
pytest-bdd step fixtures in this module).
"""

from __future__ import annotations

import json
import re

from pytest_bdd import given, parsers, scenarios, then, when

from fci_state_delta import assert_state_delta, universe_of  # noqa: E402
from fci_support import (  # noqa: E402
    CONFIG,
    DEFAULT_WEIGHTS,
    FIELDNOTES_ROOT,
    JUNE_LEDGERD,
    NOT_UTF8_CONFIG,
    fingerprint_of,
    json_with_key_twice,
    parse_gate_report,
    proposal,
    require_status,
    run_resolver,
)
from fci_vocabulary import *  # noqa: E402,F401,F403
from fci_vocabulary import check_proposal, save_proposal, _mark_initial  # noqa: E402

scenarios(
    "../walking-skeleton.feature",
    "../milestone-2-safe-first-write.feature",
    "../milestone-3-review-before-replace.feature",
    "../milestone-5-purpose-tuned-thresholds.feature",
)


# ---------------------------------------------------------------------------
# Flawed proposals (milestone-2 outline). Each keeps the other rules intact
# where possible so the named flaw is the reason for rejection.
# ---------------------------------------------------------------------------

def _flawed(flaw: str) -> dict:
    cfg = proposal("database-service")
    w = cfg["weights"]
    if flaw == "adds up to 101":
        w["maintainability"] += 1
    elif flaw == "leaves out the maintainability weight":
        w.pop("maintainability")
    elif flaw == 'adds a weight for "usability"':
        w["usability"], w["maintainability"] = w["maintainability"], 0
    elif flaw == "gives accessibility a weight of -1":
        w["accessibility"], w["maintainability"] = -1, w["maintainability"] + 2
    elif flaw == "gives data a weight of 101":
        w["data"] = 101
    elif flaw == "gives process a fractional weight of 6.5":
        w["process"], w["maintainability"] = 6.5, 4.5
    elif flaw == "gives testing a yes-or-no weight":
        w["testing"] = True
    elif flaw == "has no scoring section":
        cfg.pop("scoring")
    elif flaw == "has a healthy status band with three numbers":
        cfg["statusThresholds"]["healthy"] = [8, 9, 10]
    else:
        raise AssertionError(f"unknown flaw in feature file: {flaw!r}")
    return cfg


@when(parsers.parse("{person} checks a {name} proposal for \"{target}\" that {flaw}"))
def checks_flawed_proposal(workspace, context, person, name, target, flaw):
    check_proposal(workspace, context, target, _flawed(flaw))


@when(parsers.parse("{person} tries to save a {name} proposal for \"{target}\" that {flaw}"))
def tries_to_save_flawed(workspace, context, person, name, target, flaw):
    cfg = _flawed(flaw)
    # A fingerprint in hand does not bypass validation.
    save_proposal(workspace, context, target, cfg, fingerprint_of(json.dumps(cfg, indent=2) + "\n"))
    context["rejection_from_save"] = True


@when(parsers.parse("{person} checks the note \"{note}\" in place of a config for \"{target}\""))
def checks_non_config(workspace, context, person, note, target):
    check_proposal(workspace, context, target, note)


@then("the reason says the weights must add up to 100")
def reason_mentions_100(context):
    report = context["save"] if context.get("rejection_from_save") else context["report"]
    assert "100" in report.run.output, report.run.describe()


@then(parsers.parse("{person} is told a save needs the fingerprint of a reviewed proposal"))
def told_fingerprint_required(context, person):
    save = context["save"]
    assert "--expect" in save.run.stderr and "unrecognized" not in save.run.stderr, save.run.describe()


@then("the proposal is rejected as unreadable")
def rejected_unreadable(context):
    require_status(context["report"], "invalid")
    assert context["report"].run.exit_code == 1, context["report"].run.describe()
    assert "Traceback" not in context["report"].run.stderr, context["report"].run.describe()


# ---------------------------------------------------------------------------
# What Priya is shown before saving
# ---------------------------------------------------------------------------

@then(parsers.parse("{person} is shown a fingerprint of the config exactly as it will be saved"))
def fingerprint_matches_bytes(context, person):
    report = context["report"]
    assert report.canonical_text, report.run.describe()
    assert report.fingerprint == fingerprint_of(report.canonical_text), (
        f"shown fingerprint {report.fingerprint!r} is not the first 12 hex of "
        f"SHA-256 over the config as it will be saved ({fingerprint_of(report.canonical_text)!r})")


@then("the config as it will be saved follows the example config's layout")
def canonical_layout(context):
    text = context["report"].canonical_text
    assert text, context["report"].run.describe()
    parsed = json.loads(text)
    assert parsed == context["proposal"]
    assert list(parsed) == ["version", "weights", "statusThresholds", "security", "scoring"]
    assert list(parsed["weights"]) == list(DEFAULT_WEIGHTS)
    lines = text.split("\n")
    assert lines[2].startswith('  "weights": {'), "expected two-space indentation"
    assert '"healthy": [9, 10]' in text or '"healthy": [8, 10]' in text, "ranges must be inline pairs"
    assert text.endswith("}\n") and "\r" not in text, "expected LF endings and a final newline"


@then(parsers.parse("the check lists the change \"{line}\""))
def lists_change(context, line):
    report = context["report"]
    assert line in report.header, f"missing diff line {line!r}\n{report.run.describe()}"
    context.setdefault("asserted_changes", []).append(line)


@then("the check lists no other changes")
def lists_no_other_changes(context):
    changes = [ln for ln in context["report"].diff_lines if " -> " in ln]
    assert sorted(changes) == sorted(context.get("asserted_changes", [])), changes


@then(parsers.parse("the check says {count:d} values are unchanged"))
def unchanged_count(context, count):
    assert f"({count} values unchanged)" in context["report"].header, context["report"].run.describe()


@then("the check lists the note as removed")
def note_removed(context):
    lines = [ln for ln in context["report"].header if ln.startswith("$comment ")]
    assert lines and lines[0].endswith("-> (removed)"), context["report"].run.describe()


@then(parsers.parse("{person} is told the current config cannot be compared value by value"))
def malformed_notice(context, person):
    report = context["report"]
    require_status(report, "existing-malformed")
    assert "cannot diff by value" in report.run.stdout, report.run.describe()


@then(parsers.parse("{person} is shown the complete proposal"))
def shown_complete_proposal(context, person):
    report = context["report"]
    assert report.canonical_text, report.run.describe()
    assert json.loads(report.canonical_text) == context["proposal"]


# ---------------------------------------------------------------------------
# Existing files and the project around the config
# ---------------------------------------------------------------------------

@given(parsers.parse("{person}'s project \"{project}\" has a fitness config with a stray trailing comma"))
def project_with_malformed_config(workspace, context, person, project):
    anchor = workspace.create_project(project)
    workspace.write_raw(anchor / CONFIG, '{\n  "version": 1,\n  "weights": {"testing": 20,},\n}\n')
    _mark_initial(workspace, context)


@given(parsers.parse(
    "{person}'s project \"{project}\" has a fitness config carrying a note the config format does not know"))
def project_with_unknown_key(workspace, context, person, project):
    cfg = {"$comment": "tuned in June by Priya", **JUNE_LEDGERD}
    workspace.write_config(workspace.create_project(project), cfg)
    _mark_initial(workspace, context)


@given(parsers.parse("{person}'s project \"{project}\" has a damaged root fitness config"))
def project_with_damaged_root(workspace, context, person, project):
    anchor = workspace.create_project(project)
    workspace.write_raw(anchor / CONFIG, '{ "version": 1, "weights": ')
    _mark_initial(workspace, context)


@then("the check is refused and names the damaged fieldnotes root config")
def check_refused_names_root(workspace, context):
    report = context["report"]
    assert report.run.exit_code != 0, report.run.describe()
    assert report.status not in {"would-create", "would-replace", "unchanged"}, report.run.describe()
    assert "fieldnotes/fitness-config.json" in report.run.output, report.run.describe()


# ---------------------------------------------------------------------------
# Input the resolver cannot read: not UTF-8 text, or a key set twice
# ---------------------------------------------------------------------------

def _damaged_config_bytes(config: dict, damage: str) -> bytes:
    if damage == "is not UTF-8 text":
        return NOT_UTF8_CONFIG
    repeated = re.fullmatch(r'sets "(\w+)" twice', damage)
    if repeated is None:
        raise AssertionError(f"unknown damage in feature file: {damage!r}")
    return json_with_key_twice(config, repeated.group(1)).encode("utf-8")


@when(parsers.parse("{person} checks bytes that are not UTF-8 text in place of a config for \"{target}\""))
def checks_non_utf8(workspace, context, person, target):
    check_proposal(workspace, context, target, NOT_UTF8_CONFIG)


@when(parsers.parse(
    "{person} checks the {name} proposal for \"{target}\" written with \"{key}\" set twice"))
def checks_key_twice(workspace, context, person, name, target, key):
    check_proposal(workspace, context, target, json_with_key_twice(proposal(name), key))


@given(parsers.parse("{person}'s project \"{project}\" has a root fitness config that {damage}"))
def project_with_unreadable_root(workspace, context, person, project, damage):
    anchor = workspace.create_project(project)
    (anchor / CONFIG).write_bytes(_damaged_config_bytes(FIELDNOTES_ROOT, damage))
    _mark_initial(workspace, context)


@given(parsers.parse("{person}'s project \"{project}\" has a fitness config file that {damage}"))
def project_with_unreadable_config(workspace, context, person, project, damage):
    anchor = workspace.create_project(project)
    (anchor / CONFIG).write_bytes(_damaged_config_bytes(proposal("database-service"), damage))
    _mark_initial(workspace, context)


# ---------------------------------------------------------------------------
# Targets that are not folders, and a folder where the config belongs
# ---------------------------------------------------------------------------

@given(parsers.parse("{person}'s project \"{project}\" has a folder named \"{name}\""))
def project_with_folder_named(workspace, context, person, project, name):
    anchor = workspace.create_project(project)
    workspace.write_raw(anchor / name / "notes.txt", "kept here by hand\n")
    _mark_initial(workspace, context)


def _reviewable_fingerprint(workspace, config: dict) -> str:
    """The fingerprint a check shows for config, taken in a scratch folder
    outside the workspace so the project under test is never touched."""
    scratch = workspace.root.parent / "fingerprint-scratch"
    scratch.mkdir(exist_ok=True)
    report = parse_gate_report(run_resolver(scratch, "init", "--path", ".", "--from", "-", "--dry-run",
                                            stdin_text=json.dumps(config)))
    require_status(report, "would-create")
    return report.fingerprint


@when(parsers.parse("{person} saves the {name} proposal with its fingerprint for \"{target}\""))
def saves_with_fingerprint(workspace, context, person, name, target):
    cfg = proposal(name)
    save_proposal(workspace, context, target, cfg, _reviewable_fingerprint(workspace, cfg))


@then(parsers.parse(
    "the {action} is refused because \"{name}\" in \"{project}\" is not a regular file"))
def refused_not_regular_file(context, action, name, project):
    report = context["save" if action == "save" else "report"]
    require_status(report, "existing-not-a-file")
    assert report.run.exit_code == 1, report.run.describe()
    assert f"{project}/{name}" in report.run.stderr, report.run.describe()
    assert "not a regular file" in report.run.stderr, report.run.describe()
    assert report.fingerprint is None, "a fingerprint invites a save that cannot succeed"


def _last_run(context):
    for key in ("save", "report", "starting"):
        if key in context:
            return context[key].run
    return context["setup"]


@then(parsers.parse("the request is refused because \"{target}\" {problem}"))
def request_refused_target(context, target, problem):
    run = _last_run(context)
    assert run.exit_code == 2, run.describe()
    assert "STATUS:" not in run.stdout, run.describe()
    assert "Traceback" not in run.stderr, run.describe()
    assert target in run.stderr and problem in run.stderr, run.describe()


@given(parsers.parse("the folder \"{project}\" cannot be written to"))
def folder_read_only(workspace, not_root, project):
    workspace.make_read_only(workspace.project(project))


# ---------------------------------------------------------------------------
# Starting point and the anchor rule (data-models.md section 6.3)
# ---------------------------------------------------------------------------

def _starting_source_paths(context) -> list[str]:
    return [ln.strip() for ln in context["starting"].header
            if ln.strip().endswith(CONFIG) and not ln.startswith(("STATUS:", "Baseline-Source:"))]


@then("the starting weights equal the fieldnotes root weights")
def starting_equals_root(context):
    from fci_vocabulary import _starting_config
    config = _starting_config(context)
    assert context["starting"].header_value("Baseline-Source") == "chain", context["starting"].run.describe()
    assert config["weights"] == FIELDNOTES_ROOT["weights"], config["weights"]


@then("the starting point names the fieldnotes root config as its source")
def starting_names_root(context):
    paths = _starting_source_paths(context)
    assert len(paths) == 1 and "billing" not in paths[0], (paths, context["starting"].run.describe())


@then("the starting point does not mention the stray config")
def starting_ignores_stray(workspace, context):
    assert _starting_source_paths(context) == [], context["starting"].run.describe()
    assert str(workspace.root / CONFIG) not in context["starting"].run.output


@when(parsers.parse("{person} sets up a default fitness config for \"{target}\""))
def sets_up_default(workspace, context, person, target):
    anchor, rel = workspace.split_target(target)
    context["setup"] = run_resolver(anchor, "init", "--path", rel)


@then(parsers.parse("the new fitness config in \"{target}\" carries the built-in default weights"))
def seeded_defaults(workspace, context, target):
    run = context["setup"]
    assert run.exit_code == 0, run.describe()
    seeded = json.loads(workspace.config_path(target).read_text(encoding="utf-8"))
    assert seeded["weights"] == DEFAULT_WEIGHTS, (
        f"seeded weights came from outside the project: {seeded['weights']}")


@given(parsers.parse("a folder \"{other}\" sits next to \"{project}\""))
def neighbour_folder(workspace, context, other, project):
    workspace.write_raw(workspace.root / other / "README.md", "old ledger exports\n")
    _mark_initial(workspace, context)


@when(parsers.parse(
    "{person}, working in \"{project}\", sets up a default fitness config for the neighbouring folder \"{other}\""))
def sets_up_neighbour(workspace, context, person, project, other):
    context["setup"] = run_resolver(workspace.project(project), "init", "--path", f"../{other}")


@then("the set-up is refused because the folder is outside the project")
def setup_refused_outside(context):
    assert context["setup"].exit_code == 2, context["setup"].describe()


@then(parsers.parse("no fitness config appears in \"{other}\""))
def no_config_in(workspace, context, other):
    assert not (workspace.root / other / CONFIG).exists()
    now = workspace.snapshot()
    assert_state_delta(context["initial"], now, universe_of(context["initial"], now), {})


# ---------------------------------------------------------------------------
# Stricter validation of hand-edited configs (ADR-008)
# ---------------------------------------------------------------------------

@given(parsers.parse(
    "{person}'s project \"{project}\" has a hand-edited fitness config with a \"{domain}\" weight "
    "and a security cutoff of \"{cutoff}\""))
def hand_edited_config(workspace, context, person, project, domain, cutoff):
    cfg = proposal("database-service")
    cfg["weights"][domain] = cfg["weights"].pop("maintainability")
    cfg["security"]["confidenceThreshold"] = cutoff
    workspace.write_config(workspace.create_project(project), cfg)
    _mark_initial(workspace, context)


@then(parsers.parse("the validation names \"{word}\""))
def validation_names(context, word):
    assert word in context["validation"].output, context["validation"].describe()


@then("the validation names the security cutoff")
def validation_names_cutoff(context):
    assert "confidenceThreshold" in context["validation"].output, context["validation"].describe()


@then("the validation reports its findings without crashing")
def validation_no_crash(context):
    assert "Traceback" not in context["validation"].stderr, context["validation"].describe()


# ---------------------------------------------------------------------------
# Purpose-tuned thresholds (milestone-5)
# ---------------------------------------------------------------------------

def _band(spec: str) -> list[int]:
    lo, _, hi = spec.partition("-")
    return [int(lo), int(hi)]


@when(parsers.parse(
    "{person} checks the {name} proposal for \"{target}\" with status bands healthy {healthy}, "
    "needs attention {attention}, critical {critical} and a security cutoff of {cutoff:d}"))
def checks_with_thresholds(workspace, context, person, name, target, healthy, attention, critical, cutoff):
    cfg = proposal(name)
    cfg["statusThresholds"] = {"healthy": _band(healthy), "needsAttention": _band(attention),
                               "critical": _band(critical)}
    cfg["security"]["confidenceThreshold"] = cutoff
    check_proposal(workspace, context, target, cfg)


@then("the proposal is rejected with a reason about the status bands")
def rejected_status_bands(context):
    report = context["report"]
    require_status(report, "invalid")
    assert report.run.exit_code == 1, report.run.describe()
    assert "status" in report.run.output.lower(), report.run.describe()


@then("the proposal is rejected with a reason about the security cutoff")
def rejected_security_cutoff(context):
    report = context["report"]
    require_status(report, "invalid")
    assert report.run.exit_code == 1, report.run.describe()
    assert "confidenceThreshold" in report.run.output, report.run.describe()


# ---------------------------------------------------------------------------
# Subfolder override announced in the chain (walking skeleton 3)
# ---------------------------------------------------------------------------

@then(parsers.parse(
    "reviews of \"{target}\" will use the billing config merged with the fieldnotes root config"))
def reviews_use_merged_chain(workspace, target):
    anchor, rel = workspace.split_target(target)
    shown = run_resolver(anchor, "show", "--path", rel)
    assert shown.exit_code == 0, shown.describe()
    lines = shown.stdout.splitlines()
    assert f"Config: {rel}/{CONFIG} (merged with root, found by walking up from input path)" in lines, shown.describe()
    assert any(ln.strip() == f"1. {rel}/{CONFIG}  (override)" for ln in lines), shown.describe()
    assert any(ln.strip() == f"2. {CONFIG}  (root)" for ln in lines), shown.describe()
