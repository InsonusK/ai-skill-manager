"""Tests for AutoDiscovery strategy."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skills_manager.discovery.auto import AutoDiscovery


MOCK_DIR = Path(__file__).parent / 'mock' / 'test_auto'


class TestAutoDiscovery(unittest.TestCase):
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

    def test_empty_directory(self):
        empty = self._copy_mock('empty_directory') / 'empty'

        strategy = AutoDiscovery(empty, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 0)

    def test_single_skill_file(self):
        md = self._copy_mock('single_skill_file') / 'guide.skill.md'

        strategy = AutoDiscovery(md, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].skill_name, 'guide')
        self.assertTrue(result[0].is_flat)
        self.assertEqual(result[0].source_path, md)
        self.assertEqual(result[0].target_path, self.target / 'guide')

    def test_non_skill_file_ignored(self):
        txt = self._copy_mock('non_skill_file_ignored') / 'readme.txt'

        strategy = AutoDiscovery(txt, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 0)

    def test_directory_skill(self):
        skill_dir = self._copy_mock('directory_skill') / 'web'

        strategy = AutoDiscovery(skill_dir, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].skill_name, 'web')
        self.assertFalse(result[0].is_flat)
        self.assertEqual(result[0].target_path, self.target / 'web')

    def test_flat_directory(self):
        flat = self._copy_mock('flat_directory') / 'guides'

        strategy = AutoDiscovery(flat, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 2)
        names = {r.skill_name for r in result}
        self.assertEqual(names, {'a', 'b'})
        for mapping in result:
            self.assertTrue(mapping.is_flat)

    def test_nested_directory_skill(self):
        root = self._copy_mock('nested_directory_skill') / 'skills'

        strategy = AutoDiscovery(root, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].skill_name, 'backend')
        self.assertFalse(result[0].is_flat)

    def test_mixed_flat_and_directory(self):
        root = self._copy_mock('mixed')

        strategy = AutoDiscovery(root, self.target)
        result = strategy.discover()

        names = {r.skill_name for r in result}
        self.assertEqual(names, {'guide', 'web', 'a'})

        by_name = {r.skill_name: r for r in result}
        self.assertTrue(by_name['guide'].is_flat)
        self.assertFalse(by_name['web'].is_flat)
        self.assertTrue(by_name['a'].is_flat)

    def test_nested_flat_in_subdir(self):
        root = self._copy_mock('nested_flat_in_subdir') / 'skills'

        strategy = AutoDiscovery(root, self.target)
        result = strategy.discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].skill_name, 'react')
        self.assertTrue(result[0].is_flat)

    def test_directory_skill_with_extra_skill_md_raises(self):
        skill_dir = self._copy_mock('directory_with_extra_skill_md_raises') / 'web'

        strategy = AutoDiscovery(skill_dir, self.target)
        with self.assertRaises(ValueError):
            strategy.discover()


if __name__ == '__main__':
    unittest.main()
