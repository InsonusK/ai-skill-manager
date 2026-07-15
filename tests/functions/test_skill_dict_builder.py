"""Tests for SkillDictBuilder."""

import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.functions.skill_dict_builder import SkillDictBuilder


class TestSkillDictBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = SkillDictBuilder()

    def test_adds_new_skills_by_name(self):
        a = Skill(name="skill-a", path=Path("/repo/skill-a"), kind=SkillKind.dir)
        b = Skill(name="skill-b", path=Path("/repo/skill-b"), kind=SkillKind.dir)

        result, errors = self.builder.build([a, b])

        self.assertEqual(result, {"skill-a": a, "skill-b": b})
        self.assertEqual(errors, [])

    def test_errors_on_duplicate_name_with_different_skill(self):
        a1 = Skill(name="skill-a", path=Path("/repo/one/skill-a"), kind=SkillKind.dir)
        a2 = Skill(name="skill-a", path=Path("/repo/two/skill-a"), kind=SkillKind.dir)

        result, errors = self.builder.build([a1, a2])

        self.assertEqual(len(errors), 1)
        self.assertIn("skill-a", errors[0])

    def test_merges_into_existing_dict(self):
        existing_skill = Skill(name="skill-a", path=Path("/repo/skill-a"), kind=SkillKind.dir)
        new_skill = Skill(name="skill-b", path=Path("/repo/skill-b"), kind=SkillKind.dir)

        result, errors = self.builder.build([new_skill], existing={"skill-a": existing_skill})

        self.assertEqual(result, {"skill-a": existing_skill, "skill-b": new_skill})
        self.assertEqual(errors, [])

    def test_no_op_when_the_exact_same_skill_is_added_again(self):
        skill = Skill(name="skill-a", path=Path("/repo/skill-a"), kind=SkillKind.dir)

        result, errors = self.builder.build([skill], existing={"skill-a": skill})

        self.assertEqual(result, {"skill-a": skill})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
