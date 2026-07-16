"""Tests for LinkTargetResolver."""

import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.link.link_target import SkillLinkTarget
from ai_skill_manager.service.link_discovery.link_target_resolver import LinkTargetResolver
from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill


def _by_name(*skills: Skill) -> dict:
    return {skill.name: skill for skill in skills}


class TestLinkTargetResolver(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.resolver = LinkTargetResolver()

    def _flat_skill(self, name: str) -> Skill:
        path = self.tmp / f"{name}.skill.md"
        path.write_text("---\n")
        return Skill(name=name, path=path, kind=SkillKind.flat)

    def _dir_skill(self, name: str, parent: Path = None) -> Skill:
        folder = (parent or self.tmp) / name
        folder.mkdir()
        (folder / f"{name}.skill.md").write_text("---\n")
        return Skill(name=name, path=folder, kind=SkillKind.dir, main_file_relative_path=Path(f"{name}.skill.md"))

    def test_resolves_flat_skill_main_file(self):
        skill = self._flat_skill("guide")
        result = self.resolver.resolve(skill.path, _by_name(skill))
        self.assertEqual(result, SkillLinkTarget(skill_name="guide", relative_path=None))

    def test_resolves_dir_skill_folder_itself_to_main_file(self):
        skill = self._dir_skill("web")
        result = self.resolver.resolve(skill.path, _by_name(skill))
        self.assertEqual(result, SkillLinkTarget(skill_name="web", relative_path=Path("web.skill.md")))

    def test_resolves_dir_skill_main_file_directly(self):
        skill = self._dir_skill("web")
        result = self.resolver.resolve(skill.path / "web.skill.md", _by_name(skill))
        self.assertEqual(result, SkillLinkTarget(skill_name="web", relative_path=Path("web.skill.md")))

    def test_resolves_nested_file_in_dir_skill(self):
        skill = self._dir_skill("web")
        (skill.path / "docs").mkdir()
        nested = skill.path / "docs" / "extra.md"
        nested.write_text("# Extra\n")
        result = self.resolver.resolve(nested, _by_name(skill))
        self.assertEqual(result, SkillLinkTarget(skill_name="web", relative_path=Path("docs/extra.md")))

    def test_returns_none_when_path_belongs_to_no_known_skill(self):
        skill = self._dir_skill("web")
        orphan = self.tmp / "orphan.md"
        orphan.write_text("# Orphan\n")
        result = self.resolver.resolve(orphan, _by_name(skill))
        self.assertIsNone(result)

    def test_picks_correct_skill_among_several(self):
        a = self._dir_skill("a")
        b = self._dir_skill("b")
        result = self.resolver.resolve(b.path / "b.skill.md", _by_name(a, b))
        self.assertEqual(result.skill_name, "b")

    def test_sibling_skill_does_not_affect_resolution_of_unrelated_path(self):
        parent = self.tmp / "parent"
        parent.mkdir()
        a = self._dir_skill("a", parent=parent)
        b = self._dir_skill("b", parent=parent)
        orphan = parent / "notes.md"
        orphan.write_text("# notes\n")

        result = self.resolver.resolve(orphan, _by_name(a, b))

        self.assertIsNone(result)

    def test_reuses_index_across_calls_for_the_same_known_skills_object(self):
        skill = self._dir_skill("web")
        known_skills = _by_name(skill)

        self.resolver.resolve(skill.path / "web.skill.md", known_skills)
        index_after_first = self.resolver._index

        self.resolver.resolve(skill.path, known_skills)
        index_after_second = self.resolver._index

        # Same known_skills object across both calls - proof the index was
        # built once and reused, not rebuilt per lookup.
        self.assertIs(index_after_first, index_after_second)

    def test_rebuilds_index_when_known_skills_object_changes(self):
        a = self._dir_skill("a")
        b = self._dir_skill("b")

        self.resolver.resolve(a.path, _by_name(a))
        first_index = self.resolver._index

        result = self.resolver.resolve(b.path, _by_name(a, b))

        self.assertEqual(result.skill_name, "b")
        self.assertIsNot(self.resolver._index, first_index)

    def test_resolve_one_matches_a_single_candidate_skill(self):
        skill = self._dir_skill("web")
        nested = skill.path / "extra.md"
        nested.write_text("# extra\n")

        result = self.resolver.resolve_one(nested, skill)

        self.assertEqual(result, SkillLinkTarget(skill_name="web", relative_path=Path("extra.md")))

    def test_resolve_one_returns_none_for_unrelated_path(self):
        skill = self._dir_skill("web")
        orphan = self.tmp / "orphan.md"
        orphan.write_text("# orphan\n")

        result = self.resolver.resolve_one(orphan, skill)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
