# Milestone 1 — Walk-Up Discovery (US-01)
#
# Driving port: CLI `python3 scripts/fitness-config.py show --path <target>`.
# Tests prove the resolver walks up from a target path to the nearest
# fitness-config.json ancestor. All scenarios start @skip — DELIVER unskips
# one at a time.
#
# AC coverage: AC-01.1, AC-01.2, AC-01.3, AC-01.4, AC-01.6 (determinism)
# (AC-01.5 perf budget covered separately in integration-checkpoints.feature)

@US-01 @milestone-1 @real-io
Feature: The resolver finds the nearest fitness-config.json by walking up from a target path

  Background:
    Given Devin has a clean repo with a fitness-config.json at the repo root using the default weights

  @AC-01.1
  Scenario: Devin previews resolution for a file directly inside an override directory
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets "data=30"
    And the file "infrastructure/modules/postgresql/main.tf" exists
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf"
    Then the source chain names the module override first and the root config second
    And the effective weights reflect "data=30" from the override

  @AC-01.2
  Scenario: Devin previews resolution for a file two levels below the override directory
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets "data=30"
    And the file "infrastructure/modules/postgresql/scripts/migrate.sh" exists
    And no fitness-config.json exists in "infrastructure/modules/postgresql/scripts"
    When Devin previews the resolved config for "infrastructure/modules/postgresql/scripts/migrate.sh"
    Then the source chain names the same module override first and the root config second
    And the preview explains that the override was found by walking up from the input path

  @AC-01.3
  Scenario: Devin previews resolution for a file under no override
    Given no override exists anywhere under "infrastructure/modules/networking"
    And the file "infrastructure/modules/networking/main.tf" exists
    When Devin previews the resolved config for "infrastructure/modules/networking/main.tf"
    Then the source chain names only the root config
    And the effective weights match the root config exactly

  @AC-01.4
  Scenario: Devin previews resolution in a repo with no fitness-config.json anywhere
    Given the repo has no fitness-config.json at any level
    And the file "infrastructure/modules/networking/main.tf" exists
    When Devin previews the resolved config for "infrastructure/modules/networking/main.tf"
    Then the preview reports "built-in defaults (no fitness-config.json found)"
    And the effective weights match the documented default weights

  @AC-01.6 @property
  Scenario: Devin gets the same resolved chain every time he previews the same target
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets "data=30"
    And the file "infrastructure/modules/postgresql/main.tf" exists
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf" twice
    Then both previews produce the same source chain and effective weights
