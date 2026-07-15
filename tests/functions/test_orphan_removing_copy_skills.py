"""Tests for OrphanRemovingCopySkills."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_file_v2 import MarkdownSkillFile
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.functions.copy_skills.default_copy_skills import DefaultCopySkills
from ai_skill_manager.functions.copy_skills.orphan_removing_copy_skills import OrphanRemovingCopySkills
from ai_skill_manager.functions.file_discovery import discover as discover_files
from ai_skill_manager.functions.link_discovery import LinkDiscovery
from ai_skill_manager.functions.managed_state import tag_managed


class TestOrphanRemovingCopySkills(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.target_dir = self.tmp / "target"
        self.copy_skills = OrphanRemovingCopySkills(DefaultCopySkills())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _discovered_skill(self, name: str, content: str) -> Skill:
        folder = self.tmp / name
        folder.mkdir(exist_ok=True)
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
                known_skills={},
                queue=[],
                add_relations=False,
            )
            skill_file.links.extend(links)
        return skill

    def test_removes_managed_skill_no_longer_present(self):
        self.target_dir.mkdir(parents=True)
        orphan = self.target_dir / "orphan"
        orphan.mkdir()
        tag_managed(orphan)

        skill = self._discovered_skill("skill-a", "---\nname: skill-a\n---\n# A\n")
        self.copy_skills.copy({"skill-a": skill}, self.target_dir, self.tmp, self.target_dir)

        self.assertFalse(orphan.exists())
        self.assertTrue((self.target_dir / "skill-a").exists())

    def test_keeps_unmanaged_directories(self):
        self.target_dir.mkdir(parents=True)
        unmanaged = self.target_dir / "hand-written"
        unmanaged.mkdir()

        skill = self._discovered_skill("skill-a", "---\nname: skill-a\n---\n# A\n")
        self.copy_skills.copy({"skill-a": skill}, self.target_dir, self.tmp, self.target_dir)

        self.assertTrue(unmanaged.exists())

    def test_keeps_shared_files_directory(self):
        (self.tmp / "extra.md").write_text("# Extra\n")
        skill = self._discovered_skill("skill-a", "---\nname: skill-a\n---\n[extra](../extra.md)\n")

        self.copy_skills.copy({"skill-a": skill}, self.target_dir, self.tmp, self.target_dir)

        self.assertTrue((self.target_dir / "files" / "extra.md").exists())


if __name__ == "__main__":
    unittest.main()
