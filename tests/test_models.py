"""Tests for ai_skill_manager models."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.models import GitHubSource, LocalSource, Skill, SkillFormat, Source
from ai_skill_manager.discovery.source.auto import AutoDiscovery


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
                "subpath": "skills",
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

    def test_skill_has_optional_source(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide")
        source = LocalSource(path=self.tmpdir)

        skill = Skill(
            file_path=md,
            folder_path=None,
            format=SkillFormat.HumanFlat,
            source=source,
        )

        self.assertEqual(skill.source, source)

    def test_skill_requires_source(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide")

        with self.assertRaises(TypeError):
            Skill(
                file_path=md,
                folder_path=None,
                format=SkillFormat.HumanFlat,
            )

    def test_skill_requires_format(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide")
        source = LocalSource(path=self.tmpdir)

        with self.assertRaises(TypeError):
            Skill(file_path=md, folder_path=None, source=source)

    def test_autodiscovery_attaches_local_source(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide")

        strategy = AutoDiscovery(self.tmpdir)
        skills = strategy.discover()

        self.assertEqual(len(skills), 1)
        self.assertIsInstance(skills[0].source, LocalSource)
        self.assertEqual(skills[0].source.path, self.tmpdir)


class TestSkillName(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill(self, file_path: Path) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=None,
            format=SkillFormat.HumanFlat,
            source=LocalSource(path=self.tmpdir),
        )

    def test_name_returns_none_when_file_missing(self):
        skill = self._skill(self.tmpdir / "missing.skill.md")
        self.assertIsNone(skill.name)

    def test_name_returns_none_without_frontmatter(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("# Guide")
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_none_with_missing_terminator(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\nname: guide\n")
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_none_with_invalid_yaml(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\nname: [\n---\n# Guide")
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_none_when_frontmatter_is_not_dict(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\n- list\n---\n# Guide")
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_none_when_name_is_missing(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\n---\n# Guide")
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_none_when_name_is_not_string(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\nname: 123\n---\n# Guide")
        self.assertIsNone(self._skill(md).name)

    def test_name_returns_value_from_frontmatter(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide")
        self.assertEqual(self._skill(md).name, "guide")

    def test_name_reads_crlf_frontmatter(self):
        md = self.tmpdir / "guide.skill.md"
        md.write_bytes(b"---\r\nname: guide\r\n---\r\n# Guide")
        self.assertEqual(self._skill(md).name, "guide")
