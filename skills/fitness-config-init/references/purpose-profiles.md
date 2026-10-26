# Purpose Profiles

Starting weights for each project archetype. The skill picks the row that matches the classified purpose, then adjusts it for the project's own evidence. These numbers live only in this file. `SKILL.md` never repeats them.

Every row weighs the ten fitness domains in the resolver's order, uses whole numbers of at least 1, and adds up to 100.

| archetype | architecture | security | reliability | testing | performance | algorithms | data | accessibility | process | maintainability | sum |
|---|---|---|---|---|---|---|---|---|---|---|---|
| database-backend | 10 | 14 | 20 | 10 | 10 | 7 | 18 | 1 | 5 | 5 | 100 |
| web-frontend | 10 | 10 | 8 | 8 | 14 | 4 | 4 | 18 | 12 | 12 | 100 |
| cli-tool | 12 | 10 | 10 | 16 | 10 | 10 | 4 | 4 | 10 | 14 | 100 |
| library-sdk | 18 | 10 | 6 | 16 | 10 | 12 | 3 | 2 | 9 | 14 | 100 |
| data-pipeline | 10 | 10 | 16 | 12 | 12 | 10 | 20 | 1 | 5 | 4 | 100 |
| api-service | 12 | 20 | 16 | 12 | 12 | 6 | 6 | 2 | 8 | 6 | 100 |

For comparison, the built-in starting config (what `init --path <target> --dry-run` prints at the repository root) weighs architecture and security at 14, reliability, testing, performance, algorithms and data at 10, accessibility and process at 8, and maintainability at 6.

## Choosing a row

| Classification | Row to start from |
|---|---|
| One archetype, high confidence | That archetype's row |
| Medium confidence, or `mixed` | Ask the user for the primary purpose, then use that row |
| User-confirmed (answered, or stated in the request) | That archetype's row |
| `unknown`, or low confidence and no answer | No row. Propose the baseline unchanged, with no reasons |

`mixed` and `unknown` are classifications, not profiles. For a mixed repository, mention that a subfolder can get its own `fitness-config.json` later. Do not create one.

## Adjusting a row

1. Move any single domain by at most 4 points from the profile value. The bound and the reasons are measured from the profile, not from the baseline: a value taken unchanged from the profile is justified by the classification, and its reason is just `<archetype> profile`.
2. Each move away from the profile needs a reason that cites an evidence path from the scan or a finding from the full review. No evidence, no move.
3. Keep every weight a whole number of at least 1 and keep the total at 100. When you raise one domain, lower another by the same amount and give that move its own reason.
4. Full review results change applicability only. A domain the review skipped or found nothing to assess in (no UI for accessibility, no data store for data) may move toward 1. A low score never raises a weight: weights say how much a domain matters, not how healthy it is today.
5. When the user asks for a specific change ("performance 12, take it from architecture"), apply it exactly, even beyond the 4-point bound, and note it as a user edit in the reason column.

## Typical rationale

These lines explain why each row looks the way it does. Adapt them to the project; do not paste them as reasons, because a reason must cite this project's evidence.

- **database-backend**: Losing or corrupting stored records is the worst outcome, so reliability and data lead, with reliability highest. Security follows because the store holds user data. There is no UI, so accessibility sits at the floor.
- **web-frontend**: People use the pages directly, so accessibility leads, followed by page performance. Process and maintainability stay high because content and templates change often. Data and algorithms matter little.
- **cli-tool**: Correct behavior across flags and inputs drives testing and maintainability. Terminal output still needs readable text and exit codes, so accessibility stays above the floor.
- **library-sdk**: Other code depends on the public API, so architecture (API shape and stability) leads, with testing and maintainability close behind. Algorithms matter because callers inherit their cost.
- **data-pipeline**: Correct, complete data is the product, so data leads and reliability follows (reruns, partial failures, late inputs). Performance matters for batch windows. No UI.
- **api-service**: A service that handles requests but owns no data store. Security leads because it sits on a network boundary and handles credentials or money; reliability follows because callers depend on it staying up. Data is low because the records live elsewhere.
