"""Tests for the sync command CLI (``ai_skill_manager.cli.sync.run``)."""

import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.cli.sync import run as sync_run

MOCK_DIR = Path(__file__).parent / "mock"


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
            "type": None,
            "path": None,
            "subpath": None,
            "target": None,
            "remove_orphans": False,
            "keep_orphans": False,
            "dry_run": False,
            "force": False,
            "add_relations": None,
        }
        defaults.update(overrides)
        return type("Args", (), defaults)()

    def test_sync_command_runs(self):
        root = self._copy_mock("basic")
        config = root / "ai-skills.yaml"

        args = self._args(config=str(config))
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            exit_code = sync_run(args)
            output = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Synced: 1 skills", output)
        self.assertTrue((root / "target" / "guide" / "SKILL.md").exists())

    def test_sync_command_dry_run(self):
        root = self._copy_mock("basic")
        config = root / "ai-skills.yaml"

        args = self._args(config=str(config), dry_run=True)
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            exit_code = sync_run(args)
            output = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Dry run - no changes", output)
        self.assertFalse((root / "target").exists())

    def test_sync_command_keep_orphans(self):
        root = self._copy_mock("basic")
        target = root / "target"
        target.mkdir(parents=True)
        orphan = target / "orphan"
        orphan.mkdir()
        from ai_skill_manager.functions.managed_state import tag_managed
        tag_managed(orphan)
        config = root / "ai-skills.yaml"

        args = self._args(config=str(config), remove_orphans=False, keep_orphans=True)
        exit_code = sync_run(args)

        self.assertEqual(exit_code, 0)
        self.assertTrue(orphan.exists())

    def test_sync_command_missing_config(self):
        args = self._args(config=str(self.tmpdir / "missing.yaml"))
        exit_code = sync_run(args)
        self.assertEqual(exit_code, 1)

    def test_sync_command_direct_source(self):
        src = self.tmpdir / "skills"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide")

        args = self._args(type="auto", path=str(src), target=str(self.tmpdir / "target"))
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            exit_code = sync_run(args)
            output = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Synced: 1 skills", output)
        self.assertTrue((self.tmpdir / "target" / "guide" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
