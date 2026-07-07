import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.discovery.link.builder.markdown import MarkdownLinkBuilder
from ai_skill_manager.discovery.link.builder.wikilink import WikilinkBuilder
from ai_skill_manager.discovery.link.link_factory import search_links_in_content
from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.path_kind import PathKind
from ai_skill_manager.entities.link import PathLink, WebLink
from ai_skill_manager.entities.link.link_kind import LinkKind
from ai_skill_manager.entities.skill_file import SkillFile


class TestLinkFactory(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill(self, file_path: Path) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=None,
            source=LocalSource(scan_path=file_path.parent),
            format=SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def _skill_file(self, file_path: Path) -> SkillFile:
        return SkillFile(path=file_path, skill=self._skill(file_path))

    def _prepare_mixed(self):
        root = self.tmpdir / "repo"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Mixed\n")
        (root / "file.md").write_text("# File\n")
        (root / "img.png").write_text("")
        tmp_dir = root / "tmp"
        tmp_dir.mkdir()
        (tmp_dir / "file.md").write_text("# Absolute\n")
        (root / "wiki link.md").write_text("# Wiki\n")
        absolute_target = self.tmpdir / "absolute.md"
        absolute_target.write_text("# Absolute\n")
        self._absolute_target = absolute_target
        content = (
            "# Mixed\n"
            "[relative](./file.md)\n"
            f"[absolute]({absolute_target.as_posix()})\n"
            "[web](https://example.com)\n"
            "![image](./img.png)\n"
            "[[wiki link|text]]\n"
        )
        return root, md, content

    def test_search_links_sorts_by_offset(self):
        root = self.tmpdir / "repo"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        (root / "a.md").write_text("# A\n")
        (root / "b.md").write_text("# B\n")
        skill_file = self._skill_file(md)

        content = "[first](./a.md) [[./b.md|second]]"
        links = search_links_in_content(content, skill_file)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].path_raw.path, "./a.md")
        self.assertEqual(links[1].path_raw.path, "./b.md")

    def test_search_links_from_file(self):
        root, md, content = self._prepare_mixed()
        skill_file = self._skill_file(md)
        links = search_links_in_content(content, skill_file)

        expected = {
            "[relative](./file.md)": {
                "path_raw": "./file.md",
                "raw_kind": PathKind.relative,
                "kind": LinkKind.source,
                "text": "relative",
                "format": MarkdownLinkBuilder,
                "header": None,
                "is_image": False,
                "cls": PathLink,
                "formatted": "file.md",
            },
            f"[absolute]({self._absolute_target.as_posix()})": {
                "path_raw": self._absolute_target.as_posix(),
                "raw_kind": PathKind.os_absolute,
                "kind": LinkKind.os,
                "text": "absolute",
                "format": MarkdownLinkBuilder,
                "header": None,
                "is_image": False,
                "cls": PathLink,
                "formatted": self._absolute_target.resolve().as_posix(),
            },
            "[web](https://example.com)": {
                "url": "https://example.com",
                "text": "web",
                "format": MarkdownLinkBuilder,
                "header": None,
                "is_image": False,
                "cls": WebLink,
            },
            "![image](./img.png)": {
                "path_raw": "./img.png",
                "raw_kind": PathKind.relative,
                "kind": LinkKind.source,
                "text": "image",
                "format": MarkdownLinkBuilder,
                "header": None,
                "is_image": True,
                "cls": PathLink,
                "formatted": "img.png",
            },
            "[[wiki link|text]]": {
                "path_raw": "wiki link",
                "raw_kind": PathKind.repo_absolute,
                "kind": LinkKind.source,
                "text": "text",
                "format": WikilinkBuilder,
                "header": None,
                "is_image": False,
                "cls": PathLink,
                "formatted": "wiki link.md",
            }
        }

        self.assertEqual(len(links), len(expected))
        for link in links:
            self.assertIn(link.raw, expected, f"Unexpected link: {link.raw}")
            exp = expected[link.raw]
            self.assertIsInstance(link, exp["cls"])
            self.assertEqual(link.text, exp["text"])
            self.assertIs(link.format, exp["format"])
            self.assertEqual(link.header, exp["header"])
            self.assertEqual(link.is_image, exp["is_image"])
            if isinstance(link, PathLink):
                self.assertEqual(link.path_raw.path, exp["path_raw"])
                self.assertEqual(link.path_raw.kind, exp["raw_kind"])
                self.assertEqual(link.path.kind, exp["kind"])
                self.assertEqual(link.path.formatted, exp["formatted"])
            else:
                self.assertEqual(link.url, exp["url"])

        found_raws = {link.raw for link in links}
        self.assertEqual(found_raws, set(expected.keys()))

    def test_links_inside_example_block_are_ignored(self):
        # EN: Markdown/wiki links inside a ```example fenced code block must
        # not be treated as real links.
        # RU: Markdown/wiki-ссылки внутри fenced code block ```example не должны
        # считаться настоящими ссылками.
        root = self.tmpdir / "repo"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        (root / "outside.md").write_text("# Outside\n")
        skill_file = self._skill_file(md)

        content = (
            "# Skill\n"
            "[valid](./outside.md)\n"
            "```example\n"
            "[[ignored link]]\n"
            "[ignored too](./missing.md)\n"
            "```\n"
            "[also valid](./outside.md)\n"
        )
        links = search_links_in_content(content, skill_file)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].raw, "[valid](./outside.md)")
        self.assertEqual(links[1].raw, "[also valid](./outside.md)")

    def test_example_block_without_closing_fence_is_ignored_to_eof(self):
        # EN: An unclosed ```example block must hide links up to the end of
        # the file.
        # RU: Незакрытый блок ```example должен скрывать ссылки до конца файла.
        root = self.tmpdir / "repo"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        (root / "outside.md").write_text("# Outside\n")
        skill_file = self._skill_file(md)

        content = (
            "[valid](./outside.md)\n"
            "```example\n"
            "[ignored](./missing.md)\n"
        )
        links = search_links_in_content(content, skill_file)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].raw, "[valid](./outside.md)")

    def test_example_block_preserves_offsets_for_replacement(self):
        # EN: Masking ```example blocks must not change link offsets so that
        # later adapters can still replace links correctly.
        # RU: Маскирование блоков ```example не должно менять смещения ссылок,
        # чтобы последующие адаптеры могли корректно заменять ссылки.
        root = self.tmpdir / "repo"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        (root / "outside.md").write_text("# Outside\n")
        skill_file = self._skill_file(md)

        content = (
            "[first](./outside.md)\n"
            "```example\n"
            "[ignored](./missing.md)\n"
            "```\n"
            "[second](./outside.md)\n"
        )
        links = search_links_in_content(content, skill_file)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].raw, "[first](./outside.md)")
        self.assertEqual(links[0].start, content.index("[first"))
        self.assertEqual(links[1].raw, "[second](./outside.md)")
        self.assertEqual(links[1].start, content.index("[second"))

    def test_indented_example_block_is_ignored(self):
        # EN: A ```example block indented by up to three spaces must also hide
        # its links.
        # RU: Блок ```example с отступом до трёх пробелов также должен скрывать
        # находящиеся в нём ссылки.
        root = self.tmpdir / "repo"
        root.mkdir()
        md = root / "SKILL.md"
        md.write_text("# Skill\n")
        (root / "outside.md").write_text("# Outside\n")
        skill_file = self._skill_file(md)

        content = (
            "[valid](./outside.md)\n"
            "   ```example\n"
            "   [[ignored]]\n"
            "   ```\n"
            "[also valid](./outside.md)\n"
        )
        links = search_links_in_content(content, skill_file)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].raw, "[valid](./outside.md)")
        self.assertEqual(links[1].raw, "[also valid](./outside.md)")


if __name__ == "__main__":
    unittest.main()
