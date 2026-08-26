Feature: Skill relation queuer decides whether to queue linked skills

  Scenario: A new linked skill is queued when relation discovery is enabled
    Given relation discovery is enabled
    And no skills are queued yet
    When the queuer handles a linked skill named "linked-skill"
    Then the skill is queued

  Scenario: The same skill already queued is a no-op
    Given relation discovery is enabled
    And a skill named "linked-skill" is already queued at "/tmp/skills/linked-skill"
    When the queuer handles the same skill at "/tmp/skills/linked-skill"
    Then the skill is not queued again
    And there is no error

  Scenario: A different skill with the same name is rejected
    Given relation discovery is enabled
    And a skill named "linked-skill" is already queued at "/tmp/skills/first"
    When the queuer handles a different skill named "linked-skill" at "/tmp/skills/second"
    Then the skill is not queued
    And the error reports a conflict with "linked-skill"

  Scenario: A linked skill outside configured sources is rejected when relation discovery is disabled
    Given relation discovery is disabled
    And no skills are queued yet
    When the queuer handles a linked skill named "external-skill"
    Then the skill is not queued
    And the error reports the skill is not in configured sources
