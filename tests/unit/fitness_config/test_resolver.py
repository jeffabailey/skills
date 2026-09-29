"""Pure-function unit tests for the resolver: walk_up_chain.

The resolver walks up from a target path looking for fitness-config.json
in each ancestor directory. It returns the chain in precedence order:
nearest-to-target first (highest precedence), repo-root last (lowest).

walk_up_chain is pure: takes a starting Path and a stop boundary Path,
returns a list[Path]. No filesystem mutation; pure read-only inspection.

Test count budget (per 2x distinct-behaviors rule):
  Behavior B1: walk_up_chain returns chain in precedence order
  Behavior B2: walk_up_chain stops at stop boundary
  Behavior B3: walk_up_chain caps depth at 64 (with_status reports it)
  Behavior B4: anchored_chain never reads a config outside the anchor
  Behavior B5: a save under a root config verifies the merged (effective)
               config, and rolls back when that merge is not valid
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ._loader import resolution, write_gate
from .test_validator import complete_configs
from .test_write_gate import (UNIVERSE, config_file, formatted, indents, is_, project_folder,
                              state_delta, universe_snapshot)


# ---------------------------------------------------------------------------
# Helpers — keep test bodies focused on assertions, not setup mechanics.
# ---------------------------------------------------------------------------

def _write_config(at: Path) -> Path:
    at.parent.mkdir(parents=True, exist_ok=True)
    cfg = at / "fitness-config.json" if at.is_dir() else at
    cfg.write_text("{}")
    return cfg


# ---------------------------------------------------------------------------
# B1: walk_up_chain returns chain in precedence order across input shapes.
# Parametrized over input-variation cases that share the SAME assertion
# logic: the returned chain must equal the expected list of config paths.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case_id,override_subpath,start_kind,expect_override,expect_root",
    [
        # Both root + module override; target file inside module.
        ("module_and_root_with_file_target", "infrastructure/modules/postgresql", "file", True, True),
        # Both root + module override; target IS the module directory itself.
        ("module_and_root_with_dir_target", "infra/postgres", "dir", True, True),
        # Only root config exists; deep file target.
        ("only_root_with_deep_file_target", None, "file", False, True),
        # No configs anywhere; deep file target.
        ("no_configs_anywhere", None, "file", False, False),
    ],
)
def test_walk_up_chain_returns_chain_in_precedence_order(
    tmp_path: Path,
    case_id: str,
    override_subpath: str | None,
    start_kind: str,
    expect_override: bool,
    expect_root: bool,
):
    expected: list[Path] = []
    if expect_root:
        _write_config(tmp_path)
        expected_root = tmp_path / "fitness-config.json"
    if override_subpath is not None:
        module_dir = tmp_path / override_subpath
        module_dir.mkdir(parents=True)
        if expect_override:
            _write_config(module_dir)
            expected.append(module_dir / "fitness-config.json")
        start_dir = module_dir
    else:
        start_dir = tmp_path / "a" / "b" / "c"
        start_dir.mkdir(parents=True)
    if expect_root:
        expected.append(expected_root)

    if start_kind == "file":
        target = start_dir / "leaf.tf"
        target.touch()
    else:
        target = start_dir

    chain = resolution.walk_up_chain(target, stop=tmp_path)

    assert chain == expected, f"case={case_id}: got {chain}, expected {expected}"


# ---------------------------------------------------------------------------
# B2: walk_up_chain stops at the stop boundary even if ancestors have configs.
# ---------------------------------------------------------------------------

def test_walk_up_chain_stops_at_stop_boundary_and_excludes_ancestors_above(tmp_path: Path):
    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    (tmp_path / "fitness-config.json").write_text("{}")  # ABOVE stop -> ignored
    (outer / "fitness-config.json").write_text("{}")     # AT stop -> included
    target = inner / "leaf.txt"
    target.touch()

    chain = resolution.walk_up_chain(target, stop=outer)

    assert chain == [outer / "fitness-config.json"]


# ---------------------------------------------------------------------------
# B3: walk_up_chain caps depth at 64; walk_up_chain_with_status surfaces it.
# Parametrized over the two cases of the depth_capped flag (capped vs not).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case_id,depth,use_unreachable_stop,write_root_config,expected_depth_capped,expected_chain_nonempty",
    [
        # 70 levels deep + unreachable stop -> cap fires, depth_capped True.
        ("70_levels_unreachable_stop", 70, True, False, True, False),
        # Modest depth + reachable stop -> cap does NOT fire, depth_capped False.
        ("normal_depth_reachable_stop", 2, False, True, False, True),
    ],
)
def test_walk_up_chain_with_status_reports_depth_cap_status(
    tmp_path: Path,
    case_id: str,
    depth: int,
    use_unreachable_stop: bool,
    write_root_config: bool,
    expected_depth_capped: bool,
    expected_chain_nonempty: bool,
):
    if write_root_config:
        (tmp_path / "fitness-config.json").write_text("{}")

    cursor = tmp_path
    for i in range(depth):
        cursor = cursor / f"d{i}"
    cursor.mkdir(parents=True)
    target = cursor / "leaf.txt"
    target.touch()

    stop = Path(target.anchor) if use_unreachable_stop else tmp_path
    status = resolution.walk_up_chain_with_status(target, stop=stop)

    assert status.depth_capped is expected_depth_capped, (
        f"case={case_id}: depth_capped={status.depth_capped}"
    )
    if expected_chain_nonempty:
        assert status.chain == [tmp_path / "fitness-config.json"]
    else:
        assert status.chain == []


def test_walk_up_chain_is_deterministic_across_repeated_calls(tmp_path: Path):
    """Property: same inputs -> same chain across repeated invocations (purity)."""
    (tmp_path / "fitness-config.json").write_text("{}")
    mid = tmp_path / "a" / "b"
    mid.mkdir(parents=True)
    (mid / "fitness-config.json").write_text("{}")
    leaf = mid / "c" / "d"
    leaf.mkdir(parents=True)
    target = leaf / "main.tf"
    target.touch()

    runs = [resolution.walk_up_chain(target, stop=tmp_path) for _ in range(5)]

    assert all(run == runs[0] for run in runs)
    assert runs[0] == [
        mid / "fitness-config.json",
        tmp_path / "fitness-config.json",
    ]


# ---------------------------------------------------------------------------
# B4 (ADR-009 anchor guard): anchored_chain(target, anchor, has_config) is the
# chain `init --path` reads. Universe: the chain it returns plus every config
# path it probed outside the anchor. Strict: the probe slot must stay empty.
# The expected chain starts at target's parent, so it also pins that the
# target's own config is never in its chain, that target == anchor reads
# nothing, and that a target outside the anchor is an error.
# ---------------------------------------------------------------------------

_folder_names = st.lists(st.sampled_from(["services", "billing", "api"]), max_size=3)
_WORKSPACE = Path("/workspace")


def _config_trees(anchor: Path, target: Path):
    """Config files anywhere from the workspace down to target, incl. above the anchor."""
    folders = [target, *target.parents]
    return st.sets(st.sampled_from(folders)).map(
        lambda chosen: frozenset(folder / "fitness-config.json" for folder in chosen))


def _inside(path: Path, anchor: Path) -> bool:
    return path.parent == anchor or anchor in path.parent.parents


@given(st.data(), _folder_names, _folder_names, st.booleans())
def test_anchored_chain_never_contains_a_config_outside_the_anchor(data, anchor_parts, target_parts,
                                                                   outside):
    anchor = _WORKSPACE.joinpath(*anchor_parts, "ledgerd")
    target = (_WORKSPACE / "archive" if outside else anchor).joinpath(*target_parts)
    tree = data.draw(_config_trees(anchor, target))
    probed_outside: list[Path] = []

    def has_config(path: Path) -> bool:
        if not _inside(path, anchor):
            probed_outside.append(path)
        return path in tree

    before = {"chain": [], "probed_outside_anchor": []}
    chain, error = resolution.anchored_chain(target, anchor, has_config)
    after = {"chain": chain, "probed_outside_anchor": probed_outside}

    expected_chain = [folder / "fitness-config.json" for folder in target.parents
                      if folder / "fitness-config.json" in tree
                      and (folder == anchor or anchor in folder.parents)]
    state_delta.assert_state_delta(before, after, {"chain", "probed_outside_anchor"}, {
        "chain": is_([] if outside else expected_chain),
    })
    assert (error is not None) == outside


# ---------------------------------------------------------------------------
# B5: the post-write check verifies the EFFECTIVE config of the folder --
# the saved override merged with the configs above it (weights merge per
# domain, so a root weight outside the ten domains leaks into the override's
# folder). Universe: the saved config, its neighbour, and the save status.
# ---------------------------------------------------------------------------

@given(complete_configs(), complete_configs(), indents, st.integers(0, 20))
def test_save_under_a_root_config_keeps_it_only_when_the_merged_config_is_valid(
        override, root, indent, leaked_weight):
    root_above = {**root, "weights": {**root["weights"], "legacyDomain": leaked_weight}}
    text = formatted(override, indent)
    checked = write_gate.check_proposal(text, current=None)
    folder = project_folder(None)
    before = universe_snapshot(folder)
    outcome = write_gate.save_reviewed_proposal(text, checked.fingerprint, config_file(folder),
                                                    configs_above=[root_above])
    after = universe_snapshot(folder, outcome)
    merged_is_valid = leaked_weight == 0
    state_delta.assert_state_delta(before, after, UNIVERSE, {
        "fitness-config.json": is_(checked.canonical.encode("utf-8") if merged_is_valid else None),
        "status": is_("created" if merged_is_valid else "verify-failed-rolled-back"),
    })
