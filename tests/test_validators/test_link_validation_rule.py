"""Tests for LinkValidationRule."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.validators.rules.link_validation_rule import LinkValidationRule


MOCK_DIR = Path(__file__).parent.parent / "mock" / "test_link_validation_rule"


class TestLinkValidationRule(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def _skill(self, file_path: Path, folder_path: Path | None = None) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(path=file_path.parent),
            format=SkillFormat.Agent if folder_path else SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def _dir_skill(self, root: Path, name: str) -> Skill:
        skill_dir = root / name
        return self._skill(skill_dir / "SKILL.md", skill_dir)

    def test_internal_link_is_valid(self):
        root = self._copy_mock("internal_link")
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertEqual(result, {})

    def test_cross_skill_link_is_valid(self):
        root = self._copy_mock("cross_skill")
        a = self._dir_skill(root, "skill-a")
        b = self._dir_skill(root, "skill-b")

        rule = LinkValidationRule()
        result = rule.validate([a, b])

        self.assertEqual(result, {})

    def test_external_url_is_valid(self):
        root = self._copy_mock("external_url")
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertEqual(result, {})

    def test_link_outside_skill_set_is_invalid(self):
        root = self._copy_mock("outside_skill")
        skill = self._dir_skill(root, "skill")

        rule = LinkValidationRule()
        result = rule.validate([skill])

        self.assertIn(skill, result)
        self.assertTrue(result[skill].has_errors)

    def test_wiki_link_to_other_skill_is_valid(self):
        root = self._copy_mock("wiki_link")
        a = self._dir_skill(root, "skill-a")
        b = self._dir_skill(root, "skill-b")

        rule = LinkValidationRule()
        result = rule.validate([a, b])

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
