"""Tests for build_sources_from_config."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.config import build_sources_from_config
from ai_skill_manager.entities import GitHubSource, LocalSource


MOCK_DIR = Path(__file__).parent / "mock" / "test_build_sources"


class TestBuildSourcesFromConfig(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def test_build_local_source(self):
        root = self._copy_mock("default")
        config = root / "ai-skills.yaml"
        sources = build_sources_from_config(config)

        self.assertIsInstance(sources[0], LocalSource)
        self.assertEqual(sources[0].path, (root / "skills").resolve())

    def test_build_github_source(self):
        root = self._copy_mock("default")
        config = root / "ai-skills.yaml"
        sources = build_sources_from_config(config)

        self.assertIsInstance(sources[1], GitHubSource)
        self.assertEqual(sources[1].repo_url, "https://github.com/owner/repo")
        self.assertEqual(sources[1].tree, "main")
        self.assertEqual(sources[1].subpath, "docs")

    def test_unknown_type_defaults_to_local(self):
        root = self._copy_mock("default")
        config = root / "ai-skills.yaml"
        sources = build_sources_from_config(config)

        self.assertIsInstance(sources[2], LocalSource)


if __name__ == "__main__":
    unittest.main()
