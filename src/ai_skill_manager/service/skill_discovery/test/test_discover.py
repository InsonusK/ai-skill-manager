"""Tests for services.discover."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.source import LocalSource
from ai_skill_manager.service.skill_discovery.skill_discover import discover


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
            [LocalSource(scan_paths=(self.source_dir,))],
            progress=lambda *args: events.append(args),
        )

        self.assertEqual(
            events,
            [
                ("discover", 0, 1),
                ("discover", 1, 1),
            ],
        )

    def test_discovers_filtered_by_tags(self):
        (self.source_dir / "py.skill.md").write_text(
            "---\nname: py\ntags:\n  - python\n  - cli\n---\n"
        )
        (self.source_dir / "web.skill.md").write_text(
            "---\nname: web\ntags:\n  - web\n---\n"
        )

        skills, errors = discover(
            [LocalSource(scan_paths=(self.source_dir,), tags=("python",))]
        )

        self.assertEqual(errors, [])
        self.assertEqual(set(skills), {"py"})

    def test_discovers_filtered_by_hierarchical_tags(self):
        (self.source_dir / "a.skill.md").write_text(
            "---\nname: a\ntags:\n  - a/b\n---\n"
        )
        (self.source_dir / "b.skill.md").write_text(
            "---\nname: b\ntags:\n  - x/y\n---\n"
        )

        # Query "a/b/c" expands to "a", "b", "c", "a/b", "b/c" and "a/b/c".
        skills, errors = discover(
            [LocalSource(scan_paths=(self.source_dir,), tags=("a/b/c",))]
        )

        self.assertEqual(errors, [])
        self.assertEqual(set(skills), {"a"})

    def test_deduplicates_skills_from_overlapping_sources(self):
        (self.source_dir / "a.skill.md").write_text("---\nname: a\n---\n")

        skills, errors = discover(
            [
                LocalSource(scan_paths=(self.source_dir,)),
                LocalSource(scan_paths=(self.source_dir,)),
            ]
        )

        # The same skill discovered twice must be returned only once.
        self.assertEqual(errors, [])
        self.assertEqual(set(skills), {"a"})

    def test_name_collision_between_different_skills_is_an_error(self):
        (self.source_dir / "a").mkdir()
        (self.source_dir / "a" / "x.skill.md").write_text("---\nname: dup\n---\n")
        (self.source_dir / "b").mkdir()
        (self.source_dir / "b" / "y.skill.md").write_text("---\nname: dup\n---\n")

        skills, errors = discover([LocalSource(scan_paths=(self.source_dir,))])

        self.assertEqual(len(errors), 1)
        self.assertIn("dup", errors[0])
        self.assertEqual(len(skills), 1)


if __name__ == "__main__":
    unittest.main()
