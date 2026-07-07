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

    def _skill(self, file_path: Path, folder_path: Path | None = None, repo_path: Path | None = None) -> Skill:
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            source=LocalSource(scan_path=file_path.parent, repo_path=repo_path),
            format=SkillFormat.Agent if folder_path else SkillFormat.HumanFlat,
            source_path=file_path.parent,
        )

    def test_rewrites_flat_skill_self_link(self):
        """RU: Ссылка на сам плоский скилл переписывается в repo-absolute путь.

        В реальном синхроне плоский HumanFlat-скилл копируется в Agent-формат,
        поэтому исходная ссылка ``./guide.skill.md`` становится repo-absolute
        путём ``guide.skill.md``.
        """
        root = self._copy_mock("flat_skill")
        md = root / "guide.skill.md"
        skill = self._skill(md)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        adapter.adapt(skill, skill)

        content = md.read_text()
        self.assertIn("[details](guide.skill.md)", content)

    def test_rewrites_dir_skill_internal_link(self):
        root = self._copy_mock("dir_skill")
        skill_dir = root / "web"
        skill = self._skill(skill_dir / "web.skill.md", skill_dir, repo_path=root)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        adapter.adapt(skill, skill)

        content = (skill_dir / "web.skill.md").read_text()
        self.assertIn("[internal](web/details.md)", content)

    def test_preserves_image_prefix(self):
        root = self._copy_mock("image_link")
        skill_dir = root / "skill"
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, repo_path=root)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        adapter.adapt(skill, skill)

        content = (skill_dir / "SKILL.md").read_text()
        self.assertIn("![alt](skill/diagram.png)", content)

    def test_skips_external_urls(self):
        root = self._copy_mock("flat_skill")
        md = root / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide\n[external](https://example.com)\n")
        skill = self._skill(md)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        msg = adapter.adapt(skill, skill)["LinkAdapter"]

        self.assertEqual(msg.params["count"], 0)
        self.assertIn("https://example.com", md.read_text())

    def test_copies_source_file_to_files(self):
        # EN: A link to a file outside any skill is copied into files/.
        # RU: Ссылка на файл вне любого скилла копируется в files/.
        root = self.tmpdir / "source_file"
        root.mkdir()
        skill_dir = root / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[extra](../extra.md)\n"
        )
        (root / "extra.md").write_text("# Extra\n")
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, repo_path=root)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        msg = adapter.adapt(skill, skill)["LinkAdapter"]

        self.assertEqual(msg.params["count"], 1)
        content = (skill_dir / "SKILL.md").read_text()
        self.assertIn("[extra](./files/extra.md)", content)
        self.assertTrue((skill_dir / "files" / "extra.md").exists())

    def test_copies_source_directory_to_files(self):
        # EN: A link to a directory outside any skill is copied into files/.
        # RU: Ссылка на директорию вне любого скилла копируется в files/.
        root = self.tmpdir / "source_dir"
        root.mkdir()
        skill_dir = root / "skill"
        skill_dir.mkdir()
        assets_dir = root / "assets"
        assets_dir.mkdir(parents=True)
        (assets_dir / "image.png").write_text("png")
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[assets](../assets)\n"
        )
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, repo_path=root)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        msg = adapter.adapt(skill, skill)["LinkAdapter"]

        self.assertEqual(msg.params["count"], 1)
        content = (skill_dir / "SKILL.md").read_text()
        self.assertIn("[assets](./files/assets)", content)
        self.assertTrue((skill_dir / "files" / "assets" / "image.png").exists())

    def test_copies_os_file_to_files(self):
        # EN: An OS-absolute link to a file outside the repo is copied into files/.
        # RU: OS-абсолютная ссылка на файл вне репозитория копируется в files/.
        root = self.tmpdir / "os_file"
        root.mkdir()
        skill_dir = root / "skill"
        skill_dir.mkdir()
        external = self.tmpdir / "external.md"
        external.write_text("# External\n")
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: skill\n---\n# Skill\n[external]({external.as_posix()})\n"
        )
        skill = self._skill(skill_dir / "SKILL.md", skill_dir)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        msg = adapter.adapt(skill, skill)["LinkAdapter"]

        self.assertEqual(msg.params["count"], 1)
        content = (skill_dir / "SKILL.md").read_text()
        self.assertIn("[external](./files/external.md)", content)
        self.assertTrue((skill_dir / "files" / "external.md").exists())

    def test_copies_os_directory_to_files(self):
        # EN: An OS-absolute link to a directory outside the repo is copied into files/.
        # RU: OS-абсолютная ссылка на директорию вне репозитория копируется в files/.
        root = self.tmpdir / "os_dir"
        root.mkdir()
        skill_dir = root / "skill"
        skill_dir.mkdir()
        external_dir = self.tmpdir / "external-assets"
        external_dir.mkdir(parents=True)
        (external_dir / "image.png").write_text("png")
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: skill\n---\n# Skill\n[assets]({external_dir.as_posix()})\n"
        )
        skill = self._skill(skill_dir / "SKILL.md", skill_dir)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        msg = adapter.adapt(skill, skill)["LinkAdapter"]

        self.assertEqual(msg.params["count"], 1)
        content = (skill_dir / "SKILL.md").read_text()
        self.assertIn("[assets](./files/external-assets)", content)
        self.assertTrue((skill_dir / "files" / "external-assets" / "image.png").exists())

    def test_renames_colliding_external_file_names(self):
        # EN: Two external files with the same name get unique target names.
        # RU: Два внешних файла с одинаковым именем получают уникальные целевые имена.
        root = self.tmpdir / "collision"
        root.mkdir()
        skill_dir = root / "skill"
        skill_dir.mkdir()
        (root / "a" / "extra.md").parent.mkdir(parents=True)
        (root / "a" / "extra.md").write_text("# A\n")
        (root / "b" / "extra.md").parent.mkdir(parents=True)
        (root / "b" / "extra.md").write_text("# B\n")
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n"
            "[a](../a/extra.md)\n[b](../b/extra.md)\n"
        )
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, repo_path=root)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        msg = adapter.adapt(skill, skill)["LinkAdapter"]

        self.assertEqual(msg.params["count"], 2)
        content = (skill_dir / "SKILL.md").read_text()
        self.assertIn("[a](./files/extra_1.md)", content)
        self.assertIn("[b](./files/extra.md)", content)
        self.assertTrue((skill_dir / "files" / "extra.md").exists())
        self.assertTrue((skill_dir / "files" / "extra_1.md").exists())

    def test_copies_image_link_to_files(self):
        # EN: An image link to a file outside any skill is copied into files/.
        # RU: Ссылка на изображение вне любого скилла копируется в files/.
        root = self.tmpdir / "image"
        root.mkdir()
        skill_dir = root / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n![diagram](../diagram.png)\n"
        )
        (root / "diagram.png").write_text("png")
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, repo_path=root)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        msg = adapter.adapt(skill, skill)["LinkAdapter"]

        self.assertEqual(msg.params["count"], 1)
        content = (skill_dir / "SKILL.md").read_text()
        self.assertIn("![diagram](./files/diagram.png)", content)
        self.assertTrue((skill_dir / "files" / "diagram.png").exists())

    def test_rewrites_windows_separator_internal_link(self):
        # EN: A link authored with Windows backslashes inside a directory skill
        # must be rewritten the same way as a POSIX link.
        # RU: Ссылка с обратными слешами Windows внутри директорийного скилла
        # должна переписываться так же, как POSIX-ссылка.
        root = self.tmpdir / "windows_sep"
        root.mkdir()
        skill_dir = root / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[details](.\\details.md)\n"
        )
        (skill_dir / "details.md").write_text("# Details\n")
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, repo_path=root)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        adapter.adapt(skill, skill)

        content = (skill_dir / "SKILL.md").read_text()
        self.assertIn("[details](skill/details.md)", content)

    def test_rewrites_windows_separator_source_link(self):
        # EN: A link authored with Windows backslashes to a file outside any
        # skill must be copied into files/ and rewritten as a relative link.
        # RU: Ссылка с обратными слешами Windows на файл вне скилла должна
        # копироваться в files/ и переписываться относительной ссылкой.
        root = self.tmpdir / "windows_sep_source"
        root.mkdir()
        skill_dir = root / "skill"
        skill_dir.mkdir()
        (root / "extra.md").write_text("# Extra\n")
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[extra](.\\..\\extra.md)\n"
        )
        skill = self._skill(skill_dir / "SKILL.md", skill_dir, repo_path=root)

        adapter = Adapter(skills=[skill], adapter_list=[LinkAdapter])
        msg = adapter.adapt(skill, skill)["LinkAdapter"]

        self.assertEqual(msg.params["count"], 1)
        content = (skill_dir / "SKILL.md").read_text()
        self.assertIn("[extra](./files/extra.md)", content)
        self.assertTrue((skill_dir / "files" / "extra.md").exists())


if __name__ == "__main__":
    unittest.main()
