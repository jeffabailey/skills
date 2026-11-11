# Python test-suite optimization audit: cartcalc

Baseline: 19 tests, 3.02s summed test time, 3.81s session time; mutants 33/72 killed
(11 survived, 28 no tests, 0 timeout). Commit: fixture.
Scope: whole project; evidence not collected: none.
Setup changes: none.

## Prioritized findings

| # | File :: test | Category | Problem | Evidence | Recommended optimization | Est. time saved | Risk |
|---|---|---|---|---|---|---|---|
| 1 | tests/test_core.py :: test_cart_total_again | 1 duplicate | Line-for-line copy of `test_cart_total` | jscpd clone; identical coverage and kill set; kill_matrix --remove: 0 lost kills | Delete `test_cart_total_again` | ~0s per run | Low |
| 2 | tests/test_core.py :: test_parse_qty_one, test_parse_qty_two, test_parse_qty_three, test_parse_qty_forty_two, test_parse_qty_works | 3 verbose / 5 weak | Five tests differing only by input; `test_parse_qty_works` only checks `is not None` | Identical coverage group of 5; kill_matrix --remove of 4 of them: 0 lost kills | Fold into one `@pytest.mark.parametrize` test `test_parse_qty_accepts_positive_integers` asserting the exact value for inputs "1", "2", "3", " 42 ", "7" | ~0s, -16 lines | Low |
| 3 | tests/test_integration.py :: test_full_checkout_flow, test_full_checkout_flow_with_retry | 7 slow | Sleeps 1.5s each for a pricing service that does not exist; the retry test repeats the same checkout with a weaker assert | JUnit 1.50s and 1.51s (99% of summed time); identical coverage; retry test asserts only `> 0`; kill_matrix --remove retry test: 0 lost kills | Remove the sleeps; delete `test_full_checkout_flow_with_retry` | ~3.0s summed per run; ~65s per mutation run | Low |
| 4 | tests/test_core.py :: test_discount_runs | 5 weak | No assertion | Kills 0 mutants; identical coverage with `test_discount_half` | Delete, or assert `apply_discount(999, 10) == 900` | ~0s | Low |
| 5 | tests/test_core.py :: test_cart_internal_list_layout | 6 implementation detail | Asserts the private `_items` list layout | Reads `cart._items`; kill_matrix: 0 unique kills | Rewrite against `line_count()` and `total()` | ~0s | Medium |
| 6 | src/cartcalc/core.py :: legacy_round | junk code | Nothing calls it | vulture 60% unused function; lines 50-61 uncovered; all 28 of its mutants "no tests"; no references | Delete the function | ~0s; 28 fewer mutants per mutation run | Low |
| 7 | tests/test_core.py :: test_parse_qty_rejects_zero (first definition) | gap (shadowed test) | A second `def test_parse_qty_rejects_zero` replaces the first, so the "0" case never runs | ruff F811 at line 52; mutant `<=` -> `<` in parse_qty survives | Rename the first to `test_parse_qty_rejects_zero` and the second to `test_parse_qty_rejects_negative` so both run | ~0s | Low |
| 8 | pyproject.toml :: requests | junk dependency | Declared, never imported | deptry DEP002 | `uv remove requests` | install time only | Low |
| 9 | tests/test_core.py :: test_cart_add_merges_same_item | (not recommended) | Looks like it overlaps `test_cart_total` | kill_matrix: 4 unique kills in `Cart.add` | Keep | n/a | High |

## Gaps found (not removals)

- `apply_discount` with `pct > 100` and `pct < 0`: lines 17 and 19 never run. Add tests for `apply_discount(1000, 150) == 0` and `apply_discount(1000, -5) == 1000`.

## Totals if items 1-8 are approved

7 tests removed or merged, 1 test revived, ~3.0s summed test time saved per run, legacy_round and the requests dependency removed.
