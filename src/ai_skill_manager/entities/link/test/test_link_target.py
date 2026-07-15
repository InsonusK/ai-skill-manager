"""Tests for LinkTarget (SkillLinkTarget / ExternalLinkTarget)."""

import unittest
from pathlib import Path

from ai_skill_manager.entities.link.link_target import ExternalLinkTarget, SkillLinkTarget


class TestSkillLinkTarget(unittest.TestCase):
    def test_stores_skill_name_and_relative_path(self):
        target = SkillLinkTarget(skill_name="skill-b", relative_path=Path("docs/extra.md"))
        self.assertEqual(target.skill_name, "skill-b")
        self.assertEqual(target.relative_path, Path("docs/extra.md"))

    def test_relative_path_none_means_main_file(self):
        target = SkillLinkTarget(skill_name="skill-b", relative_path=None)
        self.assertIsNone(target.relative_path)

    def test_equality(self):
        a = SkillLinkTarget(skill_name="skill-b", relative_path=Path("a.md"))
        b = SkillLinkTarget(skill_name="skill-b", relative_path=Path("a.md"))
        self.assertEqual(a, b)


class TestExternalLinkTarget(unittest.TestCase):
    def test_stores_file_name_and_repo_absolute_path(self):
        target = ExternalLinkTarget(file_name="diagram.png", repo_absolute_path=Path("assets/diagram.png"))
        self.assertEqual(target.file_name, "diagram.png")
        self.assertEqual(target.repo_absolute_path, Path("assets/diagram.png"))

    def test_not_equal_to_skill_link_target(self):
        external = ExternalLinkTarget(file_name="a.md", repo_absolute_path=Path("a.md"))
        skill = SkillLinkTarget(skill_name="a", relative_path=Path("a.md"))
        self.assertNotEqual(external, skill)


if __name__ == "__main__":
    unittest.main()
