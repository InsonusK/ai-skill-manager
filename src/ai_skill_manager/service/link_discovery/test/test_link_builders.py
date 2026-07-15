"""Tests for markdown/wiki link builders."""

import unittest

from ai_skill_manager.service.link_discovery.builder.markdown import MarkdownLinkBuilder
from ai_skill_manager.entities.path_kind import PathKind
from ai_skill_manager.entities.link import PathLink, WebLink


class TestMarkdownLinkBuilder(unittest.TestCase):
    def test_finds_relative_link(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./file.md)")
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], PathLink)
        self.assertEqual(links[0].path_raw.path, "./file.md")
        self.assertEqual(links[0].path_raw.kind, PathKind.relative)

    def test_finds_image_link(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("![alt](./img.png)")
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0].is_image)
        self.assertIsInstance(links[0], PathLink)

    def test_finds_link_with_fragment(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./file.md#section)")
        self.assertEqual(links[0].path_raw.path, "./file.md")
        self.assertEqual(links[0].header, "#section")

    def test_finds_web_link(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("[web](https://example.com)")
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], WebLink)
        self.assertEqual(links[0].url, "https://example.com")

    def test_skill_suffix_raw_path_kept_as_written(self):
        """A link to ``a-b-c.skill`` is parsed as-is; the ``.md`` fallback is
        applied later, during target resolution, not by the builder."""
        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./a-b-c.skill)")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].path_raw.path, "./a-b-c.skill")

    def test_empty_content_returns_empty(self):
        builder = MarkdownLinkBuilder()
        links = builder.search("")
        self.assertEqual(len(links), 0)

    def test_link_type_property(self):
        """absLink.link_type returns the concrete class."""
        builder = MarkdownLinkBuilder()
        path_link = builder.search("[text](./file.md)")[0]
        web_link = builder.search("[web](https://example.com)")[0]

        self.assertIs(path_link.link_type, PathLink)
        self.assertIs(web_link.link_type, WebLink)

    def test_finds_windows_separator_link(self):
        # EN: Markdown links written with Windows backslashes are classified
        # exactly like POSIX links.
        # RU: Markdown-ссылки с обратными слешами Windows классифицируются
        # точно так же, как POSIX-ссылки.
        builder = MarkdownLinkBuilder()
        links = builder.search("[text](.\\sub\\file.md)")
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], PathLink)
        self.assertEqual(links[0].path_raw.path, ".\\sub\\file.md")
        self.assertEqual(links[0].path_raw.kind, PathKind.relative)

    def test_base_helper_methods_handle_windows_separators(self):
        # EN: The protected helpers used by builders must accept Windows
        # backslashes the same way as POSIX separators.
        # RU: Защищённые хелперы, используемые сборщиками, должны принимать
        # обратные слеши Windows так же, как POSIX-разделители.
        builder = MarkdownLinkBuilder()
        self.assertTrue(builder._is_relative(".\\file.md"))
        self.assertTrue(builder._is_relative("..\\file.md"))
        self.assertTrue(builder._is_relative("./file.md"))
        self.assertTrue(builder._is_os_absolute("/tmp/file.md"))
        self.assertEqual(builder._get_kind(".\\file.md"), PathKind.relative)
        self.assertEqual(builder._get_kind("/tmp/file.md"), PathKind.os_absolute)
        self.assertEqual(builder._get_kind("file.md"), PathKind.repo_absolute)


if __name__ == "__main__":
    unittest.main()
