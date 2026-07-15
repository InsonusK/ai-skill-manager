"""Tests for SkillDiscovery."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.functions.skill_discovery import SkillDiscovery


class TestSkillDiscovery(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.discovery = SkillDiscovery()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_discovers_flat_skill(self):
        (self.tmp / "guide.skill.md").write_text("---\nname: guide\n---\n")

        skills, errors = self.discovery.discover([LocalSource(scan_path=self.tmp)])

        self.assertEqual(errors, [])
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].name, "guide")
        self.assertEqual(skills[0].kind, SkillKind.flat)

    def test_discovers_dir_skill(self):
        folder = self.tmp / "web"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: web\n---\n")

        skills, errors = self.discovery.discover([LocalSource(scan_path=self.tmp)])

        self.assertEqual(errors, [])
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].kind, SkillKind.dir)

    def test_reports_error_for_missing_name(self):
        (self.tmp / "guide.skill.md").write_text("# no frontmatter\n")

        skills, errors = self.discovery.discover([LocalSource(scan_path=self.tmp)])

        self.assertEqual(skills, [])
        self.assertEqual(len(errors), 1)

    def test_discovers_across_multiple_sources(self):
        source_a = self.tmp / "a"
        source_a.mkdir()
        (source_a / "skill-a.skill.md").write_text("---\nname: skill-a\n---\n")
        source_b = self.tmp / "b"
        source_b.mkdir()
        (source_b / "skill-b.skill.md").write_text("---\nname: skill-b\n---\n")

        skills, errors = self.discovery.discover(
            [LocalSource(scan_path=source_a), LocalSource(scan_path=source_b)]
        )

        self.assertEqual(errors, [])
        self.assertEqual({s.name for s in skills}, {"skill-a", "skill-b"})


if __name__ == "__main__":
    unittest.main()
