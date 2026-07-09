"""Tests for check command."""

import json
import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.cli import main
from ai_skill_manager.cli.check import run as check_run


class TestCheckCommand(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _make_source_dir(self):
        src = self.tmp / "skills"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide")

        web = src / "web.skill"
        web.mkdir()
        (web / "web.skill.md").write_text("---\nname: web\n---\n# Web")
        return src

    def _args(self, **overrides):
        defaults = {
            "config": None,
            "type": None,
            "path": None,
            "subpath": None,
        }
        defaults.update(overrides)
        return type("Args", (), defaults)()

    def test_help_shows_check(self):
        with patch("sys.argv", ["ai-skill-manager", "check", "--help"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

    def test_check_single_source_auto(self):
        src = self._make_source_dir()

        args = self._args(type="auto", path=str(src))

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            exit_code = check_run(args)
            output = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("guide", output)
        self.assertIn("web", output)
        self.assertIn("Discovered skills", output)
        self.assertIn("guide.skill.md", output)
        self.assertIn("web.skill.md", output)
        self.assertIn("Total: 2 skill(s)", output)
        self.assertIn("Validation passed", output)

    def test_check_from_config(self):
        src = self._make_source_dir()
        config = self.tmp / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./skills", "type": "local"}],
            "settings": {"target": ".agents/skills"}
        }))

        args = self._args(config=str(config))

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            exit_code = check_run(args)
            output = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Discovered skills", output)
        self.assertIn("guide", output)
        self.assertIn("web", output)
        self.assertIn("guide.skill.md", output)
        self.assertIn("web.skill.md", output)
        self.assertIn("Total: 2 skill(s)", output)
        self.assertIn("Validation passed", output)

    def test_check_missing_config_exits(self):
        args = self._args(config=str(self.tmp / "missing.yaml"))

        exit_code = check_run(args)
        self.assertEqual(exit_code, 1)

    def test_check_empty_source(self):
        empty = self.tmp / "empty"
        empty.mkdir()

        args = self._args(type="auto", path=str(empty))

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            exit_code = check_run(args)
            output = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("No skills discovered.", output)
        self.assertIn("Validation passed", output)

    def test_check_reports_validation_errors(self):
        src = self.tmp / "skills"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: wrong\n---\n# Guide")

        args = self._args(type="auto", path=str(src))

        exit_code = check_run(args)
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
