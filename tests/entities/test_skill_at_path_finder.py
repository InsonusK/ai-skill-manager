"""Tests for SkillAtPathFinder."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_at_path_finder import SkillAtPathFinder
from ai_skill_manager.entities.skill_kind import SkillKind


class TestSkillAtPathFinder(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.finder = SkillAtPathFinder()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_finds_flat_skill_at_its_own_file(self):
        md = self.tmp / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n")

        result = self.finder.find(md)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "guide")
        self.assertEqual(result.kind, SkillKind.flat)

    def test_finds_dir_skill_at_its_folder(self):
        folder = self.tmp / "web"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: web\n---\n")

        result = self.finder.find(folder)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "web")
        self.assertEqual(result.kind, SkillKind.dir)

    def test_finds_dir_skill_at_its_main_file_directly(self):
        folder = self.tmp / "web"
        folder.mkdir()
        main_file = folder / "SKILL.md"
        main_file.write_text("---\nname: web\n---\n")

        result = self.finder.find(main_file)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "web")
        self.assertEqual(result.kind, SkillKind.dir)

    def test_returns_none_for_a_plain_file(self):
        plain = self.tmp / "notes.md"
        plain.write_text("# notes\n")

        result = self.finder.find(plain)

        self.assertIsNone(result)

    def test_returns_none_for_a_plain_directory(self):
        plain = self.tmp / "assets"
        plain.mkdir()
        (plain / "image.png").write_text("png")

        result = self.finder.find(plain)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
