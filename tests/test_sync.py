"""Tests for services/sync.py."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.services.sync import remove_orphans, run_sync
from ai_skill_manager.utils import tag_managed
from ai_skill_manager.validators import ValidationFailedError


class TestRunSync(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.source_dir = self.tmpdir / "source"
        self.source_dir.mkdir()
        self.target_dir = self.tmpdir / "target"

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _dir_skill(self, name: str):
        skill_dir = self.source_dir / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}\n")
        return skill_dir

    def test_rewrites_cross_skill_link(self):
        a = self._dir_skill("skill-a")
        b = self._dir_skill("skill-b")
        (a / "SKILL.md").write_text(
            "---\nname: skill-a\n---\n# A\n[link to b](../skill-b/SKILL.md)\n"
        )

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["skills_count"], 2)
        self.assertEqual(result["links_replaced"], 1)
        synced_a = (self.target_dir / "skill-a" / "SKILL.md").read_text()
        self.assertIn("[link to b](skill:skill-b)", synced_a)

    def test_rewrites_internal_link(self):
        skill = self._dir_skill("skill")
        (skill / "template.md").write_text("# Template\n")
        (skill / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[template](./template.md)\n"
        )

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["links_replaced"], 1)
        synced = (self.target_dir / "skill" / "SKILL.md").read_text()
        self.assertIn("[template](./template.md)", synced)

    def test_rewrites_wiki_link(self):
        a = self._dir_skill("skill-a")
        b = self._dir_skill("skill-b")
        (a / "SKILL.md").write_text(
            "---\nname: skill-a\n---\n# A\n[[../skill-b/SKILL.md|link to b]]\n"
        )

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["links_replaced"], 1)
        synced_a = (self.target_dir / "skill-a" / "SKILL.md").read_text()
        self.assertIn("[link to b](skill:skill-b)", synced_a)

    def test_skips_external_url(self):
        skill = self._dir_skill("skill")
        (skill / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[external](https://example.com)\n"
        )

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["links_replaced"], 0)
        synced = (self.target_dir / "skill" / "SKILL.md").read_text()
        self.assertIn("[external](https://example.com)", synced)

    def test_raises_on_invalid_link(self):
        skill = self._dir_skill("skill")
        (skill / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[bad](../nowhere.md)\n"
        )

        with self.assertRaises(ValidationFailedError):
            run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

    def test_handles_flat_skill(self):
        md = self.source_dir / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide\n")

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["skills_count"], 1)
        self.assertTrue((self.target_dir / "guide" / "SKILL.md").exists())

    def test_copies_non_markdown_files(self):
        skill = self._dir_skill("skill")
        (skill / "template.md").write_text("# Template\n")
        (skill / "data.json").write_text('{"key": "value"}\n')
        (skill / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[template](./template.md)\n"
        )

        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertTrue((self.target_dir / "skill" / "data.json").exists())
        self.assertEqual(
            (self.target_dir / "skill" / "data.json").read_text(),
            '{"key": "value"}\n',
        )

    def test_preserves_link_fragments(self):
        a = self._dir_skill("skill-a")
        b = self._dir_skill("skill-b")
        (a / "SKILL.md").write_text(
            "---\nname: skill-a\n---\n# A\n[link](../skill-b/SKILL.md#section)\n"
        )

        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        synced_a = (self.target_dir / "skill-a" / "SKILL.md").read_text()
        self.assertIn("[link](skill:skill-b#section)", synced_a)


class TestRemoveOrphans(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.target_dir = self.tmpdir / "target"
        self.target_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill(self, name: str) -> Skill:
        skill_dir = self.target_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            skill_file.write_text(f"---\nname: {name}\n---\n# {name}\n")
        return Skill(
            file_path=skill_file,
            folder_path=skill_dir,
            source_path=self.target_dir,
            source=LocalSource(scan_path=self.target_dir),
            format=SkillFormat.Agent,
        )

    def test_removes_managed_orphan_skill(self):
        orphan = self.target_dir / "orphan"
        orphan.mkdir()
        tag_managed(orphan)

        kept = self._skill("kept")

        removed = remove_orphans(self.target_dir, [kept])

        self.assertFalse(orphan.exists())
        self.assertTrue(kept.folder_path.exists())
        self.assertEqual(removed, [orphan])

    def test_keeps_unmanaged_directories(self):
        unmanaged = self.target_dir / "unmanaged"
        unmanaged.mkdir()

        kept = self._skill("kept")

        remove_orphans(self.target_dir, [kept])

        self.assertTrue(unmanaged.exists())
        self.assertTrue(kept.folder_path.exists())

    def test_keeps_copied_managed_skill(self):
        skill = self._skill("skill")
        tag_managed(skill.folder_path)

        remove_orphans(self.target_dir, [skill])

        self.assertTrue(skill.folder_path.exists())
