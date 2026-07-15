"""Tests for WebLinkExcludeRule."""

import unittest
from pathlib import Path

from ai_skill_manager.service.link_discovery import search_links_in_content
from ai_skill_manager.models import LinkWithContext
from ai_skill_manager.service.link_discovery.exclude_rule import WebLinkExcludeRule


class TestWebLinkExcludeRule(unittest.TestCase):
    def _context(self, content: str) -> LinkWithContext:
        link = search_links_in_content(content)[0]
        return LinkWithContext.build(Path("/repo/SKILL.md"), content, link)

    def test_web_link_is_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n[site](https://example.com)\n"
        rule = WebLinkExcludeRule()

        self.assertTrue(rule.should_exclude(self._context(content)))

    def test_path_link_is_not_excluded(self):
        content = "---\nname: skill\n---\n# Skill\n[file](./file.md)\n"
        rule = WebLinkExcludeRule()

        self.assertFalse(rule.should_exclude(self._context(content)))


if __name__ == "__main__":
    unittest.main()
