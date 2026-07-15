"""Tests for is_kebab_case."""

import unittest

from ai_skill_manager.entities.skill_name import is_kebab_case


class TestIsKebabCase(unittest.TestCase):
    def test_accepts_simple_kebab_case(self):
        self.assertTrue(is_kebab_case("my-skill"))

    def test_accepts_single_word(self):
        self.assertTrue(is_kebab_case("skill"))

    def test_accepts_digits(self):
        self.assertTrue(is_kebab_case("skill-2"))

    def test_rejects_empty_string(self):
        self.assertFalse(is_kebab_case(""))

    def test_rejects_leading_dash(self):
        self.assertFalse(is_kebab_case("-skill"))

    def test_rejects_trailing_dash(self):
        self.assertFalse(is_kebab_case("skill-"))

    def test_rejects_triple_dash(self):
        self.assertFalse(is_kebab_case("skill---name"))

    def test_accepts_double_dash(self):
        self.assertTrue(is_kebab_case("skill--name"))

    def test_rejects_uppercase(self):
        self.assertFalse(is_kebab_case("My-Skill"))

    def test_accepts_leading_digit(self):
        self.assertTrue(is_kebab_case("2-skill"))

    def test_rejects_underscore(self):
        self.assertFalse(is_kebab_case("my_skill"))


if __name__ == "__main__":
    unittest.main()
