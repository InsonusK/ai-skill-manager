"""Tests for SourceFactory."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import GitHubSource, LocalSource
from ai_skill_manager.service.source_factory import SourceFactory


MOCK_DIR = Path(__file__).parent / "mock" / "test_source_factory"


class TestCreateFromParams(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.factory = SourceFactory()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_local_source(self):
        src = self.tmp / "skills"
        src.mkdir()

        sources = self.factory.create_from_params(source_type="auto", path=str(src))

        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], LocalSource)
        self.assertEqual(sources[0].scan_paths, (src,))

    def test_github_source_default_subpath(self):
        sources = self.factory.create_from_params(
            source_type="github", path="https://github.com/org/repo")

        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], GitHubSource)
        self.assertEqual(sources[0].repo_url, "https://github.com/org/repo")
        self.assertEqual(sources[0].tree, "master")
        self.assertEqual(sources[0].subpaths, ("skills",))

    def test_github_source_with_tree(self):
        sources = self.factory.create_from_params(
            source_type="github", path="https://github.com/org/repo", tree="develop")

        self.assertEqual(sources[0].repo_url, "https://github.com/org/repo")
        self.assertEqual(sources[0].tree, "develop")

    def test_github_source_with_multiple_subpaths_stays_one_source(self):
        sources = self.factory.create_from_params(
            source_type="github",
            path="https://github.com/org/repo",
            subpath=["skills", "extras"],
        )

        # A single GitHubSource carries every subpath so the repository is
        # downloaded only once.
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].subpaths, ("skills", "extras"))

    def test_unknown_type_raises(self):
        with self.assertRaises(ValueError):
            self.factory.create_from_params(source_type="unknown", path="/x")


class TestCreateFromConfig(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.factory = SourceFactory()

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
        sources = self.factory.create_from_config(config)

        self.assertIsInstance(sources[0], LocalSource)
        self.assertEqual(sources[0].scan_paths, (root / "skills",))

    def test_build_github_source(self):
        root = self._copy_mock("default")
        config = root / "ai-skills.yaml"
        sources = self.factory.create_from_config(config)

        self.assertIsInstance(sources[1], GitHubSource)
        self.assertEqual(sources[1].repo_url, "https://github.com/owner/repo")
        self.assertEqual(sources[1].tree, "main")
        self.assertEqual(sources[1].subpaths, ("docs",))

    def test_build_github_source_with_list_subpath_stays_one_source(self):
        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(
            "sources:\n"
            "  - type: github\n"
            "    path: https://github.com/owner/repo\n"
            "    tree: main\n"
            "    subpath:\n"
            "      - skills\n"
            "      - docs\n"
        )
        sources = self.factory.create_from_config(config)

        # A single GitHubSource carries every subpath so the repository is
        # downloaded only once instead of once per subpath.
        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], GitHubSource)
        self.assertEqual(sources[0].repo_url, "https://github.com/owner/repo")
        self.assertEqual(sources[0].tree, "main")
        self.assertEqual(sources[0].subpaths, ("skills", "docs"))

    def test_build_local_source_with_list_subpath_stays_one_source(self):
        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(
            "sources:\n"
            "  - type: local\n"
            "    path: repo\n"
            "    subpath:\n"
            "      - skills\n"
            "      - docs\n"
        )
        (self.tmpdir / "repo" / "skills").mkdir(parents=True)
        (self.tmpdir / "repo" / "docs").mkdir(parents=True)
        sources = self.factory.create_from_config(config)

        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], LocalSource)
        self.assertEqual(
            sources[0].scan_paths,
            (self.tmpdir / "repo" / "skills", self.tmpdir / "repo" / "docs"),
        )

    def test_build_local_source_with_tags(self):
        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(
            "sources:\n"
            "  - type: local\n"
            "    path: skills\n"
            "    tags:\n"
            "      - python & cli\n"
            "      - !web\n"
        )
        (self.tmpdir / "skills").mkdir()
        sources = self.factory.create_from_config(config)

        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], LocalSource)
        self.assertEqual(sources[0].tags, ("python & cli", "!web"))

    def test_build_github_source_with_tags(self):
        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(
            "sources:\n"
            "  - type: github\n"
            "    path: https://github.com/owner/repo\n"
            "    tree: main\n"
            "    subpath:\n"
            "      - skills\n"
            "      - docs\n"
            "    tags:\n"
            "      - python | cli\n"
        )
        sources = self.factory.create_from_config(config)

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].tags, ("python | cli",))

    def test_default_skip_folder_is_examples(self):
        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(
            "sources:\n"
            "  - type: local\n"
            "    path: skills\n"
        )
        (self.tmpdir / "skills").mkdir()
        sources = self.factory.create_from_config(config)

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].skip_folder, ("examples",))

    def test_build_local_source_with_skip_folder(self):
        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(
            "sources:\n"
            "  - type: local\n"
            "    path: skills\n"
            "    skip_folder:\n"
            "      - abc\n"
            "      - xyz\n"
        )
        (self.tmpdir / "skills").mkdir()
        sources = self.factory.create_from_config(config)

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].skip_folder, ("abc", "xyz"))

    def test_build_local_source_with_string_skip_folder(self):
        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(
            "sources:\n"
            "  - type: local\n"
            "    path: skills\n"
            "    skip_folder: abc\n"
        )
        (self.tmpdir / "skills").mkdir()
        sources = self.factory.create_from_config(config)

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].skip_folder, ("abc",))

    def test_build_github_source_with_skip_folder(self):
        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(
            "sources:\n"
            "  - type: github\n"
            "    path: https://github.com/owner/repo\n"
            "    tree: main\n"
            "    subpath:\n"
            "      - skills\n"
            "      - docs\n"
            "    skip_folder:\n"
            "      - abc\n"
        )
        sources = self.factory.create_from_config(config)

        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], GitHubSource)
        self.assertEqual(sources[0].skip_folder, ("abc",))

    def test_unknown_source_type_raises(self):
        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(
            "sources:\n"
            "  - type: ftp\n"
            "    path: skills\n"
        )
        with self.assertRaises(ValueError):
            self.factory.create_from_config(config)


if __name__ == "__main__":
    unittest.main()
