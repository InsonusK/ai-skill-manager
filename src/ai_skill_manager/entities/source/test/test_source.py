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
            source = LocalSource(scan_paths=(path,))
            self.assertIsInstance(source, Source)
            self.assertEqual(source.source_type, "local")
            self.assertEqual(
                source.to_dict(),
                {"type": "local", "path": path.as_posix(), "skip_folder": ["examples"]},
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_local_source_scan_location_for_directory(self):
        path = Path("/tmp/skills")
        source = LocalSource(scan_paths=(path,))
        locations = source.get_scan_locations()
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0].scan_path, path.resolve())
        self.assertEqual(locations[0].repo_path, path.resolve())

    def test_local_source_scan_location_for_file(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            skill_file = tmpdir / "guide.skill.md"
            skill_file.write_text("# Guide")
            source = LocalSource(scan_paths=(skill_file,))
            locations = source.get_scan_locations()
            self.assertEqual(locations[0].scan_path, skill_file.resolve())
            self.assertEqual(locations[0].repo_path, tmpdir.resolve())
        finally:
            shutil.rmtree(tmpdir)

    def test_local_source_scan_location_with_custom_repo_path(self):
        scan_path = Path("/tmp/skills")
        repo_path = Path("/repo/root")
        source = LocalSource(scan_paths=(scan_path,), repo_path=repo_path)
        locations = source.get_scan_locations()
        self.assertEqual(locations[0].scan_path, scan_path.resolve())
        self.assertEqual(locations[0].repo_path, repo_path.resolve())

    def test_local_source_multiple_scan_paths(self):
        scan_a = Path("/tmp/skills")
        scan_b = Path("/tmp/docs")
        repo_path = Path("/repo/root")
        source = LocalSource(scan_paths=(scan_a, scan_b), repo_path=repo_path)
        locations = source.get_scan_locations()

        self.assertEqual(len(locations), 2)
        self.assertEqual(locations[0].scan_path, scan_a.resolve())
        self.assertEqual(locations[1].scan_path, scan_b.resolve())
        self.assertEqual(locations[0].repo_path, repo_path.resolve())
        self.assertEqual(locations[1].repo_path, repo_path.resolve())

    def test_local_source_to_dict_includes_repo_path(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            scan_path = tmpdir / "skills"
            scan_path.mkdir()
            repo_path = tmpdir / "root"
            repo_path.mkdir()
            source = LocalSource(scan_paths=(scan_path,), repo_path=repo_path)
            self.assertEqual(
                source.to_dict(),
                {
                    "type": "local",
                    "path": scan_path.as_posix(),
                    "repo_path": repo_path.as_posix(),
                    "skip_folder": ["examples"],
                },
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_local_source_to_dict_with_multiple_paths(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            scan_a = tmpdir / "skills"
            scan_a.mkdir()
            scan_b = tmpdir / "docs"
            scan_b.mkdir()
            source = LocalSource(scan_paths=(scan_a, scan_b))
            self.assertEqual(
                source.to_dict()["path"],
                [scan_a.as_posix(), scan_b.as_posix()],
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_github_source_is_abstract_source(self):
        source = GitHubSource(
            repo_url="https://github.com/owner/repo",
            tree="main",
            subpaths=("skills",),
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
                "skip_folder": ["examples"],
            },
        )

    def test_github_source_default_tree(self):
        source = GitHubSource(repo_url="https://github.com/owner/repo")
        self.assertEqual(source.tree, "master")
        self.assertEqual(source.subpaths, (None,))

    def test_github_source_str(self):
        source = GitHubSource(
            repo_url="https://github.com/owner/repo",
            tree="main",
            subpaths=("skills",),
        )
        self.assertEqual(str(source), "https://github.com/owner/repo main skills")

    def test_github_source_to_dict_with_multiple_subpaths(self):
        source = GitHubSource(
            repo_url="https://github.com/owner/repo",
            tree="main",
            subpaths=("skills", "docs"),
        )
        self.assertEqual(source.to_dict()["subpath"], ["skills", "docs"])

    def test_local_source_to_dict_includes_tags(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            scan_path = tmpdir / "skills"
            scan_path.mkdir()
            source = LocalSource(scan_paths=(scan_path,), tags=("python", "!web"))
            self.assertEqual(
                source.to_dict(),
                {
                    "type": "local",
                    "path": scan_path.as_posix(),
                    "tags": ["python", "!web"],
                    "skip_folder": ["examples"],
                },
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_github_source_to_dict_includes_tags(self):
        source = GitHubSource(
            repo_url="https://github.com/owner/repo",
            tree="main",
            subpaths=("skills",),
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
                "skip_folder": ["examples"],
            },
        )

    def test_local_source_to_dict_includes_skip_folder(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            scan_path = tmpdir / "skills"
            scan_path.mkdir()
            source = LocalSource(scan_paths=(scan_path,), skip_folder=("abc", "xyz"))
            self.assertEqual(
                source.to_dict(),
                {
                    "type": "local",
                    "path": scan_path.as_posix(),
                    "skip_folder": ["abc", "xyz"],
                },
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_github_source_to_dict_includes_skip_folder(self):
        source = GitHubSource(
            repo_url="https://github.com/owner/repo",
            tree="main",
            subpaths=("skills",),
            skip_folder=("abc",),
        )
        self.assertEqual(
            source.to_dict(),
            {
                "type": "github",
                "repo_url": "https://github.com/owner/repo",
                "tree": "main",
                "subpath": "skills",
                "skip_folder": ["abc"],
            },
        )


if __name__ == "__main__":
    unittest.main()
