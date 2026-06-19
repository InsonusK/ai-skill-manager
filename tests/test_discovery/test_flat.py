"""Tests for FlatDiscovery strategy."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.discovery.source.flat import FlatDiscovery


MOCK_DIR = Path(__file__).parent / "mock" / "test_flat"


class TestFlatDiscovery(unittest.TestCase):
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

    def test_single_skill_file(self):
        md = self._copy_mock("single_skill_file") / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide")

        strategy = FlatDiscovery(md)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "guide")
        self.assertTrue(result[0].is_flat())
        self.assertEqual(result[0].file_path, md)

    def test_non_skill_file_ignored(self):
        txt = self._copy_mock("non_md_file_ignored") / "readme.txt"

        strategy = FlatDiscovery(txt)
        result = strategy.discover()

        self.assertEqual(len(result), 0)

    def test_flat_directory(self):
        flat = self._copy_mock("flat_directory")
        for f in flat.glob("*.skill.md"):
            name = f.name[:-9]
            f.write_text(f"---\nname: {name}\n---\n# {name}")

        strategy = FlatDiscovery(flat)
        result = strategy.discover()

        self.assertEqual(len(result), 2)
        names = {r.name for r in result}
        self.assertEqual(names, {"a", "b"})
        for skill in result:
            self.assertTrue(skill.is_flat())

    def test_ignores_regular_md(self):
        """Flat mode should ignore plain .md files without .skill.md suffix."""
        flat = self._copy_mock("flat_directory")

        strategy = FlatDiscovery(flat)
        result = strategy.discover()

        names = {r.name for r in result}
        self.assertNotIn("ignored", names)

    def test_empty_directory(self):
        empty = self._copy_mock("empty_directory") / "empty"

        strategy = FlatDiscovery(empty)
        result = strategy.discover()

        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
