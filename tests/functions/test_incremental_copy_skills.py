"""Tests for IncrementalCopySkills."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_file_v2 import MarkdownSkillFile
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.functions.copy_skills.default_copy_skills import DefaultCopySkills
from ai_skill_manager.functions.copy_skills.incremental_copy_skills import IncrementalCopySkills
from ai_skill_manager.functions.file_discovery import FileDiscovery
from ai_skill_manager.functions.link_discovery import LinkDiscovery


class TestIncrementalCopySkills(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.target_dir = self.tmp / "target"
        self.copy_skills = IncrementalCopySkills(DefaultCopySkills(), version="1.0.0")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _discovered_skill(self, name: str, content: str, known_skills: dict | None = None) -> Skill:
        folder = self.tmp / name
        folder.mkdir(exist_ok=True)
        (folder / "SKILL.md").write_text(content)
        skill = Skill(name=name, path=folder, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        FileDiscovery().discover(skill)
        link_discovery = LinkDiscovery()
        for skill_file in skill.files:
            if not isinstance(skill_file, MarkdownSkillFile):
                continue
            links, _errors = link_discovery.discover(
                skill.file_absolute_path(skill_file),
                repo_path=self.tmp,
                known_skills=known_skills or {},
                queue=[],
                add_relations=False,
            )
            skill_file.links.extend(links)
        return skill

    def test_first_sync_copies_everything(self):
        skill = self._discovered_skill("skill-a", "---\nname: skill-a\n---\n# A\n")

        copied_dirs = self.copy_skills.copy({"skill-a": skill}, self.target_dir, self.tmp, self.target_dir)

        self.assertTrue((copied_dirs["skill-a"] / "SKILL.md").exists())

    def test_second_sync_skips_unchanged_skill(self):
        skill = self._discovered_skill("skill-a", "---\nname: skill-a\n---\n# A\n")
        self.copy_skills.copy({"skill-a": skill}, self.target_dir, self.tmp, self.target_dir)

        target_file = self.target_dir / "skill-a" / "SKILL.md"
        target_file.write_text("---\nname: skill-a\n---\n# stale marker\n")

        skill_again = self._discovered_skill("skill-a", "---\nname: skill-a\n---\n# A\n")
        self.copy_skills.copy({"skill-a": skill_again}, self.target_dir, self.tmp, self.target_dir)

        self.assertIn("# stale marker", target_file.read_text())

    def test_recopies_when_source_changes(self):
        skill = self._discovered_skill("skill-a", "---\nname: skill-a\n---\n# A\n")
        self.copy_skills.copy({"skill-a": skill}, self.target_dir, self.tmp, self.target_dir)

        target_file = self.target_dir / "skill-a" / "SKILL.md"
        target_file.write_text("---\nname: skill-a\n---\n# stale marker\n")

        shutil.rmtree(self.tmp / "skill-a")
        changed_skill = self._discovered_skill("skill-a", "---\nname: skill-a\n---\n# A changed\n")
        self.copy_skills.copy({"skill-a": changed_skill}, self.target_dir, self.tmp, self.target_dir)

        self.assertIn("# A changed", target_file.read_text())

    def test_recopies_when_version_changes(self):
        skill = self._discovered_skill("skill-a", "---\nname: skill-a\n---\n# A\n")
        self.copy_skills.copy({"skill-a": skill}, self.target_dir, self.tmp, self.target_dir)

        target_file = self.target_dir / "skill-a" / "SKILL.md"
        target_file.write_text("---\nname: skill-a\n---\n# stale marker\n")

        new_version_copy_skills = IncrementalCopySkills(DefaultCopySkills(), version="2.0.0")
        skill_again = self._discovered_skill("skill-a", "---\nname: skill-a\n---\n# A\n")
        new_version_copy_skills.copy({"skill-a": skill_again}, self.target_dir, self.tmp, self.target_dir)

        self.assertNotIn("# stale marker", target_file.read_text())

    def test_unchanged_skill_still_resolves_in_changed_skills_links(self):
        skill_b = self._discovered_skill("skill-b", "---\nname: skill-b\n---\n# B\n")
        self.copy_skills.copy({"skill-b": skill_b}, self.target_dir, self.tmp, self.target_dir)

        skill_b_again = self._discovered_skill("skill-b", "---\nname: skill-b\n---\n# B\n")
        skill_a = self._discovered_skill(
            "skill-a", "---\nname: skill-a\n---\n[b](../skill-b/SKILL.md)\n",
            known_skills={"skill-b": skill_b_again},
        )
        copied_dirs = self.copy_skills.copy(
            {"skill-a": skill_a, "skill-b": skill_b_again}, self.target_dir, self.tmp, self.target_dir,
        )

        content = (copied_dirs["skill-a"] / "SKILL.md").read_text()
        self.assertIn("[b](skill-b/SKILL.md)", content)


if __name__ == "__main__":
    unittest.main()
