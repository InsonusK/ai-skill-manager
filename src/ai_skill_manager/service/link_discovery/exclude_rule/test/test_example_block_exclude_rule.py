"""Tests for ExampleBlockExcludeRule."""

import unittest
from pathlib import Path

from ai_skill_manager.models import LinkWithContext
from ai_skill_manager.service.link_discovery.exclude_rule.example_block_exclude_rule import (
    ExampleBlockExcludeRule,
)
from ai_skill_manager.service.link_discovery.link_factory import search_links_in_content


class TestExampleBlockExcludeRule(unittest.TestCase):
    def setUp(self):
        self.rule = ExampleBlockExcludeRule()
        self.file_path = Path("/repo/skill/SKILL.md")

    def _contexts(self, content: str):
        return [
            LinkWithContext.build(self.file_path, content, link)
            for link in search_links_in_content(content)
        ]

    def test_links_inside_example_block_are_excluded(self):
        content = (
            "# Skill\n"
            "[valid](./outside.md)\n"
            "```example\n"
            "[[ignored link]]\n"
            "[ignored too](./missing.md)\n"
            "```\n"
            "[also valid](./outside.md)\n"
        )
        contexts = self._contexts(content)
        excluded = {ctx.base.raw: self.rule.should_exclude(ctx) for ctx in contexts}

        self.assertFalse(excluded["[valid](./outside.md)"])
        self.assertFalse(excluded["[also valid](./outside.md)"])
        self.assertTrue(excluded["[[ignored link]]"])
        self.assertTrue(excluded["[ignored too](./missing.md)"])

    def test_unclosed_example_block_excludes_to_eof(self):
        content = (
            "[valid](./outside.md)\n"
            "```example\n"
            "[ignored](./missing.md)\n"
        )
        contexts = self._contexts(content)
        excluded = {ctx.base.raw: self.rule.should_exclude(ctx) for ctx in contexts}

        self.assertFalse(excluded["[valid](./outside.md)"])
        self.assertTrue(excluded["[ignored](./missing.md)"])

    def test_indented_example_block_is_excluded(self):
        content = (
            "[valid](./outside.md)\n"
            "   ```example\n"
            "   [[ignored]]\n"
            "   ```\n"
            "[also valid](./outside.md)\n"
        )
        contexts = self._contexts(content)
        excluded = {ctx.base.raw: self.rule.should_exclude(ctx) for ctx in contexts}

        self.assertFalse(excluded["[valid](./outside.md)"])
        self.assertFalse(excluded["[also valid](./outside.md)"])
        self.assertTrue(excluded["[[ignored]]"])

    def test_should_exclude_is_stable_across_repeated_calls(self):
        content = "```example\n[[ignored]]\n```\n"
        ctx = self._contexts(content)[0]

        self.assertTrue(self.rule.should_exclude(ctx))
        self.assertTrue(self.rule.should_exclude(ctx))


if __name__ == "__main__":
    unittest.main()
