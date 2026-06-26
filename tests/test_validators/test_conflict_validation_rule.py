"""Tests for the conflict validation rule."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.validators.models import ValidationSeverity
from ai_skill_manager.validators.rules.conflict_validation_rule import ConflictValidationRule


class TestConflictValidationRule(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _skill(self, name: str, suffix: str = "") -> Skill:
        skill_file = self.tmp / f"{name}{suffix}.skill.md"
        skill_file.write_text(f"---\nname: {name}\n---\n# {name}\n")
        return Skill(
            file_path=skill_file,
            folder_path=None,
            source_path=self.tmp,
            source=LocalSource(scan_path=self.tmp),
            format=SkillFormat.HumanFlat,
        )

    def test_no_conflicts_returns_empty(self):
        rule = ConflictValidationRule()
        results = rule.validate([self._skill("a"), self._skill("b")])
        self.assertEqual(results, {})

    def test_duplicate_names_report_errors(self):
        rule = ConflictValidationRule()
        first = self._skill("same", "_a")
        second = self._skill("same", "_b")

        results = rule.validate([first, second])

        self.assertEqual(len(results), 2)
        self.assertIn(first, results)
        self.assertIn(second, results)
        for result in results.values():
            self.assertTrue(result.has_errors)
            self.assertEqual(result.severity, ValidationSeverity.ERROR)

    def test_skills_without_name_are_ignored(self):
        rule = ConflictValidationRule()
        unnamed = self._skill("")
        named = self._skill("named")

        results = rule.validate([unnamed, named])

        self.assertEqual(results, {})


if __name__ == "__main__":
    unittest.main()
