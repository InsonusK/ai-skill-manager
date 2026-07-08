"""Tests for compute_skill_hash."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.functions.hash import compute_skill_hash


MOCK_DIR = Path(__file__).parent / "mock" / "test_compute_skill_hash"


class TestComputeSkillHash(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def _skill(self, file_path: Path, folder_path: Path | None = None) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(scan_path=file_path.parent),
            format=SkillFormat.Agent if folder_path else SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def test_flat_skill_hash(self):
        root = self._copy_mock("flat")
        md = root / "guide.skill.md"
        skill = self._skill(md)

        h1 = compute_skill_hash(skill)
        h2 = compute_skill_hash(skill)
        self.assertEqual(h1, h2)

    def test_dir_skill_hash_changes_with_content(self):
        root = self._copy_mock("dir")
        skill_dir = root / "web"
        skill = self._skill(skill_dir / "SKILL.md", skill_dir)

        h1 = compute_skill_hash(skill)
        (skill_dir / "details.md").write_text("# Changed\n")
        h2 = compute_skill_hash(skill)
        self.assertNotEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()
