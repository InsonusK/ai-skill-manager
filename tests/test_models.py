"""Tests for ai_skill_manager entities/models."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import GitHubSource, LocalSource, Skill, SkillFormat, Source
from ai_skill_manager.discovery.skill.auto import AutoDiscovery
from ai_skill_manager.entities.skill_propetry import SkillProperty
from ai_skill_manager.entities.source import LocalSource as LocalSourceCls


MOCK_DIR = Path(__file__).parent / "mock" / "test_models"


class TestSource(unittest.TestCase):
    def test_local_source_is_abstract_source(self):
        path = Path("/tmp/skills")
        source = LocalSource(path=path)
        self.assertIsInstance(source, Source)
        self.assertEqual(source.source_type, "local")
        self.assertEqual(source.to_dict(), {"type": "local", "path": str(path)})

    def test_github_source_is_abstract_source(self):
        source = GitHubSource(
            repo_url="https://github.com/owner/repo",
            tree="main",
            subpath="skills",
        )
        self.assertIsInstance(source, Source)
        self.assertEqual(source.source_type, "github")
        self.assertEqual(
            source.to_dict(),
            {
                "type": "github",
                "repo_url": "https://github.com/owner/repo",
                "tree": "main",
                "subpath": ["skills"],
            },
        )

    def test_github_source_default_tree(self):
        source = GitHubSource(repo_url="https://github.com/owner/repo")
        self.assertEqual(source.tree, "master")
        self.assertIsNone(source.subpath)


class TestSkillSourceLink(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def test_skill_has_optional_source(self):
        md = self._copy_mock("name_value") / "guide.skill.md"
        source = LocalSource(path=md.parent)

        skill = Skill(
            file_path=md,
            folder_path=None,
            format=SkillFormat.HumanFlat,
            source=source,
            source_path=md.parent,
        )

        self.assertEqual(skill.source, source)

    def test_skill_requires_source(self):
        md = self._copy_mock("name_value") / "guide.skill.md"

        with self.assertRaises(TypeError):
            Skill(
                file_path=md,
                folder_path=None,
                format=SkillFormat.HumanFlat,
            )

    def test_skill_requires_format(self):
        md = self._copy_mock("name_value") / "guide.skill.md"
        source = LocalSource(path=md.parent)

        with self.assertRaises(TypeError):
            Skill(file_path=md, folder_path=None, source=source, source_path=md.parent)

    def test_autodiscovery_attaches_local_source(self):
        root = self._copy_mock("autodiscovery")
        source = LocalSource(path=root)

        strategy = AutoDiscovery(source_path=root, source=source)
        skills = strategy.discover()

        self.assertEqual(len(skills), 1)
        self.assertIsInstance(skills[0].source, LocalSourceCls)
        self.assertEqual(skills[0].source.path, root)


class TestSkillName(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def _skill(self, file_path: Path) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=None,
            format=SkillFormat.HumanFlat,
            source=LocalSource(path=file_path.parent),
            source_path=file_path.parent,
        )

    def test_name_returns_none_when_file_missing(self):
        prop = SkillProperty(self.tmpdir / "missing.skill.md")
        self.assertIsNone(prop.name)

    def test_name_returns_none_without_frontmatter(self):
        md = self._copy_mock("name_no_frontmatter") / "guide.skill.md"
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_none_with_missing_terminator(self):
        md = self._copy_mock("name_missing_terminator") / "guide.skill.md"
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_none_with_invalid_yaml(self):
        md = self._copy_mock("name_invalid_yaml") / "guide.skill.md"
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_none_when_frontmatter_is_not_dict(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\n- list\n---\n# Guide")
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_none_when_name_is_missing(self):
        md = self._copy_mock("name_missing") / "guide.skill.md"
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_none_when_name_is_not_string(self):
        md = self._copy_mock("name_not_string") / "guide.skill.md"
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_value_from_frontmatter(self):
        md = self._copy_mock("name_value") / "guide.skill.md"
        self.assertEqual(self._skill(md).name, "guide")

    def test_name_reads_crlf_frontmatter(self):
        md = self._copy_mock("name_crlf") / "guide.skill.md"
        self.assertEqual(self._skill(md).name, "guide")


if __name__ == "__main__":
    unittest.main()
