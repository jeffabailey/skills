# Walking Skeleton -- fitness-config-init (US-01..US-03)
#
# Driving port: the resolver CLI the skill hands every proposal to
#   check: fitness-config.py init --path T --from - --dry-run
#   save:  fitness-config.py init --path T --from - --expect <fingerprint>
#   chain: fitness-config.py show --path T
# run as a real subprocess with cwd = the project folder (the anchor), against
# real files under tmp_path. No mocks.
#
# The agent half of the skeleton (scan, classify, propose) cannot run under
# pytest; it is covered by @manual scenarios in milestone-1 and by the static
# checks on the skill's reference files. The first scenario below is the ONLY
# enabled scenario in this suite. Everything else carries @skip until DELIVER
# enables it.
#
# Litmus test: "Priya ends up with a reviewed, purpose-tuned config that her
# next review-full run will use" -- a stakeholder confirms that is the goal.

@walking_skeleton @driving_port @real-io @adapter-integration
Feature: Priya turns a reviewed weight proposal into the config her reviews will use

  As Priya Raman, maintainer of the ledgerd service,
  I want the proposal I reviewed to be saved exactly as I saw it,
  so that my next fitness review weighs what matters for ledgerd.

  @US-02 @US-03 @AC-03.1 @AC-03.2 @AC-03.6 @FR-4 @FR-6 @FR-8 @NFR-1
  Scenario: Priya saves a reviewed database-service config into ledgerd, which had none
    Given Priya's project "ledgerd" has no fitness config
    And Priya has checked the database-service proposal for "ledgerd"
    When Priya saves the reviewed proposal for "ledgerd"
    Then the save reports the config was created
    And the fitness config in "ledgerd" is identical to the reviewed proposal
    And the fitness config in "ledgerd" passes the resolver's validation
    And reviews of "ledgerd" will use its own fitness config
    And nothing else in "ledgerd" changed

  @skip @US-02 @AC-02.5 @ADR-009
  Scenario: Priya sees the built-in starting weights for a project at its repository root
    Given Priya's project "ledgerd" has no fitness config
    When Priya asks for the starting weights for "ledgerd"
    Then the starting weights are the built-in defaults
    And nothing has been saved in "ledgerd"

  @skip @US-03 @AC-03.5 @FR-8
  Scenario: Kenji's billing config is announced as an override of the fieldnotes root config
    Given Kenji's project "fieldnotes" has a root fitness config
    And Kenji has checked the billing proposal for "fieldnotes/services/billing"
    When Kenji saves the reviewed proposal for "fieldnotes/services/billing"
    Then the save reports the config was created
    And reviews of "fieldnotes/services/billing" will use the billing config merged with the fieldnotes root config
    And the fieldnotes root config is byte-for-byte unchanged
