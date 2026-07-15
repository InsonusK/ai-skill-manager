from ai_skill_manager.service.discovery.skill.auto import AutoDiscovery
from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.entities.source import LocalSource as LocalSourceCls
from .test_skill_name import MOCK_DIR


import shutil
import tempfile
import unittest
from pathlib import Path


class TestSkillSourceLink(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _copy_mock(self, name: str) -> Path:
        src = MOCK_DIR / name
        dst = self.tmpdir / name
        shutil.copytree(src, dst)
        return dst

    def test_skill_has_optional_source(self):
        md = self._copy_mock("name_value") / "guide.skill.md"
        source = LocalSource(scan_path=md.parent)

        skill = Skill(
            file_path=md,
            folder_path=None,
            format=SkillFormat.HumanFlat,
            source=source,
            source_path=md.parent,
        )

        self.assertEqual(skill.source, source)

    def test_skill_requires_source(self):
        md = self._copy_mock("name_value") / "guide.skill.md"

        with self.assertRaises(TypeError):
            Skill(
                file_path=md,
                folder_path=None,
                format=SkillFormat.HumanFlat,
            )

    def test_skill_requires_format(self):
        md = self._copy_mock("name_value") / "guide.skill.md"
        source = LocalSource(scan_path=md.parent)

        with self.assertRaises(TypeError):
            Skill(file_path=md, folder_path=None, source=source, source_path=md.parent)

    def test_autodiscovery_attaches_local_source(self):
        root = self._copy_mock("autodiscovery")
        source = LocalSource(scan_path=root)

        strategy = AutoDiscovery(source_path=root, source=source)
        skills = strategy.discover()

        self.assertEqual(len(skills), 1)
        self.assertIsInstance(skills[0].source, LocalSourceCls)
        self.assertEqual(skills[0].source.scan_path, root)

if __name__ == "__main__":
    unittest.main()