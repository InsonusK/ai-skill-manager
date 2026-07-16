import unittest

from ai_skill_manager.service.link_discovery.link_factory import search_links_in_content
from ai_skill_manager.entities.link import LinkData


class TestLinkFactory(unittest.TestCase):
    def test_search_links_sorts_by_offset(self):
        content = "[first](./a.md) [[./b.md|second]]"
        links = search_links_in_content(content)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].raw_path, "./a.md")
        self.assertEqual(links[1].raw_path, "./b.md")

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

        # EN: The factory only parses syntax - it never classifies a raw
        # path as web vs. file, so every result is a plain LinkData with a
        # raw_path string.
        # RU: Фабрика только разбирает синтаксис - она никогда не
        # классифицирует сырой путь как web или файл, поэтому каждый
        # результат - обычный LinkData со строкой raw_path.
        expected = {
            "[relative](./file.md)": {
                "raw_path": "./file.md",
                "text": "relative",
                "format": "markdown",
                "header": None,
                "is_image": False,
            },
            "[absolute](/tmp/absolute.md)": {
                "raw_path": "/tmp/absolute.md",
                "text": "absolute",
                "format": "markdown",
                "header": None,
                "is_image": False,
            },
            "[web](https://example.com)": {
                "raw_path": "https://example.com",
                "text": "web",
                "format": "markdown",
                "header": None,
                "is_image": False,
            },
            "![image](./img.png)": {
                "raw_path": "./img.png",
                "text": "image",
                "format": "markdown",
                "header": None,
                "is_image": True,
            },
            "[[wiki link|text]]": {
                "raw_path": "wiki link",
                "text": "text",
                "format": "wikilink",
                "header": None,
                "is_image": False,
            },
        }

        self.assertEqual(len(links), len(expected))
        for link in links:
            self.assertIsInstance(link, LinkData)
            self.assertIn(link.raw, expected, f"Unexpected link: {link.raw}")
            exp = expected[link.raw]
            self.assertEqual(link.text, exp["text"])
            self.assertEqual(link.format, exp["format"])
            self.assertEqual(link.header, exp["header"])
            self.assertEqual(link.is_image, exp["is_image"])
            self.assertEqual(link.raw_path, exp["raw_path"])

        found_raws = {link.raw for link in links}
        self.assertEqual(found_raws, set(expected.keys()))

    def test_links_inside_example_block_are_still_returned(self):
        # EN: The factory only parses syntax - it does not know about
        # ```example blocks. Excluding links found inside one is
        # ExampleBlockExcludeRule's job, applied later by LinkDiscovery.
        # RU: Фабрика только разбирает синтаксис - она ничего не знает про
        # блоки ```example. Исключение ссылок, найденных внутри такого
        # блока, - задача ExampleBlockExcludeRule, применяемого позже
        # LinkDiscovery.
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
        self.assertEqual(len(links), 4)


if __name__ == "__main__":
    unittest.main()
