"""Tests for LinkTargetResolver."""

import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.link.link_target import SkillLinkTarget
from ai_skill_manager.entities.link.link_target_resolver import LinkTargetResolver
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill


class TestLinkTargetResolver(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.resolver = LinkTargetResolver()

    def _flat_skill(self, name: str) -> Skill:
        path = self.tmp / f"{name}.skill.md"
        path.write_text("---\n")
        return Skill(name=name, path=path, kind=SkillKind.flat)

    def _dir_skill(self, name: str) -> Skill:
        folder = self.tmp / name
        folder.mkdir()
        (folder / f"{name}.skill.md").write_text("---\n")
        return Skill(name=name, path=folder, kind=SkillKind.dir, main_file_relative_path=Path(f"{name}.skill.md"))

    def test_resolves_flat_skill_main_file(self):
        skill = self._flat_skill("guide")
        result = self.resolver.resolve(skill.path, [skill])
        self.assertEqual(result, SkillLinkTarget(skill_name="guide", relative_path=None))

    def test_resolves_dir_skill_folder_itself_to_main_file(self):
        skill = self._dir_skill("web")
        result = self.resolver.resolve(skill.path, [skill])
        self.assertEqual(result, SkillLinkTarget(skill_name="web", relative_path=Path("web.skill.md")))

    def test_resolves_dir_skill_main_file_directly(self):
        skill = self._dir_skill("web")
        result = self.resolver.resolve(skill.path / "web.skill.md", [skill])
        self.assertEqual(result, SkillLinkTarget(skill_name="web", relative_path=Path("web.skill.md")))

    def test_resolves_nested_file_in_dir_skill(self):
        skill = self._dir_skill("web")
        (skill.path / "docs").mkdir()
        nested = skill.path / "docs" / "extra.md"
        nested.write_text("# Extra\n")
        result = self.resolver.resolve(nested, [skill])
        self.assertEqual(result, SkillLinkTarget(skill_name="web", relative_path=Path("docs/extra.md")))

    def test_returns_none_when_path_belongs_to_no_known_skill(self):
        skill = self._dir_skill("web")
        orphan = self.tmp / "orphan.md"
        orphan.write_text("# Orphan\n")
        result = self.resolver.resolve(orphan, [skill])
        self.assertIsNone(result)

    def test_picks_correct_skill_among_several(self):
        a = self._dir_skill("a")
        b = self._dir_skill("b")
        result = self.resolver.resolve(b.path / "b.skill.md", [a, b])
        self.assertEqual(result.skill_name, "b")


if __name__ == "__main__":
    unittest.main()
