"""Tests for InlineCodeExcludeRule."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.models import LinkWithContext
from ai_skill_manager.validators.rules.link.exclude_rule import InlineCodeExcludeRule


class TestInlineCodeExcludeRule(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.skill_file_path = self.tmpdir / "SKILL.md"
        self.skill_file_path.write_text("---\nname: skill\n---\n# Skill\n")
        self.skill = Skill(
            file_path=self.skill_file_path,
            folder_path=self.tmpdir,
            source=LocalSource(scan_path=self.tmpdir, repo_path=self.tmpdir),
            format=SkillFormat.Agent,
            source_path=self.tmpdir,
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_content(self, content: str) -> None:
        self.skill_file_path.write_text(content)

    def _context(self) -> LinkWithContext:
        skill_file = self.skill.files[0]
        return LinkWithContext.build(self.skill, skill_file, skill_file.links[0])

    def test_link_in_inline_code_is_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n`[text](./missing.md)`\n"
        self._write_content(content)
        rule = InlineCodeExcludeRule()

        self.assertTrue(rule.should_exclude(self._context(), [self.skill]))

    def test_link_in_plain_text_is_not_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n[text](./missing.md)\n"
        self._write_content(content)
        rule = InlineCodeExcludeRule()

        self.assertFalse(rule.should_exclude(self._context(), [self.skill]))

    def test_link_in_plain_fenced_block_is_not_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n```\n[text](./missing.md)\n```\n"
        self._write_content(content)
        rule = InlineCodeExcludeRule()

        self.assertFalse(rule.should_exclude(self._context(), [self.skill]))


if __name__ == "__main__":
    unittest.main()
