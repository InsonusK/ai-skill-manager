"""Tests for convert_legacy_skill."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, SkillFormat
from ai_skill_manager.entities.skill import Skill as LegacySkill
from ai_skill_manager.entities.skill_conversion import convert_legacy_skill
from ai_skill_manager.entities.skill_kind import SkillKind


class TestConvertLegacySkill(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_converts_flat_skill(self):
        md = self.tmp / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n")
        legacy = LegacySkill(
            file_path=md, folder_path=None, source_path=self.tmp,
            source=LocalSource(scan_path=self.tmp), format=SkillFormat.HumanFlat,
        )

        result = convert_legacy_skill(legacy)

        self.assertEqual(result.name, "guide")
        self.assertEqual(result.kind, SkillKind.flat)
        self.assertEqual(result.path, md.resolve())

    def test_converts_dir_skill(self):
        folder = self.tmp / "web"
        folder.mkdir()
        md = folder / "SKILL.md"
        md.write_text("---\nname: web\n---\n")
        legacy = LegacySkill(
            file_path=md, folder_path=folder, source_path=self.tmp,
            source=LocalSource(scan_path=self.tmp), format=SkillFormat.Agent,
        )

        result = convert_legacy_skill(legacy)

        self.assertEqual(result.name, "web")
        self.assertEqual(result.kind, SkillKind.dir)
        self.assertEqual(result.path, folder.resolve())
        self.assertEqual(result.main_file_relative_path, Path("SKILL.md"))

    def test_raises_when_name_missing(self):
        md = self.tmp / "guide.skill.md"
        md.write_text("# no frontmatter\n")
        legacy = LegacySkill(
            file_path=md, folder_path=None, source_path=self.tmp,
            source=LocalSource(scan_path=self.tmp), format=SkillFormat.HumanFlat,
        )

        with self.assertRaises(ValueError):
            convert_legacy_skill(legacy)


if __name__ == "__main__":
    unittest.main()
