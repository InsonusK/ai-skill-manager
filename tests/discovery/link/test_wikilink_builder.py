from pytest import param

from ai_skill_manager.discovery.link.builder.wikilink import WikilinkBuilder
from ai_skill_manager.entities.link_kind import LinkKind
import unittest
from . import MOCK_DIR
TESTCASE_MOCK_DIR = MOCK_DIR / "test_wikilink_builder"

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
    
    def test_find_repo_relative_link(self):
        builder = WikilinkBuilder()
        content = (TESTCASE_MOCK_DIR / "relative_link_tc.md").read_text()
        links = builder.search(content)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].raw, "[[skills/🧩validated/{solution}.skill.md|integration.solution.skill]]")
        self.assertEqual(links[0].path, "skills/🧩validated/{solution}.skill.md")
        self.assertEqual(links[0].text, "integration.solution.skill")
        
if __name__ == "__main__":
    unittest.main()