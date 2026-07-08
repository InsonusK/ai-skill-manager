"""Tests for services.validate."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.source import LocalSource
from ai_skill_manager.service.validate import run_validation


MOCK_DIR = Path(__file__).parent.parent / "mock" / "test_validate"


class TestRunValidation(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def test_valid_skills_report_no_errors(self):
        root = self._copy_mock("valid")
        source = LocalSource(scan_path=root.resolve())

        report = run_validation([source])

        self.assertFalse(report.has_errors)
        self.assertEqual(report.errors, {})

    def test_invalid_skills_report_errors(self):
        root = self._copy_mock("invalid")
        source = LocalSource(scan_path=root.resolve())

        report = run_validation([source])

        self.assertTrue(report.has_errors)
        self.assertGreater(len(report.errors), 0)

    def test_progress_callback_called(self):
        root = self._copy_mock("valid")
        source = LocalSource(scan_path=root.resolve())
        events = []

        run_validation([source], progress=lambda *args: events.append(args))

        self.assertTrue(any(stage == "discover" for stage, _, _ in events))
        self.assertTrue(any(stage == "validate" for stage, _, _ in events))


if __name__ == "__main__":
    unittest.main()
