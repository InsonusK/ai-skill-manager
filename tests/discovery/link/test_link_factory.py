from ai_skill_manager.discovery.link.link_factory import search_links_in_content
from ai_skill_manager.entities import LinkKind
from . import MOCK_DIR
import unittest

TESTCASE_MOCK_DIR = MOCK_DIR / "test_link_factory"


class TestLinkFactory(unittest.TestCase):
    def test_search_links_sorts_by_offset(self):
        content = "[first](./a.md) [[./b.md|second]]"
        links = search_links_in_content(content)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].path, "./a.md")
        self.assertEqual(links[1].path, "./b.md")

    def test_search_links_from_file(self):
        content = (TESTCASE_MOCK_DIR / "mixed_links.md").read_text()
        links = search_links_in_content(content)

        expected = {
            "[relative](./file.md)": {
                "path": "./file.md",
                "text": "relative",
                "format": "markdown",
                "kind": LinkKind.relative,
                "header": None,
                "is_image": False,
            },
            "[absolute](/tmp/file.md)": {
                "path": "/tmp/file.md",
                "text": "absolute",
                "format": "markdown",
                "kind": LinkKind.os_absolute,
                "header": None,
                "is_image": False,
            },
            "[web](https://example.com)": {
                "path": "https://example.com",
                "text": "web",
                "format": "markdown",
                "kind": LinkKind.web,
                "header": None,
                "is_image": False,
            },
            "![image](./img.png)": {
                "path": "./img.png",
                "text": "image",
                "format": "markdown",
                "kind": LinkKind.relative,
                "header": None,
                "is_image": True,
            },
            "[[wiki link|text]]": {
                "path": "wiki link",
                "text": "text",
                "format": "wiki",
                "kind": LinkKind.repo_absolute,
                "header": None,
                "is_image": False,
            }
        }
        
        self.assertEqual(len(links), len(expected))
        for link in links:
            self.assertIn(link.raw, expected, f"Unexpected link: {link.raw}")
            exp = expected[link.raw]
            self.assertEqual(link.path, exp["path"])
            self.assertEqual(link.text, exp["text"])
            self.assertEqual(link.format, exp["format"])
            self.assertEqual(link.kind, exp["kind"])
            self.assertEqual(link.header, exp["header"])
            self.assertEqual(link.is_image, exp["is_image"])

        found_raws = {link.raw for link in links}
        self.assertEqual(found_raws, set(expected.keys()))

if __name__ == "__main__":
    unittest.main()
