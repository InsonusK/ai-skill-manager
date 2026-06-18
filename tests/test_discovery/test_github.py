"""Tests for GitHubDiscovery strategy."""

import io
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.discovery.github import (
    GitHubDiscovery,
    _parse_github_url,
    _find_extracted_root,
)
from ai_skill_manager.core import copy_skill


MOCK_DIR = Path(__file__).parent / 'mock' / 'test_github'


def _make_archive_from_mock(mock_name: str, repo_name: str) -> bytes:
    """Build a tar.gz archive from a mock directory."""
    src = MOCK_DIR / mock_name
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path in src.rglob("*"):
            if path.is_file():
                arcname = f"{repo_name}/{path.relative_to(src)}"
                data = path.read_bytes()
                info = tarfile.TarInfo(name=arcname)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class TestParseGitHubUrl(unittest.TestCase):
    def test_https_with_git_suffix(self):
        self.assertEqual(
            _parse_github_url("https://github.com/owner/repo.git"),
            ("owner", "repo"),
        )

    def test_https_without_git_suffix(self):
        self.assertEqual(
            _parse_github_url("https://github.com/owner/repo"),
            ("owner", "repo"),
        )

    def test_https_with_trailing_slash(self):
        self.assertEqual(
            _parse_github_url("https://github.com/owner/repo/"),
            ("owner", "repo"),
        )

    def test_ssh_format(self):
        self.assertEqual(
            _parse_github_url("git@github.com:owner/repo.git"),
            ("owner", "repo"),
        )

    def test_invalid_url_raises(self):
        with self.assertRaises(ValueError):
            _parse_github_url("https://example.com/not-github")


class TestGitHubDiscovery(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.target = self.tmpdir / "target"
        self.target.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _mock_download(self, archive_bytes: bytes):
        """Return a patcher that replaces _download_archive with a writer of archive_bytes."""
        def fake_download(owner, repo, tree):
            path = self.tmpdir / "fake_archive.tar.gz"
            path.write_bytes(archive_bytes)
            return path

        return patch(
            "ai_skill_manager.discovery.github._download_archive",
            side_effect=fake_download,
        )

    def test_discover_flat_files(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
                subpath="skills",
            )
            result = strategy.discover()

        self.assertEqual(len(result), 2)
        names = {r.skill_name for r in result}
        self.assertEqual(names, {"guide", "tips"})

    def test_discover_directory_skills(self):
        archive = _make_archive_from_mock("discover_directory_skills", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
                subpath="skills",
            )
            result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].skill_name, "web")
        self.assertFalse(result[0].is_flat)

    def test_missing_subpath_returns_empty(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
                subpath="missing",
            )
            result = strategy.discover()

        self.assertEqual(len(result), 0)

    def test_default_tree_master(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-master")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                subpath="skills",
            )
            result = strategy.discover()

        self.assertEqual(len(result), 2)

    def test_default_subpath_skills(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
            )
            result = strategy.discover()

        self.assertEqual(len(result), 2)

    def test_ssh_url_accepted(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "git@github.com:owner/repo.git",
                self.target,
                tree="main",
                subpath="skills",
            )
            result = strategy.discover()

        self.assertEqual(len(result), 2)

    def test_discover_source_paths_remain_valid_after_return(self):
        archive = _make_archive_from_mock("discover_directory_skills", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
                subpath="skills",
            )
            result = strategy.discover()

        self.assertEqual(len(result), 1)
        mapping = result[0]
        self.assertEqual(mapping.skill_name, "web")
        self.assertFalse(mapping.is_flat)

        # The source_path must still exist after discover() returned
        self.assertTrue(mapping.source_path.exists())
        self.assertTrue((mapping.source_path / "web.skill.md").exists())
        self.assertEqual(
            (mapping.source_path / "web.skill.md").read_text(),
            "# Web\n",
        )

    def test_discover_and_copy_directory_skill(self):
        """End-to-end: discover from GitHub archive and copy skill to target."""
        archive = _make_archive_from_mock("discover_directory_skills", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
                subpath="skills",
            )
            result = strategy.discover()

        self.assertEqual(len(result), 1)
        mapping = result[0]

        copy_skill(mapping, dry_run=False)

        # Verify the skill was copied into the target directory
        skill_dir = self.target / "web"
        self.assertTrue(skill_dir.exists())
        self.assertTrue((skill_dir / "SKILL.md").exists())
        self.assertEqual((skill_dir / "SKILL.md").read_text(), "# Web\n")
        self.assertTrue((skill_dir / "extra.md").exists())
        self.assertEqual((skill_dir / "extra.md").read_text(), "# Extra\n")

    def test_discover_single_skill_file(self):
        """A single *.skill.md file selected via subpath is treated as a flat skill."""
        archive = _make_archive_from_mock("discover_single_skill_file", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
                subpath="skills/nested/guide.skill.md",
            )
            result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].skill_name, "guide")
        self.assertTrue(result[0].is_flat)
        self.assertTrue(result[0].source_path.exists())

    def test_discover_single_skill_file_copies_correctly(self):
        """End-to-end: discover a single *.skill.md file and copy it as a flat skill."""
        archive = _make_archive_from_mock("discover_single_skill_file", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
                subpath="skills/nested/guide.skill.md",
            )
            result = strategy.discover()

        self.assertEqual(len(result), 1)
        mapping = result[0]
        self.assertEqual(mapping.skill_name, "guide")
        self.assertTrue(mapping.is_flat)

        copy_skill(mapping, dry_run=False)

        skill_dir = self.target / "guide"
        self.assertTrue(skill_dir.exists())
        self.assertTrue((skill_dir / "SKILL.md").exists())
        self.assertEqual((skill_dir / "SKILL.md").read_text(), "# Guide\n")

    def test_discover_multiple_subpaths(self):
        """Multiple subpaths can be provided as a list."""
        archive = _make_archive_from_mock("multiple_subpaths", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
                subpath=["skills", "docs"],
            )
            result = strategy.discover()

        self.assertEqual(len(result), 2)
        names = {r.skill_name for r in result}
        self.assertEqual(names, {"web", "guide"})

    def test_discover_multiple_subpaths_mixed(self):
        """A list of subpaths can contain both directories and single *.skill.md files."""
        archive = _make_archive_from_mock("mixed_subpaths", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
                subpath=["skills", "docs/quickstart.skill.md"],
            )
            result = strategy.discover()

        self.assertEqual(len(result), 2)
        by_name = {r.skill_name: r for r in result}
        self.assertIn("web", by_name)
        self.assertFalse(by_name["web"].is_flat)
        self.assertIn("quickstart", by_name)
        self.assertTrue(by_name["quickstart"].is_flat)

    def test_discover_multiple_subpaths_skips_missing(self):
        """Missing subpaths in a list are skipped rather than failing."""
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with self._mock_download(archive):
            strategy = GitHubDiscovery(
                "https://github.com/owner/repo",
                self.target,
                tree="main",
                subpath=["missing", "skills"],
            )
            result = strategy.discover()

        self.assertEqual(len(result), 2)


class TestFindExtractedRoot(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_single_directory(self):
        (self.tmpdir / "repo-main").mkdir()
        root = _find_extracted_root(self.tmpdir)
        self.assertEqual(root.name, "repo-main")

    def test_multiple_directories_raises(self):
        (self.tmpdir / "a").mkdir()
        (self.tmpdir / "b").mkdir()
        with self.assertRaises(RuntimeError):
            _find_extracted_root(self.tmpdir)


if __name__ == "__main__":
    unittest.main()
