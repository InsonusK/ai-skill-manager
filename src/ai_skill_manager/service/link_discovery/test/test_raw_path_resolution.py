"""Tests for resolve_raw_link_path."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.service.link_discovery.raw_path_resolution import resolve_raw_link_path


class TestResolveRawLinkPath(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp
        self.skill_a = self.repo / "skill-a" / "SKILL.md"
        self.skill_a.parent.mkdir(parents=True)
        self.skill_a.write_text("---\n")
        self.skill_b = self.repo / "skill-b" / "SKILL.md"
        self.skill_b.parent.mkdir(parents=True)
        self.skill_b.write_text("---\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_resolves_relative_path(self):
        result = resolve_raw_link_path("../skill-b/SKILL.md", self.skill_a, self.repo)
        self.assertEqual(result, self.skill_b.resolve())

    def test_resolves_repo_absolute_path(self):
        result = resolve_raw_link_path("skill-b/SKILL.md", self.skill_a, self.repo)
        self.assertEqual(result, self.skill_b.resolve())

    def test_resolves_os_absolute_path(self):
        result = resolve_raw_link_path(self.skill_b.as_posix(), self.skill_a, self.repo)
        self.assertEqual(result, self.skill_b.resolve())

    def test_resolves_nonexistent_relative_path_without_raising(self):
        result = resolve_raw_link_path("../nowhere.md", self.skill_a, self.repo)
        self.assertEqual(result, (self.repo / "nowhere.md").resolve())

    def test_applies_md_suffix_fallback(self):
        target = self.repo / "skill-b" / "guide.skill.md"
        target.write_text("---\n")
        result = resolve_raw_link_path("../skill-b/guide.skill", self.skill_a, self.repo)
        self.assertEqual(result, target.resolve())


if __name__ == "__main__":
    unittest.main()
