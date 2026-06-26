from ai_skill_manager.entities import GitHubSource, LocalSource, Source


import shutil
import tempfile
import unittest
from pathlib import Path


class TestSource(unittest.TestCase):
    def test_local_source_is_abstract_source(self):
        path = Path("/tmp/skills")
        source = LocalSource(scan_path=path)
        self.assertIsInstance(source, Source)
        self.assertEqual(source.source_type, "local")
        self.assertEqual(source.to_dict(), {"type": "local", "path": str(path)})

    def test_local_source_scan_location_for_directory(self):
        source = LocalSource(scan_path=Path("/tmp/skills"))
        loc = source.get_scan_location()
        self.assertEqual(loc.source_path, Path("/tmp/skills"))
        self.assertEqual(loc.repo_path, Path("/tmp/skills"))

    def test_local_source_scan_location_for_file(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            skill_file = tmpdir / "guide.skill.md"
            skill_file.write_text("# Guide")
            source = LocalSource(scan_path=skill_file)
            loc = source.get_scan_location()
            self.assertEqual(loc.source_path, tmpdir)
            self.assertEqual(loc.repo_path, tmpdir)
        finally:
            shutil.rmtree(tmpdir)

    def test_local_source_scan_location_with_custom_repo_path(self):
        source = LocalSource(
            scan_path=Path("/tmp/skills"),
            repo_path=Path("/repo/root"),
        )
        loc = source.get_scan_location()
        self.assertEqual(loc.source_path, Path("/tmp/skills"))
        self.assertEqual(loc.repo_path, Path("/repo/root"))

    def test_local_source_to_dict_includes_repo_path(self):
        source = LocalSource(
            scan_path=Path("/tmp/skills"),
            repo_path=Path("/repo/root"),
        )
        self.assertEqual(
            source.to_dict(),
            {
                "type": "local",
                "path": "/tmp/skills",
                "repo_path": "/repo/root",
            },
        )

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
                "subpath": "skills",
            },
        )

    def test_github_source_default_tree(self):
        source = GitHubSource(repo_url="https://github.com/owner/repo")
        self.assertEqual(source.tree, "master")
        self.assertIsNone(source.subpath)

    def test_github_source_str(self):
        source = GitHubSource(
            repo_url="https://github.com/owner/repo",
            tree="main",
            subpath="skills",
        )
        self.assertEqual(str(source), "https://github.com/owner/repo main skills")


if __name__ == "__main__":
    unittest.main()
