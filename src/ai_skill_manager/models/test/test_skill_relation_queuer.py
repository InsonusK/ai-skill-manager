"""Tests for SkillRelationQueuer."""

import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.models.skill_relation_queuer import SkillRelationQueuer


class TestSkillRelationQueuer(unittest.TestCase):
    def setUp(self):
        self.candidate = Skill(name="other", path=Path("/repo/other.skill.md"), kind=SkillKind.flat)

    def test_queues_when_add_relations_enabled_and_name_unqueued(self):
        queuer = SkillRelationQueuer(add_relations=True)
        result = queuer.handle(self.candidate)
        self.assertTrue(result.queued)
        self.assertIsNone(result.error)
        self.assertEqual(queuer.queue, [self.candidate])

    def test_does_not_queue_when_add_relations_disabled(self):
        queuer = SkillRelationQueuer(add_relations=False)
        result = queuer.handle(self.candidate)
        self.assertFalse(result.queued)
        self.assertIsNotNone(result.error)
        self.assertEqual(queuer.queue, [])

    def test_errors_when_name_already_queued_under_a_different_skill(self):
        other = Skill(name="other", path=Path("/repo/elsewhere/other.skill.md"), kind=SkillKind.flat)
        queuer = SkillRelationQueuer(add_relations=True, queue=[other])
        result = queuer.handle(self.candidate)
        self.assertFalse(result.queued)
        self.assertIsNotNone(result.error)

    def test_no_op_when_the_exact_same_skill_is_already_queued(self):
        queuer = SkillRelationQueuer(add_relations=True, queue=[self.candidate])
        result = queuer.handle(self.candidate)
        self.assertFalse(result.queued)
        self.assertIsNone(result.error)
        self.assertEqual(queuer.queue, [self.candidate])

    def test_defaults_to_empty_queue(self):
        queuer = SkillRelationQueuer(add_relations=True)
        self.assertEqual(queuer.queue, [])

    def test_starting_queue_is_used_as_is(self):
        seed = [self.candidate]
        queuer = SkillRelationQueuer(add_relations=True, queue=seed)
        self.assertIs(queuer.queue, seed)


if __name__ == "__main__":
    unittest.main()
