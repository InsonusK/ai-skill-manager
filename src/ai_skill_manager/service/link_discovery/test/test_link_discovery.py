"""Tests for LinkDiscovery."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.link.link_target import ExternalLinkTarget, SkillLinkTarget
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.functions.link_discovery import LinkDiscovery


class TestLinkDiscovery(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.discovery = LinkDiscovery()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_finds_link_to_known_skill(self):
        skill_b_dir = self.tmp / "skill-b"
        skill_b_dir.mkdir()
        (skill_b_dir / "SKILL.md").write_text("---\n")
        skill_b = Skill(name="skill-b", path=skill_b_dir, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))

        skill_a_file = self.tmp / "skill-a" / "SKILL.md"
        skill_a_file.parent.mkdir()
        skill_a_file.write_text("---\nname: skill-a\n---\n[b](../skill-b/SKILL.md)\n")

        links, errors = self.discovery.discover(
            skill_a_file, repo_path=self.tmp, known_skills={"skill-b": skill_b}, queue=[], add_relations=False,
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].target, SkillLinkTarget(skill_name="skill-b", relative_path=Path("SKILL.md")))

    def test_excludes_web_links(self):
        skill_a_file = self.tmp / "skill-a" / "SKILL.md"
        skill_a_file.parent.mkdir()
        skill_a_file.write_text("---\nname: skill-a\n---\n[ext](https://example.com)\n")

        links, errors = self.discovery.discover(
            skill_a_file, repo_path=self.tmp, known_skills={}, queue=[], add_relations=False,
        )

        self.assertEqual(links, [])
        self.assertEqual(errors, [])

    def test_excludes_links_in_examples_folder(self):
        examples_file = self.tmp / "examples" / "SKILL.md"
        examples_file.parent.mkdir()
        examples_file.write_text("---\nname: examples\n---\n[bad](../nowhere.md)\n")

        links, errors = self.discovery.discover(
            examples_file, repo_path=self.tmp, known_skills={}, queue=[], add_relations=False,
        )

        self.assertEqual(links, [])
        self.assertEqual(errors, [])

    def test_external_file_link_resolves(self):
        (self.tmp / "shared.md").write_text("# Shared\n")
        skill_a_file = self.tmp / "skill-a" / "SKILL.md"
        skill_a_file.parent.mkdir()
        skill_a_file.write_text("---\nname: skill-a\n---\n[shared](../shared.md)\n")

        links, errors = self.discovery.discover(
            skill_a_file, repo_path=self.tmp, known_skills={}, queue=[], add_relations=False,
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].target, ExternalLinkTarget(file_name="shared.md", repo_absolute_path=Path("shared.md")))

    def test_collects_error_for_broken_link_without_stopping(self):
        (self.tmp / "shared.md").write_text("# Shared\n")
        skill_a_file = self.tmp / "skill-a" / "SKILL.md"
        skill_a_file.parent.mkdir()
        skill_a_file.write_text(
            "---\nname: skill-a\n---\n[bad](../nowhere.md)\n[shared](../shared.md)\n"
        )

        links, errors = self.discovery.discover(
            skill_a_file, repo_path=self.tmp, known_skills={}, queue=[], add_relations=False,
        )

        self.assertEqual(len(errors), 1)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].target, ExternalLinkTarget(file_name="shared.md", repo_absolute_path=Path("shared.md")))


if __name__ == "__main__":
    unittest.main()
