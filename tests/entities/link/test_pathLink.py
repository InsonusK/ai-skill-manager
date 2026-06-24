"""Tests for PathLink resolution.

Тесты разрешения путей в PathLink.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.link import PathLink
from ai_skill_manager.entities.link_kind import LinkKind
from ai_skill_manager.entities.skill_file import SkillFile


MOCKS_DIR = Path(__file__).parent / "mocks"


class TestPathLink(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.workdir = self.tmpdir / "mocks"
        shutil.copytree(MOCKS_DIR, self.workdir)

        self.flat_dir = self.workdir / "flat"
        self.dir_dir = self.workdir / "dir"
        self.repo_root = self.workdir

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill(self, file_path: Path, folder_path: Path | None, repo_path: Path) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(scan_path=file_path.parent, repo_path=repo_path),
            format=SkillFormat.HumanFlat if folder_path is None else SkillFormat.Agent,
            source_path=file_path.parent,
        )

    def _flat_skill_file(self) -> SkillFile:
        md = self.flat_dir / "guide.skill.md"
        return SkillFile(path=md, skill=self._skill(md, None, self.flat_dir))

    def _dir_skill_file(self) -> SkillFile:
        md = self.dir_dir / "SKILL.md"
        return SkillFile(path=md, skill=self._skill(md, self.dir_dir, self.repo_root))

    def _path_link(self, skill_file: SkillFile, raw_path: str) -> PathLink:
        return PathLink(
            raw=f"[text]({raw_path})",
            text="text",
            format="markdown",
            start=0,
            end=1,
            skill_file=skill_file,
            raw_path=raw_path,
            header_value=None,
            is_image_value=False,
        )

    # ------------------------------------------------------------------
    # relative raw path
    # ------------------------------------------------------------------
    def test_relative_flat_self(self):
        link = self._path_link(self._flat_skill_file(), "./guide.skill.md")
        self.assertEqual(link.path_raw.kind, LinkKind.relative)
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./guide.skill.md")
        self.assertTrue(link.path.exists)

    def test_relative_flat_other(self):
        link = self._path_link(self._flat_skill_file(), "./other.md")
        self.assertEqual(link.path_raw.kind, LinkKind.relative)
        self.assertEqual(link.path.kind, LinkKind.repo_absolute)
        self.assertEqual(link.path.formatted, "other.md")
        self.assertTrue(link.path.exists)

    def test_relative_dir_self(self):
        link = self._path_link(self._dir_skill_file(), "./SKILL.md")
        self.assertEqual(link.path_raw.kind, LinkKind.relative)
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./SKILL.md")
        self.assertTrue(link.path.exists)

    def test_relative_dir_inside(self):
        link = self._path_link(self._dir_skill_file(), "./details.md")
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./details.md")
        self.assertTrue(link.path.exists)

    def test_relative_dir_sub(self):
        link = self._path_link(self._dir_skill_file(), "./sub/nested.md")
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./sub/nested.md")
        self.assertTrue(link.path.exists)

    def test_relative_dir_outside_inside_repo(self):
        link = self._path_link(self._dir_skill_file(), "../other/SKILL.md")
        self.assertEqual(link.path.kind, LinkKind.repo_absolute)
        self.assertEqual(link.path.formatted, "other/SKILL.md")
        self.assertTrue(link.path.exists)

    # ------------------------------------------------------------------
    # repo_absolute raw path
    # ------------------------------------------------------------------
    def test_repo_absolute_flat_self(self):
        link = self._path_link(self._flat_skill_file(), "guide.skill.md")
        self.assertEqual(link.path_raw.kind, LinkKind.repo_absolute)
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./guide.skill.md")
        self.assertTrue(link.path.exists)

    def test_repo_absolute_flat_other(self):
        link = self._path_link(self._flat_skill_file(), "other.md")
        self.assertEqual(link.path_raw.kind, LinkKind.repo_absolute)
        self.assertEqual(link.path.kind, LinkKind.repo_absolute)
        self.assertEqual(link.path.formatted, "other.md")
        self.assertTrue(link.path.exists)

    def test_repo_absolute_dir_self(self):
        link = self._path_link(self._dir_skill_file(), "dir/SKILL.md")
        self.assertEqual(link.path_raw.kind, LinkKind.repo_absolute)
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./SKILL.md")
        self.assertTrue(link.path.exists)

    def test_repo_absolute_dir_inside(self):
        link = self._path_link(self._dir_skill_file(), "dir/details.md")
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./details.md")
        self.assertTrue(link.path.exists)

    def test_repo_absolute_dir_sub(self):
        link = self._path_link(self._dir_skill_file(), "dir/sub/nested.md")
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./sub/nested.md")
        self.assertTrue(link.path.exists)

    def test_repo_absolute_dir_outside(self):
        link = self._path_link(self._dir_skill_file(), "other/SKILL.md")
        self.assertEqual(link.path.kind, LinkKind.repo_absolute)
        self.assertEqual(link.path.formatted, "other/SKILL.md")
        self.assertTrue(link.path.exists)

    # ------------------------------------------------------------------
    # os_absolute raw path
    # ------------------------------------------------------------------
    def test_os_absolute_flat_self(self):
        link = self._path_link(self._flat_skill_file(), "/guide.skill.md")
        self.assertEqual(link.path_raw.kind, LinkKind.os_absolute)
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./guide.skill.md")
        self.assertTrue(link.path.exists)

    def test_os_absolute_flat_other(self):
        link = self._path_link(self._flat_skill_file(), "/other.md")
        self.assertEqual(link.path_raw.kind, LinkKind.os_absolute)
        self.assertEqual(link.path.kind, LinkKind.repo_absolute)
        self.assertEqual(link.path.formatted, "other.md")
        self.assertTrue(link.path.exists)

    def test_os_absolute_dir_self(self):
        link = self._path_link(self._dir_skill_file(), "/dir/SKILL.md")
        self.assertEqual(link.path_raw.kind, LinkKind.os_absolute)
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./SKILL.md")
        self.assertTrue(link.path.exists)

    def test_os_absolute_dir_inside(self):
        link = self._path_link(self._dir_skill_file(), "/dir/details.md")
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./details.md")
        self.assertTrue(link.path.exists)

    def test_os_absolute_dir_outside(self):
        link = self._path_link(self._dir_skill_file(), "/other/SKILL.md")
        self.assertEqual(link.path.kind, LinkKind.repo_absolute)
        self.assertEqual(link.path.formatted, "other/SKILL.md")
        self.assertTrue(link.path.exists)

    # ------------------------------------------------------------------
    # outside repo
    # ------------------------------------------------------------------
    def test_relative_outside_repo_raises(self):
        with self.assertRaises(ValueError):
            self._path_link(self._dir_skill_file(), "../../outside.md")

    # ------------------------------------------------------------------
    # additional cases
    # ------------------------------------------------------------------
    def test_skill_md_fallback(self):
        skill_file = self._dir_skill_file()
        target = self.dir_dir / "a-b-c.skill.md"
        target.write_text("# Skill\n")
        link = self._path_link(skill_file, "./a-b-c.skill")
        self.assertTrue(link.path.exists)
        self.assertEqual(link.path.kind, LinkKind.relative)
        self.assertEqual(link.path.formatted, "./a-b-c.skill.md")

    def test_missing_file_exists_false(self):
        link = self._path_link(self._dir_skill_file(), "./missing.md")
        self.assertFalse(link.path.exists)
        self.assertEqual(link.path.kind, LinkKind.repo_absolute)

    def test_web_path_raises(self):
        with self.assertRaises(ValueError):
            self._path_link(self._flat_skill_file(), "https://example.com")

    def test_target_property(self):
        link = self._path_link(self._flat_skill_file(), "./guide.skill.md")
        self.assertEqual(link.target, link.path.formatted)

    def test_link_type_property(self):
        link = self._path_link(self._flat_skill_file(), "./guide.skill.md")
        self.assertIs(link.link_type, PathLink)


if __name__ == "__main__":
    unittest.main()
