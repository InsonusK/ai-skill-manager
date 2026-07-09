from ai_skill_manager.entities import GitHubSource, LocalSource, Source


import shutil
import tempfile
import unittest
from pathlib import Path


class TestSource(unittest.TestCase):
    def test_local_source_is_abstract_source(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            path = tmpdir / "skills"
            path.mkdir()
            source = LocalSource(scan_path=path)
            self.assertIsInstance(source, Source)
            self.assertEqual(source.source_type, "local")
            self.assertEqual(source.to_dict(), {"type": "local", "path": path.as_posix()})
        finally:
            shutil.rmtree(tmpdir)

    def test_local_source_scan_location_for_directory(self):
        path = Path("/tmp/skills")
        source = LocalSource(scan_path=path)
        loc = source.get_scan_location()
        self.assertEqual(loc.source_path, path.resolve())
        self.assertEqual(loc.repo_path, path.resolve())

    def test_local_source_scan_location_for_file(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            skill_file = tmpdir / "guide.skill.md"
            skill_file.write_text("# Guide")
            source = LocalSource(scan_path=skill_file)
            loc = source.get_scan_location()
            self.assertEqual(loc.source_path, skill_file.resolve())
            self.assertEqual(loc.repo_path, tmpdir.resolve())
        finally:
            shutil.rmtree(tmpdir)

    def test_local_source_scan_location_with_custom_repo_path(self):
        scan_path = Path("/tmp/skills")
        repo_path = Path("/repo/root")
        source = LocalSource(scan_path=scan_path, repo_path=repo_path)
        loc = source.get_scan_location()
        self.assertEqual(loc.source_path, scan_path.resolve())
        self.assertEqual(loc.repo_path, repo_path.resolve())

    def test_local_source_to_dict_includes_repo_path(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            scan_path = tmpdir / "skills"
            scan_path.mkdir()
            repo_path = tmpdir / "root"
            repo_path.mkdir()
            source = LocalSource(scan_path=scan_path, repo_path=repo_path)
            self.assertEqual(
                source.to_dict(),
                {
                    "type": "local",
                    "path": scan_path.as_posix(),
                    "repo_path": repo_path.as_posix(),
                },
            )
        finally:
            shutil.rmtree(tmpdir)

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

    def test_local_source_to_dict_includes_tags(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            scan_path = tmpdir / "skills"
            scan_path.mkdir()
            source = LocalSource(scan_path=scan_path, tags=("python", "!web"))
            self.assertEqual(
                source.to_dict(),
                {
                    "type": "local",
                    "path": scan_path.as_posix(),
                    "tags": ["python", "!web"],
                },
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_github_source_to_dict_includes_tags(self):
        source = GitHubSource(
            repo_url="https://github.com/owner/repo",
            tree="main",
            subpath="skills",
            tags=("python | cli",),
        )
        self.assertEqual(
            source.to_dict(),
            {
                "type": "github",
                "repo_url": "https://github.com/owner/repo",
                "tree": "main",
                "subpath": "skills",
                "tags": ["python | cli"],
            },
        )


if __name__ == "__main__":
    unittest.main()
