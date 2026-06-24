import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.discovery.link.link_factory import search_links_in_content
from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.link import PathLink, WebLink
from ai_skill_manager.entities.link_kind import LinkKind
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
        content = (
            "# Mixed\n"
            "[relative](./file.md)\n"
            "[absolute](/tmp/file.md)\n"
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
                "raw_kind": LinkKind.relative,
                "kind": LinkKind.repo_absolute,
                "text": "relative",
                "format": "markdown",
                "header": None,
                "is_image": False,
                "cls": PathLink,
                "formatted": "file.md",
            },
            "[absolute](/tmp/file.md)": {
                "path_raw": "/tmp/file.md",
                "raw_kind": LinkKind.os_absolute,
                "kind": LinkKind.repo_absolute,
                "text": "absolute",
                "format": "markdown",
                "header": None,
                "is_image": False,
                "cls": PathLink,
                "formatted": "tmp/file.md",
            },
            "[web](https://example.com)": {
                "path": "https://example.com",
                "text": "web",
                "format": "markdown",
                "header": None,
                "is_image": False,
                "cls": WebLink,
            },
            "![image](./img.png)": {
                "path_raw": "./img.png",
                "raw_kind": LinkKind.relative,
                "kind": LinkKind.repo_absolute,
                "text": "image",
                "format": "markdown",
                "header": None,
                "is_image": True,
                "cls": PathLink,
                "formatted": "img.png",
            },
            "[[wiki link|text]]": {
                "path_raw": "wiki link",
                "raw_kind": LinkKind.repo_absolute,
                "kind": LinkKind.repo_absolute,
                "text": "text",
                "format": "wiki",
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
            self.assertEqual(link.format, exp["format"])
            self.assertEqual(link.header, exp["header"])
            self.assertEqual(link.is_image, exp["is_image"])
            if isinstance(link, PathLink):
                self.assertEqual(link.path_raw.path, exp["path_raw"])
                self.assertEqual(link.path_raw.kind, exp["raw_kind"])
                self.assertEqual(link.path.kind, exp["kind"])
                self.assertEqual(link.path.formatted, exp["formatted"])
            else:
                self.assertEqual(link.path, exp["path"])

        found_raws = {link.raw for link in links}
        self.assertEqual(found_raws, set(expected.keys()))


if __name__ == "__main__":
    unittest.main()
