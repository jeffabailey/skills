# Integration checkpoints -- fitness-config-init
#
# Cross-cutting guarantees that keep the new skill honest with the rest of the
# bundle: one source of starting weights (ADR-009), the audit that keeps weight
# numbers out of skill prose (extended to the new skill), and backward
# compatibility of the stricter validator (ADR-008).
#
# Driving port: fitness-config.py (init --dry-run, validate, audit) as a real
# subprocess against tmp_path folders or the real repository checkout.

@milestone-integration @driving_port @real-io
Feature: The init skill stays consistent with the rest of the fitness bundle

  @NFR-3 @ADR-009 @AC-03.2
  Scenario: The built-in starting config is the published example, byte for byte
    Given Ana's project "geo-notes" has no fitness config
    When Ana asks for the starting weights for "geo-notes"
    Then the starting config is byte-for-byte the published example config

  @skip @BR-2 @error
  Scenario: The config audit catches a weight table written into the init skill guide
    Given a skills checkout whose fitness-config-init guide contains an inline weight table
    When the maintainer runs the config audit on that checkout
    Then the audit fails and names the fitness-config-init guide

  @skip @error
  Scenario: The config audit catches the init skill guide reading the config file directly
    Given a skills checkout whose fitness-config-init guide reads fitness-config.json directly
    When the maintainer runs the config audit on that checkout
    Then the audit fails and names the fitness-config-init guide

  @skip @NFR-4
  Scenario: The shipped skills repository passes the config audit, including the init skill guide
    Given the skills repository as shipped
    When the maintainer runs the config audit on the repository
    Then the audit passes
    And the audit covered the fitness-config-init guide

  @ADR-008 @compat
  Scenario: The published example config still passes the stricter validation
    Given the published example config
    When the maintainer validates the published example config
    Then the validation passes

  @ADR-008 @compat
  Scenario: An override that only sets the security cutoff remains valid
    Given Kenji's project "fieldnotes" has an override in "services/search" that only sets the security cutoff to 5
    When Kenji validates the fitness config file in "fieldnotes/services/search"
    Then the validation passes

  @ADR-008 @requires_external
  Scenario: The resolver's validation rejects everything the published config format rejects
    Given a set of sample configs the published config format rejects
    When each sample is validated by the resolver
    Then the resolver rejects every sample
