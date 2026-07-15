"""Tests for compute_skill_hash (new model)."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.functions.file_discovery import discover as discover_files
from ai_skill_manager.functions.skill_hash import compute_skill_hash


class TestComputeSkillHash(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _discovered_flat_skill(self, content: str, filename: str = "guide.skill.md") -> Skill:
        md = self.tmp / filename
        md.write_text(content)
        skill = Skill(name="guide", path=md, kind=SkillKind.flat)
        skill.files.extend(discover_files(skill))
        return skill

    def test_same_content_same_hash(self):
        a = self._discovered_flat_skill("---\nname: guide\n---\n# Guide\n")
        b = self._discovered_flat_skill("---\nname: guide\n---\n# Guide\n")
        self.assertEqual(compute_skill_hash(a), compute_skill_hash(b))

    def test_different_content_different_hash(self):
        a = self._discovered_flat_skill("---\nname: guide\n---\n# Guide\n", filename="a.skill.md")
        b = self._discovered_flat_skill("---\nname: guide\n---\n# Guide v2\n", filename="b.skill.md")
        self.assertNotEqual(compute_skill_hash(a), compute_skill_hash(b))

    def test_dir_skill_hash_changes_when_nested_file_changes(self):
        folder = self.tmp / "web"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: web\n---\n")
        (folder / "data.json").write_text("{}")
        skill = Skill(name="web", path=folder, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        skill.files.extend(discover_files(skill))
        before = compute_skill_hash(skill)

        (folder / "data.json").write_text('{"changed": true}')
        skill2 = Skill(name="web", path=folder, kind=SkillKind.dir, main_file_relative_path=Path("SKILL.md"))
        skill2.files.extend(discover_files(skill2))
        after = compute_skill_hash(skill2)

        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
