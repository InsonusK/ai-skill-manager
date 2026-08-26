"""Tests for CLI and commands."""

import logging
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.cli import main
from ai_skill_manager.cli.__init__ import _configure_logging, _resolve_config_path
from ai_skill_manager.config import LoggingSettings


class TestCLIEntrypoint(unittest.TestCase):
    def setUp(self):
        self.original_level = logging.getLogger().level

    def tearDown(self):
        logging.getLogger().setLevel(self.original_level)

    def test_help_shows_subcommands(self):
        with patch('sys.argv', ['ai-skill-manager', '--help']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

    def test_sync_help(self):
        with patch('sys.argv', ['ai-skill-manager', 'sync', '--help']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)


class TestConfigureLogging(unittest.TestCase):
    def setUp(self):
        self.original_level = logging.getLogger().level
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        logging.getLogger().setLevel(self.original_level)
        shutil.rmtree(self.tmpdir)

    def test_applies_warning_level_by_default(self):
        _configure_logging(LoggingSettings())

        self.assertEqual(logging.getLogger().level, logging.WARNING)

    def test_applies_configured_level(self):
        _configure_logging(LoggingSettings(level="error"))

        self.assertEqual(logging.getLogger().level, logging.ERROR)

    def test_writes_to_file_when_to_file_set(self):
        log_file = self.tmpdir / "app.log"
        _configure_logging(LoggingSettings(level="info", to_file=log_file))

        logging.getLogger().info("test message")

        self.assertTrue(log_file.exists())
        self.assertIn("test message", log_file.read_text())

    def test_creates_log_directory_if_missing(self):
        log_file = self.tmpdir / "logs" / "app.log"
        _configure_logging(LoggingSettings(to_file=log_file))

        self.assertTrue(log_file.parent.exists())


class TestResolveConfigPath(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.tmpdir)

    def test_explicit_config_argument(self):
        config_path = self.tmpdir / "custom.yaml"
        config_path.write_text("sources: []\n")
        args = type("Args", (), {"config": str(config_path), "type": None})()

        result = _resolve_config_path(args)

        self.assertEqual(result, config_path.resolve())

    def test_default_config_when_present(self):
        default = self.tmpdir / "ai-skills.yaml"
        default.write_text("sources: []\n")
        args = type("Args", (), {"config": None, "type": None})()

        result = _resolve_config_path(args)

        self.assertEqual(result, default.resolve())

    def test_returns_none_when_no_default_config(self):
        args = type("Args", (), {"config": None, "type": None})()

        result = _resolve_config_path(args)

        self.assertIsNone(result)

    def test_returns_none_in_direct_source_mode(self):
        args = type("Args", (), {"config": None, "type": "auto"})()

        result = _resolve_config_path(args)

        self.assertIsNone(result)
