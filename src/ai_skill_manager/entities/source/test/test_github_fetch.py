import os
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ai_skill_manager.entities.source.github import (
    _remove_readonly_and_retry,
    fetch_repo_tree,
)
from ai_skill_manager.entities.source.git_clone import GitCloneError
from ai_skill_manager.entities import GitHubSource


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-q", "-m", message)


def _make_repo(root: Path, branch: str = "master") -> Path:
    repo = root / "origin"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", branch, str(repo)], check=True)
    (repo / "marker.txt").write_text("cloned-content")
    _commit(repo, "init")
    return repo


def _make_archive(root: Path, dirname: str, filename: str, content: str) -> Path:
    src = root / "archive-src" / dirname
    src.mkdir(parents=True)
    (src / filename).write_text(content)
    archive_path = root / "archive.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(src, arcname=dirname)
    return archive_path


class TestFetchRepoTree(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.work_dir = self.tmpdir / "work"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_uses_git_clone_when_available(self):
        repo = _make_repo(self.tmpdir)

        repo_root = fetch_repo_tree(str(repo), "master", self.work_dir)

        self.assertEqual((repo_root / "marker.txt").read_text(), "cloned-content")

    def test_falls_back_to_archive_when_git_missing(self):
        archive = _make_archive(self.tmpdir, "repo-main", "marker.txt", "archive-content")

        with mock.patch(
            "ai_skill_manager.entities.source.github.clone_git_repo",
            side_effect=GitCloneError("git executable not found in PATH"),
        ), mock.patch(
            "ai_skill_manager.entities.source.github._download_archive",
            return_value=archive,
        ) as download_mock:
            repo_root = fetch_repo_tree("https://github.com/owner/repo", "main", self.work_dir)

        download_mock.assert_called_once_with("owner", "repo", "main")
        self.assertEqual((repo_root / "marker.txt").read_text(), "archive-content")

    def test_falls_back_to_archive_when_clone_fails(self):
        archive = _make_archive(self.tmpdir, "repo-main", "marker.txt", "archive-content")

        with mock.patch(
            "ai_skill_manager.entities.source.github.clone_git_repo",
            side_effect=GitCloneError("git clone failed for ...: denied"),
        ), mock.patch(
            "ai_skill_manager.entities.source.github._download_archive",
            return_value=archive,
        ):
            repo_root = fetch_repo_tree("https://github.com/owner/repo", "main", self.work_dir)

        self.assertEqual((repo_root / "marker.txt").read_text(), "archive-content")

    def test_removes_partial_clone_directory_before_archive_fallback(self):
        archive = _make_archive(self.tmpdir, "repo-main", "marker.txt", "archive-content")

        def failing_clone(repo_url, tree, dest_dir):
            dest_dir.mkdir(parents=True)
            (dest_dir / "partial.txt").write_text("leftover")
            raise GitCloneError("git clone failed")

        with mock.patch(
            "ai_skill_manager.entities.source.github.clone_git_repo",
            side_effect=failing_clone,
        ), mock.patch(
            "ai_skill_manager.entities.source.github._download_archive",
            return_value=archive,
        ):
            repo_root = fetch_repo_tree("https://github.com/owner/repo", "main", self.work_dir)

        self.assertEqual((repo_root / "marker.txt").read_text(), "archive-content")
        self.assertFalse((self.work_dir / "repo").exists())

    def test_reraises_clone_error_when_url_is_not_github(self):
        with mock.patch(
            "ai_skill_manager.entities.source.github.clone_git_repo",
            side_effect=GitCloneError("git clone failed for ssh://git.example.com/team/repo: denied"),
        ), mock.patch(
            "ai_skill_manager.entities.source.github._download_archive"
        ) as download_mock:
            with self.assertRaises(GitCloneError) as ctx:
                fetch_repo_tree("ssh://git.example.com/team/repo", "main", self.work_dir)

        download_mock.assert_not_called()
        self.assertIn("denied", str(ctx.exception))

    def test_archive_error_propagates_when_both_strategies_fail(self):
        with mock.patch(
            "ai_skill_manager.entities.source.github.clone_git_repo",
            side_effect=GitCloneError("git clone failed"),
        ), mock.patch(
            "ai_skill_manager.entities.source.github._download_archive",
            side_effect=RuntimeError("archive download failed"),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                fetch_repo_tree("https://github.com/owner/repo", "main", self.work_dir)

        self.assertIn("archive download failed", str(ctx.exception))


class TestRemoveReadonlyAndRetry(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_makes_entry_writable_before_retrying(self):
        read_only_file = self.tmpdir / "ro.txt"
        read_only_file.write_text("data")
        read_only_file.chmod(stat.S_IREAD)
        observed_modes = []

        def func(path):
            observed_modes.append(os.stat(path).st_mode)
            os.unlink(path)

        _remove_readonly_and_retry(func, str(read_only_file), None)

        self.assertFalse(read_only_file.exists())
        self.assertTrue(observed_modes[0] & stat.S_IWRITE)


class TestGitHubSourceWithGitClone(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cleanup_of_one_source_leaves_other_sources_repository(self):
        repo_a = _make_repo(self.tmpdir / "a")
        repo_b = _make_repo(self.tmpdir / "b")
        source_a = GitHubSource(repo_url=str(repo_a), tree="master", subpaths=(None,))
        source_b = GitHubSource(repo_url=str(repo_b), tree="master", subpaths=(None,))
        try:
            locations_a = source_a.get_scan_locations()
            locations_b = source_b.get_scan_locations()
            path_a = locations_a[0].repo_path
            path_b = locations_b[0].repo_path

            source_a.cleanup()

            self.assertFalse(path_a.exists())
            self.assertTrue(path_b.exists())
        finally:
            source_a.cleanup()
            source_b.cleanup()

        self.assertFalse(path_b.exists())

    def test_cleanup_removes_read_only_files_left_by_git(self):
        # Git marks files under .git/objects read-only on Windows, which
        # used to make shutil.rmtree fail with PermissionError.
        # Git помечает файлы в .git/objects атрибутом «только чтение» на
        # Windows, из-за чего shutil.rmtree падал с PermissionError.
        source = GitHubSource(repo_url="https://github.com/owner/repo")
        leftover = self.tmpdir / "leftover"
        (leftover / "objects").mkdir(parents=True)
        read_only_file = leftover / "objects" / "pack"
        read_only_file.write_text("data")
        read_only_file.chmod(0o444)
        source._GitHubSource__context.extracted_dirs.append(leftover)

        source.cleanup()

        self.assertFalse(leftover.exists())

    def test_scan_locations_point_into_cloned_repository(self):
        repo = _make_repo(self.tmpdir)
        source = GitHubSource(repo_url=str(repo), tree="master", subpaths=(None,))
        try:
            locations = source.get_scan_locations()

            self.assertEqual(len(locations), 1)
            self.assertTrue(locations[0].scan_path.exists())
            self.assertEqual((locations[0].scan_path / "marker.txt").read_text(), "cloned-content")
            self.assertEqual(locations[0].repo_path, locations[0].scan_path)
        finally:
            source.cleanup()


if __name__ == "__main__":
    unittest.main()
