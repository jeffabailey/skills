# Integration Checkpoints — fitness-config-per-directory
#
# These scenarios validate cross-component contracts that span the resolver,
# the CLI, and the consumers (skill prompts, CI workflows).
#
# Driving port: still the CLI. Where consumers (skill prompts) are involved,
# we test the CONTRACT they rely on — the shape of show --path stdout —
# not the prompt itself. Skill-prompt updates are exercised in DELIVER's
# integration test pass against real review-* commands.
#
# AC coverage:
#   - AC-03.7 (broad-scope footnote for sub-overrides)
#   - AC-NFR-2 (determinism across runs)
#   - AC-NFR-1 (perf budget)
#   - ADR-005 (broad-scope uses only root)
#   - ADR-001 (CLI mutual exclusion of positional and --path)
#   - data-models §3.1 (embedded JSON block contract)
#   - US-08 (every per-domain skill honors override) — tagged for DELIVER

@milestone-integration @real-io
Feature: Resolver, CLI, and consumers stay aligned on the same contract

  Background:
    Given the repo has a root fitness-config.json with the default weights

  # --- ADR-005: broad-scope reviews only use the root config ---

  @ADR-005 @AC-03.7
  Scenario: A review at the repo root with module overrides present uses only the root
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" exists
    And a module override at "infrastructure/modules/networking/fitness-config.json" exists
    When Devin previews the resolved config for the repo root
    Then the source chain names only the root config
    And the preview optionally lists the discovered subtree overrides as a footnote that explains they are not applied at root scope

  @ADR-005
  Scenario: A review of a directory above a module override uses only the root
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" exists
    When Devin previews the resolved config for "infrastructure/modules"
    Then the source chain names only the root config
    And the source chain does not name the postgresql module override

  # --- CLI mutual exclusion (ADR-001 / component-boundaries §6.2) ---

  @cli-contract
  Scenario: Specifying both a positional path and --path is rejected
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" exists
    When Devin previews the resolved config supplying both a positional path and --path
    Then the preview command exits with a non-zero status indicating an argument error
    And the error explains that the positional path and --path cannot be used together

  # --- Embedded JSON block contract (data-models §3.1) ---

  @cli-contract @AC-03.2
  Scenario: Show output embeds a parseable JSON block that downstream skill prompts can extract
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets "data=30"
    And the file "infrastructure/modules/postgresql/main.tf" exists
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf"
    Then the preview output contains a fenced effective-config JSON block
    And the JSON block lists the same source chain shown in the human-readable section
    And the JSON block lists the same effective weights shown in the human-readable section

  # --- Determinism (NFR-2) ---

  @AC-NFR-2 @property
  Scenario: Resolution is deterministic across consecutive runs on the same input
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets "data=30"
    And the file "infrastructure/modules/postgresql/main.tf" exists
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf" five times
    Then all five previews produce byte-identical output

  # --- Performance (NFR-1) ---

  @AC-NFR-1 @perf
  Scenario: Resolution stays under the 100ms budget for a 10-level deep target
    Given a target file 10 levels deep with a module override 8 levels deep
    When Devin previews the resolved config for that deeply nested target 10 times
    Then the average preview wall-clock time stays under 100 milliseconds

  # --- US-08: every per-domain skill honors override (DELIVER integration) ---

  @US-08 @AC-08.4
  Scenario: No skill bypasses the resolver to read fitness-config.json directly
    Given the repository's review skill prompts and supporting scripts
    When the CI audit step greps for direct loads of fitness-config.json outside the resolver script
    Then no matches are found

  @US-08 @AC-08.2
  Scenario: A per-domain review report includes the same Config and Effective weights lines as a full review
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets "data=30"
    When the resolver is queried by any per-domain review skill scoped to "infrastructure/modules/postgresql/"
    Then the resolver output contains a Config line naming the override merged with root
    And the resolver output contains an Effective weights line listing all 10 domains
