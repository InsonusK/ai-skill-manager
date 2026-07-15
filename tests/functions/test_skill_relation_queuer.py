"""Tests for SkillRelationQueuer."""

import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.functions.skill_relation_queuer import SkillRelationQueuer


class TestSkillRelationQueuer(unittest.TestCase):
    def setUp(self):
        self.queuer = SkillRelationQueuer()
        self.candidate = Skill(name="other", path=Path("/repo/other.skill.md"), kind=SkillKind.flat)

    def test_queues_when_add_relations_enabled_and_name_unqueued(self):
        queue = []
        result = self.queuer.handle(self.candidate, queue=queue, add_relations=True)
        self.assertTrue(result.queued)
        self.assertIsNone(result.error)
        self.assertEqual(queue, [self.candidate])

    def test_does_not_queue_when_add_relations_disabled(self):
        queue = []
        result = self.queuer.handle(self.candidate, queue=queue, add_relations=False)
        self.assertFalse(result.queued)
        self.assertIsNotNone(result.error)
        self.assertEqual(queue, [])

    def test_errors_when_name_already_queued_under_a_different_skill(self):
        queue = [Skill(name="other", path=Path("/repo/elsewhere/other.skill.md"), kind=SkillKind.flat)]
        result = self.queuer.handle(self.candidate, queue=queue, add_relations=True)
        self.assertFalse(result.queued)
        self.assertIsNotNone(result.error)

    def test_no_op_when_the_exact_same_skill_is_already_queued(self):
        queue = [self.candidate]
        result = self.queuer.handle(self.candidate, queue=queue, add_relations=True)
        self.assertFalse(result.queued)
        self.assertIsNone(result.error)
        self.assertEqual(queue, [self.candidate])


if __name__ == "__main__":
    unittest.main()
