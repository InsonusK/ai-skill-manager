"""Tests for CopySkills implementations (DefaultCopySkills, ClaudePropertyCopySkills)."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_file_v2 import MarkdownSkillFile
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.service.file_discovery import discover as discover_files
from ai_skill_manager.service.link_discovery.link_discovery import LinkDiscovery
from ai_skill_manager.models import SkillRelationQueuer
from ai_skill_manager.functions.copy_skills.claude_property_copy_skills import ClaudePropertyCopySkills
from ai_skill_manager.functions.copy_skills.default_copy_skills import DefaultCopySkills


class TestDefaultCopySkills(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.target_dir = self.tmp / "target"
        self.copy_skills = DefaultCopySkills()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _discovered_skill(self, name: str, content: str, known_skills: dict | None = None) -> Skill:
        folder = self.tmp / name
        folder.mkdir()
        (folder / "SKILL.md").write_text(content)
        skill = Skill(name=name, path=folder, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        skill.files.extend(discover_files(skill))
        link_discovery = LinkDiscovery()
        for skill_file in skill.files:
            if not isinstance(skill_file, MarkdownSkillFile):
                continue
            links, _errors = link_discovery.discover(
                skill.file_absolute_path(skill_file),
                repo_path=self.tmp,
                known_skills=known_skills or {},
                skill_relation_queuer=SkillRelationQueuer(add_relations=False),
            )
            skill_file.links.extend(links)
        return skill

    def test_copies_and_rewrites_cross_skill_links(self):
        skill_b = self._discovered_skill("skill-b", "---\nname: skill-b\n---\n# B\n")
        skill_a = self._discovered_skill(
            "skill-a", "---\nname: skill-a\n---\n[b](../skill-b/SKILL.md)\n", known_skills={"skill-b": skill_b},
        )
        skills = {"skill-a": skill_a, "skill-b": skill_b}

        copied_dirs = self.copy_skills.copy(skills, self.target_dir, source_repo_path=self.tmp, output_repo_path=self.target_dir)

        self.assertEqual(set(copied_dirs), {"skill-a", "skill-b"})
        content = (copied_dirs["skill-a"] / "SKILL.md").read_text()
        self.assertIn("[b](skill-b/SKILL.md)", content)


class TestClaudePropertyCopySkills(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.target_dir = self.tmp / "target"
        self.copy_skills = ClaudePropertyCopySkills(DefaultCopySkills())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_moves_non_native_frontmatter_fields_to_body(self):
        folder = self.tmp / "skill-a"
        folder.mkdir()
        (folder / "SKILL.md").write_text(
            "---\nname: skill-a\nwhenToUse: use it\ncustomField: value\n---\n# A\n"
        )
        skill = Skill(name="skill-a", path=folder, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        skill.files.extend(discover_files(skill))

        copied_dirs = self.copy_skills.copy(
            {"skill-a": skill}, self.target_dir, source_repo_path=self.tmp, output_repo_path=self.target_dir,
        )

        content = (copied_dirs["skill-a"] / "SKILL.md").read_text()
        self.assertIn("when_to_use: use it", content)
        self.assertIn("customField: value", content)
        self.assertIn("## Metadata", content)


if __name__ == "__main__":
    unittest.main()
