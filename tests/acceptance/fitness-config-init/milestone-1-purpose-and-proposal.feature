# Milestone 1 -- Purpose classification and weight proposal (US-01, US-02)
#
# Two kinds of scenario live here:
#   1. Executable checks on the static knowledge the agent follows: the
#      purpose profile catalogue (references/purpose-profiles.md), the purpose
#      signal guide (references/purpose-signals.md) and the skill guide
#      (SKILL.md). Profiles are checked through the resolver (driving port),
#      not by re-implementing its rules.
#   2. @manual agent-eval scenarios. Classification, evidence, reasons and the
#      conversation happen inside the agent; pytest cannot run them. They are
#      run by hand (or by an agent-eval harness) against the six DISCUSS
#      fixtures and recorded in tests/functional-tests.md during DELIVER.
#
# AC coverage: AC-01.1..AC-01.6 (manual), AC-02.1..AC-02.6 (static + manual)

@US-01 @US-02 @milestone-1
Feature: The skill reads what a project is for and proposes weights that fit it

  # ---- Executable: the profile catalogue the agent starts from ------------

  @skip @AC-02.1 @BR-1 @ADR-007 @static-artifact
  Scenario: Every archetype profile is a complete, balanced weighting
    Given the purpose profile catalogue shipped with the skill
    When the skill loads its profile catalogue
    Then it offers exactly the archetypes "database-backend, web-frontend, cli-tool, library-sdk, data-pipeline, api-service"
    And every profile weighs all ten fitness domains in the standard order
    And every profile gives each domain a whole-number weight of at least 1
    And every profile's weights add up to 100

  @skip @AC-02.1 @AC-03.1 @ADR-007 @ADR-008 @static-artifact @real-io
  Scenario: The resolver would accept every archetype profile as a new config
    Given the purpose profile catalogue shipped with the skill
    And Ana's project "geo-notes" has no fitness config
    When each profile is checked as a proposal for "geo-notes"
    Then the resolver would accept every profile as a new config
    And nothing has been saved in "geo-notes"

  @skip @AC-02.3 @ADR-007 @static-artifact
  Scenario: The database-backend profile favours reliability and data over accessibility
    Given the purpose profile catalogue shipped with the skill
    And Priya's project "ledgerd" has no fitness config
    And Priya has asked for the starting weights for "ledgerd"
    When the skill loads its profile catalogue
    Then the "database-backend" profile weighs reliability and data above their starting weights
    And the "database-backend" profile weighs accessibility below its starting weight

  @skip @AC-02.4 @ADR-007 @static-artifact
  Scenario: The web-frontend profile puts accessibility first
    Given the purpose profile catalogue shipped with the skill
    When the skill loads its profile catalogue
    Then accessibility is the highest weight in the "web-frontend" profile

  @skip @US-01 @AC-01.3 @AC-01.6 @NFR-2 @static-artifact
  Scenario: The purpose signal guide defines confidence and keeps the fast scan small
    Given the purpose signal guide shipped with the skill
    When the skill loads its purpose signal guide
    Then it defines what high, medium and low confidence mean
    And it limits the fast scan to 40 files

  @skip @US-01 @US-03 @NFR-4 @static-artifact
  Scenario: The skill guide is discoverable and runs the resolver shipped beside it
    Given the fitness-config-init skill guide
    When an agent host loads the skill guide
    Then the skill is named "fitness-config-init"
    And its description says when to use it
    And it has a workflow section
    And it runs the resolver from "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py"
    And it points to its purpose profile and purpose signal references

  @skip @US-02 @US-03 @BR-2 @static-artifact @error
  Scenario: The skill guide carries no weight numbers and saves only reviewed proposals
    Given the fitness-config-init skill guide
    When an agent host loads the skill guide
    Then it contains no weight numbers of its own
    And it saves only proposals the maintainer reviewed

  # ---- Manual / agent-eval: classification (US-01) ------------------------

  @manual @skip @AC-01.1 @FR-1
  Scenario: The first thing Priya sees is the folder being configured
    Given Priya is in "/Users/priya/src/ledgerd"
    When she invokes fitness-config-init
    Then the first output line names "/Users/priya/src/ledgerd" as the target folder

  @manual @skip @AC-01.2 @FR-1
  Scenario: Fast scan is the default evidence mode
    Given Jeff invokes fitness-config-init in "jeffbaileyblog" without naming a mode
    When he presses Enter at the mode prompt
    Then the evidence header reads "fast scan"
    And no full review is started

  @manual @skip @AC-01.3 @FR-2 @FR-3 @BR-2
  Scenario: Priya sees what the skill thinks ledgerd is, and why
    Given "ledgerd" contains go.mod with pgx/v5, migrations and a StatefulSet with a disruption budget
    When Priya accepts the default mode
    Then she sees the purpose "database-backed service (no UI)" with confidence "high"
    And every evidence line names a path that exists in ledgerd

  @manual @skip @AC-01.4 @BR-3 @error
  Scenario: A nearly empty folder is reported as unknown instead of guessed
    Given Ana's "geo-notes" contains only a README with the text "TODO"
    When she invokes fitness-config-init
    Then the purpose is "unknown" with confidence "low"
    And she is told baseline values will be proposed

  @manual @skip @AC-01.5 @error
  Scenario: Tomas corrects a wrong classification in one reply
    Given the skill classified "homelab-cli" as "library"
    When Tomas replies "it's a CLI tool"
    Then the purpose used for the proposal is "CLI tool"

  @manual @skip @ADR-007 @error
  Scenario: A medium-confidence classification makes the skill ask for the primary purpose
    Given the fast scan of "fieldnotes" finds both public pages and a busy database
    When the skill classifies the project with confidence "medium"
    Then it asks Kenji for the primary purpose before proposing weights
    And it mentions per-folder overrides without creating any

  @manual @skip @AC-01.6 @NFR-1 @NFR-2
  Scenario: The fast scan leaves the project untouched
    Given Priya's ledgerd working tree is clean in git
    When the fast scan finishes
    Then git reports a clean working tree in ledgerd
    And the transcript shows at most 40 file reads and no project code run

  # ---- Manual / agent-eval: proposal (US-02) ------------------------------

  @manual @skip @AC-02.3 @AC-02.1
  Scenario: A reliability-critical service gets reliability and data weighted up
    Given ledgerd was classified "database-backed service (no UI)" with high confidence
    When the skill proposes weights
    Then reliability and data are each higher than their starting weights
    And accessibility is lower than its starting weight
    And the ten weights add up to exactly 100

  @manual @skip @AC-02.2 @FR-5 @BR-2
  Scenario: Every changed weight comes with a reason tied to the project
    Given the ledgerd proposal changes 7 of 10 weights
    When Priya reads the proposal table
    Then there are exactly 7 reasons
    And each reason cites a path or finding from the evidence list
    And the unchanged rows read "(unchanged)"

  @manual @skip @ADR-007 @error
  Scenario: The skill never moves a weight more than 4 away from the profile
    Given ledgerd was classified "database-backed service (no UI)"
    When the skill adjusts the database-backend profile using ledgerd's evidence
    Then no weight differs from the profile by more than 4
    And every adjusted weight has a reason citing evidence

  @manual @skip @AC-02.4
  Scenario: A public website gets accessibility weighted up
    Given jeffbaileyblog was classified "public web frontend (static site)"
    When the skill proposes weights
    Then accessibility is the highest weight
    And data is lower than its starting weight

  @manual @skip @AC-02.5 @BR-3 @error
  Scenario: An unknown project keeps the starting weights
    Given geo-notes was classified "unknown" with low confidence
    And Ana gave no primary purpose when asked
    When the skill proposes weights
    Then all ten weights equal the starting weights
    And no reasons are shown

  @manual @skip @AC-02.6
  Scenario: Priya adjusts a proposed weight before saving
    Given the ledgerd proposal has performance 10 and architecture 10
    When Priya says "performance 12, take it from architecture"
    Then the revised proposal shows performance 12 and architecture 8
    And the total is still 100
