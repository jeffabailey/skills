# Milestone 5 — Backward Compatibility (NFR-3)
#
# Driving port: CLI without --path. Existing CI consumers and existing
# functional tests must continue to behave identically when no --path
# flag is supplied.
#
# AC coverage: AC-04.5 (show), AC-05.6 (validate), AC-06.5 (init),
# AC-NFR-3 (cross-cutting backward compat)

@US-04 @US-05 @US-06 @milestone-5 @real-io @backward-compat
Feature: Existing CLI invocations without --path behave exactly as they did before

  @AC-05.6
  Scenario: Validate without --path still validates the single root file
    Given the repo has a valid root fitness-config.json
    When Devin validates the config without specifying a path
    Then the validate command exits with success
    And the output names the root config as valid

  @AC-05.6
  Scenario: Validate without --path still rejects an invalid root file
    Given the repo has a root fitness-config.json whose weights sum to 95 in isolation
    When Devin validates the config without specifying a path
    Then the validate command exits with a non-zero status
    And the error names the root config and the invalid sum

  @AC-04.5
  Scenario: Show without --path still prints the root effective config merged with defaults
    Given the repo has a root fitness-config.json with weights "data=20, architecture=14, security=14, reliability=10, testing=10, performance=10, algorithms=10, accessibility=4, process=4, maintainability=4"
    When Devin previews the resolved config without specifying a path
    Then the preview prints the root config merged with the documented defaults
    And the preview command exits with success

  @AC-06.5
  Scenario: Init without --path still creates a root config with default weights
    Given the repo has no fitness-config.json at the root
    When Devin initializes a config without specifying a path
    Then a root fitness-config.json is created with the documented default weights
    And the init command exits with success

  @AC-NFR-3
  Scenario: A repo with no module overrides behaves identically to today
    Given the repo has only a root fitness-config.json and no module overrides anywhere
    When Devin previews the resolved config for "src/some_file.py"
    Then the source chain names only the root config
    And the effective weights match the root config exactly
    And the preview output contains no "merged with..." phrasing
