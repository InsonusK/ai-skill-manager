"""Tests for managed_state."""

import unittest
from pathlib import Path
import tempfile
import shutil

from ai_skill_manager.functions.managed_state import is_managed, tag_managed


class TestManagedTag(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_not_managed_initially(self):
        self.assertFalse(is_managed(self.tmpdir))

    def test_tag_makes_managed(self):
        tag_managed(self.tmpdir)
        self.assertTrue(is_managed(self.tmpdir))
        # Check file exists
        self.assertTrue((self.tmpdir / '.ai-skills-managed').exists())

    def test_tag_idempotent(self):
        tag_managed(self.tmpdir)
        tag_managed(self.tmpdir)
        self.assertTrue(is_managed(self.tmpdir))


class TestManagedState(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_read_write_managed_state(self):
        from ai_skill_manager.functions.managed_state import read_managed_state, write_managed_state
        state = {'hash': 'abc123', 'adapters': [{'name': 'LinkUpdater', 'version': 1}]}
        write_managed_state(self.tmpdir, state)
        self.assertEqual(read_managed_state(self.tmpdir), state)

    def test_read_managed_state_invalid_content(self):
        from ai_skill_manager.functions.managed_state import read_managed_state
        path = self.tmpdir / '.ai-skills-managed'
        path.write_text('not-json')
        self.assertIsNone(read_managed_state(self.tmpdir))

    def test_read_managed_state_missing_file(self):
        from ai_skill_manager.functions.managed_state import read_managed_state
        self.assertIsNone(read_managed_state(self.tmpdir))


if __name__ == '__main__':
    unittest.main()
