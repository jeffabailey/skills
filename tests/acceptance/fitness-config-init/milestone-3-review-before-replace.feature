# Milestone 3 -- Review a diff before replacing an existing config (US-04)
#
# Driving port: fitness-config.py init --path T --from - --dry-run (diff) and
#               init --path T --from - --expect FP --force (replace),
# real subprocess, cwd = project folder, real files under tmp_path.
#
# The overwrite question itself ("Overwrite ...? [y/N]") is asked by the agent,
# so the answer mapping is an @manual outline. The resolver-side guarantee --
# nothing is replaced unless the agent passes the go-ahead -- is executable.
#
# AC coverage: AC-04.1..AC-04.5

@US-04 @milestone-3 @driving_port @real-io
Feature: Priya sees exactly what would change before an existing config is replaced

  @AC-04.1 @FR-7
  Scenario: Priya sees exactly which values would change
    Given Priya's project "ledgerd" already has the fitness config she tuned in June
    When Priya checks the database-service proposal for "ledgerd"
    Then the check reports the proposal would replace the current config
    And the check lists the change "weights.architecture 14 -> 10"
    And the check lists the change "weights.reliability 12 -> 18"
    And the check lists the change "weights.data 12 -> 18"
    And the check lists the change "weights.accessibility 4 -> 1"
    And the check lists the change "weights.maintainability 10 -> 5"
    And the check lists no other changes
    And the check says 11 values are unchanged
    And the fitness config in "ledgerd" is byte-for-byte unchanged

  @AC-04.3 @FR-7 @ADR-010
  Scenario: Confirming replaces the config with the reviewed proposal
    Given Priya's project "ledgerd" already has the fitness config she tuned in June
    And Priya has checked the database-service proposal for "ledgerd"
    When Priya confirms replacing the config for "ledgerd" with the reviewed proposal
    Then the save reports the config was replaced
    And the fitness config in "ledgerd" is identical to the reviewed proposal
    And the fitness config in "ledgerd" passes the resolver's validation
    And nothing else in "ledgerd" changed

  @AC-04.2 @BR-4 @error
  Scenario: Without the go-ahead the June config stays exactly as it was
    Given Priya's project "ledgerd" already has the fitness config she tuned in June
    And Priya has checked the database-service proposal for "ledgerd"
    When Priya saves the reviewed proposal for "ledgerd"
    Then the save is refused because a config already exists
    And the fitness config in "ledgerd" is byte-for-byte unchanged

  @AC-04.4 @FR-7
  Scenario: The check reports nothing to do when the proposal matches the current config
    Given Jeff's project "jeffbaileyblog" already has a fitness config equal to the public-site proposal
    When Jeff checks the public-site proposal for "jeffbaileyblog"
    Then the check reports no changes
    And nothing has been saved in "jeffbaileyblog"

  @AC-04.4 @FR-7 @error
  Scenario: Confirming an identical proposal leaves the file untouched
    Given Jeff's project "jeffbaileyblog" already has a fitness config equal to the public-site proposal
    And Jeff has checked the public-site proposal for "jeffbaileyblog"
    When Jeff confirms replacing the config for "jeffbaileyblog" with the reviewed proposal
    Then the save reports the config was unchanged
    And the fitness config in "jeffbaileyblog" is byte-for-byte unchanged

  @AC-04.5 @error
  Scenario: A broken current config is reported and the proposal is still shown
    Given Tomas's project "homelab-cli" has a fitness config with a stray trailing comma
    When Tomas checks the cli-tool proposal for "homelab-cli"
    Then Tomas is told the current config cannot be compared value by value
    And Tomas is shown the complete proposal
    And the fitness config in "homelab-cli" is byte-for-byte unchanged

  @AC-04.5 @BR-4 @error
  Scenario: A broken current config is still not replaced without the go-ahead
    Given Tomas's project "homelab-cli" has a fitness config with a stray trailing comma
    And Tomas has checked the cli-tool proposal for "homelab-cli"
    When Tomas saves the reviewed proposal for "homelab-cli"
    Then the save is refused because a config already exists
    And the fitness config in "homelab-cli" is byte-for-byte unchanged

  @AC-04.1 @ADR-011
  Scenario: A note the config format does not know is shown as removed
    Given Priya's project "ledgerd" has a fitness config carrying a note the config format does not know
    When Priya checks the database-service proposal for "ledgerd"
    Then the check lists the note as removed
    And the fitness config in "ledgerd" is byte-for-byte unchanged

  @AC-04.3 @ADR-010 @error
  Scenario: A replacement is refused if the proposal changed after Priya reviewed it
    Given Priya's project "ledgerd" already has the fitness config she tuned in June
    And Priya has checked the database-service proposal for "ledgerd"
    When the public-site proposal replaces the config for "ledgerd" against Priya's reviewed fingerprint
    Then the save is refused because it is not the proposal Priya reviewed
    And the fitness config in "ledgerd" is byte-for-byte unchanged

  # ---- Manual / agent-eval: the overwrite question ------------------------

  @manual @skip @AC-04.2 @BR-4 @error
  Scenario Outline: Only an explicit yes replaces the current config
    Given the overwrite question is shown for ledgerd
    When Priya answers "<answer>"
    Then the config in ledgerd is <outcome>

    Examples:
      | answer | outcome              |
      | y      | replaced             |
      | YES    | replaced             |
      | n      | byte-for-byte kept   |
      |        | byte-for-byte kept   |
      | nope   | byte-for-byte kept   |

  @manual @skip @AC-04.1
  Scenario: The overwrite question names the file and defaults to no
    Given ledgerd's June config differs from the proposal in 5 values
    When the skill shows the diff
    Then it ends with "Overwrite /Users/priya/src/ledgerd/fitness-config.json? [y/N]"
