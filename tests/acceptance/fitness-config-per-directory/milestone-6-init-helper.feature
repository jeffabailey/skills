# Milestone 6 — Init Helper (US-06)
#
# Driving port: CLI `init --path <dir>`. Init seeds an override file from
# the current root effective config (or DEFAULT_WEIGHTS if no root) so a
# new override is valid on first author.
#
# AC coverage: AC-06.1, AC-06.2, AC-06.3, AC-06.4
# (AC-06.5 lives in milestone-5-backward-compat.feature.)

@US-06 @milestone-6 @real-io
Feature: Init scaffolds a new module override that passes validate immediately

  @AC-06.1 @AC-06.2
  Scenario: Init seeds a new module override from the current root effective config
    Given the repo has a valid root fitness-config.json with the default weights
    And no fitness-config.json exists at "infrastructure/modules/redis"
    When Devin initializes an override at "infrastructure/modules/redis"
    Then a new fitness-config.json appears at "infrastructure/modules/redis/fitness-config.json"
    And the new file declares all 10 domain weights matching the root values
    And the init command exits with success
    And validating the effective config at "infrastructure/modules/redis" exits with success

  @AC-06.3
  Scenario: Init refuses to overwrite an existing module override
    Given a module override already exists at "infrastructure/modules/postgresql/fitness-config.json"
    When Devin initializes an override at "infrastructure/modules/postgresql"
    Then the init command exits with a non-zero status
    And the error names the existing file
    And the existing file content is unchanged

  @AC-06.4
  Scenario: Init falls back to default weights when no root config exists
    Given the repo has no root fitness-config.json
    And no fitness-config.json exists at "infrastructure/modules/redis"
    When Devin initializes an override at "infrastructure/modules/redis"
    Then a new fitness-config.json appears at "infrastructure/modules/redis/fitness-config.json"
    And the new file declares the documented default weights
    And the output notes that no root config was found and defaults were used
    And the init command exits with success

  @skip @infrastructure-failure
  Scenario: Init reports a permission failure when the target directory is not writable
    Given the directory "infrastructure/modules/locked" exists but is not writable by the current user
    When Devin initializes an override at "infrastructure/modules/locked"
    Then the init command exits with a non-zero status
    And the error names the target path
    And no partial file is left on disk
