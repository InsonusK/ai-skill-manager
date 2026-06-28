"""Tests for Validator aggregation."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import Skill, SkillFormat
from ai_skill_manager.entities.source import LocalSource
from ai_skill_manager.validators import Validator
from ai_skill_manager.validators.models import ValidationError, ValidationResult, ValidationSeverity
from ai_skill_manager.validators.rules.abs_validation_rule import absValidationRule


class AlwaysError(absValidationRule):
    def version(self) -> str:
        return "1.0.0"

    def validate(self, skills):
        return {skill: ValidationResult.single(ValidationError("err", ValidationSeverity.ERROR)) for skill in skills}


class AlwaysWarning(absValidationRule):
    def version(self) -> str:
        return "1.0.0"

    def validate(self, skills):
        return {skill: ValidationResult.single(ValidationError("warn", ValidationSeverity.WARNING)) for skill in skills}


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.skill_file = self.tmpdir / "guide.skill.md"
        self.skill_file.write_text("---\nname: guide\n---\n# Guide\n")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill(self):
        return Skill(
            file_path=self.skill_file,
            folder_path=None,
            format=SkillFormat.HumanFlat,
            source=LocalSource(scan_path=self.tmpdir),
            source_path=self.tmpdir,
        )

    def test_unique_rule_names_required(self):
        with self.assertRaises(AssertionError):
            Validator(rule_list=[AlwaysError(), AlwaysError()])

    def test_empty_skills_returns_empty_report(self):
        validator = Validator(rule_list=[])
        report = validator.validate([])
        self.assertFalse(report.has_errors)
        self.assertEqual(report.errors, {})

    def test_aggregate_errors_and_warnings(self):
        skill = self._skill()
        validator = Validator(rule_list=[AlwaysError(), AlwaysWarning()])
        report = validator.validate([skill])
        self.assertTrue(report.has_errors)
        self.assertIn(skill, report.errors)

    def test_progress_callback_called(self):
        skill = self._skill()
        validator = Validator(rule_list=[AlwaysError(), AlwaysWarning()])
        events = []
        validator.validate([skill], progress=lambda *args: events.append(args))
        self.assertEqual(
            events,
            [
                ("validate", 0, 2),
                ("validate", 1, 2),
                ("validate", 2, 2),
            ],
        )


if __name__ == "__main__":
    unittest.main()
