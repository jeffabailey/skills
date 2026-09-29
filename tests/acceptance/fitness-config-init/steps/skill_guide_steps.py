"""Steps: the knowledge the agent follows (skill guide, purpose profiles,
purpose signals), the config audit, and bundle-level consistency checks.

Binds milestone-1, milestone-4 and integration-checkpoints. The static files
are the product for the agent-judgment half of the skill; profiles are checked
through the resolver (driving port) rather than by re-implementing its rules.
@manual scenarios in these features have no step definitions: they are
skipped at collection and run as agent evals.
"""

from __future__ import annotations

import json
import re

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from fci_state_delta import assert_state_delta, universe_of  # noqa: E402
from fci_support import (  # noqa: E402
    ARCHETYPES,
    CONFIG,
    DOMAINS,
    EXAMPLE_CONFIG,
    FIELDNOTES_ROOT,
    PROFILE_CATALOGUE,
    REPO_ROOT,
    SIGNAL_GUIDE,
    SKILL_GUIDE,
    complete_config,
    parse_frontmatter,
    parse_gate_report,
    parse_profile_table,
    read_required,
    run_resolver,
    to_stdin,
)
from fci_vocabulary import *  # noqa: E402,F401,F403
from fci_vocabulary import _mark_initial, _starting_config  # noqa: E402

scenarios(
    "../milestone-1-purpose-and-proposal.feature",
    "../milestone-4-full-review-evidence.feature",
    "../integration-checkpoints.feature",
)

_WEIGHT_NUMBER = re.compile(r"\b(" + "|".join(DOMAINS) + r")\b[ \t:=*|`\"'>-]{0,4}\d{1,3}\b", re.I)


# ---------------------------------------------------------------------------
# Purpose profile catalogue
# ---------------------------------------------------------------------------

@given("the purpose profile catalogue shipped with the skill")
def profile_catalogue(context):
    context["catalogue_text"] = read_required(PROFILE_CATALOGUE, "purpose profile catalogue")


@when("the skill loads its profile catalogue")
def load_profile_catalogue(context):
    columns, rows = parse_profile_table(context["catalogue_text"])
    context["profile_columns"], context["profiles"] = columns, rows


def _profiles(context) -> dict[str, dict[str, int]]:
    if "profiles" not in context:
        load_profile_catalogue(context)
    out = {}
    for archetype, cells in context["profiles"].items():
        assert all(re.fullmatch(r"\d+", v) for v in cells.values()), (archetype, cells)
        out[archetype] = {d: int(v) for d, v in cells.items()}
    return out


@then(parsers.parse("it offers exactly the archetypes \"{names}\""))
def offers_archetypes(context, names):
    expected = [n.strip() for n in names.split(",")]
    assert expected == ARCHETYPES
    assert sorted(context["profiles"]) == sorted(expected), sorted(context["profiles"])


@then("every profile weighs all ten fitness domains in the standard order")
def profiles_standard_order(context):
    assert context["profile_columns"] == DOMAINS, context["profile_columns"]


@then("every profile gives each domain a whole-number weight of at least 1")
def profiles_floor(context):
    for archetype, weights in _profiles(context).items():
        low = {d: v for d, v in weights.items() if v < 1}
        assert not low, f"{archetype} has weights below 1: {low}"


@then("every profile's weights add up to 100")
def profiles_sum(context):
    for archetype, weights in _profiles(context).items():
        assert sum(weights.values()) == 100, f"{archetype} adds up to {sum(weights.values())}"


@when(parsers.parse("each profile is checked as a proposal for \"{target}\""))
def check_each_profile(workspace, context, target):
    anchor, rel = workspace.split_target(target)
    before = workspace.snapshot()
    context["profile_checks"] = {
        archetype: parse_gate_report(run_resolver(
            anchor, "init", "--path", rel, "--from", "-", "--dry-run",
            stdin_text=to_stdin(complete_config(weights))))
        for archetype, weights in _profiles(context).items()
    }
    after = workspace.snapshot()
    assert_state_delta(before, after, universe_of(before, after), {})


@then("the resolver would accept every profile as a new config")
def every_profile_accepted(context):
    rejected = {a: r.run.describe() for a, r in context["profile_checks"].items()
                if r.status != "would-create" or r.run.exit_code != 0}
    assert not rejected, "\n".join(f"{a}:\n{d}" for a, d in rejected.items())


@then(parsers.parse("the \"{archetype}\" profile weighs reliability and data above their starting weights"))
def profile_raises_reliability_data(context, archetype):
    start = _starting_config(context)["weights"]
    profile = _profiles(context)[archetype]
    for domain in ("reliability", "data"):
        assert profile[domain] > start[domain], f"{domain}: {profile[domain]} vs starting {start[domain]}"


@then(parsers.parse("the \"{archetype}\" profile weighs accessibility below its starting weight"))
def profile_lowers_accessibility(context, archetype):
    start = _starting_config(context)["weights"]
    assert _profiles(context)[archetype]["accessibility"] < start["accessibility"]


@then(parsers.parse("accessibility is the highest weight in the \"{archetype}\" profile"))
def accessibility_highest(context, archetype):
    profile = _profiles(context)[archetype]
    others = max(v for d, v in profile.items() if d != "accessibility")
    assert profile["accessibility"] > others, profile


# ---------------------------------------------------------------------------
# Purpose signal guide
# ---------------------------------------------------------------------------

@given("the purpose signal guide shipped with the skill")
def signal_guide(context):
    context["signals_text"] = read_required(SIGNAL_GUIDE, "purpose signal guide")


@when("the skill loads its purpose signal guide")
def load_signal_guide(context):
    context["signals"] = context["signals_text"].lower()


@then("it defines what high, medium and low confidence mean")
def defines_confidence(context):
    text = context["signals"]
    assert "confidence" in text
    for level in ("high", "medium", "low"):
        assert re.search(rf"\b{level}\b", text), f"confidence level {level!r} not defined"


@then(parsers.parse("it limits the fast scan to {count:d} files"))
def limits_reads(context, count):
    assert re.search(rf"\b{count}\b[^\n]*\bfiles?\b", context["signals"]), f"no {count}-file read budget stated"


# ---------------------------------------------------------------------------
# Skill guide (SKILL.md)
# ---------------------------------------------------------------------------

@given("the fitness-config-init skill guide")
def skill_guide(context):
    context["guide"] = read_required(SKILL_GUIDE, "fitness-config-init skill guide")


@when("an agent host loads the skill guide")
def load_skill_guide(context):
    context["frontmatter"] = parse_frontmatter(context["guide"])


@then(parsers.parse("the skill is named \"{name}\""))
def skill_named(context, name):
    assert context["frontmatter"].get("name") == name, context["frontmatter"]


@then("its description says when to use it")
def description_has_triggers(context):
    description = context["frontmatter"].get("description", "")
    assert "use when" in description.lower(), f"description lacks trigger phrases: {description!r}"


@then("it has a workflow section")
def has_workflow(context):
    assert re.search(r"^## Workflow\b", context["guide"], re.M), "no '## Workflow' section"


@then(parsers.parse("it runs the resolver from \"{path}\""))
def runs_resolver_from(context, path):
    assert path in context["guide"], f"resolver location {path!r} not referenced"


@then("it points to its purpose profile and purpose signal references")
def points_to_references(context):
    for ref, path in (("references/purpose-profiles.md", PROFILE_CATALOGUE),
                      ("references/purpose-signals.md", SIGNAL_GUIDE)):
        assert ref in context["guide"], f"{ref} not referenced"
        assert path.is_file(), f"{ref} referenced but missing"


@then("it contains no weight numbers of its own")
def no_weight_numbers(context):
    hits = [ln.strip() for ln in context["guide"].splitlines() if _WEIGHT_NUMBER.search(ln)]
    assert not hits, "weight numbers found in the skill guide:\n" + "\n".join(hits)
    assert not re.search(r'"weights"\s*:\s*\{', context["guide"]), "inline weight table found"


@then("it saves only proposals the maintainer reviewed")
def saves_reviewed_only(context):
    guide = context["guide"]
    assert "--dry-run" in guide and "--expect" in guide, (
        "the guide must check with --dry-run and save with --expect <fingerprint>")


@then(parsers.parse("it warns that a full review writes \"{path}\""))
def warns_about_report(context, path):
    assert path in context["guide"], f"{path} not disclosed"


# ---------------------------------------------------------------------------
# Config audit
# ---------------------------------------------------------------------------

def _checkout_with_guide(workspace, line: str):
    checkout = workspace.root / "checkout"
    workspace.write_raw(checkout / "skills" / "fitness-config-init" / "SKILL.md",
                        f"---\nname: fitness-config-init\n---\n\n## Workflow\n\n{line}\n")
    return checkout


@given("a skills checkout whose fitness-config-init guide contains an inline weight table")
def checkout_inline_table(workspace, context):
    context["checkout"] = _checkout_with_guide(workspace, '```json\n{ "weights": { "security": 30 } }\n```')


@given("a skills checkout whose fitness-config-init guide reads fitness-config.json directly")
def checkout_direct_read(workspace, context):
    # Literal split so the repo-wide audit grep in fitness-config-per-directory
    # does not flag this test file itself.
    context["checkout"] = _checkout_with_guide(workspace, 'cfg = json.load(open("fitness-config' + '.json"))')


@given("the skills repository as shipped")
def shipped_repository(context):
    context["checkout"] = REPO_ROOT


@when(parsers.parse("the maintainer runs the config audit on {what}"))
def run_audit(context, what):
    context["audit"] = run_resolver(context["checkout"], "audit")


@then("the audit fails and names the fitness-config-init guide")
def audit_fails_naming_guide(context):
    audit = context["audit"]
    assert audit.exit_code == 1, audit.describe()
    assert "fitness-config-init/SKILL.md" in audit.stderr, audit.describe()


@then("the audit passes")
def audit_passes(context):
    assert context["audit"].exit_code == 0, context["audit"].describe()


@then("the audit covered the fitness-config-init guide")
def audit_covered_guide(context):
    assert SKILL_GUIDE.is_file(), "fitness-config-init/SKILL.md not yet delivered"
    expected = len(list((REPO_ROOT / "skills").glob("review-*/SKILL.md"))) + 1
    expected += int((REPO_ROOT / ".github" / "fitness-review-prompt.md").is_file())
    m = re.search(r"scanned (\d+)", context["audit"].stdout)
    assert m and int(m.group(1)) == expected, (
        f"audit scanned {m.group(1) if m else '?'} files, expected {expected} "
        f"(review-* guides + fitness-config-init + prompt)\n{context['audit'].describe()}")


# ---------------------------------------------------------------------------
# Bundle consistency
# ---------------------------------------------------------------------------

@then("the starting config is byte-for-byte the published example config")
def starting_equals_example(context):
    _starting_config(context)
    assert context["starting"].canonical_text == EXAMPLE_CONFIG.read_text(encoding="utf-8"), (
        "the built-in starting config and fitness-config.example.json have drifted apart")


@given("the published example config")
def published_example():
    assert EXAMPLE_CONFIG.is_file()


@given(parsers.parse(
    "{person}'s project \"{project}\" has an override in \"{folder}\" that only sets the security cutoff to {cutoff:d}"))
def override_security_only(workspace, context, person, project, folder, cutoff):
    anchor = workspace.create_project(project)
    workspace.write_config(anchor, FIELDNOTES_ROOT)
    workspace.write_config(anchor / folder, {"version": 1, "security": {"confidenceThreshold": cutoff}})
    _mark_initial(workspace, context)


_REJECTED_SAMPLES = [
    {"version": 2},
    {"version": 1, "weights": {"usability": 100}},
    {"version": 1, "weights": {"security": 101}},
    {"version": 1, "weights": {"security": -1}},
    {"version": 1, "weights": {"security": "high"}},
    {"version": 1, "security": {"confidenceThreshold": 0}},
    {"version": 1, "security": {"confidenceThreshold": 11}},
    {"version": 1, "statusThresholds": {"healthy": [8, 9, 10]}},
    {"version": 1, "scoring": {"goodRange": "8-10"}},
]


@given("a set of sample configs the published config format rejects")
def schema_rejected_samples(workspace, context):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((REPO_ROOT / "fitness-config.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for sample in _REJECTED_SAMPLES:
        assert list(validator.iter_errors(sample)), f"schema unexpectedly accepts {sample}"
    context["samples"] = _REJECTED_SAMPLES


@when("each sample is validated by the resolver")
def validate_samples(workspace, context):
    results = []
    for idx, sample in enumerate(context["samples"]):
        path = workspace.write_raw(workspace.root / f"sample-{idx}" / CONFIG, json.dumps(sample))
        results.append((sample, run_resolver(path.parent, "validate", CONFIG)))
    context["sample_results"] = results


@then("the resolver rejects every sample")
def resolver_rejects_samples(context):
    accepted = [s for s, run in context["sample_results"] if run.exit_code == 0]
    assert not accepted, f"resolver accepts configs the schema rejects: {accepted}"
