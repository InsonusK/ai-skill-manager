"""Tests for the new SkillFile / MarkdownSkillFile entities."""

import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_file_v2 import MarkdownSkillFile, SkillFile


class TestSkillFile(unittest.TestCase):
    def test_stores_name_and_relative_path(self):
        f = SkillFile(name="data.json", path=Path("data.json"))
        self.assertEqual(f.name, "data.json")
        self.assertEqual(f.path, Path("data.json"))

    def test_nested_relative_path(self):
        f = SkillFile(name="extra.md", path=Path("docs/extra.md"))
        self.assertEqual(f.path, Path("docs/extra.md"))

    def test_equality_by_path(self):
        a = SkillFile(name="data.json", path=Path("data.json"))
        b = SkillFile(name="data.json", path=Path("data.json"))
        self.assertEqual(a, b)


class TestMarkdownSkillFile(unittest.TestCase):
    def test_is_a_skill_file(self):
        f = MarkdownSkillFile(name="SKILL.md", path=Path("SKILL.md"))
        self.assertIsInstance(f, SkillFile)

    def test_links_default_to_empty(self):
        f = MarkdownSkillFile(name="SKILL.md", path=Path("SKILL.md"))
        self.assertEqual(f.links, [])

    def test_links_can_be_set_after_construction(self):
        f = MarkdownSkillFile(name="SKILL.md", path=Path("SKILL.md"))
        f.links.append("placeholder")
        self.assertEqual(f.links, ["placeholder"])


if __name__ == "__main__":
    unittest.main()
