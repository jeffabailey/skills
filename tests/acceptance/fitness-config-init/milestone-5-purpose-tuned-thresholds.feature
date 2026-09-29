# Milestone 5 -- Tune thresholds and the security cutoff to purpose (US-06)
#
# Driving port: fitness-config.py init --path T --from - --dry-run, real
# subprocess, cwd = project folder. The contiguity rule for status bands (BR-6)
# is a completeness rule added in this release (ADR-008, R3). Choosing stricter
# thresholds for a high-stakes service is agent judgment -> @manual.
#
# AC coverage: AC-06.1..AC-06.4

@US-06 @milestone-5 @driving_port @real-io
Feature: Strictness follows the stakes of the project

  @AC-06.3 @AC-06.2 @BR-6
  Scenario: Stricter status bands that still cover every score are accepted
    Given Priya's project "ledgerd" has no fitness config
    When Priya checks the database-service proposal for "ledgerd" with status bands healthy 9-10, needs attention 6-8, critical 1-5 and a security cutoff of 5
    Then the check reports the proposal would create a new config
    And nothing has been saved in "ledgerd"

  @AC-06.3 @BR-6 @error
  Scenario Outline: Status bands with a gap or an overlap are rejected
    Given Priya's project "ledgerd" has no fitness config
    When Priya checks the database-service proposal for "ledgerd" with status bands healthy <healthy>, needs attention <attention>, critical <critical> and a security cutoff of 7
    Then the proposal is rejected with a reason about the status bands
    And nothing has been saved in "ledgerd"

    Examples: a score is left uncovered
      | healthy | attention | critical |
      | 9-10    | 5-7       | 1-4      |
      | 8-10    | 5-7       | 2-4      |

    Examples: a score falls in two bands
      | healthy | attention | critical |
      | 8-10    | 5-8       | 1-4      |

  @AC-06.2 @error
  Scenario Outline: A security cutoff outside 1 to 10 is rejected
    Given Priya's project "ledgerd" has no fitness config
    When Priya checks the database-service proposal for "ledgerd" with status bands healthy 8-10, needs attention 5-7, critical 1-4 and a security cutoff of <cutoff>
    Then the proposal is rejected with a reason about the security cutoff
    And nothing has been saved in "ledgerd"

    Examples:
      | cutoff |
      | 0      |
      | 11     |

  @manual @skip @AC-06.1
  Scenario: A payment service gets stricter thresholds, each with a reason
    Given paygate was classified as a payment-handling service
    When the skill proposes the config
    Then the security cutoff is below its starting value of 7
    And each changed threshold has a reason citing the payment webhooks

  @manual @skip @AC-06.4
  Scenario: An ordinary project keeps the starting thresholds
    Given jeffbaileyblog was classified "public web frontend (static site)"
    When the skill proposes the config
    Then the status bands, security cutoff and scoring ranges equal the starting values
    And the skill says there is no stakes signal to change thresholds
