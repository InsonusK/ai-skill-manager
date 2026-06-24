"""Tests for discover command."""

import json
import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.cli import main
from ai_skill_manager.cli.commands.discover.cli import run as discover_run


class TestDiscoverCommand(unittest.TestCase):
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

    def test_help_shows_discover(self):
        with patch("sys.argv", ["ai-skill-manager", "discover", "--help"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

    def test_discover_single_source_auto(self):
        src = self._make_source_dir()

        args = type("Args", (), {
            "config": None,
            "type": "auto",
            "path": str(src),
            "target": str(self.tmp / "target"),
            "tree": "master",
            "subpath": None,
            "verbose": False,
        })()

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            discover_run(args)
            output = stdout.getvalue()

        self.assertIn("guide", output)
        self.assertIn("web", output)
        self.assertIn("1. guide | flat | guide.skill.md", output)
        self.assertIn("2. web | directory | web.skill.md", output)
        self.assertIn("File:", output)
        self.assertIn("Total: 2 skill(s)", output)

    def test_discover_from_config(self):
        src = self._make_source_dir()
        config = self.tmp / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./skills"}],
            "settings": {"target": ".agents/skills"}
        }))

        args = type("Args", (), {
            "config": str(config),
            "type": None,
            "path": None,
            "target": None,
            "tree": "master",
            "subpath": None,
            "verbose": False,
        })()

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            discover_run(args)
            output = stdout.getvalue()

        self.assertIn("1. guide | flat | guide.skill.md", output)
        self.assertIn("2. web | directory | web.skill.md", output)
        self.assertIn("Total: 2 skill(s)", output)

    def test_discover_missing_config_exits(self):
        args = type("Args", (), {
            "config": str(self.tmp / "missing.yaml"),
            "type": None,
            "path": None,
            "target": None,
            "tree": "master",
            "subpath": None,
            "verbose": False,
        })()

        with self.assertRaises(SystemExit) as cm:
            discover_run(args)
        self.assertEqual(cm.exception.code, 1)

    def test_discover_empty_source(self):
        empty = self.tmp / "empty"
        empty.mkdir()

        args = type("Args", (), {
            "config": None,
            "type": "auto",
            "path": str(empty),
            "target": str(self.tmp / "target"),
            "tree": "master",
            "subpath": None,
            "verbose": False,
        })()

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            discover_run(args)
            output = stdout.getvalue()

        self.assertIn("No skills discovered.", output)


if __name__ == "__main__":
    unittest.main()
