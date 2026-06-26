"""Tests for SkillFile and storage-level Link integration."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.path_kind import PathKind
from ai_skill_manager.entities.link import PathLink, WebLink
from ai_skill_manager.entities.link.link_kind import LinkKind
from ai_skill_manager.entities.skill_file import SkillFile


MOCK_DIR = Path(__file__).parent.parent / "mock" / "test_skill_file"


class TestSkillFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def _skill(self, file_path: Path, folder_path: Path | None = None) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(scan_path=file_path.parent),
            format=SkillFormat.Agent if folder_path else SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def test_skill_file_is_dataclass(self):
        md = self._copy_mock("skill_with_link") / "guide.skill.md"
        skill = self._skill(md)
        sf = SkillFile(path=md, skill=skill)
        self.assertEqual(sf.path, md)

    def test_links_are_cached(self):
        md = self._copy_mock("skill_with_link") / "guide.skill.md"
        skill = self._skill(md)
        sf = SkillFile(path=md, skill=skill)
        first = sf.links
        second = sf.links
        self.assertEqual(first, second)

    def test_links_returns_path_link(self):
        md = self._copy_mock("skill_with_link") / "guide.skill.md"
        skill = self._skill(md)
        sf = SkillFile(path=md, skill=skill)
        link = sf.links[0]
        self.assertIsInstance(link, PathLink)
        self.assertEqual(link.path_raw.path, "./file.md")
        self.assertEqual(link.path_raw.kind, PathKind.relative)
        self.assertEqual(link.path.kind, LinkKind.source)
        self.assertEqual(link.path.formatted, "file.md")


class TestSkillFiles(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def _skill(self, file_path: Path, folder_path: Path | None = None) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(scan_path=file_path.parent),
            format=SkillFormat.Agent if folder_path else SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def test_skill_files_cached(self):
        skill_dir = self._copy_mock("agent_skill")
        (skill_dir / "SKILL.md").write_text("---\nname: skill\n---\n# Skill\n")
        (skill_dir / "extra.md").write_text("# Extra\n")
        skill = self._skill(skill_dir / "SKILL.md", skill_dir)
        first = skill.files
        second = skill.files
        self.assertEqual(first, second)
        self.assertEqual(len(skill.files), 2)

    def test_skill_remains_hashable_after_loading_files(self):
        md = self._copy_mock("skill_with_link") / "guide.skill.md"
        skill = self._skill(md)
        _ = skill.files
        _ = skill.files[0].links
        self.assertTrue(hash(skill))


if __name__ == "__main__":
    unittest.main()
