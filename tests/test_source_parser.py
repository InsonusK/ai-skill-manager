"""Tests for the shared CLI source parser."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.cli.common.source_parser import (
    DEFAULT_CONFIG,
    build_sources_from_args,
)
from ai_skill_manager.entities import GitHubSource, LocalSource


class TestBuildSourcesFromArgs(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _args(self, **overrides):
        defaults = {
            "config": None,
            "type": None,
            "path": None,
            "subpath": None,
        }
        defaults.update(overrides)
        return type("Args", (), defaults)()

    def test_explicit_config(self):
        config = self.tmp / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./skills", "type": "local"}],
        }))
        (self.tmp / "skills").mkdir()

        sources, config_path = build_sources_from_args(
            self._args(config=str(config)))

        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], LocalSource)
        self.assertEqual(config_path, config.resolve())

    def test_missing_config_raises(self):
        with self.assertRaises(FileNotFoundError):
            build_sources_from_args(
                self._args(config=str(self.tmp / "missing.yaml")))

    def test_auto_source(self):
        src = self.tmp / "skills"
        src.mkdir()

        sources, config_path = build_sources_from_args(
            self._args(type="auto", path=str(src)))

        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], LocalSource)
        self.assertEqual(sources[0].scan_path, src)
        self.assertIsNone(config_path)

    def test_github_source_default_tree(self):
        sources, config_path = build_sources_from_args(
            self._args(type="github", path="https://github.com/org/repo"))

        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], GitHubSource)
        self.assertEqual(sources[0].repo_url, "https://github.com/org/repo")
        self.assertEqual(sources[0].tree, "master")
        self.assertEqual(sources[0].subpath, "skills")
        self.assertIsNone(config_path)

    def test_github_source_with_tree_in_path(self):
        sources, _ = build_sources_from_args(
            self._args(type="github", path="https://github.com/org/repo develop"))

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].repo_url, "https://github.com/org/repo")
        self.assertEqual(sources[0].tree, "develop")

    def test_github_source_with_multiple_subpaths(self):
        sources, _ = build_sources_from_args(
            self._args(type="github", path="https://github.com/org/repo",
                       subpath=["skills", "extras"]))

        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0].subpath, "skills")
        self.assertEqual(sources[1].subpath, "extras")

    def test_github_requires_path(self):
        with self.assertRaises(ValueError):
            build_sources_from_args(self._args(type="github"))

    def test_unknown_type_raises(self):
        with self.assertRaises(ValueError):
            build_sources_from_args(self._args(type="unknown", path="/x"))

    def test_default_config_fallback(self):
        config = self.tmp / DEFAULT_CONFIG
        config.write_text(json.dumps({
            "sources": [{"path": "./skills", "type": "local"}],
        }))
        (self.tmp / "skills").mkdir()

        cwd = Path.cwd()
        import os
        os.chdir(self.tmp)
        try:
            sources, config_path = build_sources_from_args(self._args())
            self.assertEqual(len(sources), 1)
            self.assertEqual(config_path, config.resolve())
        finally:
            os.chdir(cwd)

    def test_no_source_and_no_default_config_raises(self):
        import os
        cwd = Path.cwd()
        os.chdir(self.tmp)
        try:
            with self.assertRaises(FileNotFoundError):
                build_sources_from_args(self._args())
        finally:
            os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
