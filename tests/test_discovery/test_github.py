"""Tests for GitHubSource acquisition and discovery."""

import io
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.entities import GitHubSource
from ai_skill_manager.entities.source.github import (
    _download_archive,
    _extract_archive,
    _find_extracted_root,
    _parse_github_url,
)
from ai_skill_manager.service.discover import discover


MOCK_DIR = Path(__file__).parent / "mock" / "test_github"


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


def _mock_download(archive_bytes: bytes, tmpdir: Path):
    """Return a patcher that replaces _download_archive with a writer of archive_bytes."""
    def fake_download(owner, repo, tree):
        path = tmpdir / "fake_archive.tar.gz"
        path.write_bytes(archive_bytes)
        return path

    return patch(
        "ai_skill_manager.entities.source.github._download_archive",
        side_effect=fake_download,
    )


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


class TestGitHubSource(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_get_scan_location_flat_files(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with _mock_download(archive, self.tmpdir):
            source = GitHubSource(
                repo_url="https://github.com/owner/repo",
                tree="main",
                subpath="skills",
            )
            loc = source.get_scan_location()

        self.assertTrue(loc.repo_path.name.startswith("repo-main"))
        self.assertEqual(loc.source_path, loc.repo_path / "skills")
        self.assertTrue(loc.source_path.is_dir())

    def test_get_scan_location_caches_result(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with _mock_download(archive, self.tmpdir) as mock:
            source = GitHubSource(
                repo_url="https://github.com/owner/repo",
                tree="main",
                subpath="skills",
            )
            loc1 = source.get_scan_location()
            loc2 = source.get_scan_location()
            mock.assert_called_once()

        self.assertEqual(loc1, loc2)

    def test_get_scan_location_repo_path_for_repo_absolute_links(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with _mock_download(archive, self.tmpdir):
            source = GitHubSource(
                repo_url="https://github.com/owner/repo",
                tree="main",
                subpath="skills",
            )
            loc = source.get_scan_location()

        self.assertEqual(loc.repo_path, loc.source_path.parent)

    def test_discover_service_finds_flat_files(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with _mock_download(archive, self.tmpdir):
            source = GitHubSource(
                repo_url="https://github.com/owner/repo",
                tree="main",
                subpath="skills",
            )
            result = discover([source])

        self.assertEqual(len(result), 2)
        names = {r.name for r in result}
        self.assertEqual(names, {"guide", "tips"})
        for skill in result:
            self.assertIsInstance(skill.source, GitHubSource)

    def test_discover_service_finds_directory_skills(self):
        archive = _make_archive_from_mock("discover_directory_skills", "repo-main")

        with _mock_download(archive, self.tmpdir):
            source = GitHubSource(
                repo_url="https://github.com/owner/repo",
                tree="main",
                subpath="skills",
            )
            result = discover([source])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "web")
        self.assertFalse(result[0].is_flat())

    def test_discover_service_missing_subpath_returns_empty(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with _mock_download(archive, self.tmpdir):
            source = GitHubSource(
                repo_url="https://github.com/owner/repo",
                tree="main",
                subpath="missing",
            )
            result = discover([source])

        self.assertEqual(len(result), 0)

    def test_discover_service_default_tree_master(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-master")

        with _mock_download(archive, self.tmpdir):
            source = GitHubSource(
                repo_url="https://github.com/owner/repo",
                subpath="skills",
            )
            result = discover([source])

        self.assertEqual(len(result), 2)

    def test_discover_service_ssh_url_accepted(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with _mock_download(archive, self.tmpdir):
            source = GitHubSource(
                repo_url="git@github.com:owner/repo.git",
                tree="main",
                subpath="skills",
            )
            result = discover([source])

        self.assertEqual(len(result), 2)

    def test_discover_service_single_skill_file(self):
        """A single *.skill.md file selected via subpath is treated as a flat skill."""
        archive = _make_archive_from_mock("discover_single_skill_file", "repo-main")

        with _mock_download(archive, self.tmpdir):
            source = GitHubSource(
                repo_url="https://github.com/owner/repo",
                tree="main",
                subpath="skills/nested/guide.skill.md",
            )
            result = discover([source])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "guide")
        self.assertTrue(result[0].is_flat())

    def test_discover_service_multiple_subpaths(self):
        """Multiple subpaths can be provided as separate GitHubSource instances."""
        archive = _make_archive_from_mock("multiple_subpaths", "repo-main")

        with _mock_download(archive, self.tmpdir):
            sources = [
                GitHubSource(
                    repo_url="https://github.com/owner/repo",
                    tree="main",
                    subpath="skills",
                ),
                GitHubSource(
                    repo_url="https://github.com/owner/repo",
                    tree="main",
                    subpath="docs",
                ),
            ]
            result = discover(sources)

        self.assertEqual(len(result), 2)
        names = {r.name for r in result}
        self.assertEqual(names, {"web", "guide"})

    def test_discover_service_mixed_subpaths(self):
        """Both directory and single-file subpaths can be discovered."""
        archive = _make_archive_from_mock("mixed_subpaths", "repo-main")

        with _mock_download(archive, self.tmpdir):
            sources = [
                GitHubSource(
                    repo_url="https://github.com/owner/repo",
                    tree="main",
                    subpath="skills",
                ),
                GitHubSource(
                    repo_url="https://github.com/owner/repo",
                    tree="main",
                    subpath="docs/quickstart.skill.md",
                ),
            ]
            result = discover(sources)

        self.assertEqual(len(result), 2)
        by_name = {r.name: r for r in result}
        self.assertIn("web", by_name)
        self.assertFalse(by_name["web"].is_flat())
        self.assertIn("quickstart", by_name)
        self.assertTrue(by_name["quickstart"].is_flat())

    def test_cleanup_removes_extracted_directory(self):
        archive = _make_archive_from_mock("discover_flat_files", "repo-main")

        with _mock_download(archive, self.tmpdir):
            source = GitHubSource(
                repo_url="https://github.com/owner/repo",
                tree="main",
                subpath="skills",
            )
            loc = source.get_scan_location()
            extracted = loc.repo_path.parent

        self.assertTrue(extracted.exists())
        source.cleanup()
        self.assertFalse(extracted.exists())

    def test_to_dict(self):
        source = GitHubSource(
            repo_url="https://github.com/owner/repo",
            tree="main",
            subpath="skills",
        )
        self.assertEqual(
            source.to_dict(),
            {
                "type": "github",
                "repo_url": "https://github.com/owner/repo",
                "tree": "main",
                "subpath": "skills",
            },
        )


class TestExtractArchive(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_extract_archive(self):
        src = self.tmpdir / "src"
        src.mkdir()
        (src / "file.txt").write_text("hello")

        archive = self.tmpdir / "archive.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(src, arcname="repo-main")

        extract_to = self.tmpdir / "extracted"
        extract_to.mkdir()
        _extract_archive(archive, extract_to)

        self.assertTrue((extract_to / "repo-main" / "file.txt").exists())
        self.assertEqual(
            (extract_to / "repo-main" / "file.txt").read_text(), "hello"
        )


class TestDownloadArchive(unittest.TestCase):
    def test_download_archive_writes_content(self):
        archive_bytes = _make_archive_from_mock("discover_flat_files", "repo-main")

        def fake_urlopen(url, timeout):
            class Response:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def read(self, size=-1):
                    nonlocal archive_bytes
                    data = archive_bytes
                    archive_bytes = b""
                    return data

            return Response()

        with patch("ai_skill_manager.entities.source.github.urllib.request.urlopen", side_effect=fake_urlopen):
            path = _download_archive("owner", "repo", "main")

        self.assertTrue(path.exists())
        self.assertEqual(path.read_bytes(), _make_archive_from_mock("discover_flat_files", "repo-main"))
        path.unlink()


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

    def test_no_directory_raises(self):
        with self.assertRaises(RuntimeError):
            _find_extracted_root(self.tmpdir)


if __name__ == "__main__":
    unittest.main()
