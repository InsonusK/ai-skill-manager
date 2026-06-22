"""Tests for sync command CLI."""

import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.commands.sync.cli import run as sync_run


MOCK_DIR = Path(__file__).parent.parent / "mock" / "test_sync_cli"


class TestSyncCLI(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def _args(self, **overrides):
        defaults = {
            "config": None,
            "target": None,
            "on_conflict": "error",
            "remove_orphans": False,
            "keep_orphans": False,
            "dry_run": False,
            "force": False,
            "verbose": False,
        }
        defaults.update(overrides)
        return type("Args", (), defaults)()

    def test_sync_command_runs(self):
        root = self._copy_mock("basic")
        config = root / "ai-skills.yaml"

        args = self._args(config=str(config))
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            sync_run(args)
            output = stdout.getvalue()

        self.assertIn("Synced: 1 skills", output)
        self.assertTrue((root / "target" / "guide" / "SKILL.md").exists())

    def test_sync_command_dry_run(self):
        root = self._copy_mock("basic")
        config = root / "ai-skills.yaml"

        args = self._args(config=str(config), dry_run=True)
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            sync_run(args)
            output = stdout.getvalue()

        self.assertIn("Dry run - no changes", output)
        self.assertFalse((root / "target").exists())

    def test_sync_command_keep_orphans(self):
        root = self._copy_mock("basic")
        target = root / "target"
        target.mkdir(parents=True)
        orphan = target / "orphan"
        orphan.mkdir()
        from ai_skill_manager.utils import tag_managed
        tag_managed(orphan)
        config = root / "ai-skills.yaml"

        args = self._args(config=str(config), remove_orphans=False, keep_orphans=True)
        sync_run(args)

        self.assertTrue(orphan.exists())

    def test_sync_command_missing_config(self):
        args = self._args(config=str(self.tmpdir / "missing.yaml"))
        with patch("sys.stderr", new_callable=StringIO) as stderr:
            with self.assertRaises(SystemExit):
                sync_run(args)
            self.assertIn("Config not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
