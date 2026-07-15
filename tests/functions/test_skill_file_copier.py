"""Tests for SkillFileCopier."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.functions.file_discovery import discover as discover_files
from ai_skill_manager.functions.skill_file_copier import SkillFileCopier


class TestSkillFileCopier(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.target_dir = self.tmp / "target"
        self.copier = SkillFileCopier()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_copies_flat_skill_as_skill_md(self):
        md = self.tmp / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide\n")
        skill = Skill(name="guide", path=md, kind=SkillKind.flat)
        skill.files.extend(discover_files(skill))

        skill_target_dir = self.copier.copy(skill, self.target_dir)

        self.assertEqual(skill_target_dir, self.target_dir / "guide")
        self.assertTrue((skill_target_dir / "SKILL.md").exists())
        self.assertIn("# Guide", (skill_target_dir / "SKILL.md").read_text())

    def test_copies_dir_skill_preserving_nested_structure(self):
        folder = self.tmp / "web"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: web\n---\n# Web\n")
        (folder / "docs").mkdir()
        (folder / "docs" / "extra.md").write_text("# Extra\n")
        skill = Skill(name="web", path=folder, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        skill.files.extend(discover_files(skill))

        skill_target_dir = self.copier.copy(skill, self.target_dir)

        self.assertTrue((skill_target_dir / "SKILL.md").exists())
        self.assertTrue((skill_target_dir / "docs" / "extra.md").exists())


if __name__ == "__main__":
    unittest.main()
