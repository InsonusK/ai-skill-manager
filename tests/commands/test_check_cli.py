"""Tests for check command CLI."""

import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.cli import main
from ai_skill_manager.cli.common.source_parser import build_sources_from_args
from ai_skill_manager.command.check import run_check
from . import MOCK_DIR


TESTCASE_MOCK_DIR = MOCK_DIR / "test_check_cli"


def _check(args):
    """Resolve CLI arguments to a list of skills."""
    sources, _ = build_sources_from_args(args)
    skills, _ = run_check(sources)
    return skills


class TestCheckCLI(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = TESTCASE_MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def _args(self, **overrides):
        defaults = {
            "config": None,
            "type": None,
            "path": None,
            "subpath": None,
        }
        defaults.update(overrides)
        return type("Args", (), defaults)()

    def test_check_from_config(self):
        root = self._copy_mock("config")
        args = self._args(config=str(root / "ai-skills.yaml"))

        skills = _check(args)
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].name, "guide")

    def test_check_single_source_auto(self):
        root = self._copy_mock("auto")
        args = self._args(type="auto", path=str(root))

        skills = _check(args)
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].name, "skill")

    def test_check_missing_config_exits(self):
        args = self._args(config=str(self.tmpdir / "missing.yaml"))

        with self.assertRaises(FileNotFoundError):
            _check(args)

    def test_check_missing_config_and_type_exits(self):
        args = self._args()

        # Change to an empty directory so the default config is not found.
        import os
        cwd = os.getcwd()
        os.chdir(self.tmpdir)
        try:
            with self.assertRaises(FileNotFoundError):
                _check(args)
        finally:
            os.chdir(cwd)

    def test_check_github_requires_path(self):
        args = self._args(type="github")

        with self.assertRaises(ValueError):
            _check(args)

    def test_check_help(self):
        with patch("sys.argv", ["ai-skill-manager", "check", "--help"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
