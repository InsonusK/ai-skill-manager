"""Tests for LinkWithContext."""

import io
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.entities import GitHubSource, LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.link.link_kind import LinkKind
from ai_skill_manager.entities.skill_file import SkillFile
from ai_skill_manager.models.link_with_context import LinkWithContext
from ai_skill_manager.service.discover import discover


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

    def _skill(self, file_path: Path, folder_path: Path | None = None, repo_path: Path | None = None) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(scan_path=file_path.parent, repo_path=repo_path),
            format=SkillFormat.Agent if folder_path else SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def _context(self, skill: Skill, file_path: Path):
        skill_file = SkillFile(path=file_path, skill=skill)
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
        source = LocalSource(scan_path=root)
        skill = Skill(
            file_path=md,
            folder_path=None,
            source=source,
            format=SkillFormat.HumanFlat,
            source_path=root,
        )
        ctx = self._context(skill, md)

        self.assertEqual(ctx.os_absolute_path, (root / "other.skill.md").resolve())

    def test_os_absolute_raw_outside_repo_resolves_as_os(self):
        # EN: An OS-absolute path outside the repository root is kept as a real
        # OS path and classified as LinkKind.os.
        # RU: Абсолютный путь ОС за пределами корня репозитория сохраняется как
        # реальный путь ОС и классифицируется как LinkKind.os.
        root = self._copy_mock("os_abs")
        md = root / "guide.skill.md"
        absolute_target = self.tmpdir / "absolute.md"
        absolute_target.write_text("# Absolute\n")
        md.write_text(
            f"---\nname: guide\n---\n# Guide\n[absolute]({absolute_target.as_posix()})\n"
        )
        skill = self._skill(md)
        ctx = self._context(skill, md)

        self.assertEqual(ctx.os_absolute_path, absolute_target.resolve())
        self.assertEqual(ctx.base.path.kind, LinkKind.os)
        self.assertFalse(ctx.base.path.is_inside_repo)

    def test_os_absolute_raw_inside_repo_resolves_as_repo_absolute(self):
        # EN: An OS-absolute path that physically lies inside the repository
        # root is treated as repo-absolute.
        # RU: Абсолютный путь ОС, физически лежащий внутри корня репозитория,
        # обрабатывается как repo-absolute.
        root = self._copy_mock("os_abs")
        md = root / "guide.skill.md"
        absolute_target = (root / "tmp" / "absolute.md").resolve()
        md.write_text(f"---\nname: guide\n---\n# Guide\n[absolute]({absolute_target.as_posix()})\n")
        skill = self._skill(md)
        ctx = self._context(skill, md)

        self.assertEqual(ctx.os_absolute_path, absolute_target)
        self.assertEqual(ctx.base.path.kind, LinkKind.source)
        self.assertTrue(ctx.base.path.is_inside_repo)

    def test_repo_absolute_path_uses_repo_path(self):
        root = self._copy_mock("repo_abs")
        md = root / "skills" / "guide.skill.md"
        source = LocalSource(scan_path=root / "skills", repo_path=root)
        skill = Skill(
            file_path=md,
            folder_path=None,
            source=source,
            format=SkillFormat.HumanFlat,
            source_path=root / "skills",
        )
        ctx = self._context(skill, md)

        self.assertEqual(ctx.os_absolute_path, (root / "other.skill.md").resolve())

    def test_repo_absolute_path_for_github_source(self):
        """Repo-absolute links resolve against the repository root, not subpath."""
        repo_mock = self._copy_mock("repo_abs")
        # other.skill.md is at the repo root so the repo-absolute link must
        # resolve against repo_path, not source_path.
        # other.skill.md находится в корне репозитория, чтобы ссылка
        # repo_absolute разрешалась относительно repo_path, а не source_path.

        archive_path = self.tmpdir / "repo-main.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(repo_mock, arcname="repo-main")

        def fake_download(owner, repo, tree):
            fake_path = self.tmpdir / "fake_archive.tar.gz"
            fake_path.write_bytes(archive_path.read_bytes())
            return fake_path

        with patch("ai_skill_manager.entities.source.github._download_archive", side_effect=fake_download):
            source = GitHubSource(
                repo_url="https://github.com/owner/repo",
                tree="main",
                subpath="skills",
            )
            skills = discover([source])

        self.assertEqual(len(skills), 1)
        skill = skills[0]
        ctx = self._context(skill, skill.file_path)
        expected = (source.get_scan_location().repo_path / "other.skill.md").resolve()
        self.assertEqual(ctx.os_absolute_path, expected)

    def test_os_absolute_path_is_cached(self):
        """Repeated accesses return the same resolved Path instance."""
        root = self._copy_mock("flat")
        md = root / "guide.skill.md"
        skill = self._skill(md)
        ctx = self._context(skill, md)

        first = ctx.os_absolute_path
        second = ctx.os_absolute_path

        self.assertIs(first, second)

    def test_os_absolute_path_is_cached_for_web_link(self):
        """Repeated accesses return the same None for web links."""
        root = self._copy_mock("flat")
        md = root / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n[external](https://example.com)\n")
        skill = self._skill(md)
        ctx = self._context(skill, md)

        first = ctx.os_absolute_path
        second = ctx.os_absolute_path

        self.assertIsNone(first)
        self.assertIs(first, second)

    def test_is_link_to_another_skill_and_file(self):
        """Links to another skill are detected by helper methods."""
        root = self._copy_mock("dir")
        skill_dir = root / "web"
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, repo_path=root)
        other_dir = root / "other"
        other_dir.mkdir()
        (other_dir / "SKILL.md").write_text("---\nname: other\n---\n# Other\n")
        other = self._skill(other_dir / "SKILL.md", other_dir, repo_path=root)

        skill_file = SkillFile(path=skill_dir / "SKILL.md", skill=skill)
        skill_file.path.write_text("---\nname: web\n---\n# Web\n[other](../other/SKILL.md)\n")
        link = skill_file.links[0]
        ctx = LinkWithContext.build(skill, skill_file, link)

        self.assertEqual(ctx.is_link_to_another_skill([skill, other]), other)
        self.assertEqual(ctx.is_link_to_another_skill_file([skill, other]), (other, other.files[0]))

    def test_getattr_forwards_to_base_and_raises(self):
        """Attribute access forwards to the wrapped link and raises sensibly."""
        root = self._copy_mock("flat")
        md = root / "guide.skill.md"
        skill = self._skill(md)
        ctx = self._context(skill, md)

        self.assertEqual(ctx.target, "./guide.skill.md")
        with self.assertRaises(AttributeError):
            _ = ctx.nonexistent_attribute

    def test_target_skill_finds_owning_skill(self):
        """target_skill returns the skill whose folder contains the link target."""
        root = self._copy_mock("dir")
        skill_dir = root / "web"
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, repo_path=root)
        other_dir = root / "other"
        other_dir.mkdir()
        (other_dir / "SKILL.md").write_text("---\nname: other\n---\n# Other\n")
        other = self._skill(other_dir / "SKILL.md", other_dir, repo_path=root)

        skill_file = SkillFile(path=skill_dir / "SKILL.md", skill=skill)
        skill_file.path.write_text("---\nname: web\n---\n# Web\n[other](../other/SKILL.md)\n")
        link = skill_file.links[0]
        ctx = LinkWithContext.build(skill, skill_file, link)

        self.assertEqual(ctx.target_skill([skill, other]), other)

    def test_target_skill_returns_none_for_source_file(self):
        """target_skill returns None when the target is not inside any skill."""
        root = self._copy_mock("dir")
        skill_dir = root / "web"
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, repo_path=root)
        orphan = root / "orphan.md"
        orphan.write_text("# Orphan\n")

        skill_file = SkillFile(path=skill_dir / "SKILL.md", skill=skill)
        skill_file.path.write_text("---\nname: web\n---\n# Web\n[orphan](../orphan.md)\n")
        link = skill_file.links[0]
        ctx = LinkWithContext.build(skill, skill_file, link)

        self.assertIsNone(ctx.target_skill([skill]))


if __name__ == "__main__":
    unittest.main()
