"""Tests for FileLinkFactory."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.service.link_discovery import search_links_in_content
from ai_skill_manager.entities.link.file_link_factory import FileLinkFactory
from ai_skill_manager.entities.link.link_target import ExternalLinkTarget, SkillLinkTarget
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill


class TestFileLinkFactory(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.factory = FileLinkFactory()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _parsed_link(self, file_path: Path, content: str):
        file_path.write_text(content, encoding="utf-8")
        return search_links_in_content(content)[0]

    def test_resolves_to_already_known_skill(self):
        skill_b_dir = self.tmp / "skill-b"
        skill_b_dir.mkdir()
        (skill_b_dir / "SKILL.md").write_text("---\n")
        skill_b = Skill(name="skill-b", path=skill_b_dir, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))

        skill_a_file = self.tmp / "skill-a" / "SKILL.md"
        skill_a_file.parent.mkdir()
        raw_link = self._parsed_link(skill_a_file, "[b](../skill-b/SKILL.md)\n")

        file_link, error = self.factory.build(
            raw_link, file_absolute_path=skill_a_file, repo_path=self.tmp,
            known_skills={"skill-b": skill_b}, queue=[], add_relations=False,
        )

        self.assertIsNone(error)
        self.assertEqual(file_link.target, SkillLinkTarget(skill_name="skill-b", relative_path=Path("SKILL.md")))

    def test_external_file_resolves_to_external_target(self):
        skill_a_file = self.tmp / "skill-a" / "SKILL.md"
        skill_a_file.parent.mkdir()
        (self.tmp / "shared.md").write_text("# Shared\n")
        raw_link = self._parsed_link(skill_a_file, "[shared](../shared.md)\n")

        file_link, error = self.factory.build(
            raw_link, file_absolute_path=skill_a_file, repo_path=self.tmp,
            known_skills={}, queue=[], add_relations=False,
        )

        self.assertIsNone(error)
        self.assertEqual(file_link.target, ExternalLinkTarget(file_name="shared.md", repo_absolute_path=Path("shared.md")))

    def test_unknown_skill_queued_when_add_relations_enabled(self):
        skill_c_dir = self.tmp / "skill-c"
        skill_c_dir.mkdir()
        (skill_c_dir / "SKILL.md").write_text("---\nname: skill-c\n---\n")

        skill_a_file = self.tmp / "skill-a" / "SKILL.md"
        skill_a_file.parent.mkdir()
        raw_link = self._parsed_link(skill_a_file, "[c](../skill-c/SKILL.md)\n")

        queue = []
        file_link, error = self.factory.build(
            raw_link, file_absolute_path=skill_a_file, repo_path=self.tmp,
            known_skills={}, queue=queue, add_relations=True,
        )

        self.assertIsNone(error)
        self.assertEqual(file_link.target, SkillLinkTarget(skill_name="skill-c", relative_path=Path("SKILL.md")))
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0].name, "skill-c")

    def test_unknown_skill_errors_when_add_relations_disabled(self):
        skill_c_dir = self.tmp / "skill-c"
        skill_c_dir.mkdir()
        (skill_c_dir / "SKILL.md").write_text("---\nname: skill-c\n---\n")

        skill_a_file = self.tmp / "skill-a" / "SKILL.md"
        skill_a_file.parent.mkdir()
        raw_link = self._parsed_link(skill_a_file, "[c](../skill-c/SKILL.md)\n")

        file_link, error = self.factory.build(
            raw_link, file_absolute_path=skill_a_file, repo_path=self.tmp,
            known_skills={}, queue=[], add_relations=False,
        )

        self.assertIsNone(file_link)
        self.assertIsNotNone(error)

    def test_missing_target_errors(self):
        skill_a_file = self.tmp / "skill-a" / "SKILL.md"
        skill_a_file.parent.mkdir()
        raw_link = self._parsed_link(skill_a_file, "[bad](../nowhere.md)\n")

        file_link, error = self.factory.build(
            raw_link, file_absolute_path=skill_a_file, repo_path=self.tmp,
            known_skills={}, queue=[], add_relations=False,
        )

        self.assertIsNone(file_link)
        self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()
