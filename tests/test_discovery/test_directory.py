"""Tests for DirectoryDiscovery strategy."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.discovery.directory import DirectoryDiscovery


MOCK_DIR = Path(__file__).parent / 'mock' / 'test_directory'


class TestDirectoryDiscovery(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.target = self.tmpdir / 'target'
        self.target.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        return dst

    def test_single_skill_directory(self):
        skill = self._copy_mock('single_skill_directory') / 'web'

        strategy = DirectoryDiscovery(skill, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].skill_name, 'web')
        self.assertFalse(result[0].is_flat)
        self.assertEqual(result[0].source_skill_md, skill / 'web.skill.md')

    def test_multiple_skill_directories(self):
        root = self._copy_mock('multiple_skill_directories') / 'skills'

        strategy = DirectoryDiscovery(root, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 2)
        names = {r.skill_name for r in result}
        self.assertEqual(names, {'api', 'web'})
        for mapping in result:
            self.assertFalse(mapping.is_flat)

    def test_ignores_directories_without_skill_md(self):
        root = self._copy_mock('ignores_directories_without_skill_md') / 'skills'

        strategy = DirectoryDiscovery(root, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].skill_name, 'valid')

    def test_file_input_ignored(self):
        md = self._copy_mock('file_input_ignored') / 'guide.md'

        strategy = DirectoryDiscovery(md, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 0)

    def test_empty_directory(self):
        empty = self._copy_mock('empty_directory') / 'empty'

        strategy = DirectoryDiscovery(empty, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 0)

    def test_self_as_skill(self):
        """If root itself has {name}.skill.md, it's a single skill."""
        root = self._copy_mock('self_as_skill') / 'my-skill'

        strategy = DirectoryDiscovery(root, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].skill_name, 'my-skill')
        self.assertFalse(result[0].is_flat)

    def test_extra_skill_md_in_same_dir_raises(self):
        """A directory skill with another *.skill.md in the same dir raises."""
        root = self._copy_mock('extra_skill_md_in_same_dir_raises') / 'my-skill'

        strategy = DirectoryDiscovery(root, self.target)
        with self.assertRaises(ValueError):
            strategy.discover()

    def test_extra_skill_md_in_subdir_raises(self):
        """A directory skill with another *.skill.md in a subdir raises."""
        root = self._copy_mock('extra_skill_md_in_subdir_raises') / 'my-skill'

        strategy = DirectoryDiscovery(root, self.target)
        with self.assertRaises(ValueError):
            strategy.discover()


if __name__ == '__main__':
    unittest.main()
