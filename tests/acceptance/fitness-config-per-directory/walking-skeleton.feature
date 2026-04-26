# Walking Skeleton — fitness-config-per-directory
#
# ONE end-to-end scenario exercising the driving port (CLI: fitness-config.py
# show --path <target>). User-centric: Devin sees that his module-specific
# weights win over the root config when he previews resolution for a file
# inside that module.
#
# This skeleton is NOT skipped. It drives Feature 0 build and forces the
# software-crafter to wire walk-up + deep-merge + reporter end-to-end.
#
# Litmus test (Dim 5): "Devin previews module-specific weights for a Postgres
# review" — a non-technical stakeholder confirms "yes, that is what users need."

@walking-skeleton @real-io @adapter-integration @US-01 @US-02 @US-04
Feature: Devin previews module-specific weights before reviewing his Postgres module

  As Devin Park, an infrastructure engineer maintaining a multi-module repo,
  I want to preview the resolved fitness config for a file in my Postgres
  module, so that I can confirm module-specific weights apply before running
  a full review.

  Scenario: Devin previews module-specific weights for a Postgres review target
    Given the repo has a root fitness-config.json with weights "architecture=14, security=14, reliability=10, testing=10, performance=10, algorithms=10, data=10, accessibility=8, process=8, maintainability=6"
    And a module override at "infrastructure/modules/postgresql/fitness-config.json" sets weights "architecture=14, security=14, reliability=20, testing=10, performance=6, algorithms=4, data=30, accessibility=0, process=1, maintainability=1"
    And the file "infrastructure/modules/postgresql/main.tf" exists
    When Devin previews the resolved config for "infrastructure/modules/postgresql/main.tf"
    Then the preview confirms the override applies on top of the root
    And the effective weights show "data" at 30 and "reliability" at 20
    And the effective weights sum to 100
    And the preview names the module config as the highest-precedence source
    And the preview names the root config as the next source in precedence
