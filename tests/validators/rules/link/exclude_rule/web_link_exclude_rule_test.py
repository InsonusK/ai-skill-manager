"""Tests for WebLinkExcludeRule."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.models import LinkWithContext
from ai_skill_manager.validators.rules.link.exclude_rule import WebLinkExcludeRule


class TestWebLinkExcludeRule(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        skill_file = self.tmpdir / "SKILL.md"
        skill_file.write_text("---\nname: skill\n---\n# Skill\n")
        self.skill = Skill(
            file_path=skill_file,
            folder_path=self.tmpdir,
            source=LocalSource(scan_path=self.tmpdir, repo_path=self.tmpdir),
            format=SkillFormat.Agent,
            source_path=self.tmpdir,
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _context(self) -> LinkWithContext:
        skill_file = self.skill.files[0]
        return LinkWithContext.build(self.skill, skill_file, skill_file.links[0])

    def test_web_link_is_excluded(self):
        self.skill.files[0].path.write_text(
            "---\nname: skill\n---\n# Skill\n[site](https://example.com)\n"
        )
        rule = WebLinkExcludeRule()

        self.assertTrue(rule.should_exclude(self._context(), [self.skill]))

    def test_path_link_is_not_excluded(self):
        self.skill.files[0].path.write_text(
            "---\nname: skill\n---\n# Skill\n[file](./file.md)\n"
        )
        rule = WebLinkExcludeRule()

        self.assertFalse(rule.should_exclude(self._context(), [self.skill]))


if __name__ == "__main__":
    unittest.main()
