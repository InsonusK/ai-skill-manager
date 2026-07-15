"""Tests for markdown/wiki link builders."""

import unittest

from ai_skill_manager.service.link_discovery.builder.markdown import MarkdownLinkBuilder
from ai_skill_manager.entities.link import LinkData


class TestMarkdownLinkBuilder(unittest.TestCase):
    def test_finds_relative_link(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./file.md)")
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], LinkData)
        self.assertEqual(links[0].raw_path, "./file.md")

    def test_finds_image_link(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("![alt](./img.png)")
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0].is_image)

    def test_finds_link_with_fragment(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./file.md#section)")
        self.assertEqual(links[0].raw_path, "./file.md")
        self.assertEqual(links[0].header, "#section")

    def test_finds_web_link_without_classifying_it(self):
        # EN: The builder only finds syntax; deciding a link is a web
        # address is done later, in the classification/exclude step.
        # RU: Сборщик только находит синтаксис; решение о том, что ссылка -
        # веб-адрес, принимается позже, на шаге классификации/исключения.
        builder = MarkdownLinkBuilder()
        links = builder.search("[web](https://example.com)")
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], LinkData)
        self.assertEqual(links[0].raw_path, "https://example.com")

    def test_skill_suffix_raw_path_kept_as_written(self):
        """A link to ``a-b-c.skill`` is parsed as-is; the ``.md`` fallback is
        applied later, during target resolution, not by the builder."""
        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./a-b-c.skill)")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].raw_path, "./a-b-c.skill")

    def test_empty_content_returns_empty(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("")
        self.assertEqual(len(links), 0)

    def test_finds_windows_separator_link(self):
        # EN: Markdown links written with Windows backslashes are parsed
        # as-is; classification happens later.
        # RU: Markdown-ссылки с обратными слешами Windows разбираются
        # как есть; классификация происходит позже.
        builder = MarkdownLinkBuilder()
        links = builder.search("[text](.\\sub\\file.md)")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].raw_path, ".\\sub\\file.md")


if __name__ == "__main__":
    unittest.main()
