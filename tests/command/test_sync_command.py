"""Tests for the new SyncCommand orchestrator."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.command.sync_command import SyncCommand, SyncTarget
from ai_skill_manager.entities import LocalSource
from ai_skill_manager.functions.copy_skills.default_copy_skills import DefaultCopySkills


class TestSyncCommand(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.source_dir = self.tmp / "source"
        self.source_dir.mkdir()
        self.target_dir = self.tmp / "target"
        self.command = SyncCommand()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _dir_skill(self, name: str, content: str) -> Path:
        folder = self.source_dir / name
        folder.mkdir()
        (folder / "SKILL.md").write_text(content)
        return folder

    def _targets(self):
        return [SyncTarget(name="default", path=self.target_dir, copy_skills=DefaultCopySkills())]

    def test_copies_skills_and_rewrites_cross_skill_link(self):
        self._dir_skill("skill-a", "---\nname: skill-a\n---\n[b](../skill-b/SKILL.md)\n")
        self._dir_skill("skill-b", "---\nname: skill-b\n---\n# B\n")

        result = self.command.run(
            sources=[LocalSource(scan_path=self.source_dir)],
            targets=self._targets(),
            source_repo_path=self.source_dir,
            dry_run=False,
            add_relations=False,
        )

        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.skills), 2)
        content = (self.target_dir / "skill-a" / "SKILL.md").read_text()
        self.assertIn("[b](skill-b/SKILL.md)", content)

    def test_dry_run_does_not_touch_target(self):
        self._dir_skill("skill-a", "---\nname: skill-a\n---\n# A\n")

        result = self.command.run(
            sources=[LocalSource(scan_path=self.source_dir)],
            targets=self._targets(),
            source_repo_path=self.source_dir,
            dry_run=True,
            add_relations=False,
        )

        self.assertEqual(result.errors, [])
        self.assertFalse(self.target_dir.exists())

    def test_errors_block_copy_entirely(self):
        self._dir_skill("skill-a", "---\nname: skill-a\n---\n[bad](../nowhere.md)\n")

        result = self.command.run(
            sources=[LocalSource(scan_path=self.source_dir)],
            targets=self._targets(),
            source_repo_path=self.source_dir,
            dry_run=False,
            add_relations=False,
        )

        self.assertEqual(len(result.errors), 1)
        self.assertFalse(self.target_dir.exists())

    def test_collects_link_errors_from_multiple_files_without_stopping(self):
        # EN: A broken link in one file must not stop link discovery for the
        # skill's other files - this is SyncCommand's job now that file
        # discovery only finds files and LinkDiscovery only resolves one
        # file's links.
        # RU: Битая ссылка в одном файле не должна останавливать обнаружение
        # ссылок для остальных файлов скилла - это задача SyncCommand,
        # раз обнаружение файлов теперь только находит файлы, а LinkDiscovery
        # только разрешает ссылки одного файла.
        folder = self._dir_skill("skill-a", "---\nname: skill-a\n---\n[bad](../nowhere.md)\n")
        (folder / "notes.md").write_text("# Notes\n[also-bad](../also-nowhere.md)\n")

        result = self.command.run(
            sources=[LocalSource(scan_path=self.source_dir)],
            targets=self._targets(),
            source_repo_path=self.source_dir,
            dry_run=False,
            add_relations=False,
        )

        self.assertEqual(len(result.errors), 2)

    def test_add_relations_pulls_in_unconfigured_skill(self):
        # skill-a is the only configured source; skill-c lives elsewhere and
        # is only reachable via the link.
        self._dir_skill("skill-a", "---\nname: skill-a\n---\n[c](../../other/skill-c/SKILL.md)\n")
        other_dir = self.tmp / "other" / "skill-c"
        other_dir.mkdir(parents=True)
        (other_dir / "SKILL.md").write_text("---\nname: skill-c\n---\n# C\n")

        result = self.command.run(
            sources=[LocalSource(scan_path=self.source_dir)],
            targets=self._targets(),
            source_repo_path=self.tmp,
            dry_run=False,
            add_relations=True,
        )

        self.assertEqual(result.errors, [])
        self.assertEqual({s.name for s in result.skills}, {"skill-a", "skill-c"})
        self.assertTrue((self.target_dir / "skill-c" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
