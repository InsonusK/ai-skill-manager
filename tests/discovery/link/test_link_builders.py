"""Tests for markdown/wiki link builders."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.discovery.link.builder.markdown import MarkdownLinkBuilder
from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.path_kind import PathKind
from ai_skill_manager.entities.link import PathLink, WebLink
from ai_skill_manager.entities.link.link_kind import LinkKind
from ai_skill_manager.entities.skill_file import SkillFile


class TestMarkdownLinkBuilder(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill(self, file_path: Path, folder_path: Path | None = None) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(scan_path=file_path.parent),
            format=SkillFormat.Agent if folder_path else SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def _skill_file(self, file_path: Path, folder_path: Path | None = None) -> SkillFile:
        return SkillFile(path=file_path, skill=self._skill(file_path, folder_path))

    def test_finds_relative_link(self):
        root = self.tmpdir / "skill"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        target = root / "file.md"
        target.write_text("# File\n")
        skill_file = self._skill_file(md, root)

        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./file.md)", skill_file)
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], PathLink)
        self.assertIs(links[0].skill_file, skill_file)
        self.assertEqual(links[0].path_raw.path, "./file.md")
        self.assertEqual(links[0].path_raw.kind, PathKind.relative)
        self.assertEqual(links[0].path.kind, LinkKind.skill)
        self.assertEqual(links[0].path.formatted, "./file.md")

    def test_finds_image_link(self):
        root = self.tmpdir / "skill"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        target = root / "img.png"
        target.write_text("")
        skill_file = self._skill_file(md, root)

        builder = MarkdownLinkBuilder()
        links = builder.search("![alt](./img.png)", skill_file)
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0].is_image)
        self.assertIsInstance(links[0], PathLink)

    def test_finds_link_with_fragment(self):
        root = self.tmpdir / "skill"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        target = root / "file.md"
        target.write_text("# File\n")
        skill_file = self._skill_file(md, root)

        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./file.md#section)", skill_file)
        self.assertEqual(links[0].path_raw.path, "./file.md")
        self.assertEqual(links[0].header, "#section")

    def test_finds_web_link(self):
        root = self.tmpdir / "skill"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        skill_file = self._skill_file(md, root)

        builder = MarkdownLinkBuilder()
        links = builder.search("[web](https://example.com)", skill_file)
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], WebLink)
        self.assertIs(links[0].skill_file, skill_file)
        self.assertEqual(links[0].url, "https://example.com")
        self.assertEqual(links[0].path.formatted, "https://example.com")

    def test_skill_md_fallback(self):
        """A link to ``a-b-c.skill`` resolves to ``a-b-c.skill.md``."""
        root = self.tmpdir / "skill"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        target = root / "a-b-c.skill.md"
        target.write_text("# Skill file\n")
        skill_file = self._skill_file(md, root)

        builder = MarkdownLinkBuilder()
        links = builder.search("[text](./a-b-c.skill)", skill_file)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].path.os_path, target.resolve())
        self.assertEqual(links[0].path.formatted, "./a-b-c.skill.md")

    def test_empty_content_returns_empty(self):
        root = self.tmpdir / "skill"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        skill_file = self._skill_file(md, root)

        builder = MarkdownLinkBuilder()
        links = builder.search("", skill_file)
        self.assertEqual(len(links), 0)

    def test_link_type_property(self):
        """absLink.link_type returns the concrete class."""
        root = self.tmpdir / "skill"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        (root / "file.md").write_text("# File\n")
        skill_file = self._skill_file(md, root)

        builder = MarkdownLinkBuilder()
        path_link = builder.search("[text](./file.md)", skill_file)[0]
        web_link = builder.search("[web](https://example.com)", skill_file)[0]

        self.assertIs(path_link.link_type, PathLink)
        self.assertIs(web_link.link_type, WebLink)

    def test_finds_windows_separator_link(self):
        # EN: Markdown links written with Windows backslashes must resolve
        # exactly like POSIX links.
        # RU: Markdown-ссылки с обратными слешами Windows должны разрешаться
        # точно так же, как POSIX-ссылки.
        root = self.tmpdir / "skill"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        target = root / "sub" / "file.md"
        target.parent.mkdir()
        target.write_text("# File\n")
        skill_file = self._skill_file(md, root)

        builder = MarkdownLinkBuilder()
        links = builder.search("[text](.\\sub\\file.md)", skill_file)
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], PathLink)
        self.assertEqual(links[0].path_raw.path, ".\\sub\\file.md")
        self.assertEqual(links[0].path_raw.kind, PathKind.relative)
        self.assertEqual(links[0].path.kind, LinkKind.skill)
        self.assertEqual(links[0].path.formatted, "./sub/file.md")
        self.assertTrue(links[0].path.exists)

    def test_base_helper_methods_handle_windows_separators(self):
        # EN: The protected helpers used by builders must accept Windows
        # backslashes the same way as POSIX separators.
        # RU: Защищённые хелперы, используемые сборщиками, должны принимать
        # обратные слеши Windows так же, как POSIX-разделители.
        builder = MarkdownLinkBuilder()
        self.assertTrue(builder._is_relative(".\\file.md"))
        self.assertTrue(builder._is_relative("..\\file.md"))
        self.assertTrue(builder._is_relative("./file.md"))
        self.assertTrue(builder._is_os_absolute("/tmp/file.md"))
        self.assertEqual(builder._get_kind(".\\file.md"), PathKind.relative)
        self.assertEqual(builder._get_kind("/tmp/file.md"), PathKind.os_absolute)
        self.assertEqual(builder._get_kind("file.md"), PathKind.repo_absolute)


if __name__ == "__main__":
    unittest.main()
