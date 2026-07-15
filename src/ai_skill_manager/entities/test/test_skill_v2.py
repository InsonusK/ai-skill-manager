"""Tests for the new Skill entity (name, path, kind, files)."""

import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill


class TestSkill(unittest.TestCase):
    def test_stores_name_path_kind(self):
        skill = Skill(name="my-skill", path=Path("/repo/my-skill"), kind=SkillKind.dir)
        self.assertEqual(skill.name, "my-skill")
        self.assertEqual(skill.path, Path("/repo/my-skill"))
        self.assertEqual(skill.kind, SkillKind.dir)

    def test_files_default_to_empty(self):
        skill = Skill(name="my-skill", path=Path("/repo/my-skill"), kind=SkillKind.dir)
        self.assertEqual(skill.files, [])

    def test_files_can_be_set_after_construction(self):
        skill = Skill(name="my-skill", path=Path("/repo/my-skill"), kind=SkillKind.dir)
        skill.files.append("placeholder")
        self.assertEqual(skill.files, ["placeholder"])

    def test_rejects_invalid_name(self):
        with self.assertRaises(ValueError):
            Skill(name="My_Skill", path=Path("/repo/my-skill"), kind=SkillKind.dir)

    def test_rejects_empty_name(self):
        with self.assertRaises(ValueError):
            Skill(name="", path=Path("/repo/my-skill"), kind=SkillKind.dir)

    def test_flat_skill_kind(self):
        skill = Skill(name="my-skill", path=Path("/repo/my-skill.skill.md"), kind=SkillKind.flat)
        self.assertEqual(skill.kind, SkillKind.flat)

    def test_is_hashable_by_identity_fields(self):
        a = Skill(name="my-skill", path=Path("/repo/my-skill"), kind=SkillKind.dir)
        b = Skill(name="my-skill", path=Path("/repo/my-skill"), kind=SkillKind.dir)
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(a, b)

    def test_flat_skill_main_file_is_none_or_dot(self):
        skill = Skill(name="my-skill", path=Path("/repo/my-skill.skill.md"), kind=SkillKind.flat)
        self.assertTrue(skill.is_main_file(None))
        self.assertFalse(skill.is_main_file(Path("other.md")))

    def test_dir_skill_main_file_matches_recorded_relative_path(self):
        skill = Skill(
            name="web",
            path=Path("/repo/web.skill"),
            kind=SkillKind.dir,
            main_file_relative_path=Path("web.skill.md"),
        )
        self.assertTrue(skill.is_main_file(Path("web.skill.md")))
        self.assertFalse(skill.is_main_file(Path("docs/extra.md")))


if __name__ == "__main__":
    unittest.main()
