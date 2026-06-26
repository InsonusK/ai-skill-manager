import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.discovery.link.builder.wikilink import WikilinkBuilder
from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.path_kind import PathKind
from ai_skill_manager.entities.link import PathLink
from ai_skill_manager.entities.link.link_kind import LinkKind
from ai_skill_manager.entities.skill_file import SkillFile
from . import MOCK_DIR

TESTCASE_MOCK_DIR = MOCK_DIR / "test_wikilink_builder"


class TestWikilinkBuilder(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.workdir = self.tmpdir / "wiki_mock"
        shutil.copytree(TESTCASE_MOCK_DIR, self.workdir)

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

    def test_finds_wiki_link(self):
        builder = WikilinkBuilder()
        skill_dir = self.workdir
        md = skill_dir / "SKILL.md"
        md.write_text("# Skill\n")
        # Make sure the target file exists for PathLink resolution.
        target = skill_dir / "file.md"
        target.write_text("# File\n")
        skill_file = self._skill_file(md, skill_dir)
        links = builder.search("[[./file.md|text]]", skill_file)
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], PathLink)
        self.assertIs(links[0].skill_file, skill_file)
        self.assertEqual(links[0].path_raw.path, "./file.md")
        self.assertEqual(links[0].path_raw.kind, PathKind.relative)
        self.assertEqual(links[0].path.kind, LinkKind.skill)

    def test_finds_wiki_link_without_text(self):
        builder = WikilinkBuilder()
        skill_dir = self.workdir
        md = skill_dir / "SKILL.md"
        md.write_text("# Skill\n")
        target = skill_dir / "file.md"
        target.write_text("# File\n")
        skill_file = self._skill_file(md, skill_dir)
        links = builder.search("[[./file.md]]", skill_file)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].path_raw.path, "./file.md")
        self.assertEqual(links[0].text, "file.md")

    def test_empty_content_returns_empty(self):
        builder = WikilinkBuilder()
        skill_dir = self.workdir
        md = skill_dir / "SKILL.md"
        md.write_text("# Skill\n")
        skill_file = self._skill_file(md, skill_dir)
        links = builder.search("", skill_file)
        self.assertEqual(len(links), 0)

    def test_find_repo_relative_link(self):
        builder = WikilinkBuilder()
        skill_dir = self.workdir
        md = skill_dir / "SKILL.md"
        md.write_text("# Skill\n")
        skill_file = self._skill_file(md, skill_dir)
        content = (self.workdir / "relative_link_tc.md").read_text()
        links = builder.search(content, skill_file)
        self.assertEqual(len(links), 1)
        self.assertIsInstance(links[0], PathLink)
        self.assertEqual(links[0].raw, "[[skills/🧩validated/{solution}.skill.md|integration.solution.skill]]")
        self.assertEqual(links[0].path_raw.path, "skills/🧩validated/{solution}.skill.md")
        self.assertEqual(links[0].path_raw.kind, PathKind.repo_absolute)
        self.assertEqual(links[0].path.kind, LinkKind.skill)
        self.assertEqual(links[0].text, "integration.solution.skill")


if __name__ == "__main__":
    unittest.main()
