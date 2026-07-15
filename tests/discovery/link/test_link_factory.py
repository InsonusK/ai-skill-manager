import unittest

from ai_skill_manager.discovery.link.builder.markdown import MarkdownLinkBuilder
from ai_skill_manager.discovery.link.builder.wikilink import WikilinkBuilder
from ai_skill_manager.discovery.link.link_factory import search_links_in_content
from ai_skill_manager.entities.path_kind import PathKind
from ai_skill_manager.entities.link import PathLink, WebLink


class TestLinkFactory(unittest.TestCase):
    def test_search_links_sorts_by_offset(self):
        content = "[first](./a.md) [[./b.md|second]]"
        links = search_links_in_content(content)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].path_raw.path, "./a.md")
        self.assertEqual(links[1].path_raw.path, "./b.md")

    def test_search_links_from_file(self):
        content = (
            "# Mixed\n"
            "[relative](./file.md)\n"
            "[absolute](/tmp/absolute.md)\n"
            "[web](https://example.com)\n"
            "![image](./img.png)\n"
            "[[wiki link|text]]\n"
        )
        links = search_links_in_content(content)

        expected = {
            "[relative](./file.md)": {
                "path_raw": "./file.md",
                "raw_kind": PathKind.relative,
                "text": "relative",
                "format": MarkdownLinkBuilder,
                "header": None,
                "is_image": False,
                "cls": PathLink,
            },
            "[absolute](/tmp/absolute.md)": {
                "path_raw": "/tmp/absolute.md",
                "raw_kind": PathKind.os_absolute,
                "text": "absolute",
                "format": MarkdownLinkBuilder,
                "header": None,
                "is_image": False,
                "cls": PathLink,
            },
            "[web](https://example.com)": {
                "url": "https://example.com",
                "text": "web",
                "format": MarkdownLinkBuilder,
                "header": None,
                "is_image": False,
                "cls": WebLink,
            },
            "![image](./img.png)": {
                "path_raw": "./img.png",
                "raw_kind": PathKind.relative,
                "text": "image",
                "format": MarkdownLinkBuilder,
                "header": None,
                "is_image": True,
                "cls": PathLink,
            },
            "[[wiki link|text]]": {
                "path_raw": "wiki link",
                "raw_kind": PathKind.repo_absolute,
                "text": "text",
                "format": WikilinkBuilder,
                "header": None,
                "is_image": False,
                "cls": PathLink,
            }
        }

        self.assertEqual(len(links), len(expected))
        for link in links:
            self.assertIn(link.raw, expected, f"Unexpected link: {link.raw}")
            exp = expected[link.raw]
            self.assertIsInstance(link, exp["cls"])
            self.assertEqual(link.text, exp["text"])
            self.assertIs(link.format, exp["format"])
            self.assertEqual(link.header, exp["header"])
            self.assertEqual(link.is_image, exp["is_image"])
            if isinstance(link, PathLink):
                self.assertEqual(link.path_raw.path, exp["path_raw"])
                self.assertEqual(link.path_raw.kind, exp["raw_kind"])
            else:
                self.assertEqual(link.url, exp["url"])

        found_raws = {link.raw for link in links}
        self.assertEqual(found_raws, set(expected.keys()))

    def test_links_inside_example_block_are_ignored(self):
        # EN: Markdown/wiki links inside a ```example fenced code block must
        # not be treated as real links.
        # RU: Markdown/wiki-ссылки внутри fenced code block ```example не должны
        # считаться настоящими ссылками.
        content = (
            "# Skill\n"
            "[valid](./outside.md)\n"
            "```example\n"
            "[[ignored link]]\n"
            "[ignored too](./missing.md)\n"
            "```\n"
            "[also valid](./outside.md)\n"
        )
        links = search_links_in_content(content)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].raw, "[valid](./outside.md)")
        self.assertEqual(links[1].raw, "[also valid](./outside.md)")

    def test_example_block_without_closing_fence_is_ignored_to_eof(self):
        # EN: An unclosed ```example block must hide links up to the end of
        # the file.
        # RU: Незакрытый блок ```example должен скрывать ссылки до конца файла.
        content = (
            "[valid](./outside.md)\n"
            "```example\n"
            "[ignored](./missing.md)\n"
        )
        links = search_links_in_content(content)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].raw, "[valid](./outside.md)")

    def test_example_block_preserves_offsets_for_replacement(self):
        # EN: Masking ```example blocks must not change link offsets so that
        # later adapters can still replace links correctly.
        # RU: Маскирование блоков ```example не должно менять смещения ссылок,
        # чтобы последующие адаптеры могли корректно заменять ссылки.
        content = (
            "[first](./outside.md)\n"
            "```example\n"
            "[ignored](./missing.md)\n"
            "```\n"
            "[second](./outside.md)\n"
        )
        links = search_links_in_content(content)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].raw, "[first](./outside.md)")
        self.assertEqual(links[0].start, content.index("[first"))
        self.assertEqual(links[1].raw, "[second](./outside.md)")
        self.assertEqual(links[1].start, content.index("[second"))

    def test_indented_example_block_is_ignored(self):
        # EN: A ```example block indented by up to three spaces must also hide
        # its links.
        # RU: Блок ```example с отступом до трёх пробелов также должен скрывать
        # находящиеся в нём ссылки.
        content = (
            "[valid](./outside.md)\n"
            "   ```example\n"
            "   [[ignored]]\n"
            "   ```\n"
            "[also valid](./outside.md)\n"
        )
        links = search_links_in_content(content)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].raw, "[valid](./outside.md)")
        self.assertEqual(links[1].raw, "[also valid](./outside.md)")


if __name__ == "__main__":
    unittest.main()
