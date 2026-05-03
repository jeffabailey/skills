# Milestone 3 — Provenance Reporting (US-03, US-04)
#
# Driving port: CLI `show --path <target>`. The CLI's stdout IS the
# provenance contract. Skill prompts (consumers) embed those lines verbatim
# in fitness review reports — that integration is covered in
# integration-checkpoints.feature.
#
# AC coverage:
#   - US-03 header rendering: AC-03.3, AC-03.4, AC-03.5, AC-03.6
#     (AC-03.1, AC-03.2, AC-03.7 are about the embedded report header
#      produced by the skill prompt — covered in integration-checkpoints.feature)
#   - US-04 show subcommand: AC-04.1, AC-04.2, AC-04.3, AC-04.4

@US-03 @US-04 @milestone-3 @real-io
Feature: The show command displays the resolved config so anyone reading a review can trust which weights applied

  Background:
    Given the repo has a root fitness-config.json with the default weights

  @AC-03.3 @AC-04.1 @AC-04.2 @AC-04.3 @AC-04.4
  Scenario: Show output for a target inside an override directory names both files
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets weights "data=30, reliability=20, performance=6, algorithms=4, accessibility=0, process=1, maintainability=1"
    And the file "infrastructure/modules/postgresql/main.tf" exists
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf"
    Then the preview lists the module override first and the root second in precedence order
    And the preview names the override using the phrasing "merged with root"
    And the preview displays the effective weights as a table with one row per domain
    And the preview shows the effective total of 100 with an OK status
    And the preview command exits with success

  @AC-03.4 @AC-04.1
  Scenario: Show output for a target with no override names only the root config
    Given no override exists anywhere under "src"
    And the file "src/somefile.py" exists
    When Devin previews the resolved config for "src/somefile.py"
    Then the preview names only the root config without any "merged with..." phrasing
    And the preview shows the effective total of 100 with an OK status

  @AC-03.5
  Scenario: Show output when no fitness-config.json exists anywhere
    Given the repo has no fitness-config.json at any level
    When Devin previews the resolved config for the current directory
    Then the preview reports "built-in defaults (no fitness-config.json found)"
    And the preview displays the documented default weights as a table

  @AC-03.6
  Scenario: Show output lists all 10 domains in the effective weights line
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets "data=30"
    And the file "infrastructure/modules/postgresql/main.tf" exists
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf"
    Then the inline effective-weights line lists all 10 domain names with their effective values
    And the domains are ordered by descending effective weight, ties broken alphabetically

  @AC-04.1 @property
  Scenario: Show output is byte-identical for the same target across two invocations
    Given a module override at "infrastructure/modules/postgresql/fitness-config.json" sets "data=30"
    And the file "infrastructure/modules/postgresql/main.tf" exists
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf" twice
    Then both previews produce byte-identical output
