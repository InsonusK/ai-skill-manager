"""Tests for sync result formatter."""

import unittest

from ai_skill_manager.cli.formatters import format_sync_result


class TestSyncFormatter(unittest.TestCase):
    def test_basic_sync(self):
        result = {"skills_count": 3}
        output = format_sync_result(result)
        self.assertIn("Synced: 3 skills", output)

    def test_skipped_count(self):
        result = {"skills_count": 3, "skipped_count": 2}
        output = format_sync_result(result)
        self.assertIn("skipped: 2", output)

    def test_links_replaced(self):
        result = {"skills_count": 1, "links_replaced": 5}
        output = format_sync_result(result)
        self.assertIn("Links replaced: 5", output)

    def test_fix_summary(self):
        result = {"skills_count": 1, "fix_summary": {"fixed": 2, "external": 1, "broken": 1}}
        output = format_sync_result(result)
        self.assertIn("fixed: 2", output)
        self.assertIn("external: 1", output)
        self.assertIn("broken: 1", output)

    def test_broken_fixes(self):
        result = {
            "skills_count": 1,
            "fixes": [
                {"status": "fixed", "file": "a.md", "old": "old"},
                {"status": "broken", "file": "b.md", "old": "bad", "reason": "missing"},
            ],
        }
        output = format_sync_result(result)
        self.assertIn("Broken links:", output)
        self.assertIn("b.md", output)
        self.assertIn("missing", output)

    def test_dry_run(self):
        result = {"skills_count": 1, "dry_run": True}
        output = format_sync_result(result)
        self.assertIn("Dry run - no changes", output)


if __name__ == "__main__":
    unittest.main()
