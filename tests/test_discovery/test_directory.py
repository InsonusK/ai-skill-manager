"""Tests for DirectoryDiscovery strategy."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.discovery.source.directory import DirectoryDiscovery


MOCK_DIR = Path(__file__).parent / "mock" / "test_directory"


class TestDirectoryDiscovery(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        return dst

    def test_single_skill_directory(self):
        skill = self._copy_mock("single_skill_directory") / "web"
        (skill / "web.skill.md").write_text("---\nname: web\n---\n# Web")

        strategy = DirectoryDiscovery(skill)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "web")
        self.assertFalse(result[0].is_flat())
        self.assertEqual(result[0].file_path, skill / "web.skill.md")

    def test_multiple_skill_directories(self):
        root = self._copy_mock("multiple_skill_directories") / "skills"
        for subdir in root.iterdir():
            if subdir.is_dir():
                skill_md = subdir / f"{subdir.name}.skill.md"
                skill_md.write_text(f"---\nname: {subdir.name}\n---\n# {subdir.name}")

        strategy = DirectoryDiscovery(root)
        result = strategy.discover()

        self.assertEqual(len(result), 2)
        names = {r.name for r in result}
        self.assertEqual(names, {"api", "web"})
        for skill in result:
            self.assertFalse(skill.is_flat())

    def test_ignores_directories_without_skill_md(self):
        root = self._copy_mock("ignores_directories_without_skill_md") / "skills"
        valid = root / "valid"
        (valid / "valid.skill.md").write_text("---\nname: valid\n---\n# Valid")

        strategy = DirectoryDiscovery(root)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "valid")

    def test_file_input_ignored(self):
        md = self._copy_mock("file_input_ignored") / "guide.md"

        strategy = DirectoryDiscovery(md)
        result = strategy.discover()

        self.assertEqual(len(result), 0)

    def test_empty_directory(self):
        empty = self._copy_mock("empty_directory") / "empty"

        strategy = DirectoryDiscovery(empty)
        result = strategy.discover()

        self.assertEqual(len(result), 0)

    def test_self_as_skill(self):
        """If root itself has {name}.skill.md, it's a single skill."""
        root = self._copy_mock("self_as_skill") / "my-skill"
        (root / "my-skill.skill.md").write_text("---\nname: my-skill\n---\n# My Skill")

        strategy = DirectoryDiscovery(root)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "my-skill")
        self.assertFalse(result[0].is_flat())

    def test_extra_skill_md_in_same_dir_raises(self):
        """A directory skill with another *.skill.md in the same dir raises."""
        root = self._copy_mock("extra_skill_md_in_same_dir_raises") / "my-skill"

        strategy = DirectoryDiscovery(root)
        with self.assertRaises(ValueError):
            strategy.discover()

    def test_extra_skill_md_in_subdir_raises(self):
        """A directory skill with another *.skill.md in a subdir raises."""
        root = self._copy_mock("extra_skill_md_in_subdir_raises") / "my-skill"

        strategy = DirectoryDiscovery(root)
        with self.assertRaises(ValueError):
            strategy.discover()


if __name__ == "__main__":
    unittest.main()
