"""Tests for InlineCodeExcludeRule."""

import unittest
from pathlib import Path

from ai_skill_manager.service.link_discovery import search_links_in_content
from ai_skill_manager.models import LinkWithContext
from ai_skill_manager.validators.rules.link.exclude_rule import InlineCodeExcludeRule


class TestInlineCodeExcludeRule(unittest.TestCase):
    def _context(self, content: str) -> LinkWithContext:
        link = search_links_in_content(content)[0]
        return LinkWithContext.build(Path("/repo/SKILL.md"), content, link)

    def test_link_in_inline_code_is_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n`[text](./missing.md)`\n"
        rule = InlineCodeExcludeRule()

        self.assertTrue(rule.should_exclude(self._context(content)))

    def test_link_in_plain_text_is_not_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n[text](./missing.md)\n"
        rule = InlineCodeExcludeRule()

        self.assertFalse(rule.should_exclude(self._context(content)))

    def test_link_in_plain_fenced_block_is_not_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n```\n[text](./missing.md)\n```\n"
        rule = InlineCodeExcludeRule()

        self.assertFalse(rule.should_exclude(self._context(content)))


if __name__ == "__main__":
    unittest.main()
