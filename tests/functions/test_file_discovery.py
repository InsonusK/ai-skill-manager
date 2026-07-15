"""Tests for FileDiscovery."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_file_v2 import MarkdownSkillFile, SkillFile
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.functions.file_discovery import FileDiscovery


class TestFileDiscovery(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.discovery = FileDiscovery()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_flat_skill_gets_a_single_markdown_file(self):
        md = self.tmp / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide\n")
        skill = Skill(name="guide", path=md, kind=SkillKind.flat)

        self.discovery.discover(skill)

        self.assertEqual(len(skill.files), 1)
        self.assertIsInstance(skill.files[0], MarkdownSkillFile)
        self.assertEqual(skill.files[0].links, [])
        self.assertTrue(skill.is_main_file(skill.files[0].path))

    def test_dir_skill_gets_all_nested_files(self):
        folder = self.tmp / "web"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: web\n---\n# Web\n")
        (folder / "data.json").write_text("{}")
        (folder / "docs").mkdir()
        (folder / "docs" / "extra.md").write_text("# Extra\n")
        skill = Skill(name="web", path=folder, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))

        self.discovery.discover(skill)

        names = {f.name for f in skill.files}
        self.assertEqual(names, {"SKILL.md", "data.json", "extra.md"})
        by_name = {f.name: f for f in skill.files}
        self.assertIsInstance(by_name["SKILL.md"], MarkdownSkillFile)
        self.assertIsInstance(by_name["extra.md"], MarkdownSkillFile)
        self.assertNotIsInstance(by_name["data.json"], MarkdownSkillFile)
        self.assertEqual(by_name["data.json"].__class__, SkillFile)


if __name__ == "__main__":
    unittest.main()
