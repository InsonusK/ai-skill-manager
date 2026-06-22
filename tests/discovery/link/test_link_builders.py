"""Tests for markdown/wiki link builders."""

import unittest

# Import entities first to avoid circular imports when pulling link builders.
from ai_skill_manager.entities.link_kind import LinkKind
from ai_skill_manager.discovery.link.builder.markdown import MarkdownLinkBuilder


class TestMarkdownLinkBuilder(unittest.TestCase):
    def test_finds_relative_link(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./file.md)")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].path, "./file.md")
        self.assertEqual(links[0].kind, LinkKind.relative)

    def test_finds_image_link(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("![alt](./img.png)")
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0].is_image)

    def test_finds_link_with_fragment(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./file.md#section)")
        self.assertEqual(links[0].path, "./file.md")
        self.assertEqual(links[0].header, "#section")

    def test_empty_content_returns_empty(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("")
        self.assertEqual(len(links), 0)


if __name__ == "__main__":
    unittest.main()
