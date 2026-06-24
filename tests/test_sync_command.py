"""Tests for the sync command integration."""

import json
import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.cli import main
from ai_skill_manager.cli.commands.sync.api import DEFAULT_TARGET, run_sync
from ai_skill_manager.cli.commands.sync.cli import run as sync_run


class TestSyncAPI(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _make_source_dir(self):
        src = self.tmp / "skills"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide")

        web = src / "web"
        web.mkdir()
        (web / "SKILL.md").write_text("---\nname: web\n---\n# Web")
        return src

    def _write_config(self, **settings):
        config = self.tmp / "ai-skills.yaml"
        data = {
            "sources": [{"path": "./skills","type":"local"}],
            "settings": settings,
        }
        config.write_text(json.dumps(data))
        return config

    def test_sync_from_config(self):
        self._make_source_dir()
        config = self._write_config(target="./target")

        result = run_sync(config_path=config)

        self.assertEqual(result["skills_count"], 2)
        self.assertTrue((self.tmp / "target" / "guide" / "SKILL.md").exists())
        self.assertTrue((self.tmp / "target" / "web" / "SKILL.md").exists())

    def test_sync_target_override(self):
        self._make_source_dir()
        config = self._write_config(target="./target")
        override = self.tmp / "override"

        run_sync(config_path=config, target_dir=override)

        self.assertTrue((override / "guide" / "SKILL.md").exists())
        self.assertFalse((self.tmp / "target").exists())

    def test_sync_dry_run(self):
        self._make_source_dir()
        config = self._write_config(target="./target")

        result = run_sync(config_path=config, dry_run=True)

        self.assertTrue(result.get("dry_run"))
        self.assertFalse((self.tmp / "target").exists())

    def test_sync_keep_orphans(self):
        target = self.tmp / "target"
        target.mkdir(parents=True)
        orphan = target / "orphan"
        orphan.mkdir()
        from ai_skill_manager.utils import tag_managed
        tag_managed(orphan)

        self._make_source_dir()
        config = self._write_config(target="./target")

        run_sync(config_path=config, remove_orphans=False)

        self.assertTrue(orphan.exists())
        self.assertTrue((target / "guide").exists())

    def test_sync_missing_config(self):
        with self.assertRaises(FileNotFoundError):
            run_sync(config_path=self.tmp / "missing.yaml")

    def test_sync_conflict_error(self):
        src_a = self.tmp / "repo_a"
        src_a.mkdir()
        (src_a / "same.skill.md").write_text("---\nname: same\n---\n# A")

        src_b = self.tmp / "repo_b"
        src_b.mkdir()
        (src_b / "same.skill.md").write_text("---\nname: same\n---\n# B")

        config = self.tmp / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./repo_a", "type":"local"}, {"path": "./repo_b", "type":"local"}],
            "settings": {"target": "./target"}
        }))

        with self.assertRaises(ValueError) as ctx:
            run_sync(config_path=config, on_conflict="error")

        self.assertIn("CONFLICT", str(ctx.exception))

    def test_sync_conflict_last_wins(self):
        src_a = self.tmp / "repo_a"
        src_a.mkdir()
        (src_a / "same.skill.md").write_text("---\nname: same\n---\n# A")

        src_b = self.tmp / "repo_b"
        src_b.mkdir()
        (src_b / "same.skill.md").write_text("---\nname: same\n---\n# B")

        config = self.tmp / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./repo_a", "type":"local"}, {"path": "./repo_b", "type":"local"}],
            "settings": {"target": "./target"}
        }))

        run_sync(config_path=config, on_conflict="last_wins")

        self.assertIn("# B", (self.tmp / "target" / "same" / "SKILL.md").read_text())


class TestSyncCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _make_source_dir(self):
        src = self.tmp / "skills"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide")
        return src

    def test_sync_command_runs(self):
        self._make_source_dir()
        config = self.tmp / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./skills", "type":"local"}],
            "settings": {"target": "./target"}
        }))

        args = type("Args", (), {
            "config": str(config),
            "target": None,
            "on_conflict": "error",
            "remove_orphans": False,
            "keep_orphans": False,
            "dry_run": False,
            "force": False,
            "verbose": False,
        })()

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            sync_run(args)
            output = stdout.getvalue()

        self.assertIn("Synced: 1 skills", output)
        self.assertTrue((self.tmp / "target" / "guide" / "SKILL.md").exists())

    def test_sync_command_dry_run(self):
        self._make_source_dir()
        config = self.tmp / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./skills", "type":"local"}],
            "settings": {"target": "./target"}
        }))

        args = type("Args", (), {
            "config": str(config),
            "target": None,
            "on_conflict": "error",
            "remove_orphans": False,
            "keep_orphans": False,
            "dry_run": True,
            "force": False,
            "verbose": False,
        })()

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            sync_run(args)
            output = stdout.getvalue()

        self.assertIn("Dry run - no changes", output)
        self.assertFalse((self.tmp / "target").exists())

    def test_sync_help(self):
        with patch("sys.argv", ["ai-skill-manager", "sync", "--help"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
