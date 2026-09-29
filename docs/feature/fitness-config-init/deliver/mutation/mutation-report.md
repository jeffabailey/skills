# Mutation testing report: fitness-config-init (DELIVER phase 5)

**Gate: PASS.** The final kill rate is 95.6% (1187 of 1242 tested mutants). The first run killed 87.1% before any tests were added. All 55 remaining survivors are equivalent or benign mutants, listed below with a reason for each. Production code did not change. No dead code was found.

## Scope and run configuration

| Item | Value |
|---|---|
| Tool | cosmic-ray 8.7.0 (scratch venv outside the repo), `local` distributor |
| Modules mutated | `scripts/fitness_config/{model,parsing,resolution,validation,render,write_gate,adapters,audit,cli}.py` (the 29-line stub `scripts/fitness-config.py` was excluded) |
| Test command (every module) | `python -m pytest -x -q -p no:cacheprovider tests/unit/fitness_config tests/acceptance/fitness-config-init tests/acceptance/fitness-config-per-directory`, run from the repo's `.venv` with `PYTHONDONTWRITEBYTECODE=1`, so a `.pyc` can never serve a stale mutant |
| Per-mutant timeout | 60 s. No mutant timed out and none was incompetent, so every kill is a real test failure. |
| Isolation | One session per module. Each session ran in its own `git clone --local` of the repo under the session scratchpad, so modules ran in parallel without seeing each other's mutants. The real working tree was never mutated. |
| Baseline | 182 passed, 32 skipped in about 10 s per run of the feature test set |
| Commit under test | first run: `60d446d`; re-runs of survivors: `363f5ab`, `96c6fac`, then `31dfd0d` (validation only) |

### Annotation filter (396 mutants skipped)

Every module under test starts with `from __future__ import annotations` except `model.py`, which has no annotations. Under that import, annotations are stored as strings and never evaluated. The package also never introspects them (`dataclass` only string-matches `ClassVar`). So a mutant inside a function or `AnnAssign` annotation, such as `str | None` becoming `str - None`, is equivalent by construction.

A small filter marked every mutant whose span lies wholly inside an annotation as `SKIPPED` before the run. It uses stdlib `ast`, and the script lives in the scratchpad (`mut/annotation_filter.py`). Module-level type aliases are runtime expressions and were still mutated, for example `Parsed = tuple[object, str | None]` and `PublishResult = ...`. All of those alias mutants were killed.

### Timings (wall clock, on 16 cores)

| Run | Wall time |
|---|---|
| Aborted first attempt, before the annotation filter | ~1.7 min |
| First run, 7 modules in parallel (model done earlier, in 30 s) | 21 s (parsing) to 8.8 min (render) |
| cli + validation | 11 min unsharded, then the rest in 2.3 min as 4 shards each |
| Survivor re-run after the first test commit (5 modules) | 3.0 min |
| Survivor re-run of every module after the second commit | 4.8 min |
| Validation survivor re-run after the third commit | 1.9 min |
| **Total mutation wall time** | **~23 min**. The first survivor re-run overlapped the shards. |

## Kill rates per module

These rates are killed ÷ tested. SKIPPED (annotation-only) mutants are left out of both numbers.

| Module | Generated | Skipped (annotation) | Tested | Killed before | Rate before | Killed after | Rate after |
|---|---:|---:|---:|---:|---:|---:|---:|
| model | 46 | 0 | 46 | 46 | 100.0% | 46 | 100.0% |
| parsing | 52 | 33 | 19 | 19 | 100.0% | 19 | 100.0% |
| audit | 73 | 0 | 73 | 71 | 97.3% | 73 | 100.0% |
| resolution | 270 | 33 | 237 | 211 | 89.0% | 231 | 97.5% |
| validation | 369 | 0 | 369 | 317 | 85.9% | 360 | 97.6% |
| render | 171 | 22 | 149 | 119 | 79.9% | 140 | 94.0% |
| cli | 280 | 88 | 192 | 166 | 86.5% | 179 | 93.2% |
| write_gate | 219 | 121 | 98 | 89 | 90.8% | 89 | 90.8% |
| adapters | 158 | 99 | 59 | 44 | 74.6% | 50 | 84.7% |
| **Total** | **1638** | **396** | **1242** | **1082** | **87.1%** | **1187** | **95.6%** |

Every module now clears the 80% bar. Before the new tests, `adapters` (74.6%) and `render` (79.9%) were in the WARN band. If equivalent mutants are left out, the effective kill rate is 100%.

## Test gaps found and closed

These 105 mutants survived the first run and were real gaps. Each is now killed by a new or strengthened test. The tests are in commits `363f5ab`, `96c6fac` and `31dfd0d`.

| Module:line (mutant) | Gap | Test added |
|---|---|---|
| resolution:19, 42, 54, 55, 57 (cap 63/65, `visited` start, `==`, `>=`, `is`, `break`→`continue`) | The ADR-006 depth-cap boundary (64) was only tested at 2 and 70 levels. | `test_resolver.py::test_walk_up_depth_cap_fires_exactly_past_64_folders` (62–66 levels) |
| resolution:46 (`exists() or is_file()`) | A folder named `fitness-config.json` could have joined the chain. | `test_a_folder_named_like_the_config_is_not_part_of_the_chain` |
| resolution:48, 51, 52 (`<=` stop, `>`/`continue` at root) | A walk from a target outside the stop folder was untested. | `test_a_target_outside_the_stop_folder_walks_up_to_the_filesystem_root` |
| resolution:77, 88, 89, 91 | Non-object chain entries, and taking the nearest declared version | `test_merger.py::test_deep_merge_chain_ignores_non_object_entries_and_takes_the_nearest_version` (property) |
| resolution:147 (`>=`/`>` "version") | Legacy `merge_defaults` sections were never checked. | `test_merge_defaults_fills_every_section_and_drops_the_version` (property). The legacy-show acceptance step now compares full JSON. |
| validation:46–51 (fix wording) and 77 (`!=`→`>`) | The fix advice for older, newer and mixed chains was unchecked, and version 0 passed the chain check. | `test_validator.py::test_the_version_mismatch_fix_advice_fits_the_versions_in_the_chain` (property) |
| validation:71, 74, 75 | A non-object entry could hide a later mismatch, a non-integer version could pass, and the list of declared versions could be cut short. | `test_the_chain_version_check_sees_every_entry` (property) |
| validation:107 (`[0]`→`[-1]`/`[1]`) | The effective-sum error did not have to name the nearest file first. | `test_an_effective_sum_off_100_names_the_nearest_chain_file_first` (property) |
| validation:123 (`len <= 2`) | A one-number range was accepted. | New FLAWS entry `"one-number range"` |
| validation:128 (`<=`) | Version 0 was accepted per file. | New FLAWS entry `"version 0"` |
| validation:136, 139 (`==` domains, `%`) | The sum was skipped beside an unknown domain, and a total of 200 read as 100. | `test_a_complete_weights_table_off_100_is_named_beside_an_unknown_domain` (property) |
| validation:196, 226 | A missing key was also reported as unknown, unknown keys in fixed sections were unreported, a weight typo was reported twice, and a reversed scoring range was not caught. | `test_a_proposal_with_one_completeness_flaw_gets_exactly_the_violation_naming_it` (property) |
| validation:210 | The band gap/overlap error could show the wrong numbers. | `test_a_gap_or_overlap_in_the_status_bands_shows_each_band_as_given` (property) |
| render:23 | A chain entry outside the base folder crashed instead of printing an absolute path. | `test_reporter.py::test_config_sources_list_every_chain_entry_once_nearest_first` (property) |
| render:40, 46 | Intermediate chain entries, their numbering and the root line for chains of 3 or more | same property |
| render:51, 53 (`~`, `^`, `%`, `>>`, `!=`, `is not`) | The weights total `OK`/`ERROR` was never checked for totals other than 100 or for fractional weights. | `test_the_weights_total_is_ok_exactly_when_it_is_100_within_tolerance` (property) |
| render:151 (`ensure_ascii=True`) | Non-ASCII text in the review diff showed as `\u` escapes. | `test_a_text_value_in_the_review_shows_as_written` (property) |
| audit:34 | An unreadable or non-UTF-8 audited file would crash the audit. | `test_an_audited_file_that_cannot_be_read_is_skipped_without_crashing` |
| adapters:30 | Legacy `validate` on a folder would raise a traceback. | New scenario in `milestone-2-safe-first-write.feature`: *Validating a folder in place of the config file…* |
| adapters:53 (mode 0o665/0o667) | The created file's permissions were unchecked. | `test_adapters.py::test_a_created_config_is_a_plain_data_file` (umask 000/022/077) |
| adapters:85, 86 | `restore` (rollback) was only reachable through a race and was never exercised on a real file. | `test_adapters.py::test_restore_puts_back_the_state_before_the_save` |
| cli:78 | Legacy `show` ignored the file (only `"weights"` was asserted). | The legacy-show step in `config_resolution_steps.py` was strengthened to compare full JSON. |
| cli:91 | `validate --path` on a not-yet-created file in an existing folder | New scenario in `milestone-4-error-handling.feature` |
| cli:152, 153 | The validate success line (nearest config, or built-in defaults) was unchecked, and an empty chain crashed. | New Then step on the partial-override scenario, plus the new scenario *Validate with no config anywhere…* |
| cli:239 (`show_canonical=True`) | A save echoed the config, against data-models §6. | The `the save reports the config was …` step now asserts that no config body is printed. |
| cli:248, 258, 269, 270 | Write-gate flags on `show`/`validate`/legacy `init`, `--from` values other than `-`, and `audit --path` were not refused. | New outline in milestone-2: *Write-gate options outside init --path are refused before anything runs* (6 examples) |

## Surviving mutants (55): all equivalent or benign

Classification key: **E** means equivalent (no observable behaviour can differ). **B** means benign (observable only in formatting, message wording, a defensive or unreachable path, or a random-name length). For every survivor the action is "none: no test added".

| Module:line | Operator | Class | Justification |
|---|---|---|---|
| adapters.py:31 | ReplaceOrWithAnd | B | Message wording: `strerror and exc` prints the full `OSError` text instead of `strerror`. The file is still named and there is no traceback. |
| adapters.py:75 | ReplaceOrWithAnd | B | Same as above, for the write-failed message. |
| adapters.py:52 (×2) | NumberReplacer | B | The temp file's random suffix length (`token_hex(3/5)`) changes nothing observable. |
| adapters.py:53 (×4) | BitOr→Add/BitXor | E | `O_WRONLY`, `O_CREAT` and `O_EXCL` are disjoint bit flags, so `+`, `^` and `\|` give the same value. |
| adapters.py:53 | BitOr→Mod | B | `O_CREAT % O_EXCL` drops `O_EXCL` on the temp file only. The name has 32 random bits, so a collision cannot be staged. The config file itself is still published exclusively through `os.link`. |
| cli.py:44 (×2) | NumberReplacer (indent 1/3) | B | Seed-file indentation. The seed is plain JSON that readers parse, and the byte-exact canonical form applies only to gated saves. |
| cli.py:79 (×2) | NumberReplacer (indent 1/3) | B | Legacy `show` JSON indentation. Consumers parse it, and the content is now asserted in full. |
| cli.py:90 (×2) | AddNot / Delete_Not | E | `base` is always `Path.cwd()`: joining an absolute path to it gives the absolute path, and a relative path already resolves against the cwd. |
| cli.py:317 | AddNot | E | Same reason as cli.py:90. |
| cli.py:228 | ReplaceFalseWithTrue | E | The default for `force` is never used, because the only caller always passes `args.force`. |
| cli.py:248 | Eq→LtE (`<= "init"`) | E | `audit` returns before this line, and `show`/`validate` sort after `init`, so only `init` passes. |
| cli.py:258 | NotEq→IsNot | E | CPython caches single-character strings, so the argv `"-"` is the same object as the literal. |
| cli.py:269, 359 | Eq→LtE (`<= "audit"`) | E | `audit` is the smallest of the four argparse choices. |
| cli.py:345 | Eq→GtE (`>= "validate"`) | E | `validate` is the largest remaining choice, and `show` is handled first. |
| render.py:34 | Eq→LtE | E | An empty chain returns before this line. |
| render.py:35, 38 | NumberReplacer `[0]`→`[-1]` | E | A one-entry list has the same first and last element. |
| render.py:53 | LtE→Lt | E | No double `t` gives `abs(t - 100)` exactly equal to `0.01` (0.01 cannot be represented at the spacing of doubles near 100), so `<` and `<=` never differ. |
| render.py:72 (×2) | NumberReplacer (indent 1/3) | B | Indentation of the machine-read JSON block between the sentinels. Consumers parse it. |
| render.py:104 | ReplaceFalseWithTrue (`ensure_ascii`) | E | Canonical bytes hold only known ASCII keys and numeric values, since validation runs first. |
| render.py:120 | frozen=False | E | Nothing assigns to a `ValueDiff`. Testing frozenness would be a language-guarantee test, which is banned. |
| render.py:151 | Is→Eq | E | `_Missing` defines no `__eq__`, so `==` falls back to identity. |
| resolution.py:22 | frozen=False | E | Nothing mutates a `WalkUpResult`. |
| resolution.py:27 | default `depth_capped=True` | E | The only constructor call always passes `depth_capped`. |
| resolution.py:37 | `resolve(strict=True)` | E | The stop folder is always the cwd or the anchor, both existing directories, so strict resolution cannot raise. |
| resolution.py:51 (×2) | Eq→GtE / Eq→Is | E | A parent is never greater than its child. At the root, `Path.parent` returns the same object. |
| resolution.py:147 | NotEq→IsNot | E | Both `"version"` strings are interned compile-time constants. |
| validation.py:22 | frozen=False | E | Nothing mutates a `ValidationResult`. |
| validation.py:77 | NotEq→IsNot | E | Small ints are cached in CPython, and the version is an `int` by this point. |
| validation.py:101, 139 | LtE→Lt | E | The same float-precision argument as render.py:53. |
| validation.py:128 (×2) | `type() ==` / `version is 1` | E | `type(x) is int` and `type(x) == int` agree, and the version is a cached small int. |
| validation.py:196 | Eq→GtE (`>= "weights"`) | E | The other section names all sort before `weights`, so only `weights` passes, as with `==`. |
| validation.py:196 | Eq→Is | E | Both strings are interned literals from `SECTION_DEFAULTS` and the comparison. |
| validation.py:222 | IsNot→NotEq | E | `type(v) is not int` and `type(v) != int` agree. |
| write_gate.py:47, 65 | frozen=False | E | Nothing mutates `ConfigFile` or `GateOutcome`, and `dataclasses.replace` works either way. |
| write_gate.py:117, 140 (×2 each) | Eq→Is / Eq→LtE | E | `_prepare_proposal` returns the `GateStatus.INVALID` or `READY` constant object itself, and `"ready" <= "invalid"` is False. |
| write_gate.py:134 | default `force=True` | B | Unreachable through the driving port: the CLI always passes `force`, and so does every test helper. The safe default is documented in the signature. |
| write_gate.py:155 | NotEq→IsNot | E | The ConfigFile adapter returns the `GateStatus` constants themselves. |
| write_gate.py:155 | NotEq→Gt | E | By the port contract, `create` reports only CREATED, REFUSED_EXISTS or WRITE_FAILED, and all of these sort above `created`. `replace` reports only REPLACED or WRITE_FAILED, and `write-failed` sorts above `replaced`. |

## Tests added (test budget)

- **Unit, pure core (properties, Hypothesis):** 11 new properties across the merger (2), validator (6) and reporter (3) test files, plus 2 new FLAWS entries in an existing property.
- **Unit, resolution against a real folder:** 3 examples: the depth boundary (parametrized over 62–66 levels), a folder named like the config, and a walk from outside the stop folder.
- **Integration (adapter IO boundary):** 2 examples. Restore rollback, and file mode parametrized over 3 umasks.
- **Audit:** 1 example.
- **CLI acceptance:**
  - 3 new scenarios, 1 new scenario outline with 6 examples, and 4 new step definitions.
  - 3 existing steps strengthened, which only adds assertions: legacy show content, save output, and naming the nearest config.

Each test pins a behaviour that no test asserted before, as shown by the mutants it kills. No existing test was weakened, removed or skipped.

## Post-mutation safety

- Every mutation ran in scratchpad clones. `git status` on the repo shows no changes under `scripts/` or `tests/` beyond the committed tests. `scripts/` is unchanged since `60d446d`.
- `uv run pytest -x tests -q`: 241 passed, 32 skipped, 75 subtests passed.
