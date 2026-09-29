# Derived view of journey-fitness-config-init.yaml and user-stories.md (source of truth).
Feature: Tune a fitness config to the project's purpose
  As a maintainer adopting fitness reviews
  I want a fitness-config.json whose weights match what my project is for
  So that the overall fitness score says something true about its health

  Background:
    Given the baseline weights are architecture 14, security 14, reliability 10, testing 10, performance 10, algorithms 10, data 10, accessibility 8, process 8, maintainability 6

  @walking_skeleton @US-01
  Scenario: Maintainer sees what the skill thinks the project is, and why
    Given Priya is in /Users/priya/src/ledgerd, which contains go.mod with pgx/v5, 42 migrations, and a StatefulSet
    When she invokes fitness-config-init and accepts the default mode
    Then she sees the purpose "database-backed service (no UI)" with confidence "high"
    And each evidence line names a path that exists in ledgerd

  @US-01
  Scenario: Sparse folder is reported as unknown instead of guessed
    Given Ana's ~/scratch/geo-notes contains only a README with the text "TODO"
    When she invokes fitness-config-init
    Then the purpose is "unknown" with confidence "low"
    And she is told baseline values will be proposed

  @US-01
  Scenario: Fast scan leaves the project untouched
    Given Priya's ledgerd working tree is clean in git
    When the fast scan finishes
    Then git status in ledgerd still shows a clean tree

  @walking_skeleton @US-02
  Scenario: Reliability-critical service gets reliability and data weighted up
    Given ledgerd was classified "database-backed service (no UI)" with high confidence
    When the skill proposes weights
    Then reliability and data are each higher than 10
    And accessibility is lower than 8
    And the ten weights sum to exactly 100

  @US-02
  Scenario: Every changed weight comes with a reason tied to the project
    Given the ledgerd proposal changes 7 of 10 weights
    When Priya reads the proposal table
    Then there are exactly 7 reasons
    And each reason cites a path or finding from the evidence list

  @walking_skeleton @US-03
  Scenario: Valid config is written to a project that had none
    Given ledgerd has no fitness-config.json
    And the accepted proposal passes the schema and resolver checks
    When the skill writes the config
    Then /Users/priya/src/ledgerd/fitness-config.json exists
    And "fitness-config.py validate --path ." run in ledgerd reports it valid

  @US-03
  Scenario: Invalid proposal is never written
    Given an accepted proposal whose weights sum to 101
    When the skill reaches the write step
    Then no fitness-config.json is created
    And the message states the weights sum to 101 and must be 100

  @US-03
  Scenario: Config in a subfolder is announced as an override
    Given fieldnotes/fitness-config.json exists and Kenji runs the skill in fieldnotes/services/billing
    When the config is written
    Then the summary shows the new file as override and the root file as root

  @US-04
  Scenario: Declining keeps the current config
    Given ledgerd already has fitness-config.json with reliability 12
    And the overwrite prompt is shown
    When Priya answers "n" or just presses Enter
    Then fitness-config.json is byte-identical to before

  @US-04
  Scenario: Confirming replaces the config with the reviewed proposal
    Given the overwrite prompt is shown for ledgerd
    When Priya answers "y"
    Then fitness-config.json equals the proposal shown in the diff

  @US-05
  Scenario: Maintainer is warned before a full review writes a report
    Given Kenji chooses the full review for fieldnotes
    When the skill is about to start review-full
    Then it states that docs/fitness-report.md will be written
    And it proceeds only after Kenji confirms

  @US-06
  Scenario: Status bands always cover every score from 1 to 10
    Given any proposal that changes statusThresholds
    When it is shown
    Then the healthy, needsAttention, and critical ranges cover 1 to 10 with no gaps or overlaps
