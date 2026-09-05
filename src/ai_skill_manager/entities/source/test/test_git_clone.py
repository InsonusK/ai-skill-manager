import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ai_skill_manager.entities.source.git_clone import GitCloneError, clone_git_repo


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _make_repo(root: Path, branch: str = "master") -> Path:
    repo = root / "origin"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", branch, str(repo)], check=True)
    _git(repo, "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-q", "--allow-empty", "-m", "init")
    return repo


class TestCloneGitRepo(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_clone_copies_repository_files(self):
        repo = _make_repo(self.tmpdir)
        (repo / "SKILL.md").write_text("# Skill")
        _git(repo, "add", ".")
        _git(repo, "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-q", "-m", "add skill")

        dest = self.tmpdir / "dest"
        result = clone_git_repo(str(repo), "master", dest)

        self.assertEqual(result, dest)
        self.assertEqual((dest / "SKILL.md").read_text(), "# Skill")

    def test_clone_checks_out_requested_tree(self):
        repo = _make_repo(self.tmpdir)
        (repo / "master.txt").write_text("master")
        _git(repo, "add", ".")
        _git(repo, "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-q", "-m", "master file")
        _git(repo, "checkout", "-q", "-b", "feature")
        (repo / "feature.txt").write_text("feature")
        _git(repo, "add", ".")
        _git(repo, "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-q", "-m", "feature file")

        dest = self.tmpdir / "dest"
        clone_git_repo(str(repo), "feature", dest)

        self.assertTrue((dest / "feature.txt").exists())
        self.assertEqual((dest / "feature.txt").read_text(), "feature")

    def test_clone_raises_when_git_executable_missing(self):
        with mock.patch(
            "ai_skill_manager.entities.source.git_clone.shutil.which", return_value=None
        ):
            with self.assertRaises(GitCloneError) as ctx:
                clone_git_repo("https://example.com/owner/repo.git", "master", self.tmpdir / "dest")

        self.assertIn("git", str(ctx.exception).lower())

    def test_clone_raises_with_stderr_when_clone_fails(self):
        repo = _make_repo(self.tmpdir)

        with self.assertRaises(GitCloneError) as ctx:
            clone_git_repo(str(repo / "does-not-exist"), "master", self.tmpdir / "dest")

        self.assertIn("does-not-exist", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
