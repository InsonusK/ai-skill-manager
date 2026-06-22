"""Tests for LinkAdapter."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.adapters import Adapter
from ai_skill_manager.adapters.rules.link_adapter import LinkAdapter
from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.source import LocalSource as LocalSourceCls


MOCK_DIR = Path(__file__).parent / "mock" / "test_link_adapter"


class TestLinkAdapter(unittest.TestCase):
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
            source=LocalSource(path=file_path.parent),
            format=SkillFormat.Agent if folder_path else SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def test_rewrites_flat_skill_self_link(self):
        root = self._copy_mock("flat_skill")
        md = root / "guide.skill.md"
        skill = self._skill(md)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        adapter.adapt(skill, skill)

        content = md.read_text()
        self.assertIn("[details](./SKILL.md)", content)

    def test_rewrites_dir_skill_internal_link(self):
        root = self._copy_mock("dir_skill")
        skill_dir = root / "web"
        skill = self._skill(skill_dir / "web.skill.md", skill_dir)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        adapter.adapt(skill, skill)

        content = (skill_dir / "web.skill.md").read_text()
        self.assertIn("[internal](./details.md)", content)

    def test_preserves_image_prefix(self):
        root = self._copy_mock("image_link")
        skill_dir = root / "skill"
        skill = self._skill(skill_dir / "SKILL.md", skill_dir)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        adapter.adapt(skill, skill)

        content = (skill_dir / "SKILL.md").read_text()
        self.assertIn("![alt](./diagram.png)", content)

    def test_skips_external_urls(self):
        root = self._copy_mock("flat_skill")
        md = root / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide\n[external](https://example.com)\n")
        skill = self._skill(md)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        msg = adapter.adapt(skill, skill)["LinkAdapter"]

        self.assertEqual(msg.params["count"], 0)
        self.assertIn("https://example.com", md.read_text())


if __name__ == "__main__":
    unittest.main()
