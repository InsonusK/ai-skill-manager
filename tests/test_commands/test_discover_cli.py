"""Tests for discover command CLI."""

import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.cli import main
from ai_skill_manager.commands.discover.cli import _discover


MOCK_DIR = Path(__file__).parent.parent / "mock" / "test_discover_cli"


class TestDiscoverCLI(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def test_discover_from_config(self):
        root = self._copy_mock("config")
        args = type("Args", (), {
            "config": str(root / "ai-skills.yaml"),
            "type": None,
            "path": None,
            "tree": "master",
            "subpath": None,
            "verbose": False,
        })()

        skills = _discover(args)
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].name, "guide")

    def test_discover_single_source_auto(self):
        root = self._copy_mock("auto")
        args = type("Args", (), {
            "config": None,
            "type": "auto",
            "path": str(root),
            "tree": "master",
            "subpath": None,
            "verbose": False,
        })()

        skills = _discover(args)
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].name, "skill")

    def test_discover_missing_config_exits(self):
        args = type("Args", (), {
            "config": str(self.tmpdir / "missing.yaml"),
            "type": None,
            "path": None,
            "tree": "master",
            "subpath": None,
            "verbose": False,
        })()

        with self.assertRaises(FileNotFoundError):
            _discover(args)

    def test_discover_missing_config_and_type_exits(self):
        args = type("Args", (), {
            "config": None,
            "type": None,
            "path": None,
            "tree": "master",
            "subpath": None,
            "verbose": False,
        })()

        # Change to an empty directory so the default config is not found.
        import os
        cwd = os.getcwd()
        os.chdir(self.tmpdir)
        try:
            with self.assertRaises(ValueError):
                _discover(args)
        finally:
            os.chdir(cwd)

    def test_discover_github_requires_path(self):
        args = type("Args", (), {
            "config": None,
            "type": "github",
            "path": None,
            "tree": "master",
            "subpath": None,
            "verbose": False,
        })()

        with self.assertRaises(ValueError):
            _discover(args)

    def test_discover_help(self):
        with patch("sys.argv", ["ai-skill-manager", "discover", "--help"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
