"""Tests for ExternalFileCopier."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.functions.external_file_copier import ExternalFileCopier


class TestExternalFileCopier(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo_path = self.tmp
        self.target_dir = self.tmp / "target"
        self.target_dir.mkdir()
        self.copier = ExternalFileCopier()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_copies_file_into_shared_files_dir(self):
        (self.repo_path / "shared.md").write_text("# Shared\n")

        result = self.copier.copy(Path("shared.md"), repo_path=self.repo_path, target_dir=self.target_dir)

        self.assertEqual(result, Path("files/shared.md"))
        self.assertTrue((self.target_dir / "files" / "shared.md").exists())

    def test_reuses_already_copied_file(self):
        (self.repo_path / "shared.md").write_text("# Shared\n")

        first = self.copier.copy(Path("shared.md"), repo_path=self.repo_path, target_dir=self.target_dir)
        second = self.copier.copy(Path("shared.md"), repo_path=self.repo_path, target_dir=self.target_dir)

        self.assertEqual(first, second)
        self.assertEqual(len(list((self.target_dir / "files").iterdir())), 1)

    def test_copies_directory(self):
        assets = self.repo_path / "assets"
        assets.mkdir()
        (assets / "image.png").write_text("png")

        result = self.copier.copy(Path("assets"), repo_path=self.repo_path, target_dir=self.target_dir)

        self.assertEqual(result, Path("files/assets"))
        self.assertTrue((self.target_dir / "files" / "assets" / "image.png").exists())

    def test_renames_on_name_collision(self):
        (self.repo_path / "a").mkdir()
        (self.repo_path / "a" / "extra.md").write_text("A")
        (self.repo_path / "b").mkdir()
        (self.repo_path / "b" / "extra.md").write_text("B")

        first = self.copier.copy(Path("a/extra.md"), repo_path=self.repo_path, target_dir=self.target_dir)
        second = self.copier.copy(Path("b/extra.md"), repo_path=self.repo_path, target_dir=self.target_dir)

        self.assertNotEqual(first, second)
        self.assertEqual((self.target_dir / first).read_text(), "A")
        self.assertEqual((self.target_dir / second).read_text(), "B")


if __name__ == "__main__":
    unittest.main()
