"""Tests for the sync command integration."""

import json
import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.cli import main
from ai_skill_manager.command.sync import DEFAULT_TARGET, run_sync
from ai_skill_manager.cli.sync import run as sync_run
from ai_skill_manager.validators import ValidationFailedError


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
            "sources": [{"path": "./skills", "type": "local"}],
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
        from ai_skill_manager.functions.managed_state import tag_managed
        tag_managed(orphan)

        self._make_source_dir()
        config = self._write_config(target="./target")

        run_sync(config_path=config, remove_orphans=False)

        self.assertTrue(orphan.exists())
        self.assertTrue((target / "guide").exists())

    def test_sync_missing_config(self):
        with self.assertRaises(FileNotFoundError):
            run_sync(config_path=self.tmp / "missing.yaml")

    def test_sync_conflict_is_validation_error(self):
        src_a = self.tmp / "repo_a"
        src_a.mkdir()
        (src_a / "same.skill.md").write_text("---\nname: same\n---\n# A")

        src_b = self.tmp / "repo_b"
        src_b.mkdir()
        (src_b / "same.skill.md").write_text("---\nname: same\n---\n# B")

        config = self.tmp / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./repo_a", "type": "local"}, {"path": "./repo_b", "type": "local"}],
            "settings": {"target": "./target"}
        }))

        with self.assertRaises(ValidationFailedError) as ctx:
            run_sync(config_path=config)

        self.assertTrue(ctx.exception.report.has_errors)

    def test_sync_link_includes_target_dir_relative_to_config_base(self):
        # EN: When target is a subdirectory of the config base (repo root),
        # repo-absolute links include the target_dir prefix.
        # RU: Когда target — поддиректория config base (корня репо),
        # repo-absolute ссылки включают префикс target_dir.
        src = self.tmp / "skills"
        src.mkdir()
        skill_a = src / "skill-a"
        skill_a.mkdir()
        (skill_a / "SKILL.md").write_text(
            "---\nname: skill-a\n---\n# A\n[link to b](../skill-b/SKILL.md)\n"
        )
        skill_b = src / "skill-b"
        skill_b.mkdir()
        (skill_b / "SKILL.md").write_text("---\nname: skill-b\n---\n# B\n")

        config = self._write_config(target="./agents/skills")
        run_sync(config_path=config)

        synced_a = (self.tmp / "agents" / "skills" / "skill-a" / "SKILL.md").read_text()
        self.assertIn("[link to b](agents/skills/skill-b/SKILL.md)", synced_a)


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
        }
        defaults.update(overrides)
        return type("Args", (), defaults)()

    def test_sync_command_runs(self):
        self._make_source_dir()
        config = self.tmp / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./skills", "type": "local"}],
            "settings": {"target": "./target"}
        }))

        args = self._args(config=str(config))

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            sync_run(args)
            output = stdout.getvalue()

        self.assertIn("Synced: 1 skills", output)
        self.assertTrue((self.tmp / "target" / "guide" / "SKILL.md").exists())

    def test_sync_command_dry_run(self):
        self._make_source_dir()
        config = self.tmp / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./skills", "type": "local"}],
            "settings": {"target": "./target"}
        }))

        args = self._args(config=str(config), dry_run=True)

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            sync_run(args)
            output = stdout.getvalue()

        self.assertIn("Dry run - no changes", output)
        self.assertFalse((self.tmp / "target").exists())

    def test_sync_command_direct_source(self):
        src = self._make_source_dir()

        args = self._args(type="auto", path=str(src), target=str(self.tmp / "target"))

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            sync_run(args)
            output = stdout.getvalue()

        self.assertIn("Synced: 1 skills", output)
        self.assertTrue((self.tmp / "target" / "guide" / "SKILL.md").exists())

    def test_sync_help(self):
        with patch("sys.argv", ["ai-skill-manager", "sync", "--help"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
