"""Tests for AutoDiscovery strategy."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.service.skill_discovery.skill.auto import AutoDiscovery
from ai_skill_manager.entities.skill_kind import SkillKind
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
        source = LocalSource(scan_paths=(source_path,))
        return AutoDiscovery(scan_path=source_path, source=source)

    def test_empty_directory(self):
        empty = self._copy_mock("empty_directory") / "empty"

        strategy = self._discover(empty)
        result, errors = strategy.discover()

        self.assertEqual(len(result), 0)
        self.assertEqual(errors, [])

    def test_single_skill_file(self):
        md = self._copy_mock("single_skill_file") / "guide.skill.md"

        strategy = self._discover(md)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "guide")
        self.assertEqual(result[0].kind, SkillKind.flat)
        self.assertEqual(result[0].path, md.resolve())

    def test_non_skill_file_ignored(self):
        txt = self._copy_mock("non_skill_file_ignored") / "readme.txt"

        strategy = self._discover(txt)
        result, errors = strategy.discover()

        self.assertEqual(len(result), 0)
        self.assertEqual(errors, [])

    def test_directory_skill(self):
        skill_dir = self._copy_mock("directory_skill") / "web.skill"

        strategy = self._discover(skill_dir)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "web")
        self.assertEqual(result[0].kind, SkillKind.dir)
        self.assertEqual(result[0].path, skill_dir.resolve())
        self.assertEqual(result[0].main_file_relative_path, Path("web.skill.md"))

    def test_agent_skill(self):
        skill_dir = self._copy_mock("agent_skill") / "agent"

        strategy = self._discover(skill_dir)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "agent")
        self.assertEqual(result[0].kind, SkillKind.dir)
        self.assertEqual(result[0].path, skill_dir.resolve())
        self.assertEqual(result[0].main_file_relative_path, Path("SKILL.md"))

    def test_conflicting_skill_markers_raises(self):
        skill_dir = self._copy_mock("conflicting_skill_markers_raises") / "conflict"

        strategy = self._discover(skill_dir)
        with self.assertRaises(ValueError):
            strategy.discover()

    def test_flat_directory(self):
        flat = self._copy_mock("flat_directory") / "guides"

        strategy = self._discover(flat)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        self.assertEqual(len(result), 2)
        names = {r.name for r in result}
        self.assertEqual(names, {"a", "b"})
        for skill in result:
            self.assertEqual(skill.kind, SkillKind.flat)

    def test_nested_directory_skill(self):
        root = self._copy_mock("nested_directory_skill") / "skills"

        strategy = self._discover(root)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "backend")
        self.assertEqual(result[0].kind, SkillKind.dir)

    def test_mixed_flat_and_directory(self):
        root = self._copy_mock("mixed")

        strategy = self._discover(root)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        names = {r.name for r in result}
        self.assertEqual(names, {"guide", "web", "a"})

        by_name = {r.name: r for r in result}
        self.assertEqual(by_name["guide"].kind, SkillKind.flat)
        self.assertEqual(by_name["web"].kind, SkillKind.dir)
        self.assertEqual(by_name["a"].kind, SkillKind.flat)

    def test_nested_flat_in_subdir(self):
        root = self._copy_mock("nested_flat_in_subdir") / "skills"

        strategy = self._discover(root)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "react")
        self.assertEqual(result[0].kind, SkillKind.flat)

    def test_directory_skill_with_extra_skill_md_raises(self):
        skill_dir = self._copy_mock("directory_with_extra_skill_md_raises") / "web.skill"

        strategy = self._discover(skill_dir)
        with self.assertRaises(ValueError):
            strategy.discover()

    def test_human_dir_and_matching_flat_file_takes_directory(self):
        """If {dir}.skill.md is both a flat and directory pattern, prefer directory."""
        skill_dir = self._copy_mock("human_dir_and_matching_flat_file_takes_directory") / "web.skill"

        strategy = self._discover(skill_dir)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "web")
        self.assertEqual(result[0].kind, SkillKind.dir)

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
        source = LocalSource(scan_paths=(missing.resolve(),))
        strategy = AutoDiscovery(scan_path=missing.resolve(), source=source)

        result, errors = strategy.discover()

        self.assertEqual(len(result), 0)
        self.assertEqual(errors, [])

    def _build_dir_skill_with_nested(self, skill_dir: Path, nested_dir_name: str) -> None:
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("---\nname: skill\n---\n# Skill\n")
        nested = skill_dir / nested_dir_name
        nested.mkdir()
        (nested / "nested.skill.md").write_text("---\nname: nested\n---\n# Nested\n")

    def test_default_skip_folder_ignores_nested_flat_skill(self):
        skill_dir = self.tmpdir / "skill"
        self._build_dir_skill_with_nested(skill_dir, "examples")

        source = LocalSource(scan_paths=(skill_dir,))
        strategy = AutoDiscovery(scan_path=skill_dir, source=source)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "skill")

    def test_custom_skip_folder_ignores_nested_flat_skill(self):
        skill_dir = self.tmpdir / "skill"
        self._build_dir_skill_with_nested(skill_dir, "abc")

        source = LocalSource(scan_paths=(skill_dir,), skip_folder=("abc",))
        strategy = AutoDiscovery(scan_path=skill_dir, source=source)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "skill")

    def test_empty_skip_folder_does_not_ignore_nested_skill(self):
        skill_dir = self.tmpdir / "skill"
        self._build_dir_skill_with_nested(skill_dir, "examples")

        source = LocalSource(scan_paths=(skill_dir,), skip_folder=())
        strategy = AutoDiscovery(scan_path=skill_dir, source=source)

        with self.assertRaises(ValueError):
            strategy.discover()

    def test_skip_folder_ignores_nested_directory_skill(self):
        skill_dir = self.tmpdir / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: skill\n---\n# Skill\n")
        examples = skill_dir / "examples"
        examples.mkdir()
        nested = examples / "nested"
        nested.mkdir()
        (nested / "SKILL.md").write_text("---\nname: nested\n---\n# Nested\n")

        source = LocalSource(scan_paths=(skill_dir,))
        strategy = AutoDiscovery(scan_path=skill_dir, source=source)
        result, errors = strategy.discover()

        self.assertEqual(errors, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "skill")

    def test_flat_file_missing_name_is_collected_not_raised(self):
        """A *.skill.md file with no frontmatter name is a collected error,
        not a fatal exception - the rest of the scan still proceeds."""
        root = self.tmpdir / "skills"
        root.mkdir()
        (root / "noname.skill.md").write_text("# No name\n")
        (root / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide\n")

        source = LocalSource(scan_paths=(root,))
        strategy = AutoDiscovery(scan_path=root, source=source)
        result, errors = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "guide")
        self.assertEqual(len(errors), 1)
        self.assertIn("noname.skill.md", errors[0])

    def test_directory_skill_missing_name_is_collected_not_raised(self):
        """An Agent/HumanDir main file with no frontmatter name is a
        collected error, not a fatal exception."""
        skill_dir = self.tmpdir / "agent"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# No name\n")

        source = LocalSource(scan_paths=(skill_dir,))
        strategy = AutoDiscovery(scan_path=skill_dir, source=source)
        result, errors = strategy.discover()

        self.assertEqual(result, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("SKILL.md", errors[0])


if __name__ == "__main__":
    unittest.main()
