"""Pure-function unit tests for the resolver: walk_up_chain.

The resolver walks up from a target path looking for fitness-config.json
in each ancestor directory. It returns the chain in precedence order:
nearest-to-target first (highest precedence), repo-root last (lowest).

walk_up_chain is pure: takes a starting Path and a stop boundary Path,
returns a list[Path]. No filesystem mutation; pure read-only inspection.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Load fitness-config.py as a module despite its hyphenated filename.
SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "fitness-config.py"
_spec = importlib.util.spec_from_file_location("fitness_config", SCRIPT)
fitness_config = importlib.util.module_from_spec(_spec)
sys.modules["fitness_config"] = fitness_config
_spec.loader.exec_module(fitness_config)


def test_walk_up_chain_returns_module_then_root_when_both_exist(tmp_path: Path):
    # Given: root config + module override + target inside the module
    (tmp_path / "fitness-config.json").write_text("{}")
    module_dir = tmp_path / "infrastructure" / "modules" / "postgresql"
    module_dir.mkdir(parents=True)
    (module_dir / "fitness-config.json").write_text("{}")
    target = module_dir / "main.tf"
    target.touch()

    chain = fitness_config.walk_up_chain(target, stop=tmp_path)

    assert len(chain) == 2
    assert chain[0] == module_dir / "fitness-config.json"
    assert chain[1] == tmp_path / "fitness-config.json"


def test_walk_up_chain_returns_only_root_when_no_module_override(tmp_path: Path):
    (tmp_path / "fitness-config.json").write_text("{}")
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    target = deep / "leaf.txt"
    target.touch()

    chain = fitness_config.walk_up_chain(target, stop=tmp_path)

    assert chain == [tmp_path / "fitness-config.json"]


def test_walk_up_chain_returns_empty_when_no_config_anywhere(tmp_path: Path):
    deep = tmp_path / "a" / "b"
    deep.mkdir(parents=True)
    target = deep / "leaf.txt"
    target.touch()

    chain = fitness_config.walk_up_chain(target, stop=tmp_path)

    assert chain == []


def test_walk_up_chain_accepts_directory_target(tmp_path: Path):
    (tmp_path / "fitness-config.json").write_text("{}")
    sub = tmp_path / "sub"
    sub.mkdir()

    chain = fitness_config.walk_up_chain(sub, stop=tmp_path)

    assert chain == [tmp_path / "fitness-config.json"]


def test_walk_up_chain_treats_file_and_its_parent_dir_as_equivalent_starts(tmp_path: Path):
    # Given: root config + override + a file inside the override directory
    (tmp_path / "fitness-config.json").write_text("{}")
    module_dir = tmp_path / "infra" / "postgres"
    module_dir.mkdir(parents=True)
    (module_dir / "fitness-config.json").write_text("{}")
    file_target = module_dir / "main.tf"
    file_target.touch()

    # When: walk from the file vs from the parent directory
    from_file = fitness_config.walk_up_chain(file_target, stop=tmp_path)
    from_dir = fitness_config.walk_up_chain(module_dir, stop=tmp_path)

    # Then: chains are identical — file input is normalized to its parent dir
    assert from_file == from_dir
    assert from_file == [
        module_dir / "fitness-config.json",
        tmp_path / "fitness-config.json",
    ]


def test_walk_up_chain_stops_at_stop_boundary_even_if_ancestor_has_config(tmp_path: Path):
    # Given: a config above the stop boundary, plus one inside it
    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    (tmp_path / "fitness-config.json").write_text("{}")  # outside stop, MUST be ignored
    (outer / "fitness-config.json").write_text("{}")     # at stop boundary, INCLUDED
    target = inner / "leaf.txt"
    target.touch()

    chain = fitness_config.walk_up_chain(target, stop=outer)

    # Walk-up halts at the stop boundary (.git equivalent in production)
    assert chain == [outer / "fitness-config.json"]


def test_walk_up_chain_caps_ascent_to_avoid_infinite_walks(tmp_path: Path):
    # Given: a deeply nested target far past the 64-level guard, with no stop
    # boundary on the way up. Build a 70-level chain to force the cap to fire.
    cursor = tmp_path
    for i in range(70):
        cursor = cursor / f"d{i}"
    cursor.mkdir(parents=True)
    target = cursor / "leaf.txt"
    target.touch()

    # Configure stop at filesystem root (effectively unreachable within budget)
    chain = fitness_config.walk_up_chain(target, stop=Path(target.anchor))

    # The cap must terminate the walk; chain must remain a list (never raise).
    # No configs exist anywhere on the path, so the chain is empty.
    assert chain == []


# ---------------------------------------------------------------------------
# Depth-cap signal — Step 03-01, ADR-006: walk_up_chain_with_status returns
# both the chain and a `depth_capped` boolean so the CLI can fail-closed
# with a specific pathological-tree error rather than silently truncating.
# ---------------------------------------------------------------------------

def test_walk_up_chain_with_status_reports_depth_capped_when_walk_terminates_at_64(tmp_path: Path):
    # Build a 70-level deep target with an unreachable stop (filesystem root).
    cursor = tmp_path
    for i in range(70):
        cursor = cursor / f"d{i}"
    cursor.mkdir(parents=True)
    target = cursor / "leaf.txt"
    target.touch()

    status = fitness_config.walk_up_chain_with_status(
        target, stop=Path(target.anchor)
    )

    assert status.chain == []
    assert status.depth_capped is True


def test_walk_up_chain_with_status_reports_no_cap_when_stop_reached_normally(tmp_path: Path):
    (tmp_path / "fitness-config.json").write_text("{}")
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    target = sub / "leaf.txt"
    target.touch()

    status = fitness_config.walk_up_chain_with_status(target, stop=tmp_path)

    assert status.chain == [tmp_path / "fitness-config.json"]
    assert status.depth_capped is False


def test_walk_up_chain_is_deterministic_across_repeated_calls(tmp_path: Path):
    # Given: a tree with multiple configs at different depths
    (tmp_path / "fitness-config.json").write_text("{}")
    mid = tmp_path / "a" / "b"
    mid.mkdir(parents=True)
    (mid / "fitness-config.json").write_text("{}")
    leaf = mid / "c" / "d"
    leaf.mkdir(parents=True)
    target = leaf / "main.tf"
    target.touch()

    # When: invoked many times with identical inputs
    runs = [fitness_config.walk_up_chain(target, stop=tmp_path) for _ in range(5)]

    # Then: every invocation produces the same chain (no ordering, no state)
    assert all(run == runs[0] for run in runs)
    assert runs[0] == [
        mid / "fitness-config.json",
        tmp_path / "fitness-config.json",
    ]
