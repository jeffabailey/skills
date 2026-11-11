# Rust test-suite optimization audit: cartcalc

Baseline: 19 tests, 3.24s summed test time, 1.53s wall time; mutants 35/52 caught
(17 missed, 0 timeout). Commit: fixture.
Scope: whole crate; evidence not collected: none.

## Prioritized findings

| # | File :: test | Category | Problem | Evidence | Recommended optimization | Est. time saved | Risk |
|---|---|---|---|---|---|---|---|
| 1 | src/lib.rs :: tests::cart_total_again | 1 duplicate | Byte-for-byte copy of `cart_total` | Identical production coverage with `cart_total`; same inputs and assertion; removal simulation: 0 lost kills | Delete `cart_total_again` | ~0.01s per run | Low |
| 2 | src/lib.rs :: tests::parse_qty_one, parse_qty_two, parse_qty_three, parse_qty_forty_two, parse_qty_works | 3 verbose / 5 weak | Five tests with identical coverage differing only by input; `parse_qty_works` only checks `is_ok()` | Identical coverage group of 5; removal simulation of 4 of them: 0 lost kills | Fold into one table-driven test `parse_qty_accepts_positive_integers` asserting the exact value for inputs "1", "2", "3", "42", "7" | ~0s, -16 lines | Low |
| 3 | tests/integration.rs :: full_checkout_flow, full_checkout_flow_with_retry | 7 slow | Sleeps 1.5s each for a pricing service that does not exist; the retry test repeats the same checkout with a weaker assert | JUnit 1.513s and 1.518s (93% of summed time); identical coverage; retry test asserts only `total > 0` | Remove the sleeps; delete `full_checkout_flow_with_retry` | ~3.0s summed, ~1.5s wall per run; ~78s per mutation run (52 mutants) | Low |
| 4 | src/lib.rs :: tests::discount_runs | 5 weak | No assertion (`let _ = ...`) | Identical coverage with `discount_half`; 0 lost kills when removed | Delete, or assert `apply_discount(999, 10) == 900` | ~0s | Low |
| 5 | src/lib.rs :: tests::cart_internal_vec_layout | 6 implementation detail | Asserts Vec order and capacity via `#[doc(hidden)]` `raw_items()` | Asserts on internal layout; contract (line count, total) asserted elsewhere | Rewrite against `line_count()` and `total()` | ~0s | Medium |
| 6 | src/lib.rs :: legacy_round | junk code | Private, `#[allow(dead_code)]`, never called | Lines 68-76 uncovered by every test; all 15 of its mutants missed; no references in the crate | Delete the function | ~0s; 15 fewer mutants per mutation run (~25s) | Low |
| 7 | src/lib.rs :: tests::discount_fifty_percent | 1 duplicate | Same input and assertion as `discount_half`, more verbose | Identical coverage; 0 lost kills | Delete | ~0s | Low |
| 8 | src/lib.rs :: tests::cart_add_merges_same_item | (not recommended) | Looks like it overlaps `cart_total` | Removal simulation lost 4 kills (`Cart::line_count`, `+=` in `Cart::add`) | Keep | n/a | High |

## Gaps found (not removals)

- `apply_discount` with `pct > 100`: mutant `replace > with ==` survives. Add a test that `apply_discount(1000, 150) == 0`.

## Totals if items 1-7 are approved

7 tests removed or merged, ~3.0s summed test time saved per run, legacy_round removed.
