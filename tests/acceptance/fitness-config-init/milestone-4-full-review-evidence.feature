# Milestone 4 -- Use a full review to sharpen the proposal (US-05)
#
# Full mode runs the existing review-full skill; the resolver is unchanged in
# this release (component-boundaries.md section 4). Everything observable here
# happens inside the agent session, so all but one scenario are @manual
# agent-eval scenarios. The executable one checks the skill guide discloses the
# side effect.
#
# AC coverage: AC-05.1..AC-05.5

@US-05 @milestone-4
Feature: Kenji uses a full review to ground the proposal in real findings

  @skip @AC-05.2 @FR-9 @static-artifact
  Scenario: The skill guide warns that a full review writes a report into the project
    Given the fitness-config-init skill guide
    When an agent host loads the skill guide
    Then it warns that a full review writes "docs/fitness-report.md"

  @manual @skip @AC-05.1 @FR-1
  Scenario Outline: The evidence mode comes only from the argument, clear wording, or the prompt
    Given Kenji invokes fitness-config-init with "<request>"
    When the skill decides the evidence mode
    Then the mode is <mode>

    Examples:
      | request                      | mode                                  |
      | full                         | full, after the report warning        |
      | full review first            | full, after the report warning        |
      | do a quick one               | fast                                  |
      | set up fitness config        | asked; pressing Enter means fast      |
      | fast, or full if needed      | asked; pressing Enter means fast      |

  @manual @skip @AC-05.2 @FR-9
  Scenario: Kenji is warned before a full review writes a report
    Given Kenji chooses the full review for fieldnotes
    When the skill is about to start review-full
    Then it states that docs/fitness-report.md will be written in fieldnotes
    And it proceeds only after Kenji confirms

  @manual @skip @AC-05.3
  Scenario: A review finding appears in the reason for a changed weight
    Given review-full on fieldnotes reported 3 unsafe migrations under review-data
    When the skill proposes weights
    Then the data reason cites that finding

  @manual @skip @AC-05.3 @ADR-007
  Scenario: A skipped domain is lowered with the review as evidence
    Given review-full on ledgerd skipped accessibility for lack of frontend files
    When the skill proposes weights
    Then the accessibility reason cites the skip
    And no weight is raised because of a low review score

  @manual @skip @AC-05.4 @error
  Scenario: A failed domain review does not stop the proposal
    Given review-performance fails during the full review of homelab-cli
    When the skill proposes weights
    Then the performance value uses fast-scan evidence
    And the output says the performance review failed

  @manual @skip @AC-05.4 @error
  Scenario: A full review that only looked at pending changes is not used as evidence
    Given fieldnotes has uncommitted changes
    And review-full reports a scope of changed files instead of the fieldnotes folder
    When the skill reads the review report
    Then it says review-full reviewed changes only and its results are not used
    And the proposal uses fast-scan evidence

  @manual @skip @AC-05.5 @NFR-1
  Scenario: A full review writes only the report and the config
    Given fieldnotes's working tree is clean in git
    When Kenji completes a full-mode run and accepts the proposal
    Then git shows only docs/fitness-report.md and fitness-config.json as changed
