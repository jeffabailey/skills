# Milestone 2 -- Only a valid, reviewed config reaches disk (US-03, US-02 gate)
#
# Driving port: fitness-config.py init --path T [--from -] [--dry-run]
#               [--expect FP] and fitness-config.py validate <file>,
# real subprocess, cwd = project folder (anchor), real files under tmp_path.
#
# Covers the write gate (ADR-010), the strict validator and completeness rules
# (ADR-008), the anchor rule (ADR-009) and the regression tests for the
# walk-above-the-project defect in the existing `init --path` (data-models.md
# section 6.3, tests a/b/c).
#
# AC coverage: AC-02.1, AC-02.5, AC-03.1..AC-03.4, AC-03.6

@US-03 @milestone-2 @driving_port @real-io
Feature: Only a valid config that Priya reviewed is ever saved

  # ---- Happy path: what Priya sees before anything is saved ---------------

  @AC-03.2 @NFR-3 @ADR-010
  Scenario: The fingerprint Priya sees identifies exactly the config that will be saved
    Given Priya's project "ledgerd" has no fitness config
    When Priya checks the database-service proposal for "ledgerd"
    Then the check reports the proposal would create a new config
    And Priya is shown a fingerprint of the config exactly as it will be saved
    And the config as it will be saved follows the example config's layout
    And nothing has been saved in "ledgerd"

  @AC-02.5 @ADR-009
  Scenario: Starting weights for a subfolder come from the configs above it
    Given Kenji's project "fieldnotes" has a root fitness config
    When Kenji asks for the starting weights for "fieldnotes/services/billing"
    Then the starting weights equal the fieldnotes root weights
    And the starting point names the fieldnotes root config as its source
    And nothing has been saved in "fieldnotes"

  # ---- Error paths: rejected proposals -------------------------------------

  @AC-03.3 @AC-02.1 @BR-5 @error
  Scenario: A proposal whose weights add up to 101 is never saved
    Given Priya's project "ledgerd" has no fitness config
    When Priya checks a database-service proposal for "ledgerd" that adds up to 101
    Then the proposal is rejected with a reason naming "101"
    And the reason says the weights must add up to 100
    And nothing has been saved in "ledgerd"

  @AC-03.3 @AC-02.1 @BR-1 @ADR-008 @error
  Scenario Outline: An incomplete or out-of-range proposal is rejected with the reason
    Given Priya's project "ledgerd" has no fitness config
    When Priya checks a database-service proposal for "ledgerd" that <flaw>
    Then the proposal is rejected with a reason naming "<named>"
    And nothing has been saved in "ledgerd"

    Examples:
      | flaw                                            | named           |
      | leaves out the maintainability weight           | maintainability |
      | adds a weight for "usability"                   | usability       |
      | gives accessibility a weight of -1              | accessibility   |
      | gives data a weight of 101                      | data            |
      | gives process a fractional weight of 6.5        | process         |
      | gives testing a yes-or-no weight                | testing         |
      | has no scoring section                          | scoring         |
      | has a healthy status band with three numbers    | healthy         |

  @AC-03.3 @error
  Scenario: Something that is not a config at all is rejected
    Given Priya's project "ledgerd" has no fitness config
    When Priya checks the note "reliability: high" in place of a config for "ledgerd"
    Then the proposal is rejected as unreadable
    And nothing has been saved in "ledgerd"

  @AC-03.3 @BR-5 @error
  Scenario: Saving an unbalanced proposal is refused even with a fingerprint in hand
    Given Priya's project "ledgerd" has no fitness config
    When Priya tries to save a database-service proposal for "ledgerd" that adds up to 101
    Then the proposal is rejected with a reason naming "101"
    And nothing has been saved in "ledgerd"

  # ---- Error paths: reviewed-proposal guarantee ----------------------------

  @skip @AC-03.2 @ADR-010 @error
  Scenario: A proposal that differs from the one Priya reviewed is never saved
    Given Priya's project "ledgerd" has no fitness config
    And Priya has checked the database-service proposal for "ledgerd"
    When the public-site proposal is saved for "ledgerd" against Priya's reviewed fingerprint
    Then the save is refused because it is not the proposal Priya reviewed
    And nothing has been saved in "ledgerd"

  @skip @ADR-010 @error
  Scenario: A proposal cannot be saved without the fingerprint from a check
    Given Priya's project "ledgerd" has no fitness config
    When Priya saves the database-service proposal for "ledgerd" without a reviewed fingerprint
    Then the save is refused
    And Priya is told a save needs the fingerprint of a reviewed proposal
    And nothing has been saved in "ledgerd"

  @skip @AC-03.4 @BR-4 @error
  Scenario: An existing config is never replaced without Priya's go-ahead
    Given Priya's project "ledgerd" already has the fitness config she tuned in June
    And Priya has checked the database-service proposal for "ledgerd"
    When Priya saves the reviewed proposal for "ledgerd"
    Then the save is refused because a config already exists
    And the fitness config in "ledgerd" is byte-for-byte unchanged

  # ---- Error paths: the project around the config -------------------------

  @skip @AC-03.3 @error
  Scenario: A damaged config higher up stops the check and names the damaged file
    Given Kenji's project "fieldnotes" has a damaged root fitness config
    When Kenji checks the billing proposal for "fieldnotes/services/billing"
    Then the check is refused and names the damaged fieldnotes root config
    And nothing has been saved in "fieldnotes"

  @skip @AC-03.3 @AC-03.6 @infrastructure-failure @error
  Scenario: A folder Priya cannot write to is left without a partial config
    Given Priya's project "ledgerd" has no fitness config
    And Priya has checked the database-service proposal for "ledgerd"
    And the folder "ledgerd" cannot be written to
    When Priya saves the reviewed proposal for "ledgerd"
    Then the save reports the config was not written
    And nothing has been saved in "ledgerd"

  # ---- Regression: the starting point never reaches outside the project ---
  # data-models.md section 6.3: cmd_init_path walked from the target's parent
  # with stop=cwd; when target == cwd the walk climbed past the project.

  @regression @ADR-009 @error
  Scenario: Starting weights at the project root ignore a config outside the project
    Given a stray fitness config favouring accessibility sits in the folder above "ledgerd"
    And Priya's project "ledgerd" has no fitness config
    When Priya asks for the starting weights for "ledgerd"
    Then the starting weights are the built-in defaults
    And the starting point does not mention the stray config

  @regression @ADR-009 @error
  Scenario: A default config set up at the project root ignores a config outside the project
    Given a stray fitness config favouring accessibility sits in the folder above "ledgerd"
    And Priya's project "ledgerd" has no fitness config
    When Priya sets up a default fitness config for "ledgerd"
    Then the new fitness config in "ledgerd" carries the built-in default weights

  @regression @ADR-009 @error
  Scenario: No config is ever created for a folder outside the project
    Given Priya's project "ledgerd" has no fitness config
    And a folder "ledgerd-archive" sits next to "ledgerd"
    When Priya, working in "ledgerd", sets up a default fitness config for the neighbouring folder "ledgerd-archive"
    Then the set-up is refused because the folder is outside the project
    And no fitness config appears in "ledgerd-archive"

  # ---- Stricter validation of hand-edited configs (ADR-008) --------------

  @AC-03.1 @ADR-008 @error
  Scenario: Validating a hand-edited config names every problem without crashing
    Given Priya's project "ledgerd" has a hand-edited fitness config with a "usability" weight and a security cutoff of "high"
    When Priya validates the fitness config file in "ledgerd"
    Then the validation fails
    And the validation names "usability"
    And the validation names the security cutoff
    And the validation reports its findings without crashing
