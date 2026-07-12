"""Tests for NameValidationRule."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.validators.rules.name_validator import NameValidationRule


class TestNameValidationRule(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill(
        self,
        file_path: Path,
        folder_path: Path | None = None,
        name: str = "skill",
        fmt: SkillFormat | None = None,
    ) -> Skill:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(f"---\nname: {name}\n---\n# {name}\n")
        if fmt is None:
            fmt = SkillFormat.Agent if folder_path else SkillFormat.HumanFlat
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(scan_path=file_path.parent),
            format=fmt,
            source_path=file_path.parent,
        )

    def test_agent_valid_name(self):
        skill_dir = self.tmpdir / "skill"
        skill_dir.mkdir()
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, name="skill")
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(result, {})

    def test_agent_invalid_folder_name(self):
        skill_dir = self.tmpdir / "wrong"
        skill_dir.mkdir()
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, name="skill")
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(len(result), 1)
        self.assertTrue(list(result.values())[0].has_errors)

    def test_flat_valid_name(self):
        md = self.tmpdir / "guide.skill.md"
        skill = self._skill(md, None, name="guide")
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(result, {})

    def test_flat_invalid_file_name(self):
        md = self.tmpdir / "guide.skill.md"
        skill = self._skill(md, None, name="other")
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(len(result), 1)
        self.assertTrue(list(result.values())[0].has_errors)

    def test_dir_valid_name(self):
        skill_dir = self.tmpdir / "guide.skill"
        skill_dir.mkdir()
        skill = self._skill(skill_dir / "guide.skill.md", skill_dir, name="guide", fmt=SkillFormat.HumanDir)
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(result, {})

    def test_dir_invalid_folder_and_file_name(self):
        skill_dir = self.tmpdir / "guide.skill"
        skill_dir.mkdir()
        skill = self._skill(skill_dir / "other.skill.md", skill_dir, name="other", fmt=SkillFormat.HumanDir)
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(len(result), 1)
        self.assertTrue(list(result.values())[0].has_errors)

    def test_dir_folder_name_missing_skill_suffix(self):
        skill_dir = self.tmpdir / "guide"
        skill_dir.mkdir()
        skill = self._skill(skill_dir / "guide.skill.md", skill_dir, name="guide", fmt=SkillFormat.HumanDir)
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(len(result), 1)
        self.assertTrue(list(result.values())[0].has_errors)

    def test_dir_multiple_errors(self):
        skill_dir = self.tmpdir / "guide"
        skill_dir.mkdir()
        skill = self._skill(skill_dir / "other.skill.md", skill_dir, name="guide", fmt=SkillFormat.HumanDir)
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(len(result), 1)
        self.assertEqual(len(list(result.values())[0].errors), 2)

    def test_flat_invalid_file_extension(self):
        md = self.tmpdir / "guide.md"
        md.write_text("---\nname: guide\n---\n# Guide\n")
        skill = Skill(
            file_path=md,
            folder_path=None,
            source=LocalSource(scan_path=self.tmpdir),
            format=SkillFormat.HumanFlat,
            source_path=self.tmpdir,
        )
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(len(result), 1)
        self.assertTrue(list(result.values())[0].has_errors)

    def test_missing_name(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\n---\n# Guide\n")
        skill = Skill(
            file_path=md,
            folder_path=None,
            source=LocalSource(scan_path=self.tmpdir),
            format=SkillFormat.HumanFlat,
            source_path=self.tmpdir,
        )
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(len(result), 1)
        self.assertTrue(list(result.values())[0].has_errors)

    def test_is_kebab_case_allows_double_dash_separator(self):
        self.assertTrue(NameValidationRule.is_kebab_case("plateau-async-monolith--project-feature-data-access"))
        self.assertTrue(NameValidationRule.is_kebab_case("a--b"))

    def test_is_kebab_case_rejects_triple_dash(self):
        self.assertFalse(NameValidationRule.is_kebab_case("plateau---invalid"))
        self.assertFalse(NameValidationRule.is_kebab_case("a---b"))

    def test_is_kebab_case_rejects_leading_or_trailing_dash(self):
        self.assertFalse(NameValidationRule.is_kebab_case("-plateau"))
        self.assertFalse(NameValidationRule.is_kebab_case("plateau-"))

    def test_flat_valid_name_with_double_dash(self):
        md = self.tmpdir / "plateau-async-monolith--project-feature-data-access.skill.md"
        skill = self._skill(md, None, name="plateau-async-monolith--project-feature-data-access")
        rule = NameValidationRule()
        result = rule.validate([skill])
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
