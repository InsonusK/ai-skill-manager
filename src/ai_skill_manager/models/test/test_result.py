"""Tests for the generic Result model."""

import unittest

from ai_skill_manager.models import Result


class TestResult(unittest.TestCase):
    def test_unpacks_like_a_tuple(self):
        result = Result(value=["a", "b"], errors=[])

        value, errors = result

        self.assertEqual(value, ["a", "b"])
        self.assertEqual(errors, [])

    def test_has_errors_true_when_errors_present(self):
        result = Result(value=None, errors=["boom"])
        self.assertTrue(result.has_errors)

    def test_has_errors_false_when_no_errors(self):
        result = Result(value=None, errors=[])
        self.assertFalse(result.has_errors)

    def test_as_tuple(self):
        result = Result(value=42, errors=["oops"])
        self.assertEqual(result.as_tuple(), (42, ["oops"]))


if __name__ == "__main__":
    unittest.main()
