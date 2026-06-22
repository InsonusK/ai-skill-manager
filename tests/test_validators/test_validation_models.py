"""Tests for validation model classes."""

import unittest

from ai_skill_manager.validators.models import ValidationError, ValidationReport, ValidationResult, ValidationSeverity


class TestValidationError(unittest.TestCase):
    def test_str_formats_message(self):
        err = ValidationError("missing {field}", ValidationSeverity.ERROR, {"field": "name"})
        self.assertEqual(str(err), "missing name")

    def test_repr_contains_message(self):
        err = ValidationError("missing", ValidationSeverity.WARNING)
        self.assertIn("missing", repr(err))

    def test_to_log_contains_severity(self):
        err = ValidationError("oops", ValidationSeverity.ERROR)
        self.assertIn("ERROR", err.to_log())
        self.assertIn("oops", err.to_log())


class TestValidationResult(unittest.TestCase):
    def test_single_factory(self):
        err = ValidationError("x", ValidationSeverity.ERROR)
        result = ValidationResult.single(err)
        self.assertTrue(result.has_errors)
        self.assertFalse(result.has_warnings)

    def test_severity_warning(self):
        err = ValidationError("x", ValidationSeverity.WARNING)
        result = ValidationResult([err])
        self.assertFalse(result.has_errors)
        self.assertTrue(result.has_warnings)
        self.assertEqual(result.severity, ValidationSeverity.WARNING)

    def test_severity_success(self):
        result = ValidationResult([])
        self.assertFalse(result.has_errors)
        self.assertFalse(result.has_warnings)
        self.assertEqual(result.severity, ValidationSeverity.SUCCESS)


class TestValidationReport(unittest.TestCase):
    def test_empty_report_has_no_errors(self):
        report = ValidationReport({})
        self.assertFalse(report.has_errors)
        self.assertEqual(report.errors, {})

    def test_errors_filters_only_error_results(self):
        err = ValidationError("x", ValidationSeverity.ERROR)
        warn = ValidationError("y", ValidationSeverity.WARNING)
        result = ValidationReport({
            "skill": {
                "rule1": ValidationResult([err]),
                "rule2": ValidationResult([warn]),
            }
        })
        self.assertTrue(result.has_errors)
        errors = result.errors
        self.assertIn("skill", errors)
        self.assertIn("rule1", errors["skill"])
        self.assertNotIn("rule2", errors["skill"])


if __name__ == "__main__":
    unittest.main()
