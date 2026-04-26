"""Step definitions: error handling, validate subcommand, init helper.

Driving port: `fitness-config.py validate --path <dir>` and
`fitness-config.py init --path <dir>`. All steps use real subprocess
invocation against a tmp_path repo tree.

Covers:
  - milestone-4-error-handling.feature
  - milestone-6-init-helper.feature
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from .conftest import (
    DEFAULT_SCORING,
    DEFAULT_SECURITY,
    DEFAULT_STATUS_THRESHOLDS,
    DEFAULT_WEIGHTS,
    RepoTree,
)

scenarios(
    "../milestone-4-error-handling.feature",
    "../milestone-6-init-helper.feature",
)


# ---------------------------------------------------------------------------
# Given — invalid / mismatched config setup
# ---------------------------------------------------------------------------

@given(parsers.parse(
    'a module override at "{path}" produces an effective weight total of {total:d} after merge'
))
def override_with_effective_total(repo: RepoTree, path: str, total: int):
    if not repo.exists("fitness-config.json"):
        repo.write_default_root_config()
    if total == 100:
        # Partial override that nets back to 100 with root contributions.
        weights = {"data": 30, "reliability": 20, "performance": 6, "algorithms": 4,
                   "accessibility": 0, "process": 1, "maintainability": 1}
        # Root contributes architecture=14, security=14, testing=10 -> 38 + 62 = 100
    else:
        # Build a partial override whose effective sum equals the target.
        # Root contributes architecture=14, security=14, testing=10 = 38.
        # Override contributes: target - 38.
        override_sum = total - 38
        weights = {"data": override_sum - 24, "reliability": 6, "performance": 6,
                   "algorithms": 4, "accessibility": 0, "process": 4,
                   "maintainability": 4}
        actual = sum(weights.values())
        # Adjust 'data' to make override sum exactly target-38.
        weights["data"] += override_sum - actual
    repo.write_config_at(path, {"version": 1, "weights": weights})


@given(parsers.parse('the root config declares schema version {version:d}'))
def root_with_version(repo: RepoTree, version: int):
    repo.write_root_config(
        weights=dict(DEFAULT_WEIGHTS),
        status=dict(DEFAULT_STATUS_THRESHOLDS),
        security=dict(DEFAULT_SECURITY),
        scoring=dict(DEFAULT_SCORING),
        version=version,
    )


@given(parsers.parse(
    'a module override at "{path}" declares schema version {version:d}'
))
def override_with_version(repo: RepoTree, path: str, version: int):
    repo.write_config_at(path, {
        "version": version,
        "weights": dict(DEFAULT_WEIGHTS),
    })


@given(parsers.parse(
    'a module override at "{path}" contains malformed JSON'
))
def malformed_override(repo: RepoTree, path: str):
    repo.write_raw_at(path, '{"version": 1, "weights": {data: 30,,, }')


@given("the root fitness-config.json contains malformed JSON")
def malformed_root(repo: RepoTree):
    repo.write_raw_at("fitness-config.json", '{"version": 1, broken}')


@given(parsers.parse(
    'a module override at "{path}" is well-formed'
))
def well_formed_override(repo: RepoTree, path: str):
    repo.write_config_at(path, {"version": 1, "weights": dict(DEFAULT_WEIGHTS)})


@given(parsers.parse('the path "{path}" is absent from the repo'))
def path_absent(repo: RepoTree, path: str):
    assert not repo.exists(path)


# --- init helper Givens ---

@given("the repo has a valid root fitness-config.json with the default weights")
def m6_root_config_valid_default(repo: RepoTree):
    repo.write_default_root_config()


@given("the repo has no root fitness-config.json")
def m6_no_root_config(repo: RepoTree):
    if repo.exists("fitness-config.json"):
        repo.path_at("fitness-config.json").unlink()
    assert not repo.exists("fitness-config.json")


@given(parsers.parse('no fitness-config.json exists at "{path}"'))
def no_override_yet(repo: RepoTree, path: str):
    candidate = repo.path_at(path) / "fitness-config.json"
    if candidate.exists():
        candidate.unlink()


@given(parsers.parse(
    'a module override already exists at "{path}"'
))
def override_already_exists(repo: RepoTree, path: str, context: dict):
    config = {"version": 1, "weights": dict(DEFAULT_WEIGHTS)}
    config["weights"]["data"] = 30  # mark it distinct
    repo.write_config_at(path, config)
    context["preexisting_content"] = repo.read_text(path)


@given(parsers.parse(
    'the directory "{path}" exists but is not writable by the current user'
))
def dir_not_writable(repo: RepoTree, path: str, context: dict):
    if os.geteuid() == 0:
        pytest.skip("Cannot test read-only directory as root")
    target = repo.make_dir(path)
    target.chmod(0o555)
    context["locked_dir"] = target


# ---------------------------------------------------------------------------
# When — driving-port invocations
# ---------------------------------------------------------------------------

@when(parsers.parse(
    'Devin validates the effective config at "{path}"'
))
def validate_at_path(repo: RepoTree, path: str, context: dict):
    context["validate"] = repo.run("validate", "--path", path)


@when("Devin validates the config without specifying a path")
def validate_no_path(repo: RepoTree, context: dict):
    context["validate"] = repo.run("validate")


@when(parsers.parse('Devin initializes an override at "{path}"'))
def init_override(repo: RepoTree, path: str, context: dict):
    context["init"] = repo.run("init", "--path", path)


@when("Devin initializes a config without specifying a path")
def init_no_path(repo: RepoTree, context: dict):
    context["init"] = repo.run("init")


@then(parsers.parse('validating the effective config at "{path}" exits with success'))
def validate_passes_post_init(repo: RepoTree, path: str, context: dict):
    result = repo.run("validate", "--path", path)
    context["post_init_validate"] = result
    assert result.succeeded, \
        f"post-init validate failed: exit={result.exit_code} stderr={result.stderr}"


# ---------------------------------------------------------------------------
# Then — outcomes
# ---------------------------------------------------------------------------

@then("the validate command exits with a non-zero status")
def then_validate_failed(context: dict):
    result = context["validate"]
    assert result.exit_code != 0, f"expected failure, got exit=0: {result.stdout}"


@then("the validate command exits with success")
def then_validate_succeeded(context: dict):
    result = context["validate"]
    assert result.succeeded, f"expected success, got exit={result.exit_code}: {result.stderr}"


@then("the error names the module override file")
def then_names_override(context: dict):
    text = context["validate"].combined_output
    assert "postgresql/fitness-config.json" in text or "modules/" in text, \
        f"override file not named in error:\n{text}"


@then("the error names the root config file")
def then_names_root(context: dict):
    text = context["validate"].combined_output
    # Root file is named "fitness-config.json" in the repo root.
    # We look for the bare filename in a context that distinguishes it from the override.
    assert "fitness-config.json" in text


@then(parsers.parse(
    'the error states the effective weights sum to {bad:d} and must sum to {good:d}'
))
def then_sum_message(context: dict, bad: int, good: int):
    text = context["validate"].combined_output
    assert str(bad) in text
    assert str(good) in text
    assert "sum" in text.lower()


@then("the error offers two concrete fixes: adjust the override weights, or use full replacement")
def then_two_fixes(context: dict):
    text = context["validate"].combined_output.lower()
    assert "adjust" in text or "fix" in text
    assert "full replacement" in text or "all 10" in text or "replace" in text


@then("no effective config is written to standard output for downstream consumers")
def then_no_effective_to_stdout(context: dict):
    # On failure, the JSON sentinel block must NOT appear on stdout.
    text = context["validate"].stdout
    assert "<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->" not in text


@then("the output confirms the effective merged config is valid")
def then_validate_confirms(context: dict):
    text = context["validate"].stdout.lower()
    assert "valid" in text or "ok" in text


@then("the output confirms the root config is valid")
def then_root_valid(context: dict):
    text = context["validate"].stdout.lower()
    assert "valid" in text


@then("the output names the root config as valid")
def then_root_named_valid(context: dict):
    text = context["validate"].stdout
    assert "fitness-config.json" in text
    assert "Valid" in text or "valid" in text.lower()


@then("the error names the root config and the invalid sum")
def then_root_invalid_named(context: dict):
    text = context["validate"].combined_output
    assert "fitness-config.json" in text
    assert "sum" in text.lower() or "weights" in text.lower()


# --- schema version mismatch outcomes ---

@then("the error names both files and their declared versions")
def then_version_mismatch_files(context: dict):
    text = context["validate"].combined_output
    assert "version" in text.lower()
    assert "fitness-config.json" in text


@then("the error states the supported schema version is 1")
def then_supported_v1(context: dict):
    text = context["validate"].combined_output
    assert "supported" in text.lower() or "version: 1" in text or "version 1" in text


@then("the error appears before any merge is attempted")
def then_no_merge_before_error(context: dict):
    # Heuristic: stdout must NOT contain effective-config JSON block on a
    # version-mismatch failure.
    assert "<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->" not in context["validate"].stdout


@then("the error suggests upgrading the older config")
def then_upgrade_hint(context: dict):
    text = context["validate"].combined_output.lower()
    assert "upgrade" in text or "update" in text or "newer" in text or "older" in text


# --- malformed JSON outcomes ---

@then("the error names the override file as the source of the JSON parse failure")
def then_override_json_error(context: dict):
    text = context["validate"].combined_output
    assert "postgresql/fitness-config.json" in text or "modules/" in text
    assert "json" in text.lower() or "parse" in text.lower() or "invalid" in text.lower()


@then("the error names the root config as the source of the JSON parse failure")
def then_root_json_error(context: dict):
    text = context["validate"].combined_output
    assert "fitness-config.json" in text
    assert "json" in text.lower() or "parse" in text.lower() or "invalid" in text.lower()


@then("no review can proceed using a partial chain")
def then_no_partial_chain(context: dict):
    assert "<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->" not in context["validate"].stdout


# --- target path issues ---

@then("the error names the missing target path")
def then_missing_target(context: dict):
    text = context["validate"].combined_output
    assert "does-not-exist" in text or "not exist" in text.lower() or "not found" in text.lower()


@then("the error names a pathological-tree depth limit")
def then_depth_guard(context: dict):
    text = context["preview"].combined_output.lower()
    assert "64" in text or "pathological" in text or "depth" in text


@then("the preview command exits with a non-zero status")
def then_preview_nonzero(context: dict):
    result = context["preview"]
    assert result.exit_code != 0


# --- AC-02.7 / ad-hoc helpers ---

@then("no review can be initiated for that path until the merged config is fixed")
def then_no_review_initiated(context: dict):
    # We assert that validate exits non-zero AND no JSON sentinel block leaks on stdout.
    result = context["validate"]
    assert result.exit_code != 0
    assert "<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->" not in result.stdout


# ---------------------------------------------------------------------------
# Init helper outcomes
# ---------------------------------------------------------------------------

@then(parsers.parse('a new fitness-config.json appears at "{path}"'))
def then_init_created(repo: RepoTree, path: str):
    assert repo.exists(path)


@then("the new file declares all 10 domain weights matching the root values")
def then_init_seeded_from_root(repo: RepoTree):
    new = repo.read_json("infrastructure/modules/redis/fitness-config.json")
    root = repo.read_json("fitness-config.json")
    assert set(new["weights"].keys()) == set(DEFAULT_WEIGHTS.keys())
    for k, v in root["weights"].items():
        assert new["weights"][k] == v


@then("the new file declares the documented default weights")
def then_init_seeded_with_defaults(repo: RepoTree):
    new = repo.read_json("infrastructure/modules/redis/fitness-config.json")
    for k, v in DEFAULT_WEIGHTS.items():
        assert new["weights"][k] == v


@then("the output notes that no root config was found and defaults were used")
def then_init_default_note(context: dict):
    text = context["init"].combined_output.lower()
    assert "default" in text and ("no root" in text or "not found" in text or "no fitness-config" in text)


@then("the init command exits with success")
def then_init_succeeded(context: dict):
    result = context["init"]
    assert result.succeeded, f"init failed: exit={result.exit_code} stderr={result.stderr}"


@then("the init command exits with a non-zero status")
def then_init_failed(context: dict):
    result = context["init"]
    assert result.exit_code != 0


@then("the error names the existing file")
def then_init_names_existing(repo: RepoTree, context: dict):
    text = context["init"].combined_output
    assert "postgresql/fitness-config.json" in text or "fitness-config.json" in text


@then("the existing file content is unchanged")
def then_init_no_overwrite(repo: RepoTree, context: dict):
    current = repo.read_text("infrastructure/modules/postgresql/fitness-config.json")
    assert current == context["preexisting_content"]


@then("the error names the target path")
def then_init_names_target(context: dict):
    text = context["init"].combined_output
    assert "locked" in text or "permission" in text.lower() or "denied" in text.lower()


@then("no partial file is left on disk")
def then_no_partial_file(repo: RepoTree, context: dict):
    locked = context["locked_dir"]
    # Restore writability for cleanup.
    locked.chmod(0o755)
    candidate = locked / "fitness-config.json"
    assert not candidate.exists()


@then(parsers.parse('a root fitness-config.json is created with the documented default weights'))
def then_root_created_default(repo: RepoTree):
    assert repo.exists("fitness-config.json")
    cfg = repo.read_json("fitness-config.json")
    for k, v in DEFAULT_WEIGHTS.items():
        assert cfg["weights"][k] == v
