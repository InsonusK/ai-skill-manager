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

        errors = self.discovery.discover(skill, repo_path=self.tmp, known_skills={}, queue=[], add_relations=False)

        self.assertEqual(errors, [])
        self.assertEqual(len(skill.files), 1)
        self.assertIsInstance(skill.files[0], MarkdownSkillFile)
        self.assertTrue(skill.is_main_file(skill.files[0].path))

    def test_dir_skill_gets_all_nested_files(self):
        folder = self.tmp / "web"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: web\n---\n# Web\n")
        (folder / "data.json").write_text("{}")
        (folder / "docs").mkdir()
        (folder / "docs" / "extra.md").write_text("# Extra\n")
        skill = Skill(name="web", path=folder, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))

        errors = self.discovery.discover(skill, repo_path=self.tmp, known_skills={}, queue=[], add_relations=False)

        self.assertEqual(errors, [])
        names = {f.name for f in skill.files}
        self.assertEqual(names, {"SKILL.md", "data.json", "extra.md"})
        by_name = {f.name: f for f in skill.files}
        self.assertIsInstance(by_name["SKILL.md"], MarkdownSkillFile)
        self.assertIsInstance(by_name["extra.md"], MarkdownSkillFile)
        self.assertNotIsInstance(by_name["data.json"], MarkdownSkillFile)
        self.assertEqual(by_name["data.json"].__class__, SkillFile)

    def test_enriches_markdown_files_with_links(self):
        skill_b_dir = self.tmp / "skill-b"
        skill_b_dir.mkdir()
        (skill_b_dir / "SKILL.md").write_text("---\n")
        skill_b = Skill(name="skill-b", path=skill_b_dir, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))

        folder = self.tmp / "skill-a"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: skill-a\n---\n[b](../skill-b/SKILL.md)\n")
        skill_a = Skill(name="skill-a", path=folder, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))

        errors = self.discovery.discover(
            skill_a, repo_path=self.tmp, known_skills={"skill-b": skill_b}, queue=[], add_relations=False,
        )

        self.assertEqual(errors, [])
        main_file = next(f for f in skill_a.files if f.name == "SKILL.md")
        self.assertEqual(len(main_file.links), 1)

    def test_collects_link_errors_without_stopping(self):
        folder = self.tmp / "skill-a"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: skill-a\n---\n[bad](../nowhere.md)\n")
        (folder / "notes.md").write_text("# Notes\n[also-bad](../also-nowhere.md)\n")
        skill = Skill(name="skill-a", path=folder, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))

        errors = self.discovery.discover(skill, repo_path=self.tmp, known_skills={}, queue=[], add_relations=False)

        self.assertEqual(len(errors), 2)
        # Both files were still processed despite the first file's error.
        self.assertEqual(len(skill.files), 2)


if __name__ == "__main__":
    unittest.main()
