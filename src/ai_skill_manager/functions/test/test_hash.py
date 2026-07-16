"""Tests for compute_hash."""

import unittest
from pathlib import Path
import tempfile

from ai_skill_manager.functions.hash import compute_hash


class TestComputeHash(unittest.TestCase):
    def test_same_content_same_hash(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('hello world')
            path = Path(f.name)

        try:
            h1 = compute_hash(path)
            h2 = compute_hash(path)
            self.assertEqual(h1, h2)
            self.assertEqual(len(h1), 64)  # SHA256 hex length
        finally:
            path.unlink()

    def test_different_content_different_hash(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('content A')
            path1 = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('content B')
            path2 = Path(f.name)

        try:
            self.assertNotEqual(compute_hash(path1), compute_hash(path2))
        finally:
            path1.unlink()
            path2.unlink()

    def test_binary_file(self):
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            f.write(bytes(range(256)))
            path = Path(f.name)

        try:
            h = compute_hash(path)
            self.assertEqual(len(h), 64)
        finally:
            path.unlink()


if __name__ == '__main__':
    unittest.main()
