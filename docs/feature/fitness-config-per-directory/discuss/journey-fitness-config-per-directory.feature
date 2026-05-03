Feature: Per-directory fitness config
  As Devin Park, infrastructure engineer
  I want to drop a fitness-config.json into a module subdirectory
  So that reviews of that subtree use module-specific weights instead of generic root weights

  Background:
    Given the repo has a root fitness-config.json with the default 10-domain weights summing to 100
    And the repo contains infrastructure/modules/postgresql/main.tf
    And the repo contains infrastructure/modules/logging/main.tf

  # ---------------------------------------------------------------
  # Happy path
  # ---------------------------------------------------------------

  Scenario: Devin reviews a postgresql module with module-specific weights
    Given infrastructure/modules/postgresql/fitness-config.json exists with data=30, reliability=20, architecture=14, security=14, testing=10, performance=6, algorithms=4, accessibility=0, process=1, maintainability=1
    When Devin runs a fitness review scoped to infrastructure/modules/postgresql/
    Then the review uses effective weights data=30 and reliability=20
    And the report header names "infrastructure/modules/postgresql/fitness-config.json" as the override
    And the report header names "fitness-config.json" as the root
    And the overall score is a weighted average using those effective weights

  Scenario: Devin inspects which config will apply via the show subcommand
    Given infrastructure/modules/postgresql/fitness-config.json exists
    When Devin runs "fitness-config.py show --path infrastructure/modules/postgresql/main.tf"
    Then output lists both config files in precedence order
    And output displays the effective merged weights as a table
    And output displays "total 100 OK"

  # ---------------------------------------------------------------
  # Edge case: walk-up from a deeper file
  # ---------------------------------------------------------------

  Scenario: Resolver walks up from a nested file to find the nearest config
    Given infrastructure/modules/postgresql/fitness-config.json exists
    And infrastructure/modules/postgresql/scripts/migrate.sh exists
    And infrastructure/modules/postgresql/scripts/ has no fitness-config.json of its own
    When Devin runs "fitness-config.py show --path infrastructure/modules/postgresql/scripts/migrate.sh"
    Then output names "infrastructure/modules/postgresql/fitness-config.json" as the override
    And output explains it found this by walking up from the input path

  # ---------------------------------------------------------------
  # Edge case: review at root falls back cleanly
  # ---------------------------------------------------------------

  Scenario: Review at repo root uses only the root config
    Given infrastructure/modules/postgresql/fitness-config.json exists
    When Devin runs a fitness review scoped to the repo root
    Then the review uses only the root fitness-config.json weights
    And the report header names "fitness-config.json" as the only config source
    And the report header does not name any module-level override
    And a note explains that subtree overrides apply only when review scope is within their directory

  # ---------------------------------------------------------------
  # Error: invalid weight sum after merge
  # ---------------------------------------------------------------

  Scenario: Override leaves merged weights summing to less than 100
    Given root fitness-config.json defines all 10 weights summing to 100
    And infrastructure/modules/postgresql/fitness-config.json overrides data=30, reliability=20, performance=6, algorithms=4, accessibility=0, process=1, maintainability=1 (sum=62) but does not override architecture, security, testing
    And root architecture=14, security=14, testing=10 contribute 38 from root
    And the effective merged sum is 100
    When Devin runs "fitness-config.py validate --path infrastructure/modules/postgresql/"
    Then validation passes
    And the message confirms the effective merged weights sum to 100

  Scenario: Override produces effective weights that do NOT sum to 100
    Given root fitness-config.json defines all 10 weights summing to 100
    And infrastructure/modules/postgresql/fitness-config.json overrides every weight, but the override sums to 95
    When Devin runs "fitness-config.py validate --path infrastructure/modules/postgresql/"
    Then validation fails with exit code 1
    And the error message names both config files
    And the error message states "Effective weights sum to 95, must sum to 100"
    And the error message offers two concrete fixes: adjust the override, or use full-replacement mode
    And no fitness review proceeds with this config

  # ---------------------------------------------------------------
  # Error: schema version mismatch
  # ---------------------------------------------------------------

  Scenario: Child config uses a schema version different from root
    Given root fitness-config.json has version 1
    And infrastructure/modules/postgresql/fitness-config.json has version 2
    When Devin runs "fitness-config.py validate --path infrastructure/modules/postgresql/"
    Then validation fails with exit code 1
    And the error message names both files and their versions
    And the error message states the supported version

  # ---------------------------------------------------------------
  # Provenance: report header proves which config applied
  # ---------------------------------------------------------------

  Scenario: Devin trusts the report because the header names the applied config
    Given infrastructure/modules/postgresql/fitness-config.json exists with data=30
    When Devin runs review-full scoped to infrastructure/modules/postgresql/
    Then the first 10 lines of the report contain "Config: infrastructure/modules/postgresql/fitness-config.json (merged with root)"
    And the first 10 lines contain an "Effective weights:" line listing all 10 domain weights
    And those weights match the values used in the weighted overall score calculation
