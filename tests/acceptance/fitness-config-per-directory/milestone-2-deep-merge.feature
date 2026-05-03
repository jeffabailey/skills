# Milestone 2 — Deep-Merge Semantics (US-02)
#
# Driving port: CLI `python3 scripts/fitness-config.py show --path <target>`
# and `validate --path <dir>` (read effective merged config and report it).
#
# AC coverage: AC-02.1, AC-02.2, AC-02.6, AC-02.7
# (AC-02.3, AC-02.4, AC-02.5 invalid-merge errors live in milestone-4-error-handling.feature)

@US-02 @milestone-2 @real-io
Feature: A module override deep-merges over the root, leaving unmentioned settings inherited

  Background:
    Given the repo has a root fitness-config.json with weights "architecture=14, security=14, reliability=10, testing=10, performance=10, algorithms=10, data=10, accessibility=8, process=8, maintainability=6"

  @AC-02.1
  Scenario: A partial override only restates the weights Devin cares about
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets weights "data=30, reliability=20, performance=6, algorithms=4, accessibility=0, process=1, maintainability=1"
    And the override does not mention "architecture", "security", or "testing"
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf"
    Then the effective weights show "architecture=14", "security=14", and "testing=10" inherited from the root
    And the effective weights show "data=30, reliability=20, performance=6, algorithms=4, accessibility=0, process=1, maintainability=1" from the override
    And the effective weights sum to 100

  @AC-02.2
  Scenario: A full override replaces every root weight
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets all 10 weights summing to 100
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf"
    Then every effective weight comes from the override
    And no effective weight is inherited from the root

  @AC-02.6
  Scenario: Other top-level settings merge independently of weights
    Given the root config defines status thresholds with healthy "[8,10]"
    And a module override at "infrastructure/modules/postgresql/fitness-config.json" sets only the security confidence threshold to 9
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf"
    Then the effective status thresholds healthy range is "[8,10]" inherited from the root
    And the effective security confidence threshold is 9 from the override

  @AC-02.6
  Scenario: A status threshold range is replaced as a whole when the override sets it
    Given the root config defines status thresholds with healthy "[8,10]"
    And a module override at "infrastructure/modules/postgresql/fitness-config.json" sets status thresholds healthy to "[9,10]"
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf"
    Then the effective status thresholds healthy range is "[9,10]" from the override

  @AC-02.7
  Scenario: A merge that produces an invalid total blocks the review chain entirely
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" produces an effective weight total of 95 after merge
    When Devin validates the effective config at "infrastructure/modules/postgresql/"
    Then the validate command exits with a non-zero status
    And no review can be initiated for that path until the merged config is fixed
