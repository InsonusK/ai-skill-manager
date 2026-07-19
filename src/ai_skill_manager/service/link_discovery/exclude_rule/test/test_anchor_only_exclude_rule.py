"""Tests for AnchorOnlyExcludeRule."""

import unittest
from pathlib import Path

from ai_skill_manager.service.link_discovery import search_links_in_content
from ai_skill_manager.models import LinkWithContext
from ai_skill_manager.service.link_discovery.exclude_rule import AnchorOnlyExcludeRule


class TestAnchorOnlyExcludeRule(unittest.TestCase):
    def _context(self, content: str) -> LinkWithContext:
        link = search_links_in_content(content)[0]
        return LinkWithContext.build(Path("/repo/SKILL.md"), content, link)

    def test_anchor_only_markdown_link_is_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n[TOC](#section)\n"
        rule = AnchorOnlyExcludeRule()

        self.assertTrue(rule.should_exclude(self._context(content)))

    def test_anchor_only_wikilink_is_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n[[#section]]\n"
        rule = AnchorOnlyExcludeRule()

        self.assertTrue(rule.should_exclude(self._context(content)))

    def test_path_link_is_not_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n[file](./file.md)\n"
        rule = AnchorOnlyExcludeRule()

        self.assertFalse(rule.should_exclude(self._context(content)))

    def test_path_link_with_fragment_is_not_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n[file](./file.md#section)\n"
        rule = AnchorOnlyExcludeRule()

        self.assertFalse(rule.should_exclude(self._context(content)))


if __name__ == "__main__":
    unittest.main()
