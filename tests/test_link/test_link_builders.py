"""Tests for markdown/wiki link builders."""

import unittest
from pathlib import Path

# Import entities first to avoid circular imports when pulling link builders.
from ai_skill_manager.entities.link_kind import LinkKind
from ai_skill_manager.discovery.link.factory.builder.markdown import MarkdownLinkBuilder
from ai_skill_manager.discovery.link.factory.builder.wikilink import WikilinkBuilder
from ai_skill_manager.discovery.link.factory.link_factory import search_links_in_content


MOCK_DIR = Path(__file__).parent.parent / "mock" / "test_link_builders"


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


class TestWikilinkBuilder(unittest.TestCase):
    def test_finds_wiki_link(self):
        builder = WikilinkBuilder()
        links = builder.search("[[./file.md|text]]")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].path, "./file.md")
        self.assertEqual(links[0].kind, LinkKind.relative)

    def test_finds_wiki_link_without_text(self):
        builder = WikilinkBuilder()
        links = builder.search("[[./file.md]]")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].path, "./file.md")

    def test_empty_content_returns_empty(self):
        builder = WikilinkBuilder()
        links = builder.search("")
        self.assertEqual(len(links), 0)


class TestLinkFactory(unittest.TestCase):
    def test_search_links_sorts_by_offset(self):
        content = "[first](./a.md) [[./b.md|second]]"
        links = search_links_in_content(content)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].path, "./a.md")
        self.assertEqual(links[1].path, "./b.md")

    def test_search_links_from_file(self):
        content = (MOCK_DIR / "mixed_links.md").read_text()
        links = search_links_in_content(content)
        paths = {link.path for link in links}
        self.assertIn("./file.md", paths)
        self.assertIn("./img.png", paths)
        self.assertIn("https://example.com", paths)
        self.assertIn("./file.md", paths)  # wiki link resolves to same


if __name__ == "__main__":
    unittest.main()
