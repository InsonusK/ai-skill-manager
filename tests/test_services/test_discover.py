"""Tests for services.discover."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.source import LocalSource
from ai_skill_manager.services.discover import discover


class TestDiscover(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.source_dir = self.tmpdir / "source"
        self.source_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_progress_callback_called(self):
        (self.source_dir / "a.skill.md").write_text("---\nname: a\n---\n")
        (self.source_dir / "b.skill.md").write_text("---\nname: b\n---\n")
        events = []

        discover(
            [LocalSource(scan_path=self.source_dir)],
            progress=lambda *args: events.append(args),
        )

        self.assertEqual(
            events,
            [
                ("discover", 0, 1),
                ("discover", 1, 1),
            ],
        )


if __name__ == "__main__":
    unittest.main()
