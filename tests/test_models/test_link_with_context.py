"""Tests for LinkWithContext."""

import unittest
from pathlib import Path

from ai_skill_manager.service.link_discovery.builder.markdown import MarkdownLinkBuilder
from ai_skill_manager.entities.link import PathLink
from ai_skill_manager.models.link_with_context import LinkWithContext


class TestLinkWithContext(unittest.TestCase):
    def _link(self) -> PathLink:
        return PathLink(
            raw="[text](./file.md)",
            text="text",
            format=MarkdownLinkBuilder,
            start=0,
            end=1,
            raw_path="./file.md",
        )

    def test_build_stores_file_location_and_link(self):
        file_path = Path("/repo/skill/SKILL.md")
        content = "[text](./file.md)"
        link = self._link()

        ctx = LinkWithContext.build(file_path, content, link)

        self.assertEqual(ctx.file_path, file_path)
        self.assertEqual(ctx.content, content)
        self.assertIs(ctx.base, link)

    def test_getattr_forwards_to_base_and_raises(self):
        """Attribute access forwards to the wrapped link and raises sensibly."""
        ctx = LinkWithContext.build(Path("/repo/SKILL.md"), "content", self._link())

        self.assertEqual(ctx.raw, "[text](./file.md)")
        with self.assertRaises(AttributeError):
            _ = ctx.nonexistent_attribute


if __name__ == "__main__":
    unittest.main()
