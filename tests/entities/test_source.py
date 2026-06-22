from ai_skill_manager.entities import GitHubSource, LocalSource, Source


import unittest
from pathlib import Path


class TestSource(unittest.TestCase):
    def test_local_source_is_abstract_source(self):
        path = Path("/tmp/skills")
        source = LocalSource(path=path)
        self.assertIsInstance(source, Source)
        self.assertEqual(source.source_type, "local")
        self.assertEqual(source.to_dict(), {"type": "local", "path": str(path)})

    def test_github_source_is_abstract_source(self):
        source = GitHubSource(
            repo_url="https://github.com/owner/repo",
            tree="main",
            subpath="skills",
        )
        self.assertIsInstance(source, Source)
        self.assertEqual(source.source_type, "github")
        self.assertEqual(
            source.to_dict(),
            {
                "type": "github",
                "repo_url": "https://github.com/owner/repo",
                "tree": "main",
                "subpath": ["skills"],
            },
        )

    def test_github_source_default_tree(self):
        source = GitHubSource(repo_url="https://github.com/owner/repo")
        self.assertEqual(source.tree, "master")
        self.assertIsNone(source.subpath)
    
if __name__ == "__main__":
    unittest.main()