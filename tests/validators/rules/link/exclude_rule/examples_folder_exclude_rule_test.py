"""Tests for SkipFolderExcludeRule default behaviour (examples folder)."""

import unittest
from pathlib import Path

from ai_skill_manager.service.link_discovery import search_links_in_content
from ai_skill_manager.models import LinkWithContext
from ai_skill_manager.validators.rules.link.exclude_rule import SkipFolderExcludeRule


class TestExamplesFolderExcludeRule(unittest.TestCase):
    def _context(self, relative_dir: str) -> LinkWithContext:
        content = "---\nname: skill\n---\n# Skill\n[file](./file.md)\n"
        file_path = Path("/repo") / relative_dir / "SKILL.md"
        link = search_links_in_content(content)[0]
        return LinkWithContext.build(file_path, content, link)

    def test_default_skips_examples_folder(self):
        rule = SkipFolderExcludeRule()

        self.assertTrue(rule.should_exclude(self._context("skill/examples")))

    def test_default_does_not_skip_other_folders(self):
        rule = SkipFolderExcludeRule()

        self.assertFalse(rule.should_exclude(self._context("skill/docs")))

    def test_empty_list_disables_exclusions(self):
        rule = SkipFolderExcludeRule(skip_folders=[])

        self.assertFalse(rule.should_exclude(self._context("skill/examples")))

    def test_custom_folder_overrides_default(self):
        rule = SkipFolderExcludeRule(skip_folders=["another_folder"])

        self.assertTrue(rule.should_exclude(self._context("skill/another_folder")))

    def test_custom_folder_does_not_skip_examples(self):
        rule = SkipFolderExcludeRule(skip_folders=["another_folder"])

        self.assertFalse(rule.should_exclude(self._context("skill/examples")))


if __name__ == "__main__":
    unittest.main()
