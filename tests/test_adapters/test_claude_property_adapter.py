"""Tests for ClaudePropertyAdapter."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.adapters import Adapter
from ai_skill_manager.adapters.rules.claude_property_adapter import ClaudePropertyAdapter
from ai_skill_manager.entities import LocalSource, Skill, SkillFormat


class TestClaudePropertyAdapter(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill(self, content: str) -> Skill:
        md = self.tmpdir / "SKILL.md"
        md.write_text(content)
        return Skill(
            file_path=md,
            folder_path=None,
            source=LocalSource(scan_path=md.parent),
            format=SkillFormat.HumanFlat,
            source_path=md.parent,
        )

    def _adapt(self, skill: Skill):
        adapter = Adapter(skills=[skill], adapter_list=[ClaudePropertyAdapter])
        return adapter.adapt(skill, skill)["ClaudePropertyAdapter"]

    def test_renames_when_to_use_when_absent(self):
        skill = self._skill(
            "---\nname: guide\nwhenToUse: Use this when doing X\n---\n# Guide\n"
        )

        msg = self._adapt(skill)

        content = skill.file_path.read_text()
        self.assertEqual(msg.params["count"], 1)
        self.assertIn("when_to_use: Use this when doing X", content)
        self.assertNotIn("whenToUse", content)

    def test_joins_list_when_to_use_with_comma(self):
        skill = self._skill(
            "---\nname: guide\nwhenToUse:\n  - first case\n  - second case\n---\n# Guide\n"
        )

        self._adapt(skill)

        content = skill.file_path.read_text()
        self.assertIn("when_to_use: first case,second case", content)

    def test_warns_and_keeps_existing_when_to_use_on_conflict(self):
        skill = self._skill(
            "---\nname: guide\nwhenToUse: legacy value\nwhen_to_use: existing value\n---\n# Guide\n"
        )

        with self.assertLogs(
            "ai_skill_manager.adapters.rules.claude_property_adapter.claude_property_adapter",
            level="WARNING",
        ):
            msg = self._adapt(skill)

        content = skill.file_path.read_text()
        self.assertEqual(msg.params["count"], 1)
        self.assertIn("when_to_use: existing value", content)
        self.assertIn("whenToUse: legacy value", content)
        self.assertIn("## Metadata", content)

    def test_moves_unknown_fields_into_metadata_block(self):
        skill = self._skill(
            "---\nname: guide\ntags:\n  - workflow\n  - git\nmetadata:\n  domain: docs\n---\n# Guide\n"
        )

        msg = self._adapt(skill)

        content = skill.file_path.read_text()
        self.assertEqual(msg.params["count"], 2)
        self.assertNotIn("tags:", content.split("## Metadata")[0])
        self.assertIn("## Metadata", content)
        self.assertIn("tags:", content)
        self.assertIn("workflow", content)
        self.assertIn("domain: docs", content)

    def test_leaves_native_fields_untouched(self):
        skill = self._skill(
            "---\nname: guide\ndescription: A guide\nallowed-tools: Bash, Read\nmodel: opus\n---\n# Guide\n"
        )

        msg = self._adapt(skill)

        content = skill.file_path.read_text()
        self.assertEqual(msg.params["count"], 0)
        self.assertIn("allowed-tools: Bash, Read", content)
        self.assertIn("model: opus", content)
        self.assertNotIn("## Metadata", content)

    def test_noop_when_nothing_to_move(self):
        original = "---\nname: guide\ndescription: A guide\n---\n# Guide\n"
        skill = self._skill(original)
        mtime_before = skill.file_path.stat().st_mtime_ns

        msg = self._adapt(skill)

        self.assertEqual(msg.params["count"], 0)
        self.assertEqual(skill.file_path.read_text(), original)
        self.assertEqual(skill.file_path.stat().st_mtime_ns, mtime_before)


if __name__ == "__main__":
    unittest.main()
