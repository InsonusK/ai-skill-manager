import unittest

from ai_skill_manager.discovery.link.builder.wikilink import WikilinkBuilder
from ai_skill_manager.entities.path_kind import PathKind
from ai_skill_manager.entities.link import PathLink


class TestWikilinkBuilder(unittest.TestCase):
    def test_finds_wiki_link(self):
        builder = WikilinkBuilder()
        links = builder.search("[[./file.md|text]]")
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], PathLink)
        self.assertEqual(links[0].path_raw.path, "./file.md")
        self.assertEqual(links[0].path_raw.kind, PathKind.relative)

    def test_finds_wiki_link_without_text(self):
        builder = WikilinkBuilder()
        links = builder.search("[[./file.md]]")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].path_raw.path, "./file.md")
        self.assertEqual(links[0].text, "file.md")

    def test_empty_content_returns_empty(self):
        builder = WikilinkBuilder()
        links = builder.search("")
        self.assertEqual(len(links), 0)

    def test_find_repo_relative_link(self):
        builder = WikilinkBuilder()
        content = (
            'created_by:\n'
            '  - "[[skills/🧩validated/{solution}.skill.md|integration.solution.skill]]"\n'
        )
        links = builder.search(content)
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], PathLink)
        self.assertEqual(links[0].raw, "[[skills/🧩validated/{solution}.skill.md|integration.solution.skill]]")
        self.assertEqual(links[0].path_raw.path, "skills/🧩validated/{solution}.skill.md")
        self.assertEqual(links[0].path_raw.kind, PathKind.repo_absolute)
        self.assertEqual(links[0].text, "integration.solution.skill")

    def test_finds_wiki_link_with_windows_separators(self):
        # EN: Wiki links authored on Windows with backslashes are classified
        # exactly like POSIX links.
        # RU: Wiki-ссылки, созданные на Windows с обратными слешами,
        # классифицируются точно так же, как POSIX-ссылки.
        builder = WikilinkBuilder()
        raw_wiki = r"[[.\sub\file.md|text]]"
        links = builder.search(raw_wiki)
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], PathLink)
        self.assertEqual(links[0].path_raw.path, r".\sub\file.md")
        self.assertEqual(links[0].path_raw.kind, PathKind.relative)


if __name__ == "__main__":
    unittest.main()
