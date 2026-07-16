"""Tests for sync result formatter."""

import unittest

from ai_skill_manager.cli.common.formatters import format_sync_result


class TestSyncFormatter(unittest.TestCase):
    def test_basic_sync(self):
        result = {"skills_count": 3}
        output = format_sync_result(result)
        self.assertIn("Synced: 3 skills", output)

    def test_dry_run(self):
        result = {"skills_count": 1, "dry_run": True}
        output = format_sync_result(result)
        self.assertIn("Dry run - no changes", output)


if __name__ == "__main__":
    unittest.main()
