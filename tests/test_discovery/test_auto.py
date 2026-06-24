"""Tests for AutoDiscovery strategy."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.discovery.skill.auto import AutoDiscovery
from ai_skill_manager.entities.skill_format import SkillFormat
from ai_skill_manager.entities.source import LocalSource


MOCK_DIR = Path(__file__).parent / "mock" / "test_auto"


class TestAutoDiscovery(unittest.TestCase):
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

    def _discover(self, path: Path) -> AutoDiscovery:
        resolved = path.resolve()
        source_path = resolved.parent if resolved.is_file() else resolved
        source = LocalSource(path=source_path)
        return AutoDiscovery(source_path=source_path, source=source)

    def test_empty_directory(self):
        empty = self._copy_mock("empty_directory") / "empty"

        strategy = self._discover(empty)
        result = strategy.discover()

        self.assertEqual(len(result), 0)

    def test_single_skill_file(self):
        md = self._copy_mock("single_skill_file") / "guide.skill.md"

        strategy = self._discover(md)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "guide")
        self.assertTrue(result[0].is_flat())
        self.assertEqual(result[0].format, SkillFormat.HumanFlat)
        self.assertEqual(result[0].file_path, md)

    def test_non_skill_file_ignored(self):
        txt = self._copy_mock("non_skill_file_ignored") / "readme.txt"

        strategy = self._discover(txt)
        result = strategy.discover()

        self.assertEqual(len(result), 0)

    def test_directory_skill(self):
        skill_dir = self._copy_mock("directory_skill") / "web.skill"

        strategy = self._discover(skill_dir)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "web")
        self.assertFalse(result[0].is_flat())
        self.assertEqual(result[0].format, SkillFormat.HumanDir)
        self.assertEqual(result[0].folder_path, skill_dir)

    def test_agent_skill(self):
        skill_dir = self._copy_mock("agent_skill") / "agent"

        strategy = self._discover(skill_dir)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "agent")
        self.assertFalse(result[0].is_flat())
        self.assertEqual(result[0].format, SkillFormat.Agent)
        self.assertEqual(result[0].file_path, skill_dir / "SKILL.md")

    def test_conflicting_skill_markers_raises(self):
        skill_dir = self._copy_mock("conflicting_skill_markers_raises") / "conflict"

        strategy = self._discover(skill_dir)
        with self.assertRaises(ValueError):
            strategy.discover()

    def test_flat_directory(self):
        flat = self._copy_mock("flat_directory") / "guides"

        strategy = self._discover(flat)
        result = strategy.discover()

        self.assertEqual(len(result), 2)
        names = {r.name for r in result}
        self.assertEqual(names, {"a", "b"})
        for skill in result:
            self.assertTrue(skill.is_flat())

    def test_nested_directory_skill(self):
        root = self._copy_mock("nested_directory_skill") / "skills"

        strategy = self._discover(root)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "backend")
        self.assertFalse(result[0].is_flat())

    def test_mixed_flat_and_directory(self):
        root = self._copy_mock("mixed")

        strategy = self._discover(root)
        result = strategy.discover()

        names = {r.name for r in result}
        self.assertEqual(names, {"guide", "web", "a"})

        by_name = {r.name: r for r in result}
        self.assertTrue(by_name["guide"].is_flat())
        self.assertFalse(by_name["web"].is_flat())
        self.assertTrue(by_name["a"].is_flat())

    def test_nested_flat_in_subdir(self):
        root = self._copy_mock("nested_flat_in_subdir") / "skills"

        strategy = self._discover(root)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "react")
        self.assertTrue(result[0].is_flat())

    def test_directory_skill_with_extra_skill_md_raises(self):
        skill_dir = self._copy_mock("directory_with_extra_skill_md_raises") / "web.skill"

        strategy = self._discover(skill_dir)
        with self.assertRaises(ValueError):
            strategy.discover()

    def test_human_dir_and_matching_flat_file_takes_directory(self):
        """If {dir}.skill.md is both a flat and directory pattern, prefer directory."""
        skill_dir = self._copy_mock("human_dir_and_matching_flat_file_takes_directory") / "web.skill"

        strategy = self._discover(skill_dir)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "web")
        self.assertFalse(result[0].is_flat())
        self.assertEqual(result[0].format, SkillFormat.HumanDir)

    def test_agent_with_extra_flat_file_raises_conflict(self):
        """Agent SKILL.md + unrelated *.skill.md is ambiguous."""
        skill_dir = self._copy_mock("agent_with_extra_flat_file_raises_conflict") / "agent"

        strategy = self._discover(skill_dir)
        with self.assertRaises(ValueError):
            strategy.discover()

    def test_agent_with_nested_skill_raises(self):
        skill_dir = self._copy_mock("agent_with_nested_skill_raises") / "agent"

        strategy = self._discover(skill_dir)
        with self.assertRaises(ValueError):
            strategy.discover()

    def test_multiple_directory_patterns_raises(self):
        """Both SKILL.md and {dir}.skill.md in the same directory conflict."""
        skill_dir = self._copy_mock("multiple_directory_patterns_raises") / "ambiguous"

        strategy = self._discover(skill_dir)
        with self.assertRaises(ValueError):
            strategy.discover()

    def test_missing_source_path_returns_empty(self):
        """A missing source path produces an empty result."""
        missing = self.tmpdir / "missing"
        source = LocalSource(path=missing.resolve())
        strategy = AutoDiscovery(source_path=missing.resolve(), source=source)

        result = strategy.discover()

        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
