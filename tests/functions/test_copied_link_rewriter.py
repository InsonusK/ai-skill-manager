"""Tests for CopiedLinkRewriter."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_file_v2 import MarkdownSkillFile
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.functions.external_file_copier import ExternalFileCopier
from ai_skill_manager.service.file_discovery import discover as discover_files
from ai_skill_manager.service.link_discovery.link_discovery import LinkDiscovery
from ai_skill_manager.models import SkillRelationQueuer
from ai_skill_manager.functions.copied_link_rewriter import CopiedLinkRewriter
from ai_skill_manager.functions.skill_file_copier import SkillFileCopier


class TestCopiedLinkRewriter(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        # EN: Discovery resolves raw link text against the *source* tree;
        # the rewriter formats output relative to the *destination*'s
        # conceptual repo root. They are unrelated paths in general.
        # RU: Обнаружение резолвит сырой текст ссылки относительно
        # *исходного* дерева; переписыватель форматирует вывод относительно
        # концептуального корня репозитория *назначения*. В общем случае
        # это никак не связанные пути.
        self.source_repo_path = self.tmp
        self.target_dir = self.tmp / "target"
        self.output_repo_path = self.target_dir
        self.link_discovery = LinkDiscovery()
        self.skill_copier = SkillFileCopier()
        self.external_copier = ExternalFileCopier()
        self.rewriter = CopiedLinkRewriter(self.external_copier)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _discover_and_copy(self, skill: Skill, known_skills: dict) -> Path:
        skill.files.extend(discover_files(skill))
        for skill_file in skill.files:
            if not isinstance(skill_file, MarkdownSkillFile):
                continue
            links, _errors = self.link_discovery.discover(
                skill.file_absolute_path(skill_file),
                repo_path=self.source_repo_path,
                known_skills=known_skills,
                skill_relation_queuer=SkillRelationQueuer(add_relations=False),
            )
            skill_file.links.extend(links)
        return self.skill_copier.copy(skill, self.target_dir)

    def test_rewrites_link_to_another_skills_main_file(self):
        skill_b_dir = self.tmp / "skill-b"
        skill_b_dir.mkdir()
        (skill_b_dir / "SKILL.md").write_text("---\n")
        skill_b = Skill(name="skill-b", path=skill_b_dir, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        skill_b_target_dir = self._discover_and_copy(skill_b, {})

        skill_a_dir = self.tmp / "skill-a"
        skill_a_dir.mkdir()
        (skill_a_dir / "SKILL.md").write_text("---\nname: skill-a\n---\n[b](../skill-b/SKILL.md)\n")
        skill_a = Skill(name="skill-a", path=skill_a_dir, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        skill_a_target_dir = self._discover_and_copy(skill_a, {"skill-b": skill_b})

        known_skills = {"skill-a": skill_a, "skill-b": skill_b}
        copied_skill_dirs = {"skill-a": skill_a_target_dir, "skill-b": skill_b_target_dir}
        count = self.rewriter.rewrite(skill_a, skill_a_target_dir, self.target_dir, self.source_repo_path, self.output_repo_path, copied_skill_dirs, known_skills)

        self.assertEqual(count, 1)
        content = (skill_a_target_dir / "SKILL.md").read_text()
        self.assertIn("[b](skill-b/SKILL.md)", content)

    def test_rewrites_link_to_nested_file_in_another_skill(self):
        skill_b_dir = self.tmp / "skill-b"
        skill_b_dir.mkdir()
        (skill_b_dir / "SKILL.md").write_text("---\n")
        (skill_b_dir / "docs").mkdir()
        (skill_b_dir / "docs" / "extra.md").write_text("# Extra\n")
        skill_b = Skill(name="skill-b", path=skill_b_dir, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        skill_b_target_dir = self._discover_and_copy(skill_b, {})

        skill_a_dir = self.tmp / "skill-a"
        skill_a_dir.mkdir()
        (skill_a_dir / "SKILL.md").write_text("---\nname: skill-a\n---\n[extra](../skill-b/docs/extra.md)\n")
        skill_a = Skill(name="skill-a", path=skill_a_dir, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        skill_a_target_dir = self._discover_and_copy(skill_a, {"skill-b": skill_b})

        known_skills = {"skill-a": skill_a, "skill-b": skill_b}
        copied_skill_dirs = {"skill-a": skill_a_target_dir, "skill-b": skill_b_target_dir}
        self.rewriter.rewrite(skill_a, skill_a_target_dir, self.target_dir, self.source_repo_path, self.output_repo_path, copied_skill_dirs, known_skills)

        content = (skill_a_target_dir / "SKILL.md").read_text()
        self.assertIn("[extra](skill-b/docs/extra.md)", content)

    def test_rewrites_external_file_link_and_copies_it(self):
        (self.tmp / "shared.md").write_text("# Shared\n")
        skill_a_dir = self.tmp / "skill-a"
        skill_a_dir.mkdir()
        (skill_a_dir / "SKILL.md").write_text("---\nname: skill-a\n---\n[shared](../shared.md)\n")
        skill_a = Skill(name="skill-a", path=skill_a_dir, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        skill_a_target_dir = self._discover_and_copy(skill_a, {})

        known_skills = {"skill-a": skill_a}
        copied_skill_dirs = {"skill-a": skill_a_target_dir}
        count = self.rewriter.rewrite(skill_a, skill_a_target_dir, self.target_dir, self.source_repo_path, self.output_repo_path, copied_skill_dirs, known_skills)

        self.assertEqual(count, 1)
        content = (skill_a_target_dir / "SKILL.md").read_text()
        self.assertIn("[shared](files/shared.md)", content)
        self.assertTrue((self.target_dir / "files" / "shared.md").exists())


if __name__ == "__main__":
    unittest.main()
