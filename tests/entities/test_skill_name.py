"""Tests for ai_skill_manager entities/models."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_propetry import SkillProperty
from . import MOCK_DIR


class TestSkillName(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def test_name_returns_none_when_file_missing(self):
        prop = SkillProperty(self.tmpdir / "missing.skill.md")
        self.assertIsNone(prop.name)

    def test_name_returns_none_without_frontmatter(self):
        md = self._copy_mock("name_no_frontmatter") / "guide.skill.md"
        self.assertIsNone(SkillProperty(md).name)

    def test_name_returns_none_with_missing_terminator(self):
        md = self._copy_mock("name_missing_terminator") / "guide.skill.md"
        self.assertIsNone(SkillProperty(md).name)

    def test_name_returns_none_with_invalid_yaml(self):
        md = self._copy_mock("name_invalid_yaml") / "guide.skill.md"
        self.assertIsNone(SkillProperty(md).name)

    def test_name_returns_none_when_frontmatter_is_not_dict(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\n- list\n---\n# Guide")
        self.assertIsNone(SkillProperty(md).name)

    def test_name_returns_none_when_name_is_missing(self):
        md = self._copy_mock("name_missing") / "guide.skill.md"
        self.assertIsNone(SkillProperty(md).name)

    def test_name_returns_none_when_name_is_not_string(self):
        md = self._copy_mock("name_not_string") / "guide.skill.md"
        self.assertIsNone(SkillProperty(md).name)

    def test_name_returns_value_from_frontmatter(self):
        md = self._copy_mock("name_value") / "guide.skill.md"
        self.assertEqual(SkillProperty(md).name, "guide")

    def test_name_reads_crlf_frontmatter(self):
        md = self._copy_mock("name_crlf") / "guide.skill.md"
        self.assertEqual(SkillProperty(md).name, "guide")


if __name__ == "__main__":
    unittest.main()
