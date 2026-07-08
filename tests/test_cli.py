"""Tests for CLI and commands."""

import unittest
from unittest.mock import patch

from ai_skill_manager.cli import main


class TestCLIEntrypoint(unittest.TestCase):
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

    def test_check_help(self):
        with patch('sys.argv', ['ai-skill-manager', 'check', '--help']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
