# Milestone 4 — Error Handling (US-02 invalid-merge, US-05, US-07)
#
# Driving port: CLI `validate --path <dir>` and `show --path <target>`.
# Fail-closed: every error must surface a non-zero exit status with a
# message that names every file in the chain and points at remediation.
#
# AC coverage:
#   - AC-02.3, AC-02.4, AC-02.5, AC-02.7 (sum != 100 after merge)
#   - AC-05.1, AC-05.2, AC-05.3, AC-05.4, AC-05.5 (validate effective)
#   - AC-07.1, AC-07.2, AC-07.3, AC-07.4, AC-07.5 (schema version mismatch)
#   - Plus malformed JSON, missing target path, walk-up depth guard

@US-02 @US-05 @US-07 @milestone-4 @real-io
Feature: Invalid configs and broken merges are caught with clear errors before any review runs

  Background:
    Given the repo has a root fitness-config.json with the default weights

  # --- effective merged sum violations (US-02 / US-05) ---

  @skip @AC-02.3 @AC-02.4 @AC-02.5 @AC-05.2 @AC-05.3 @AC-05.4
  Scenario: Validate fails when the effective merged weights sum to less than 100
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" produces an effective weight total of 95 after merge
    When Devin validates the effective config at "infrastructure/modules/postgresql/"
    Then the validate command exits with a non-zero status
    And the error names the module override file
    And the error names the root config file
    And the error states the effective weights sum to 95 and must sum to 100
    And the error offers two concrete fixes: adjust the override weights, or use full replacement

  @skip @AC-02.7
  Scenario: Validate failure prevents any review from proceeding for that scope
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" produces an effective weight total of 95 after merge
    When Devin validates the effective config at "infrastructure/modules/postgresql/"
    Then the validate command exits with a non-zero status
    And no effective config is written to standard output for downstream consumers

  @skip @AC-05.1
  Scenario: Validate succeeds when a partial override merges to a valid total
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" produces an effective weight total of 100 after merge
    When Devin validates the effective config at "infrastructure/modules/postgresql/"
    Then the validate command exits with success
    And the output confirms the effective merged config is valid

  @skip @AC-05.5
  Scenario: Validate without --path preserves the legacy single-file behavior
    Given the repo has a valid root fitness-config.json
    When Devin validates the config without specifying a path
    Then the validate command exits with success
    And the output confirms the root config is valid

  # --- schema version mismatch (US-07) ---

  @skip @AC-07.1
  Scenario: Matching schema versions across the chain validate successfully
    Given the root config declares schema version 1
    And a module override at "infrastructure/modules/postgresql/fitness-config.json" declares schema version 1
    When Devin validates the effective config at "infrastructure/modules/postgresql/"
    Then the validate command exits with success

  @skip @AC-07.2 @AC-07.4 @AC-07.5
  Scenario: Child config declares a newer schema version than root
    Given the root config declares schema version 1
    And a module override at "infrastructure/modules/postgresql/fitness-config.json" declares schema version 2
    When Devin validates the effective config at "infrastructure/modules/postgresql/"
    Then the validate command exits with a non-zero status
    And the error names both files and their declared versions
    And the error states the supported schema version is 1
    And the error appears before any merge is attempted

  @skip @AC-07.3 @AC-07.4
  Scenario: Child config declares an older schema version than root
    Given the root config declares schema version 2
    And a module override at "infrastructure/modules/postgresql/fitness-config.json" declares schema version 1
    When Devin validates the effective config at "infrastructure/modules/postgresql/"
    Then the validate command exits with a non-zero status
    And the error names both files and their declared versions
    And the error suggests upgrading the older config

  # --- malformed JSON in the chain ---

  @skip @infrastructure-failure
  Scenario: Malformed JSON in the override file is reported with the path that failed to parse
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" contains malformed JSON
    When Devin validates the effective config at "infrastructure/modules/postgresql/"
    Then the validate command exits with a non-zero status
    And the error names the override file as the source of the JSON parse failure
    And no review can proceed using a partial chain

  @skip @infrastructure-failure
  Scenario: Malformed JSON in the root config blocks resolution from any subtree
    Given the root fitness-config.json contains malformed JSON
    And a module override at "infrastructure/modules/postgresql/fitness-config.json" is well-formed
    When Devin validates the effective config at "infrastructure/modules/postgresql/"
    Then the validate command exits with a non-zero status
    And the error names the root config as the source of the JSON parse failure

  # --- target path issues ---

  @skip @infrastructure-failure
  Scenario: Validate against a target path that does not exist reports a clear error
    Given the path "infrastructure/modules/does-not-exist" is absent from the repo
    When Devin validates the effective config at "infrastructure/modules/does-not-exist"
    Then the validate command exits with a non-zero status
    And the error names the missing target path

  @skip @infrastructure-failure
  Scenario: Walk-up reports a pathological-tree error past the depth guard
    Given Devin invokes resolution from a path 100 levels deep with no fitness-config.json on the way up
    When Devin previews the resolved config for that deeply nested path
    Then the preview command exits with a non-zero status
    And the error names a pathological-tree depth limit
