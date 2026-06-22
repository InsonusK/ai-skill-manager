"""Tests for LinkWithContext."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.skill_file import SkillFile
from ai_skill_manager.models.link_with_context import LinkWithContext


MOCK_DIR = Path(__file__).parent.parent / "mock" / "test_link_with_context"


class TestLinkWithContext(unittest.TestCase):
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
            source=LocalSource(path=file_path.parent),
            format=SkillFormat.Agent if folder_path else SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def _context(self, skill: Skill, file_path: Path):
        skill_file = SkillFile(path=file_path)
        link = skill_file.links[0]
        return LinkWithContext.build(skill, skill_file, link)

    def test_os_absolute_path_for_relative_link(self):
        root = self._copy_mock("flat")
        md = root / "guide.skill.md"
        skill = self._skill(md)
        ctx = self._context(skill, md)

        self.assertEqual(ctx.os_absolute_path, md.resolve())

    def test_is_link_to_skill_file_for_flat(self):
        root = self._copy_mock("flat")
        md = root / "guide.skill.md"
        skill = self._skill(md)
        ctx = self._context(skill, md)

        self.assertTrue(ctx.is_link_to_skill_file)

    def test_is_link_to_skill_file_for_dir(self):
        root = self._copy_mock("dir")
        skill_dir = root / "web"
        skill = self._skill(skill_dir / "SKILL.md", skill_dir)
        ctx = self._context(skill, skill_dir / "SKILL.md")

        self.assertTrue(ctx.is_link_to_skill_file)

    def test_repo_absolute_path(self):
        root = self._copy_mock("repo_abs")
        md = root / "skills" / "guide.skill.md"
        source = LocalSource(path=root)
        skill = Skill(
            file_path=md,
            folder_path=None,
            source=source,
            format=SkillFormat.HumanFlat,
            source_path=root,
        )
        ctx = self._context(skill, md)

        self.assertEqual(ctx.os_absolute_path, (root / "other.skill.md").resolve())

    def test_os_absolute_link(self):
        root = self._copy_mock("os_abs")
        md = root / "guide.skill.md"
        skill = self._skill(md)
        ctx = self._context(skill, md)

        self.assertEqual(ctx.os_absolute_path, Path("/tmp/absolute.md"))

    def test_to_skill_format_for_flat_self_link(self):
        root = self._copy_mock("flat")
        md = root / "guide.skill.md"
        skill = self._skill(md)
        ctx = self._context(skill, md)

        self.assertEqual(ctx.to_skill_format([]), "./SKILL.md")

    def test_to_skill_format_for_cross_skill(self):
        root = self._copy_mock("dir")
        skill_dir = root / "web"
        skill = self._skill(skill_dir / "SKILL.md", skill_dir)
        other_dir = root / "other"
        other_dir.mkdir()
        (other_dir / "SKILL.md").write_text("---\nname: other\n---\n# Other\n")
        other = self._skill(other_dir / "SKILL.md", other_dir)

        skill_file = SkillFile(path=skill_dir / "SKILL.md")
        skill_file.path.write_text("---\nname: web\n---\n# Web\n[other](../other/SKILL.md)\n")
        link = skill_file.links[0]
        ctx = LinkWithContext.build(skill, skill_file, link)

        self.assertEqual(ctx.to_skill_format([skill, other]), "skill:other")


if __name__ == "__main__":
    unittest.main()
