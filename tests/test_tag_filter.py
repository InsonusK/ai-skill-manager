"""Tests for tag expression parsing and filtering."""

import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.source import LocalSource
from ai_skill_manager.service.discover import discover
from ai_skill_manager.functions.tag_filter import (
    compile_tag_expression,
    filter_skills_by_tags,
    matches_tag_expressions,
)


class TestCompileTagExpression(unittest.TestCase):
    def test_simple_tag(self):
        matcher = compile_tag_expression("python")
        self.assertTrue(matcher({"python"}))
        self.assertFalse(matcher({"cli"}))

    def test_and(self):
        matcher = compile_tag_expression("python & cli")
        self.assertTrue(matcher({"python", "cli"}))
        self.assertFalse(matcher({"python"}))
        self.assertFalse(matcher({"cli"}))

    def test_or(self):
        matcher = compile_tag_expression("python | cli")
        self.assertTrue(matcher({"python"}))
        self.assertTrue(matcher({"cli"}))
        self.assertFalse(matcher({"other"}))

    def test_not(self):
        matcher = compile_tag_expression("!python")
        self.assertTrue(matcher({"cli"}))
        self.assertFalse(matcher({"python"}))

    def test_parentheses(self):
        matcher = compile_tag_expression("(python & cli) | web")
        self.assertTrue(matcher({"python", "cli"}))
        self.assertTrue(matcher({"web"}))
        self.assertFalse(matcher({"python"}))

    def test_and_higher_precedence_than_or(self):
        matcher = compile_tag_expression("python & cli | web")
        # '&' has higher precedence than '|': parses as (python & cli) | web.
        self.assertTrue(matcher({"python", "cli"}))
        self.assertTrue(matcher({"python", "web"}))
        self.assertTrue(matcher({"cli", "web"}))
        self.assertFalse(matcher({"python"}))

    def test_not_with_and(self):
        matcher = compile_tag_expression("python & !cli")
        self.assertTrue(matcher({"python", "web"}))
        self.assertFalse(matcher({"python", "cli"}))

    def test_hierarchical_tag_matches_exact(self):
        matcher = compile_tag_expression("a/b/c")
        self.assertTrue(matcher({"a/b/c"}))

    def test_hierarchical_tag_matches_components_and_segments(self):
        matcher = compile_tag_expression("a/b/c")
        self.assertTrue(matcher({"a"}))
        self.assertTrue(matcher({"b"}))
        self.assertTrue(matcher({"c"}))
        self.assertTrue(matcher({"a/b"}))
        self.assertTrue(matcher({"b/c"}))
        self.assertTrue(matcher({"a/b/c"}))
        self.assertFalse(matcher({"a/c"}))
        self.assertFalse(matcher({"d"}))

    def test_hierarchical_two_components(self):
        matcher = compile_tag_expression("a/b")
        self.assertTrue(matcher({"a"}))
        self.assertTrue(matcher({"b"}))
        self.assertTrue(matcher({"a/b"}))
        self.assertFalse(matcher({"a/b/c"}))

    def test_invalid_empty(self):
        with self.assertRaises(ValueError):
            compile_tag_expression("")

    def test_invalid_unexpected_token(self):
        with self.assertRaises(ValueError):
            compile_tag_expression("python &")

    def test_invalid_missing_closing_paren(self):
        with self.assertRaises(ValueError):
            compile_tag_expression("(python & cli")


class TestMatchesTagExpressions(unittest.TestCase):
    def test_empty_expressions_match_all(self):
        self.assertTrue(matches_tag_expressions(["python"], []))

    def test_multiple_expressions_all_must_match(self):
        self.assertTrue(
            matches_tag_expressions(
                ["python", "cli"],
                ["python", "cli | web"],
            )
        )
        self.assertFalse(
            matches_tag_expressions(
                ["python"],
                ["python", "cli"],
            )
        )

    def test_multiple_expressions_use_hierarchical_tags(self):
        self.assertTrue(
            matches_tag_expressions(
                ["a/b", "b/c"],
                ["a/b", "b/c"],
            )
        )


class TestFilterSkillsByTags(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.source_dir = self.tmpdir / "source"
        self.source_dir.mkdir()

        (self.source_dir / "py.skill.md").write_text(
            "---\nname: py\ntags:\n  - python\n  - cli\n---\n"
        )
        (self.source_dir / "web.skill.md").write_text(
            "---\nname: web\ntags:\n  - web\n---\n"
        )
        (self.source_dir / "notags.skill.md").write_text("---\nname: notags\n---\n")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir)

    def test_filter_keeps_matching_skills(self):
        skills = discover([LocalSource(scan_path=self.source_dir)])
        self.assertEqual(len(skills), 3)

        filtered = filter_skills_by_tags(skills, ["python"])
        self.assertEqual({s.name for s in filtered}, {"py"})

    def test_filter_with_and(self):
        skills = discover([LocalSource(scan_path=self.source_dir)])
        filtered = filter_skills_by_tags(skills, ["python & cli"])
        self.assertEqual({s.name for s in filtered}, {"py"})

    def test_filter_with_not(self):
        skills = discover([LocalSource(scan_path=self.source_dir)])
        filtered = filter_skills_by_tags(skills, ["!python"])
        self.assertEqual({s.name for s in filtered}, {"web", "notags"})

    def test_no_expressions_returns_all(self):
        skills = discover([LocalSource(scan_path=self.source_dir)])
        self.assertEqual(len(filter_skills_by_tags(skills, [])), 3)


if __name__ == "__main__":
    unittest.main()
