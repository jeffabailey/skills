"""Universe-bound state-delta assertion (Mandate 8), local to this suite.

The Python reference port (`nwave_ai.state_delta`) is not installed in this
repo, and the suite must stay stdlib + pytest + pytest-bdd only, so this is a
minimal equivalent with the same four-parameter contract:

    assert_state_delta(before, after, universe, expected)

- `before` / `after`: snapshots mapping an observable name to a value.
- `universe`: every observable name the step promises to track.
- `expected`: predicate per name that is allowed (or required) to change.
- Every universe name NOT in `expected` must be unchanged. Fail-closed.

In this suite the observables are the files a maintainer can see in the
workspace (relative path -> content hash + modification time). They are
port-exposed: the filesystem is the resolver's only driven adapter, and the
file tree is what the user inspects with `git status`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class Predicate:
    describe: str
    check: Callable[[Any, Any], bool]


def unchanged() -> Predicate:
    return Predicate("unchanged", lambda before, after: before == after)


def absent() -> Predicate:
    return Predicate("absent after", lambda before, after: after is None)


def anything() -> Predicate:
    return Predicate("anything (asserted elsewhere)", lambda before, after: True)


def set_to_content(sha256_hex: str) -> Predicate:
    """File exists after the action with exactly this content hash."""
    return Predicate(
        f"content sha256={sha256_hex[:12]}...",
        lambda before, after: after is not None and after.sha256 == sha256_hex,
    )


def assert_state_delta(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    universe: set[str],
    expected: Mapping[str, Predicate],
) -> None:
    stray = set(expected) - set(universe)
    if stray:
        raise AssertionError(f"expected names outside the declared universe: {sorted(stray)}")
    violations: list[str] = []
    for name in sorted(universe):
        predicate = expected.get(name, unchanged())
        was, now = before.get(name), after.get(name)
        if not predicate.check(was, now):
            violations.append(f"  {name}: expected {predicate.describe}; before={was!r} after={now!r}")
    if violations:
        raise AssertionError("State delta violated:\n" + "\n".join(violations))


def universe_of(before: Mapping[str, Any], after: Mapping[str, Any]) -> set[str]:
    """Every observable present before or after the action."""
    return set(before) | set(after)
