"""Tests for tools.link_path."""

import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities.path_kind import PathKind
from ai_skill_manager.tools.link_path import (
    classify_raw_path,
    existing_file,
    is_http_link,
    split_fragment,
)


class TestIsHttpLink(unittest.TestCase):
    def test_recognizes_common_schemes(self):
        for url in ("http://x", "https://x", "mailto:a@b.c", "ftp://x", "file://x"):
            self.assertTrue(is_http_link(url), url)

    def test_rejects_local_paths(self):
        for path in ("./a.md", "../a.md", "/a.md", "a.md"):
            self.assertFalse(is_http_link(path), path)


class TestSplitFragment(unittest.TestCase):
    def test_no_fragment(self):
        self.assertEqual(split_fragment("a.md"), ("a.md", ""))

    def test_with_fragment(self):
        self.assertEqual(split_fragment("a.md#section"), ("a.md", "#section"))


class TestClassifyRawPath(unittest.TestCase):
    def test_relative(self):
        self.assertEqual(classify_raw_path("./file.md"), PathKind.relative)
        self.assertEqual(classify_raw_path("../file.md"), PathKind.relative)

    def test_os_absolute(self):
        self.assertEqual(classify_raw_path("/tmp/file.md"), PathKind.os_absolute)

    def test_windows_drive_letter_is_os_absolute(self):
        self.assertEqual(classify_raw_path("C:/foo/bar"), PathKind.os_absolute)

    def test_repo_absolute_fallback(self):
        self.assertEqual(classify_raw_path("file.md"), PathKind.repo_absolute)

    def test_windows_separators_classified_like_posix(self):
        self.assertEqual(classify_raw_path(".\\file.md"), PathKind.relative)
        self.assertEqual(classify_raw_path("..\\file.md"), PathKind.relative)

    def test_web_link_raises(self):
        with self.assertRaises(ValueError):
            classify_raw_path("https://example.com")


class TestExistingFile(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_returns_path_when_it_exists(self):
        target = self.tmp / "a.md"
        target.write_text("hi")
        self.assertEqual(existing_file(target), target)

    def test_falls_back_to_md_suffix(self):
        target = self.tmp / "a-b-c.skill"
        md_target = self.tmp / "a-b-c.skill.md"
        md_target.write_text("hi")
        self.assertEqual(existing_file(target), md_target)

    def test_returns_none_when_neither_exists(self):
        self.assertIsNone(existing_file(self.tmp / "missing.md"))


if __name__ == "__main__":
    unittest.main()
