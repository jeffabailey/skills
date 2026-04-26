"""Step definitions: config resolution, deep-merge, show subcommand.

Steps speak the domain language (root config, module override, effective
weights, source chain). All steps invoke the driving port — the
`fitness-config.py` CLI — via the `repo.run(...)` helper.

This module covers:
  - walking-skeleton.feature
  - milestone-1-walk-up-discovery.feature
  - milestone-2-deep-merge.feature
  - milestone-3-provenance.feature (show subcommand half)
  - milestone-5-backward-compat.feature
  - integration-checkpoints.feature (resolution-related scenarios)
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from .conftest import (
    DEFAULT_SCORING,
    DEFAULT_SECURITY,
    DEFAULT_STATUS_THRESHOLDS,
    DEFAULT_WEIGHTS,
    RepoTree,
    assert_text_contains_all,
    find_embedded_json_block,
    parse_int_pair,
    parse_weights_string,
)

scenarios(
    "../walking-skeleton.feature",
    "../milestone-1-walk-up-discovery.feature",
    "../milestone-2-deep-merge.feature",
    "../milestone-3-provenance.feature",
    "../milestone-5-backward-compat.feature",
    "../integration-checkpoints.feature",
)


# ---------------------------------------------------------------------------
# Given — repo state setup
# ---------------------------------------------------------------------------

@given(parsers.parse(
    'the repo has a root fitness-config.json with weights "{spec}"'
))
def root_config_with_weights(repo: RepoTree, spec: str):
    repo.write_root_config(
        weights=parse_weights_string(spec),
        status=dict(DEFAULT_STATUS_THRESHOLDS),
        security=dict(DEFAULT_SECURITY),
        scoring=dict(DEFAULT_SCORING),
    )


@given("the repo has a root fitness-config.json with the default weights")
def root_config_with_defaults(repo: RepoTree):
    repo.write_default_root_config()


@given("Devin has a clean repo with a fitness-config.json at the repo root using the default weights")
def background_root_default(repo: RepoTree):
    repo.write_default_root_config()


@given("the repo has a valid root fitness-config.json")
def root_config_valid(repo: RepoTree):
    repo.write_default_root_config()


@given("the repo has a valid root fitness-config.json with the default weights")
def root_config_valid_default(repo: RepoTree):
    repo.write_default_root_config()


@given(parsers.parse(
    'the repo has a root fitness-config.json with weights "{spec}" and status thresholds healthy "{healthy}"'
))
def root_config_with_status(repo: RepoTree, spec: str, healthy: str):
    repo.write_root_config(
        weights=parse_weights_string(spec),
        status={**DEFAULT_STATUS_THRESHOLDS, "healthy": parse_int_pair(healthy)},
        security=dict(DEFAULT_SECURITY),
        scoring=dict(DEFAULT_SCORING),
    )


@given('the root config defines status thresholds with healthy "[8,10]"')
def root_status_8_10(repo: RepoTree):
    # Already covered by default root in scenarios that use this step alongside the
    # default-weights Background, but we repeat to make a standalone Given safe.
    if not repo.exists("fitness-config.json"):
        repo.write_default_root_config()


@given("the repo has no fitness-config.json at any level")
def no_config_anywhere(repo: RepoTree):
    # The Background may have written a root config; this Given overrides
    # the Background to establish a tree with no fitness-config.json anywhere.
    root_cfg = repo.path_at("fitness-config.json")
    if root_cfg.exists():
        root_cfg.unlink()
    # Confirm there is none anywhere in the tree.
    for stray in repo.root.rglob("fitness-config.json"):
        stray.unlink()


@given("the repo has only a root fitness-config.json and no module overrides anywhere")
def only_root_config(repo: RepoTree):
    repo.write_default_root_config()


@given("the repo has no root fitness-config.json")
def no_root_config(repo: RepoTree):
    assert not repo.exists("fitness-config.json")


@given("the repo has no fitness-config.json at the root")
def no_root_config_at_root(repo: RepoTree):
    # Milestone-5 phrasing for the bare-`init` backward-compat scenario.
    # Same precondition as `no_root_config` but co-located here so pytest-bdd
    # 8.x can resolve it from this scenario module.
    if repo.exists("fitness-config.json"):
        repo.path_at("fitness-config.json").unlink()
    assert not repo.exists("fitness-config.json")


@given(parsers.parse(
    'the repo has a root fitness-config.json whose weights sum to 95 in isolation'
))
def root_config_invalid_sum(repo: RepoTree):
    bad_weights = dict(DEFAULT_WEIGHTS)
    bad_weights["data"] = 5  # default 10 -> 5 makes sum 95
    repo.write_root_config(weights=bad_weights)


# --- module override Givens ---

@given(parsers.parse(
    'a module override at "{path}" sets weights "{spec}"'
))
def module_override_with_weights(repo: RepoTree, path: str, spec: str):
    repo.write_config_at(path, {"version": 1, "weights": parse_weights_string(spec)})


@given(parsers.parse('a module override at "{path}" sets "{spec}"'))
def module_override_partial(repo: RepoTree, path: str, spec: str):
    repo.write_config_at(path, {"version": 1, "weights": parse_weights_string(spec)})


@given(parsers.parse(
    'a module override at "{path}" sets all 10 weights summing to 100'
))
def module_override_full(repo: RepoTree, path: str):
    full = {
        "architecture": 10, "security": 10, "reliability": 25, "testing": 10,
        "performance": 5, "algorithms": 5, "data": 30, "accessibility": 0,
        "process": 3, "maintainability": 2,
    }
    repo.write_config_at(path, {"version": 1, "weights": full})


@given(parsers.parse(
    'a module override at "{path}" sets only the security confidence threshold to {value:d}'
))
def module_override_security(repo: RepoTree, path: str, value: int):
    repo.write_config_at(path, {
        "version": 1,
        "security": {"confidenceThreshold": value},
    })


@given(parsers.parse(
    'a module override at "{path}" sets status thresholds healthy to "{healthy}"'
))
def module_override_status(repo: RepoTree, path: str, healthy: str):
    repo.write_config_at(path, {
        "version": 1,
        "statusThresholds": {"healthy": parse_int_pair(healthy)},
    })


@given(parsers.parse('the override does not mention "architecture", "security", or "testing"'))
def assert_override_omissions(repo: RepoTree):
    # Documentation-only Given: confirms test reader's understanding of partial-override semantics.
    pass


@given(parsers.parse('a module override at "{path}" exists'))
def module_override_exists(repo: RepoTree, path: str):
    if not repo.exists(path):
        repo.write_config_at(path, {"version": 1, "weights": dict(DEFAULT_WEIGHTS)})


@given(parsers.parse('the file "{path}" exists'))
def file_exists(repo: RepoTree, path: str):
    repo.touch_file(path)


@given(parsers.parse('no fitness-config.json exists in "{path}"'))
def no_config_at(repo: RepoTree, path: str):
    candidate = repo.path_at(path) / "fitness-config.json"
    assert not candidate.exists()


@given(parsers.parse('no override exists anywhere under "{path}"'))
def no_override_under(repo: RepoTree, path: str):
    repo.make_dir(path)
    # Walk and confirm no fitness-config.json anywhere in subtree.
    for sub in repo.path_at(path).rglob("fitness-config.json"):
        raise AssertionError(f"Unexpected override file present: {sub}")


# ---------------------------------------------------------------------------
# When — driving-port invocations
# ---------------------------------------------------------------------------

@when(parsers.parse('Devin previews the resolved config for "{path}"'))
def preview_resolution(repo: RepoTree, path: str, context: dict):
    result = repo.run("show", "--path", path)
    context["preview"] = result


@when(parsers.parse('Devin previews the resolved config for "{path}" twice'))
def preview_twice(repo: RepoTree, path: str, context: dict):
    first = repo.run("show", "--path", path)
    second = repo.run("show", "--path", path)
    context["previews"] = [first, second]


@when(parsers.parse('Devin previews the resolved config for "{path}" five times'))
def preview_five(repo: RepoTree, path: str, context: dict):
    context["previews"] = [repo.run("show", "--path", path) for _ in range(5)]


@when(parsers.parse('Devin previews the resolved config for "{path}" {n:d} times'))
def preview_n(repo: RepoTree, path: str, n: int, context: dict):
    context["previews"] = [repo.run("show", "--path", path) for _ in range(n)]


@when("Devin previews the resolved config for the current directory")
def preview_cwd(repo: RepoTree, context: dict):
    context["preview"] = repo.run("show", "--path", ".")


@when("Devin previews the resolved config for the repo root")
def preview_repo_root(repo: RepoTree, context: dict):
    context["preview"] = repo.run("show", "--path", str(repo.root))


@when(parsers.parse('Devin previews the resolved config for "{path}" supplying both a positional path and --path'))
def preview_both_args(repo: RepoTree, path: str, context: dict):
    repo.write_default_root_config()
    context["preview"] = repo.run("show", path, "--path", path)


@when("Devin previews the resolved config supplying both a positional path and --path")
def preview_both_default(repo: RepoTree, context: dict):
    context["preview"] = repo.run("show", "fitness-config.json", "--path", ".")


@when("Devin previews the resolved config without specifying a path")
def preview_no_args(repo: RepoTree, context: dict):
    context["preview"] = repo.run("show")


@when("Devin validates the config without specifying a path")
def validate_no_path_m5(repo: RepoTree, context: dict):
    context["validate"] = repo.run("validate")


@when("Devin initializes a config without specifying a path")
def init_no_path_m5(repo: RepoTree, context: dict):
    context["init"] = repo.run("init")


@when(parsers.parse(
    'Devin previews the resolved config for that deeply nested target {n:d} times'
))
def preview_deep_n(repo: RepoTree, n: int, context: dict):
    deep_path = context["deep_path"]
    timings = []
    previews = []
    for _ in range(n):
        start = time.perf_counter()
        result = repo.run("show", "--path", deep_path)
        timings.append(time.perf_counter() - start)
        previews.append(result)
    context["previews"] = previews
    context["timings"] = timings


@when("Devin previews the resolved config for that deeply nested path")
def preview_deep_one(repo: RepoTree, context: dict):
    context["preview"] = repo.run("show", "--path", context["deep_path"])


@given(parsers.parse(
    'Devin invokes resolution from a path {depth:d} levels deep with no fitness-config.json on the way up'
))
def deep_path_no_config(repo: RepoTree, depth: int, context: dict):
    parts = [f"d{i}" for i in range(depth)]
    rel = "/".join(parts)
    repo.touch_file(f"{rel}/leaf.txt")
    context["deep_path"] = f"{rel}/leaf.txt"


@given("a target file 10 levels deep with a module override 8 levels deep")
def target_10_deep(repo: RepoTree, context: dict):
    parts = [f"d{i}" for i in range(10)]
    rel = "/".join(parts)
    repo.touch_file(f"{rel}/leaf.txt")
    override_dir = "/".join(parts[:8])
    repo.write_config_at(
        f"{override_dir}/fitness-config.json",
        {"version": 1, "weights": dict(DEFAULT_WEIGHTS)},
    )
    context["deep_path"] = f"{rel}/leaf.txt"


# ---------------------------------------------------------------------------
# Then — observable outcomes from the driving port
# ---------------------------------------------------------------------------

@then("the preview confirms the override applies on top of the root")
def then_preview_confirms_override(context: dict):
    preview = context["preview"]
    assert preview.succeeded, preview.combined_output
    assert "merged with root" in preview.stdout


@then(parsers.parse(
    'the effective weights show "{domain}" at {value:d} and "{domain2}" at {value2:d}'
))
def then_effective_weights_shows(context: dict, domain: str, value: int, domain2: str, value2: int):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None, "expected embedded JSON block in show output"
    weights = block["effective"]["weights"]
    assert weights[domain] == value, f"{domain}={weights[domain]} expected {value}"
    assert weights[domain2] == value2, f"{domain2}={weights[domain2]} expected {value2}"


@then("the effective weights sum to 100")
def then_weights_sum_100(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    total = sum(block["effective"]["weights"].values())
    assert abs(total - 100) <= 0.01, f"sum was {total}"


@then("the preview names the module config as the highest-precedence source")
def then_module_first(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    chain = block["source_chain"]
    assert len(chain) >= 1
    assert "postgresql/fitness-config.json" in chain[0]


@then("the preview names the root config as the next source in precedence")
def then_root_second(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    chain = block["source_chain"]
    assert len(chain) >= 2
    assert chain[-1].endswith("fitness-config.json")
    assert "postgresql" not in chain[-1]


@then("the source chain names the module override first and the root config second")
def then_chain_module_root(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    chain = block["source_chain"]
    assert len(chain) == 2, f"expected 2 entries, got {chain}"
    assert "modules/" in chain[0]
    assert chain[1].endswith("fitness-config.json")


@then('the effective weights reflect "data=30" from the override')
def then_data_30(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    assert block["effective"]["weights"]["data"] == 30


@then("the source chain names the same module override first and the root config second")
def then_same_chain(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    chain = block["source_chain"]
    assert len(chain) == 2
    assert "postgresql/fitness-config.json" in chain[0]


@then("the preview explains that the override was found by walking up from the input path")
def then_walkup_explanation(context: dict):
    text = context["preview"].stdout.lower()
    assert "walk" in text or "walking up" in text or "ancestor" in text or "found by" in text, \
        "expected walk-up explanation in preview"


@then("the source chain names only the root config")
def then_root_only_chain(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    chain = block["source_chain"]
    assert len(chain) == 1, f"expected single-entry chain, got {chain}"
    assert chain[0].endswith("fitness-config.json")


@then("the effective weights match the root config exactly")
def then_weights_match_root(context: dict, repo: RepoTree):
    root_data = repo.read_json("fitness-config.json")
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    for k, v in root_data["weights"].items():
        assert block["effective"]["weights"][k] == v


@then('the preview reports "built-in defaults (no fitness-config.json found)"')
def then_defaults_message(context: dict):
    assert "built-in defaults" in context["preview"].stdout
    assert "no fitness-config.json found" in context["preview"].stdout


@then("the effective weights match the documented default weights")
def then_default_weights(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    for k, v in DEFAULT_WEIGHTS.items():
        assert block["effective"]["weights"][k] == v


@then("both previews produce the same source chain and effective weights")
def then_two_previews_same(context: dict):
    a, b = context["previews"]
    assert a.stdout == b.stdout, "previews differ — non-deterministic output"


@then("both previews produce byte-identical output")
def then_byte_identical_two(context: dict):
    a, b = context["previews"]
    assert a.stdout == b.stdout
    assert a.stderr == b.stderr


@then("all five previews produce byte-identical output")
def then_byte_identical_five(context: dict):
    previews = context["previews"]
    first = previews[0].stdout
    for idx, p in enumerate(previews[1:], start=2):
        assert p.stdout == first, f"preview #{idx} differs from preview #1"


@then(parsers.parse('the average preview wall-clock time stays under {millis:d} milliseconds'))
def then_perf_budget(context: dict, millis: int):
    timings = context["timings"]
    avg_ms = sum(timings) / len(timings) * 1000
    assert avg_ms < millis, f"avg {avg_ms:.1f}ms exceeded budget {millis}ms"


# --- deep merge specifics (milestone 2) ---

@then('the effective weights show "architecture=14", "security=14", and "testing=10" inherited from the root')
def then_inherited_weights(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    w = block["effective"]["weights"]
    assert w["architecture"] == 14
    assert w["security"] == 14
    assert w["testing"] == 10


@then(parsers.parse(
    'the effective weights show "{spec}" from the override'
))
def then_override_weights(context: dict, spec: str):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    w = block["effective"]["weights"]
    for domain, expected in parse_weights_string(spec).items():
        assert w[domain] == expected, f"{domain}={w[domain]} expected {expected}"


@then("every effective weight comes from the override")
def then_all_from_override(context: dict, repo: RepoTree):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    override = repo.read_json("infrastructure/modules/postgresql/fitness-config.json")
    for k, v in override["weights"].items():
        assert block["effective"]["weights"][k] == v


@then("no effective weight is inherited from the root")
def then_none_inherited(context: dict, repo: RepoTree):
    # Tautologically holds when full override is present and previous step passes;
    # we explicitly assert the override sums to 100 here for clarity.
    override = repo.read_json("infrastructure/modules/postgresql/fitness-config.json")
    assert abs(sum(override["weights"].values()) - 100) <= 0.01


@then('the effective status thresholds healthy range is "[8,10]" inherited from the root')
def then_healthy_8_10(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    healthy = block["effective"]["statusThresholds"]["healthy"]
    assert list(healthy) == [8, 10]


@then(parsers.parse(
    'the effective security confidence threshold is {value:d} from the override'
))
def then_security_threshold(context: dict, value: int):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    assert block["effective"]["security"]["confidenceThreshold"] == value


@then('the effective status thresholds healthy range is "[9,10]" from the override')
def then_healthy_9_10(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    assert list(block["effective"]["statusThresholds"]["healthy"]) == [9, 10]


# --- show-table rendering (milestone 3) ---

@then("the preview lists the module override first and the root second in precedence order")
def then_lists_chain_in_order(context: dict):
    text = context["preview"].stdout
    assert "config sources" in text or "Config sources" in text or "source" in text.lower()
    block = find_embedded_json_block(text)
    assert block is not None
    chain = block["source_chain"]
    assert len(chain) == 2
    assert "modules/" in chain[0]


@then('the preview names the override using the phrasing "merged with root"')
def then_merged_with_root(context: dict):
    assert "merged with root" in context["preview"].stdout


@then("the preview displays the effective weights as a table with one row per domain")
def then_weights_table(context: dict):
    text = context["preview"].stdout
    for domain in DEFAULT_WEIGHTS.keys():
        assert domain in text, f"domain {domain} missing from preview table"


@then(parsers.parse('the preview shows the effective total of {total:d} with an OK status'))
def then_total_ok(context: dict, total: int):
    text = context["preview"].stdout
    assert str(total) in text
    assert "OK" in text


@then("the preview command exits with success")
def then_preview_succeeded(context: dict):
    result = context["preview"]
    assert result.succeeded, f"exit={result.exit_code} stderr={result.stderr}"


@then('the preview names only the root config without any "merged with..." phrasing')
def then_root_only_no_merged(context: dict):
    text = context["preview"].stdout
    assert "merged with" not in text
    block = find_embedded_json_block(text)
    assert block is not None
    assert len(block["source_chain"]) == 1


@then("the preview displays the documented default weights as a table")
def then_default_weights_table(context: dict):
    text = context["preview"].stdout
    for domain in DEFAULT_WEIGHTS.keys():
        assert domain in text


@then("the inline effective-weights line lists all 10 domain names with their effective values")
def then_inline_weights_line(context: dict):
    text = context["preview"].stdout
    # Look for a single line containing all 10 domain names.
    for line in text.splitlines():
        if all(d in line for d in DEFAULT_WEIGHTS.keys()):
            return
    raise AssertionError("No single line lists all 10 domains in the preview output")


@then("the domains are ordered by descending effective weight, ties broken alphabetically")
def then_domains_ordered(context: dict):
    text = context["preview"].stdout
    block = find_embedded_json_block(text)
    assert block is not None
    weights = block["effective"]["weights"]
    expected_order = sorted(weights.keys(), key=lambda d: (-weights[d], d))
    # Find the inline line with all domains and verify ordering.
    for line in text.splitlines():
        if all(d in line for d in DEFAULT_WEIGHTS.keys()):
            positions = [line.index(d) for d in expected_order]
            assert positions == sorted(positions), \
                f"domains not in descending-weight order: {expected_order} positions={positions}"
            return
    raise AssertionError("No inline weights line found to verify order")


# --- backward compatibility (milestone 5) ---

@then("the preview prints the root config merged with the documented defaults")
def then_show_no_path(context: dict):
    text = context["preview"].stdout
    # Legacy show prints JSON of merged-with-defaults config.
    assert '"weights"' in text


@then('the preview output contains no "merged with..." phrasing')
def then_no_merged_phrase(context: dict):
    assert "merged with" not in context["preview"].stdout


# --- integration checkpoints ---

@then("the preview optionally lists the discovered subtree overrides as a footnote that explains they are not applied at root scope")
def then_optional_footnote(context: dict):
    # AC-03.7 says the SKILL prompt produces this footnote; the resolver
    # itself does not. We assert only that the source chain is root-only.
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    assert len(block["source_chain"]) == 1


@then("the source chain does not name the postgresql module override")
def then_no_pg_override(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None
    for entry in block["source_chain"]:
        assert "postgresql" not in entry


@then("the preview command exits with a non-zero status indicating an argument error")
def then_argparse_error(context: dict):
    result = context["preview"]
    assert result.exit_code != 0
    # argparse uses exit code 2 for argument errors.
    assert result.exit_code == 2 or "argument" in result.stderr.lower() or "mutually exclusive" in result.stderr.lower()


@then("the error explains that the positional path and --path cannot be used together")
def then_mutex_message(context: dict):
    text = context["preview"].combined_output.lower()
    assert "mutually exclusive" in text or "cannot be used together" in text or "not allowed with" in text


@then("the preview output contains a fenced effective-config JSON block")
def then_fenced_json(context: dict):
    block = find_embedded_json_block(context["preview"].stdout)
    assert block is not None, "expected sentinel-delimited JSON block"


@then("the JSON block lists the same source chain shown in the human-readable section")
def then_json_chain_matches(context: dict):
    text = context["preview"].stdout
    block = find_embedded_json_block(text)
    assert block is not None
    for entry in block["source_chain"]:
        # The path should appear somewhere in the human-readable section.
        # We split off the JSON sentinel block to check.
        human_part = text.split("<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->")[0]
        assert Path(entry).name in human_part or entry in human_part


@then("the JSON block lists the same effective weights shown in the human-readable section")
def then_json_weights_match(context: dict):
    text = context["preview"].stdout
    block = find_embedded_json_block(text)
    assert block is not None
    human_part = text.split("<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->")[0]
    for domain, value in block["effective"]["weights"].items():
        assert domain in human_part, f"domain {domain} missing from human-readable section"


# --- US-08 audit ---

@given("the repository's review skill prompts and supporting scripts")
def repo_review_artifacts(repo: RepoTree, context: dict):
    # We grep the REAL repo (not tmp_path), since this scenario validates
    # the actual codebase audit, not a synthetic fixture.
    context["audit_root"] = Path(__file__).resolve().parents[4]


@when("the CI audit step greps for direct loads of fitness-config.json outside the resolver script")
def run_audit_grep(context: dict):
    import re
    audit_root = context["audit_root"]
    pattern = re.compile(r"(json\.load.*fitness-config\.json|open.*fitness-config\.json)")
    matches = []
    for p in audit_root.rglob("*"):
        if not p.is_file():
            continue
        if "scripts/fitness-config.py" in str(p):
            continue
        if "tests/acceptance/fitness-config-per-directory" in str(p):
            continue
        if "/docs/" in str(p) or p.suffix not in {".py", ".md"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line in text.splitlines():
            if pattern.search(line):
                matches.append((str(p), line.strip()))
    context["audit_matches"] = matches


@then("no matches are found")
def then_no_audit_matches(context: dict):
    assert context["audit_matches"] == [], \
        f"audit found violations: {context['audit_matches']}"


@given(parsers.parse('a module override at "{path}" sets "data=30"'))
def given_pg_data_30(repo: RepoTree, path: str):
    repo.write_config_at(path, {"version": 1, "weights": {"data": 30}})


@when(parsers.parse('the resolver is queried by any per-domain review skill scoped to "{scope}"'))
def query_resolver_for_domain(repo: RepoTree, scope: str, context: dict):
    context["preview"] = repo.run("show", "--path", scope)


@then("the resolver output contains a Config line naming the override merged with root")
def then_config_line(context: dict):
    text = context["preview"].stdout
    config_lines = [ln for ln in text.splitlines() if ln.startswith("Config:")]
    assert config_lines, "no Config: line in resolver output"
    assert "merged with root" in config_lines[0]


@then("the resolver output contains an Effective weights line listing all 10 domains")
def then_effective_weights_line(context: dict):
    text = context["preview"].stdout
    weight_lines = [ln for ln in text.splitlines() if ln.startswith("Effective weights:")]
    assert weight_lines, "no Effective weights: line in resolver output"
    for domain in DEFAULT_WEIGHTS.keys():
        assert domain in weight_lines[0], f"{domain} missing from Effective weights line"


# ---------------------------------------------------------------------------
# Validate-related steps duplicated for milestone-2 AC-02.7 which exercises
# the validate driving port. Source-of-truth definitions live in
# error_handling_steps.py for milestone-4; pytest-bdd 8.x scopes step
# definitions to the module that registers the scenario, so the AC-02.7
# scenario in milestone-2 needs these defs co-located here.
# ---------------------------------------------------------------------------

@given(parsers.parse(
    'a module override at "{path}" produces an effective weight total of {total:d} after merge'
))
def m2_override_with_effective_total(repo: RepoTree, path: str, total: int):
    if not repo.exists("fitness-config.json"):
        repo.write_default_root_config()
    if total == 100:
        weights = {"data": 30, "reliability": 20, "performance": 6, "algorithms": 4,
                   "accessibility": 0, "process": 1, "maintainability": 1}
    else:
        override_sum = total - 38
        weights = {"data": override_sum - 24, "reliability": 6, "performance": 6,
                   "algorithms": 4, "accessibility": 0, "process": 4,
                   "maintainability": 4}
        actual = sum(weights.values())
        weights["data"] += override_sum - actual
    repo.write_config_at(path, {"version": 1, "weights": weights})


@when(parsers.parse('Devin validates the effective config at "{path}"'))
def m2_validate_at_path(repo: RepoTree, path: str, context: dict):
    context["validate"] = repo.run("validate", "--path", path)


@then("the validate command exits with a non-zero status")
def m2_then_validate_failed(context: dict):
    result = context["validate"]
    assert result.exit_code != 0, f"expected failure, got exit=0: {result.stdout}"


@then("no review can be initiated for that path until the merged config is fixed")
def m2_then_no_review_initiated(context: dict):
    result = context["validate"]
    assert result.exit_code != 0
    assert "<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->" not in result.stdout


# ---------------------------------------------------------------------------
# Milestone-5 backward-compat Then steps. The same outcomes are asserted by
# error_handling_steps.py for milestone-4 and milestone-6, but pytest-bdd 8.x
# scopes step definitions to the module that registers the scenario, so the
# milestone-5 scenarios (loaded above) need their Then steps co-located here.
# ---------------------------------------------------------------------------

@then("the validate command exits with success")
def m5_then_validate_succeeded(context: dict):
    result = context["validate"]
    assert result.succeeded, f"expected success, got exit={result.exit_code}: {result.stderr}"


@then("the output names the root config as valid")
def m5_then_root_named_valid(context: dict):
    text = context["validate"].stdout
    assert "fitness-config.json" in text
    assert "Valid" in text or "valid" in text.lower()


@then("the error names the root config and the invalid sum")
def m5_then_root_invalid_named(context: dict):
    text = context["validate"].combined_output
    assert "fitness-config.json" in text
    assert "sum" in text.lower() or "weights" in text.lower()


@then(parsers.parse('a root fitness-config.json is created with the documented default weights'))
def m5_then_root_created_default(repo: RepoTree):
    assert repo.exists("fitness-config.json")
    cfg = repo.read_json("fitness-config.json")
    for k, v in DEFAULT_WEIGHTS.items():
        assert cfg["weights"][k] == v


@then("the init command exits with success")
def m5_then_init_succeeded(context: dict):
    result = context["init"]
    assert result.succeeded, f"init failed: exit={result.exit_code} stderr={result.stderr}"
